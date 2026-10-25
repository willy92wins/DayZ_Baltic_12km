#!/usr/bin/env python3
"""Independent ESRI ASCII Grid Validator for DayZ terrain pipeline."""
import argparse
import json
import math
from pathlib import Path
import sys
import numpy as np

REQUIRED_HDRS = {"ncols", "nrows", "cellsize", "nodata_value"}
ORIGIN_KEYS = {"xllcorner", "yllcorner", "xllcenter", "yllcenter"}


def parse_header(lines):
    raw, errors = {}, []
    for i, line in enumerate(lines, start=1):
        parts = line.strip().split()
        if len(parts) != 2:
            errors.append(f"Header line {i} malformed: expected 2 tokens, got {len(parts)}")
            continue
        k, v = parts[0].lower(), parts[1]
        if k in raw:
            errors.append(f"Duplicate header key '{k}' at line {i}")
        raw[k] = v

    unknown = set(raw.keys()) - (REQUIRED_HDRS | ORIGIN_KEYS)
    if unknown:
        errors.append(f"Unknown header key(s): {sorted(list(unknown))}")

    for req in REQUIRED_HDRS:
        if req not in raw:
            errors.append(f"Missing required header key: '{req}'")

    for axis in ("x", "y"):
        corner, center = f"{axis}llcorner", f"{axis}llcenter"
        if corner in raw and center in raw:
            errors.append(f"Conflicting {axis} origin: both {corner} and {center} present")
        elif corner not in raw and center not in raw:
            errors.append(f"Missing {axis} origin header: need {corner} or {center}")

    if errors:
        return None, errors

    header = {}
    try:
        header["ncols"] = int(raw["ncols"])
        header["nrows"] = int(raw["nrows"])
        if header["ncols"] <= 0 or header["nrows"] <= 0:
            errors.append("ncols and nrows must be positive integers")
    except ValueError:
        errors.append("ncols and nrows must be valid integers")

    try:
        header["cellsize"] = float(raw["cellsize"])
        if not math.isfinite(header["cellsize"]) or header["cellsize"] <= 0:
            errors.append("cellsize must be finite positive float")
    except ValueError:
        errors.append("cellsize must be valid float")

    try:
        header["nodata_value"] = float(raw["nodata_value"])
        if not math.isfinite(header["nodata_value"]):
            errors.append("nodata_value must be finite float")
    except ValueError:
        errors.append("nodata_value must be valid float")

    cs = header.get("cellsize", 0.0)
    for axis in ("x", "y"):
        corner, center = f"{axis}llcorner", f"{axis}llcenter"
        try:
            if corner in raw:
                val = float(raw[corner])
            else:
                val = float(raw[center]) - 0.5 * cs
            if not math.isfinite(val):
                errors.append(f"{corner} resolved to non-finite value")
            header[corner] = val
        except ValueError:
            errors.append(f"Invalid float for {axis} origin")

    return header, errors


def validate_against_spec(hdr, spec):
    errors, checks = [], {}
    tols = spec.get("tolerances", {})
    cs_tol = tols.get("cellsize", spec.get("cellsize_tolerance", 1e-4))
    orig_tol = tols.get("origin", spec.get("origin_tolerance", min(1e-3, 0.001 * hdr.get("cellsize", 1.0))))

    if hdr.get("ncols") != spec.get("ncols"):
        errors.append(f"ncols mismatch: got {hdr.get('ncols')}, expected {spec.get('ncols')}")
    if hdr.get("nrows") != spec.get("nrows"):
        errors.append(f"nrows mismatch: got {hdr.get('nrows')}, expected {spec.get('nrows')}")
    checks["dimensions"] = "FAIL" if errors else "PASS"

    dim_err_len = len(errors)
    if abs(hdr.get("cellsize", 0.0) - spec.get("cellsize", 0.0)) > cs_tol:
        errors.append(f"cellsize mismatch: got {hdr.get('cellsize')}, expected {spec.get('cellsize')} (tol {cs_tol})")
    for k in ("xllcorner", "yllcorner"):
        if k in spec:
            actual = hdr.get(k, 0.0)
            if abs(actual - float(spec[k])) > orig_tol:
                errors.append(f"{k} mismatch: got {actual}, expected {spec[k]} (tol {orig_tol})")
    checks["headers"] = "FAIL" if len(errors) > dim_err_len else "PASS"
    return checks, errors


def validate_grid_data(filepath, hdr, spec):
    errors, checks = [], {}
    nrows, ncols = hdr["nrows"], hdr["ncols"]
    nd_val = hdr["nodata_value"]
    grid = np.empty((nrows, ncols), dtype=np.float64)
    min_z, max_z = float("inf"), float("-inf")
    non_finite_cnt, nodata_cnt = 0, 0

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for _ in range(6):
            f.readline()

        for r in range(nrows):
            line = f.readline()
            if not line:
                errors.append(f"Premature EOF: expected {nrows} rows, stopped at row {r}")
                return None, min_z, max_z, checks, errors
            toks = line.strip().split()
            if len(toks) != ncols:
                errors.append(f"Row {r} width mismatch: expected {ncols} samples, got {len(toks)}")
                return None, min_z, max_z, checks, errors
            try:
                row_vals = np.array(toks, dtype=np.float64)
            except ValueError as e:
                errors.append(f"Row {r} parse failure: {e}")
                return None, min_z, max_z, checks, errors

            nf = ~np.isfinite(row_vals)
            if np.any(nf):
                non_finite_cnt += int(np.sum(nf))
            nd = row_vals == nd_val
            if np.any(nd):
                nodata_cnt += int(np.sum(nd))

            grid[r, :] = row_vals
            finite_vals = row_vals[~nf]
            if finite_vals.size > 0:
                r_min, r_max = float(np.min(finite_vals)), float(np.max(finite_vals))
                if r_min < min_z: min_z = r_min
                if r_max > max_z: max_z = r_max

        extra_lines = sum(1 for line in f if line.strip())
        if extra_lines > 0:
            errors.append(f"Trailing data: found {extra_lines} extra non-empty lines after {nrows} rows")

    if non_finite_cnt > 0:
        errors.append(f"Found {non_finite_cnt} non-finite (NaN/Inf) elevation values")
    if nodata_cnt > 0:
        errors.append(f"Found {nodata_cnt} declared NoData values in terrain grid")
    checks["finite_and_nodata"] = "FAIL" if (non_finite_cnt or nodata_cnt) else "PASS"

    h_tol = spec.get("tolerances", {}).get("height", spec.get("height_tolerance", 1e-3))
    b_err = False
    if "height_min" in spec and min_z < (spec["height_min"] - h_tol):
        errors.append(f"Min elevation {min_z} below spec height_min {spec['height_min']}")
        b_err = True
    if "height_max" in spec and max_z > (spec["height_max"] + h_tol):
        errors.append(f"Max elevation {max_z} exceeds spec height_max {spec['height_max']}")
        b_err = True
    checks["height_bounds"] = "FAIL" if b_err else "PASS"

    return grid, min_z, max_z, checks, errors


def check_controls(grid, spec):
    controls = spec.get("controls")
    if controls is None:
        return "NOT_VERIFIED", "SKIPPED", []
    if not isinstance(controls, list):
        return "FAILED", "FAIL", ["'controls' in spec must be a list"]
    if len(controls) == 0:
        return "NOT_VERIFIED", "SKIPPED", []

    errors = []
    nrows, ncols = grid.shape
    for ctrl in controls:
        name = ctrl.get("name", "unnamed")
        r, c = ctrl.get("row"), ctrl.get("col")
        exp_z = ctrl.get("expected_z")
        tol = ctrl.get("tolerance", 0.05)
        if r is None or c is None or exp_z is None:
            errors.append(f"Control '{name}' missing required row, col, or expected_z")
            continue
        if not (isinstance(r, int) and isinstance(c, int) and 0 <= r < nrows and 0 <= c < ncols):
            errors.append(f"Control '{name}' coords ({r}, {c}) out of bounds ({nrows}x{ncols})")
            continue
        if not math.isfinite(float(exp_z)) or not math.isfinite(float(tol)) or float(tol) < 0:
            errors.append(f"Control '{name}' has invalid expected_z/tolerance")
            continue
        actual_z = float(grid[r, c])
        if abs(actual_z - float(exp_z)) > float(tol):
            errors.append(f"Control '{name}' at ({r},{c}) z={actual_z:.3f}, expected {exp_z} (tol {tol})")

    status = "FAILED" if errors else "CONTROL_SAMPLES_MATCH"
    check = "FAIL" if errors else "PASS"
    return status, check, errors


def write_report(path, report):
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, allow_nan=False)
    except Exception as e:
        sys.stderr.write(f"Failed to write report to {path}: {e}\n")
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description="ESRI ASCII Grid Validator")
    parser.add_argument("file", help="Path to ESRI ASCII grid file")
    parser.add_argument("--spec", required=True, help="Path to spec JSON or JSON string")
    parser.add_argument("--report", required=True, help="Path to write report JSON")
    args = parser.parse_args()

    report = {"status": "FAIL", "errors": [], "checks": {}, "geometric_orientation": "NOT_VERIFIED", "summary": {}}

    try:
        spec_p = Path(args.spec)
        if spec_p.is_file():
            with open(spec_p, "r", encoding="utf-8") as f:
                spec = json.load(f)
        else:
            spec = json.loads(args.spec)

        for req in ("ncols", "nrows", "cellsize", "xllcorner", "yllcorner"):
            if req not in spec:
                raise ValueError(f"Spec missing required field: '{req}'")
            if not math.isfinite(float(spec[req])):
                raise ValueError(f"Spec field is non-finite: '{req}'")
        for req in ("ncols", "nrows"):
            if type(spec[req]) is not int or not 0 < spec[req] <= 16384:
                raise ValueError(f"Spec field requires an integer in 1..16384: '{req}'")
        if spec['cellsize'] <= 0:
            raise ValueError('Spec cellsize must be positive')
        for key, value in spec.get('tolerances', {}).items():
            if not math.isfinite(float(value)) or float(value) < 0:
                raise ValueError(f'Invalid tolerance: {key}')
        for key in ('height_min', 'height_max', 'origin_tolerance', 'cellsize_tolerance', 'height_tolerance'):
            if key in spec and not math.isfinite(float(spec[key])):
                raise ValueError(f'Invalid spec value: {key}')

        grid_p = Path(args.file)
        if not grid_p.is_file():
            raise FileNotFoundError(f"Input grid file not found: {args.file}")

        header_lines = []
        with open(grid_p, "r", encoding="utf-8", errors="replace") as f:
            for _ in range(6):
                line = f.readline()
                if not line: break
                header_lines.append(line)

        if len(header_lines) < 6:
            raise ValueError(f"File has only {len(header_lines)} lines; expected 6-line header")

        hdr, hdr_errors = parse_header(header_lines)
        if hdr_errors:
            report["errors"].extend(hdr_errors)
            report["checks"]["header_syntax"] = "FAIL"
            write_report(args.report, report)
            sys.exit(1)
        report["checks"]["header_syntax"] = "PASS"

        spec_checks, spec_errors = validate_against_spec(hdr, spec)
        report["checks"].update(spec_checks)
        report["errors"].extend(spec_errors)
        if spec_errors:
            write_report(args.report, report)
            sys.exit(1)

        grid, min_z, max_z, grid_checks, grid_errors = validate_grid_data(grid_p, hdr, spec)
        report["checks"].update(grid_checks)
        report["errors"].extend(grid_errors)

        if grid is not None:
            orient_stat, ctrl_check, ctrl_errors = check_controls(grid, spec)
            report["geometric_orientation"] = orient_stat
            report["checks"]["controls"] = ctrl_check
            report["errors"].extend(ctrl_errors)
            report["summary"] = {
                "ncols": hdr["ncols"], "nrows": hdr["nrows"], "cellsize": hdr["cellsize"],
                "xllcorner": hdr["xllcorner"], "yllcorner": hdr["yllcorner"],
                "nodata_value": hdr["nodata_value"],
                "min_z": min_z if math.isfinite(min_z) else None,
                "max_z": max_z if math.isfinite(max_z) else None
            }

        if not report["errors"]:
            report["status"] = "PASS"

    except Exception as exc:
        report["status"] = "FAIL"
        report["errors"].append(f"Execution error: {type(exc).__name__}: {exc}")

    write_report(args.report, report)
    sys.exit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
