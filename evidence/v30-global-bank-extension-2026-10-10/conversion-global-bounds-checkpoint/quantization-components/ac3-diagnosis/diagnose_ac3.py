from __future__ import annotations

from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np

HERE = Path(__file__).resolve().parent
CONSUMER = HERE.parent
CONVERTER = CONSUMER / "convert_components.py"
PLAN = CONSUMER / "PLAN.md"
TESTS = CONSUMER / "test_components.py"
RECEIPT = CONSUMER / "real-conversion-01/receipt.json"
EXECUTOR = CONSUMER.parent / "float32-neighborhood-v1/executor.py"
COMPAT = CONSUMER.parent / "float32-neighborhood-v1/real-enumeration-01/compatibility-diagnostic.json"
OUT_JSON = HERE / "certificate.json"
OUT_MD = HERE / "certificate.md"

EXPECTED = {
    CONVERTER: "418016b91cfd84d60eb3f95c99cc043eea164de1afa2548f665d68d616aec876",
    PLAN: "82da5f4a14abd749a8bd59fd865dffca05dbf4be67df29df58cce105aed2899c",
    TESTS: "81062389833baac05c1b3d58265c140b16bca3569a8b71f833e49e5ed51f0a80",
    EXECUTOR: "9a0dbffc55e9956209083fe4963e2636b6f0174de1dc150bdfa15f070d48149e",
    COMPAT: "0cb852c2aa3bdd99e7b1dbdfb079df5f9faa65c3db854a3ff1389b25d8b53da7",
    RECEIPT: "53bd39ddf07e4ffac35a3de7ebdd045970d331ff2f071d2b33a61bf9f61707fb",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha_map(paths):
    return {str(Path(path).resolve()): sha256(Path(path)) for path in paths}


def load_module():
    if sha256(CONVERTER) != EXPECTED[CONVERTER]:
        raise RuntimeError("converter source pin changed")
    spec = importlib.util.spec_from_file_location("wet_bank_component_converter_diagnostic", CONVERTER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load pinned converter module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def exact_t(spec, ha, hb):
    da = Fraction.from_float(float(np.float32(ha))) - spec.level_a
    db = Fraction.from_float(float(np.float32(hb))) - spec.level_b
    if da * db >= 0:
        return None
    tab = da / (da - db)
    return tab if spec.dry_endpoint == 0 else 1 - tab


def main():
    if OUT_JSON.exists() or OUT_MD.exists():
        raise RuntimeError("diagnostic outputs must be fresh")
    for path, wanted in EXPECTED.items():
        if sha256(path) != wanted:
            raise RuntimeError(f"input pin mismatch: {path}")
    # Pin the readset before importing the executor and constructing any tables.
    # This is a diagnostic read only; end hashes must match these exact bytes.
    preliminary_module = load_module()
    local_inputs = [CONVERTER, PLAN, TESTS, COMPAT, *preliminary_module.load_executor().source_paths()]
    readset_start = sha_map(local_inputs)
    for path, wanted in EXPECTED.items():
        if path != RECEIPT and readset_start.get(str(path.resolve())) != wanted:
            raise RuntimeError(f"input pin mismatch in diagnostic readset: {path}")
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if receipt.get("status") != "NO_FEASIBLE_AC3" or not receipt.get("source_readset_equal"):
        raise RuntimeError("the preserved conversion receipt is not the expected AC-3 terminal")

    cc = preliminary_module
    capture = {}
    original_propagate = cc.propagate
    original_build = cc.build_problem

    def capture_propagate(domains, relations, subset=None):
        capture["initial_domains"] = dict(domains)
        result = original_propagate(domains, relations, subset)
        capture["relations"] = relations
        capture["final_domains"] = dict(result[0])
        capture["contradiction"] = result[1]
        return result

    def capture_build(executor, data, deadline=None):
        capture["executor"] = executor
        capture["data"] = data
        return original_build(executor, data, deadline)

    cc.propagate = capture_propagate
    cc.build_problem = capture_build
    caught = None
    try:
        cc._load_real_problem(time.monotonic() + 100.0)
    except cc.ConversionStop as exc:
        caught = {"status": exc.status, "message": str(exc)}
    finally:
        cc.propagate = original_propagate
        cc.build_problem = original_build

    if caught is None or caught["status"] != "NO_FEASIBLE_AC3":
        raise RuntimeError(f"expected exact AC-3 infeasibility, got {caught}")

    data = capture["data"]
    executor = capture["executor"]
    relations = capture["relations"]
    trace = capture["contradiction"]["trace"]
    vars_rc = np.asarray(data["vars_rc"], dtype=np.int32)
    focus_rc = (864, 1187)
    focus_hits = np.flatnonzero(np.all(vars_rc == np.asarray(focus_rc, dtype=np.int32), axis=1))
    if len(focus_hits) != 1 or int(focus_hits[0]) != 83:
        raise RuntimeError("focus variable identity changed")
    focus = int(focus_hits[0])
    options = executor.build_neighbor_options(data["raw_x"], data["lo"], data["hi"])
    domain_start = dict(capture["initial_domains"])
    replay = dict(domain_start)
    replay_events = []
    for sequence, event in enumerate(trace):
        rel = relations[int(event["relation"])]
        xi, xj = int(event["variable"]), int(event["against"])
        support_domain = cc.bit_options(replay[xj])
        removed = tuple(int(v) for v in event["removed_options"])
        unsupported = {
            int(ox): [int(oy) for oy in support_domain
                      if not cc.relation_allows(rel, xi, int(ox), xj, int(oy))]
            for ox in removed
        }
        if any(not values for values in unsupported.values()):
            raise RuntimeError(f"trace event {sequence} removes a supported option")
        replay[xi] = cc.mask_of(event["remaining"])
        replay_events.append({
            "sequence": sequence,
            "variable_index": xi,
            "variable_rc": list(map(int, vars_rc[xi])),
            "against_index": xj,
            "against_rc": list(map(int, vars_rc[xj])),
            "relation_index": int(event["relation"]),
            "relation_kind": rel.kind,
            "relation_source": rel.source,
            "relation_endpoints_rc": [list(map(int, rc)) for rc in rel.endpoints_rc],
            "removed_options": list(removed),
            "against_domain_options_at_step": list(support_domain),
            "unsupported_by_against_options": unsupported,
            "remaining_options": list(event["remaining"]),
        })
    if replay != capture["final_domains"] or replay[focus] != 0:
        raise RuntimeError("AC-3 trace replay did not reproduce production domain state")

    focus_rows = []
    decimal_by_source = {}
    for source in ("crossing:76", "crossing:80"):
        matches = [(rid, rel) for rid, rel in enumerate(relations) if rel.source == source]
        if len(matches) != 1:
            raise RuntimeError(f"expected one production relation {source}")
        rid, rel = matches[0]
        focus_position = 0 if rel.a == focus else 1 if rel.b == focus else None
        if focus_position is None:
            raise RuntimeError(f"{source} does not constrain focus")
        supported_focus = sorted({pair[focus_position] for a in range(3) for b in range(3)
                                  if rel.table[a][b] for pair in [(a, b)]})
        crossing_index = int(source.split(":")[1])
        spec = data["cross_specs"][crossing_index]
        endpoint_to_var = {
            tuple(map(int, spec.edge_rc[0])): int(rel.a),
            tuple(map(int, spec.edge_rc[1])): int(rel.b),
        }
        if tuple(map(int, rel.endpoints_rc[0])) != tuple(map(int, spec.edge_rc[0])) or \
                tuple(map(int, rel.endpoints_rc[1])) != tuple(map(int, spec.edge_rc[1])):
            raise RuntimeError("production relation endpoint order differs from crossing spec")
        direct_table = []
        t_table = []
        for oa in range(3):
            direct_row = []
            t_row = []
            for ob in range(3):
                grid = data["closed"].copy()
                grid[spec.local_a] = options[rel.a][oa]
                grid[spec.local_b] = options[rel.b][ob]
                direct = bool(executor.direct_crossings_pass(grid, (spec,)))
                t_value = exact_t(spec, options[rel.a][oa], options[rel.b][ob])
                scalar = bool(t_value is not None and spec.t_lower <= t_value <= spec.t_upper)
                if direct != scalar or direct != bool(rel.table[oa][ob]):
                    raise RuntimeError(f"crossing table mismatch at {source} option pair {(oa, ob)}")
                direct_row.append(direct)
                t_row.append(None if t_value is None else float(t_value))
            direct_table.append(direct_row)
            t_table.append(t_row)
        levels = [float(spec.level_a), float(spec.level_b)]
        width = float(spec.t_upper - spec.t_lower)
        focus_rows.append({
            "source": source,
            "relation_index": rid,
            "surface": spec.surface,
            "cell_rc": list(spec.cell_rc),
            "edge_rc": [list(rc) for rc in spec.edge_rc],
            "endpoint_variable_indices": [int(rel.a), int(rel.b)],
            "endpoint_variable_rc": [list(map(int, vars_rc[rel.a])), list(map(int, vars_rc[rel.b]))],
            "focus_endpoint_position": focus_position,
            "level_endpoints_m": levels,
            "t_interval_exact": [str(spec.t_lower), str(spec.t_upper)],
            "t_interval_decimal": [float(spec.t_lower), float(spec.t_upper)],
            "t_width_fraction": width,
            "width_along_6m_edge_m": 6.0 * width,
            "dry_endpoint": int(spec.dry_endpoint),
            "direct_supported_pairs_option_indices": [[a, b] for a in range(3) for b in range(3) if direct_table[a][b]],
            "focus_supported_option_indices": supported_focus,
            "all_direct_fraction_tables_agree": True,
            "t_values_by_option_pair": t_table,
        })
        decimal_by_source[source] = (spec, rel)

    focus_option_values = [float(x) for x in options[focus]]
    if focus_rows[0]["source"] != "crossing:76" or focus_rows[1]["source"] != "crossing:80":
        raise RuntimeError("crossing output order changed")
    forced = set(focus_rows[0]["focus_supported_option_indices"])
    permitted = set(focus_rows[1]["focus_supported_option_indices"])
    if forced != {2} or permitted != {0, 1} or forced & permitted:
        raise RuntimeError("the expected two-crossing option contradiction was not reproduced")

    source_end = sha_map(local_inputs)
    expected_input_hashes = {str(path.resolve()): wanted for path, wanted in EXPECTED.items() if path != RECEIPT}
    for path, wanted in expected_input_hashes.items():
        if source_end.get(path) != wanted:
            raise RuntimeError(f"source drift after AC-3 diagnostic: {path}")
    if source_end != readset_start:
        raise RuntimeError("readset changed during AC-3 diagnostic")

    report = {
        "schema": "ev94.wet-bank-f32-ac3-conflict-certificate.v1",
        "status": "CERTIFIED_NO_ASSIGNMENT_WITHIN_MINUS_ONE_ZERO_PLUS_ONE_ULP",
        "conversion_or_search_executed": False,
        "pinned_conversion_receipt": {"path": str(RECEIPT.resolve()), "sha256": sha256(RECEIPT),
                                       "status": receipt["status"], "elapsed_seconds": receipt["elapsed_seconds"],
                                       "peak_working_set_bytes": receipt["peak_working_set_bytes"],
                                       "source_readset_equal": receipt["source_readset_equal"]},
        "diagnostic_exception": caught,
        "focus": {"variable_index": focus, "rc": list(focus_rc), "raw_float32_m": float(data["raw_x"][focus]),
                  "three_options_order_minus1_raw_plus1_m": focus_option_values,
                  "initial_unary_domain_options": list(cc.bit_options(domain_start[focus])),
                  "final_ac3_domain_options": list(cc.bit_options(capture["final_domains"][focus]))},
        "two_relation_certificate": {
            "crossing_76_forces_focus_plus_one": True,
            "crossing_80_excludes_focus_plus_one": True,
            "intersection_of_supported_focus_options": [],
            "no_endpoint_neighbor_option_in_current_domain_changes_these_sets": True,
            "records": focus_rows,
        },
        "ac3_trace_event_count": len(replay_events),
        "ac3_trace_replay_matches_production": True,
        "ac3_trace": replay_events,
        "source_readset_start": readset_start,
        "source_readset_end": source_end,
        "source_readset_equal": readset_start == source_end,
        "interpretation": {
            "finding": "Exact crossing-interval tables disagree on the shared focus value: crossing 76 requires its +1 ULP choice, while crossing 80 forbids that choice for every ±1 endpoint combination.",
            "not_established": "This does not determine whether a larger, mathematically derived representable neighborhood is feasible; it proves only infeasibility of the frozen three-value domain. No ±2 or other widened domain was tested.",
            "interval_scale": "The t intervals are not zero-width; the raw crossings sit within roughly micrometre-scale edge distance of active interval boundaries. Their ULP directions conflict at the shared vertex.",
        },
        "diagnostic_script_sha256": sha256(Path(__file__)),
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    md = [
        "# Certificado AC-3 para la conversión float32",
        "",
        "**Resultado:** no existe asignación dentro de las tres opciones de cada variable (−1 ULP, raw, +1 ULP). No se ejecutó búsqueda ni conversión.",
        "",
        f"En el foco `{focus_rc}`, crossing 76 permite para el foco solo la opción `+1`; crossing 80 permite solo `−1/raw`. Las tablas directas del ejecutor y las fracciones exactas coinciden en los nueve pares de cada cruce. El conflicto no depende de qué opción vecina se elija dentro de ±1.",
        "",
        f"Crossing 76 tiene ancho t {focus_rows[0]['t_width_fraction']:.8f} (≈{focus_rows[0]['width_along_6m_edge_m']:.6f} m en una arista de 6 m); crossing 80, {focus_rows[1]['t_width_fraction']:.8f} (≈{focus_rows[1]['width_along_6m_edge_m']:.6f} m). La evidencia apunta a posiciones raw cercanas a límites de intervalo y direcciones ULP incompatibles, no a un intervalo de ancho cero.",
        "",
        "Esto certifica la inviabilidad del dominio de tres valores, no la inviabilidad de un dominio representable más amplio. No se ensayó ni se recomienda un ±2 arbitrario; cualquier extensión exigiría derivar el vecindario mínimo de las desigualdades exactas y aprobación separada.",
        "",
        f"JSON reproducible: `{OUT_JSON}`. Receipt de la ejecución preservada: `{RECEIPT}` (NO_FEASIBLE_AC3, readset igual).",
    ]
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "trace_events": len(replay_events),
                      "focus_options": focus_option_values,
                      "crossing_76_focus_options": sorted(forced),
                      "crossing_80_focus_options": sorted(permitted),
                      "report": str(OUT_JSON.resolve()), "report_sha256": sha256(OUT_JSON)}, indent=2))


if __name__ == "__main__":
    main()
