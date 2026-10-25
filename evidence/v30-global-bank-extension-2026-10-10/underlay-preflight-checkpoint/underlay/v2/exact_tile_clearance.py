"""Exact piecewise-affine clearance bound for the one-cell factor-32 ROI tile."""
import hashlib
import json
from pathlib import Path

import numpy as np


BASE = Path(r"E:\DayZ-Baltic-Build\v30-mixed-bank-incremental-fixed-20261010\candidate\terrain.npz")
P_PATH = Path(r"E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\build-focal\candidate\plane.npy")
F_PATH = Path(r"E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\build-focal\candidate\visible-field.npy")
OUT = Path(__file__).with_name("exact-clearance.json")

# The V4 gray-patch sub-ROI x=918..1012,y=465..500 projects inside one
# factor-32 cell under the existing EV73/EV74 transferred pose. The cell bounds
# are half-open and deliberately exceed the projected sub-ROI.
R0, C0, R1, C1 = 864, 384, 896, 416
FACTORS = (1, 2, 4, 8, 16, 32)
TRIANGLES = (((0, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (1, 1)))
CORNER_INDEX = {(0, 0): 0, (0, 1): 1, (1, 0): 2, (1, 1): 3}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    with np.load(BASE) as archive:
        h_native_f32 = archive["heights"].astype(np.float32)
    h_native = h_native_f32.astype(np.float64)
    p_plane = np.load(P_PATH).astype(np.float64)
    # Stored per native cell in [NW, NE, SW, SE] order.
    f_corners = np.load(F_PATH).astype(np.float64)
    if h_native.shape != (2048, 2048) or p_plane.shape != (2047, 2047) or f_corners.shape != (2047, 2047, 4):
        raise ValueError("Unexpected frozen terrain/P/F array shape")

    h_diag_f32 = h_native_f32.copy()
    source_tile = h_native_f32[R0:R1 + 1, C0:C1 + 1]
    h_diag_f32[R0:R1 + 1, C0:C1 + 1] = (source_tile.astype(np.float64) - 6.10).astype(np.float32)
    actual_vertex_drop = source_tile.astype(np.float64) - h_diag_f32[R0:R1 + 1, C0:C1 + 1].astype(np.float64)

    def coarse_surface_at_native_vertices(factor: int, height_grid: np.ndarray) -> np.ndarray:
        """Evaluate the factor mesh on all native vertices in the audited tile."""
        rows = np.arange(R0, R1 + 1)
        cols = np.arange(C0, C1 + 1)
        out = np.empty((rows.size, cols.size), dtype=np.float64)
        for ir, row in enumerate(rows):
            r_nw = (row // factor) * factor
            r_se = r_nw + factor
            v = (row - r_nw) / factor
            for ic, col in enumerate(cols):
                c_nw = (col // factor) * factor
                c_ne = c_nw + factor
                u = (col - c_nw) / factor
                nw, ne = height_grid[r_nw, c_nw], height_grid[r_nw, c_ne]
                sw, se = height_grid[r_se, c_nw], height_grid[r_se, c_ne]
                # Same NW-SE diagonal as the native mesh and F.
                if v <= u:
                    out[ir, ic] = (1 - u) * nw + (u - v) * ne + v * se
                else:
                    out[ir, ic] = (1 - v) * nw + (v - u) * sw + u * se
        return out

    def evaluate_grid(height_grid: np.ndarray) -> list[dict]:
        rows = []
        for factor in FACTORS:
            hc = coarse_surface_at_native_vertices(factor, height_grid.astype(np.float64))
            if factor == 1 and not np.array_equal(hc, height_grid[R0:R1 + 1, C0:C1 + 1].astype(np.float64)):
                raise AssertionError("Factor-1 fixture failed: native surface must be identical")
            p_max = (-np.inf, None)
            f_max = (-np.inf, None)
            finite_p_cells = 0
            finite_f_triangle_vertices = 0
            for row in range(R0, R1):
                for col in range(C0, C1):
                    p = p_plane[row, col]
                    if np.isfinite(p):
                        finite_p_cells += 1
                        for dr, dc in ((0, 0), (0, 1), (1, 0), (1, 1)):
                            excess = hc[row - R0 + dr, col - C0 + dc] - p
                            if excess > p_max[0]:
                                p_max = (float(excess), [row, col, row + dr, col + dc, float(p)])
                    for tri_name, tri in zip(("NW_NE_SE", "NW_SW_SE"), TRIANGLES):
                        ys = [f_corners[row, col, CORNER_INDEX[(dr, dc)]] for dr, dc in tri]
                        if all(np.isfinite(y) for y in ys):
                            for (dr, dc), y in zip(tri, ys):
                                finite_f_triangle_vertices += 1
                                excess = hc[row - R0 + dr, col - C0 + dc] - y
                                if excess > f_max[0]:
                                    f_max = (float(excess), [row, col, tri_name, row + dr, col + dc, [float(v) for v in ys]])
            rows.append({
                "factor": factor,
                "spacing_m": 6 * factor,
                "max_h_minus_P_m": p_max[0],
                "max_P_witness": p_max[1],
                "finite_P_cells": finite_p_cells,
                "max_h_minus_F_m": f_max[0],
                "max_F_witness": f_max[1],
                "finite_F_triangle_vertex_comparisons": finite_f_triangle_vertices,
            })
        return rows

    rows = evaluate_grid(h_native_f32)
    diag_rows = evaluate_grid(h_diag_f32)

    max_excess = max(max(row["max_h_minus_P_m"], row["max_h_minus_F_m"]) for row in rows)
    chosen_drop = 6.10
    report = {
        "status": "EXACT_PIECEWISE_AFFINE_CLEARANCE_BOUND_FOR_DIAGNOSTIC_TILES",
        "sources": {str(path): sha256(path) for path in (BASE, P_PATH, F_PATH)},
        "world_grid": {"native_spacing_m": 6, "x": "6*c", "z": "12282-6*r", "diagonal": "NW-SE"},
        "target": {
            "screen_roi_pixels_half_open": [918, 465, 1012, 500],
            "transfer_source": "EV73 image + EV74/EV76 pose/FOV transfer; not per-frame V4 calibrated",
            "factor32_rows": [R0, R1],
            "factor32_cols": [C0, C1],
            "world_xz_bounds_m": [C0 * 6, C1 * 6, 12282 - R1 * 6, 12282 - R0 * 6],
            "meaning": "one 192 m factor-32 cell; all nested factor grids use vertices inside these aligned bounds",
        },
        "method": {
            "surface_evaluation": "piecewise-affine barycentric interpolation on nested factor grids, all sharing native NW-SE diagonal",
            "P": "per-cell constant; max(Hfactor-P) occurs at a native-triangle vertex",
            "F": "per-cell NW_NE_SE and NW_SW_SE affine triangles; max(Hfactor-F) occurs at overlay vertices; the coarse and native/F diagonals coincide inside each native cell",
            "coverage": "all finite P cells and all finite F triangles in the full one-cell tile; no point sampling",
            "counts": "one row per factor, with finite-cell/triangle comparison counts and witnesses",
        },
        "factors": rows,
        "post_float32_diagnostic_factors": diag_rows,
        "bound": {
            "max_excess_over_P_or_F_m": max_excess,
            "selected_uniform_drop_m": chosen_drop,
            "minimum_nominal_clearance_after_drop_m": chosen_drop - max_excess,
            "actual_float32_vertex_drop_m": {"min": float(np.min(actual_vertex_drop)), "max": float(np.max(actual_vertex_drop))},
            "post_float32_max_H_minus_P_or_F_m": max(max(row["max_h_minus_P_m"], row["max_h_minus_F_m"]) for row in diag_rows),
            "interpretation": "the ideal uniform drop is 6.10 m; the report also recomputes every factor after storing heights as float32, so quantization is included",
        },
        "limits": [
            "This bounds geometry relative to the pinned nominal P and F fields; it is not a bound on animated/fake waves or the engine's selected LOD.",
            "The transferred screen ROI is approximate because V4 did not store per-capture camera/FOV readback; the one-cell rectangular coverage is intentionally larger than that projected ROI.",
            "It is a diagnostic-only deformation that changes terrain and shore geometry over 192 x 384 m; it is not a production terrain proposal.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["bound"], indent=2))


if __name__ == "__main__":
    main()

