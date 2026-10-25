from __future__ import annotations

import csv
import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

G = Path(r"E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010")
BUILD = G / "build-wide-slope"
OUT = BUILD / "subcell-flag-probe"
CLASSIFICATION = BUILD / "anomaly-classification/classification.json"
ANOMALIES_CSV = BUILD / "ev95-physical-anomalies.csv"
NATIVE = BUILD / "native-snapshot.log"
NATIVE_REFERENCE = BUILD / "native-reference.json"
NATIVE_VERIFY = BUILD / "native-verification.json"
RISKS = BUILD / "missions/BalticEV95WideBankV1.BalticTrial/risks.csv"
EV95_INIT = BUILD / "missions/BalticEV95WideBankV1.BalticTrial/init.c"
TEMPORAL_INIT = Path(r"C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticAnomalyTemporalV1.BalticTrial/init.c")
TERRAIN = BUILD / "candidate/terrain.npz"
P_FIELD = BUILD / "candidate/plane.npy"
F_FIELD = BUILD / "candidate/visible-field.npy"
STAGE = BUILD / "stage.json"
DEPLOY = BUILD / "deploy.json"
INDEX_RUN = G / "ev93-face-index/runs/20261010T092417Z-63d4cec3"
INDEX_MANIFEST = INDEX_RUN / "manifest.json"
INDEX_BUILDER = G / "ev93-face-index/build_face_index.py"
MISSION_SOURCE = OUT / "mission/BalticEV95SubcellFlagsV1.BalticTrial/init.c"
POINTS_CSV = OUT / "mission/BalticEV95SubcellFlagsV1.BalticTrial/points.csv"
SELECTION = OUT / "selection.json"
MANIFEST_OUT = OUT / "probe-manifest.json"
NATIVE_LINT = OUT / "native-probe-lint.json"
VALIDATOR = Path(r"C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py")

PINS = {
    CLASSIFICATION: "9dd964d4896166979da56c06d686ed14ed69020d468119931f27762a3dcbf089",
    ANOMALIES_CSV: "f8d8195166e8a1f81c045c14edeead726ba513cacd1ee7fa34e208b964574e41",
    NATIVE: "f01f9076638d71ad4d8a51be2c5e898f31a3bd8e58ca5128b34f47b467bfb913",
    NATIVE_REFERENCE: "3e0f5efe388d2453c4c40936eeec590d8dcab262a4990c6c11cd65896d4c9fcd",
    NATIVE_VERIFY: "c6835dd6caf4c1f40240f0ce449600de09dba15aacb321ad368bb21b631704c4",
    RISKS: "0f1da0395d76488930f2afbb57bdd1e8c09be5d913f3a7ffe2eb007ba5a0757f",
    EV95_INIT: "8428ddfc5a951767928b8736528489bc577bc4083eb351d71c0a4380cbac8077",
    TEMPORAL_INIT: "b9485174501c93bb151731cb421a14a01705d7302983cb2605c93f886e361354",
    TERRAIN: "40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a",
    P_FIELD: "768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0",
    F_FIELD: "f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c",
    STAGE: "b04b066d99f9c22a4fffd77c66762d3e9e744dfa2bbf20d8508f076845571dda",
    DEPLOY: "f5a9c8185812e0b77a804ef9811e0405b5a7969f8ccfc19b85cc29d23cac03ca",
    INDEX_MANIFEST: "c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c",
    INDEX_BUILDER: "d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e",
    VALIDATOR: "da5101225292e7296117c572e224e510b9586dacccd85a8a6a71933ed36d8d2f",
}
WATER_PBO_SHA = "3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14"
EXPECTED_WATER_WRP_SHA = "3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_face_index_builder():
    spec = importlib.util.spec_from_file_location("ev93_face_index", INDEX_BUILDER)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import index API from {INDEX_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cross2(a, b):
    return float(a[0] * b[1] - a[1] * b[0])


def barycentric_and_edge_clearance(x: float, z: float, triangle: np.ndarray):
    p = np.asarray([x, z], dtype=np.float64)
    xy = triangle[:, [0, 2]].astype(np.float64)
    v0, v1, v2 = xy
    den = cross2(v1 - v0, v2 - v0)
    if den == 0.0:
        return None
    l1 = cross2(p - v0, v2 - v0) / den
    l2 = cross2(v1 - v0, p - v0) / den
    bary = np.asarray([1.0 - l1 - l2, l1, l2], dtype=np.float64)
    if np.min(bary) < -1e-10:
        return None
    edge_lengths = np.asarray([
        np.linalg.norm(v2 - v1),
        np.linalg.norm(v2 - v0),
        np.linalg.norm(v1 - v0),
    ], dtype=np.float64)
    twice_area = abs(den)
    altitudes = twice_area / edge_lengths
    distances = bary * altitudes
    return {"barycentric": bary.tolist(), "min_barycentric_weight": float(np.min(bary)),
            "min_edge_distance_m": float(np.min(distances))}


def exact_face_hits(index, kind: str, row: int, col: int, x: float, z: float):
    arrays = index.query_window(max(0, row - 1), min(2047, row), max(0, col - 1), min(2047, col), kind=kind)
    hits = []
    for i in range(len(arrays["kind"])):
        if arrays["degenerate"][i]:
            continue
        metrics = barycentric_and_edge_clearance(x, z, arrays["xyz"][i])
        if metrics is None:
            continue
        hits.append({"object_id": int(arrays["object_id"][i]), "model_id": int(arrays["model_id"][i]),
                     "face_id": int(arrays["face_id"][i]), **metrics})
    return hits


def read_rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.reader(f, delimiter=";"))


def make_points(targets, controls):
    points = []
    directions = [(dx, dz) for dx in (-1, 0, 1) for dz in (-1, 0, 1) if (dx, dz) != (0, 0)]
    for index, target in enumerate(targets):
        group = f"T{index:02d}_R{target['row']}_C{target['col']}"
        base = target["xz_m"]
        points.append({"sample_id": f"{group}_CENTER", "role": "anomaly_center", "group_id": group,
                       "class": target["class"], "row": target["row"], "col": target["col"],
                       "ring_m": 0.0, "dx_m": 0.0, "dz_m": 0.0, "x": base[0], "z": base[1]})
        for radius in (0.05, 0.25, 1.0):
            rcode = f"{radius:.2f}".replace(".", "")
            for dx_sign, dz_sign in directions:
                dx, dz = radius * dx_sign, radius * dz_sign
                points.append({"sample_id": f"{group}_R{rcode}_X{dx_sign:+d}_Z{dz_sign:+d}",
                               "role": "anomaly_offset", "group_id": group, "class": target["class"],
                               "row": target["row"], "col": target["col"], "ring_m": radius,
                               "dx_m": dx, "dz_m": dz, "x": base[0] + dx, "z": base[1] + dz})
    for control in controls:
        points.append({"sample_id": control["sample_id"], "role": control["role"],
                       "group_id": control["group_id"], "class": control["class"],
                       "row": -1, "col": -1, "ring_m": 0.0, "dx_m": 0.0, "dz_m": 0.0,
                       "x": control["x"], "z": control["z"]})
    if len(points) != 279 or len({p["sample_id"] for p in points}) != len(points):
        raise AssertionError("point population/count/uniqueness mismatch")
    return points


def main():
    started = {str(path): sha(path) for path in PINS}
    for path, expected in PINS.items():
        if started[str(path)] != expected:
            raise RuntimeError(f"pinned input changed: {path}: {started[str(path)]} != {expected}")
    with np.load(TERRAIN, allow_pickle=False) as data:
        h = data["heights"]
        cls = data["cls"]
        levels = data["level"]
        water = data["water"]
    p = np.load(P_FIELD, mmap_mode="r")
    f = np.load(F_FIELD, mmap_mode="r")
    stage = json.loads(STAGE.read_text(encoding="utf-8"))
    deploy = json.loads(DEPLOY.read_text(encoding="utf-8"))
    index_manifest_doc = json.loads(INDEX_MANIFEST.read_text(encoding="utf-8"))
    if stage.get("terrain_sha256") != PINS[TERRAIN] or stage.get("source_wrp_sha256") != EXPECTED_WATER_WRP_SHA:
        raise AssertionError("EV95 stage terrain/WRP identity differs from the pinned face-index source")
    if (deploy.get("terrain_sha256") != PINS[TERRAIN] or deploy.get("water_pbo_exact") is not True or
        deploy.get("files", {}).get("baltic_water_v30.pbo") != WATER_PBO_SHA):
        raise AssertionError("EV95 deployment does not pin the expected terrain and exact water PBO")
    if (index_manifest_doc.get("base_identity", {}).get("water_pbo_sha256") != WATER_PBO_SHA or
        index_manifest_doc.get("base_identity", {}).get("wrp_source_sha256") != EXPECTED_WATER_WRP_SHA):
        raise AssertionError("face index source WRP/water PBO identity mismatch")
    classification = json.loads(CLASSIFICATION.read_text(encoding="utf-8"))
    if classification.get("status") != "COMPLETE_OFFLINE_STATIC_CLASSIFICATION" or len(classification["rows"]) != 24:
        raise RuntimeError("classification source is not complete for exactly 24 anomalies")
    class1 = [x for x in classification["rows"] if x["class"] == 1]
    class3_submerged = []
    for x in classification["rows"]:
        if x["class"] != 3:
            continue
        faces = x["physical"]["exactly_contains_sample_point"]
        differences = [float(x["ground_m"] - face["face_y_at_point_m"]) for face in faces]
        if faces and all(d < -1e-5 for d in differences):
            class3_submerged.append(x)
    if len(class1) != 6 or len(class3_submerged) != 5:
        raise AssertionError(f"target selection changed: class1={len(class1)} class3_submerged={len(class3_submerged)}")
    target_rows = sorted(class1 + class3_submerged, key=lambda x: (x["row"], x["col"]))
    targets = []
    for x in target_rows:
        row, col = int(x["row"]), int(x["col"])
        if x["xz_m"] != [float(col * 6), float((2047 - row) * 6)]:
            raise AssertionError(f"native grid coordinate mismatch at {(row, col)}")
        adjacent = x["adjacent_compiled_fields"]
        ffinite = int(sum(any(np.isfinite(v) for v in cell["F4"]) for cell in adjacent))
        pfinite = int(sum(np.isfinite(cell["P"]) for cell in adjacent))
        if x["class"] == 1 and (pfinite or ffinite):
            raise AssertionError(f"class1 unknown-field target unexpectedly has finite adjacent data at {(row, col)}")
        if x["class"] == 3 and (pfinite != 4 or ffinite != 4):
            raise AssertionError(f"class3 wet target lacks full P/F context at {(row, col)}")
        targets.append({"row": row, "col": col, "xz_m": x["xz_m"], "class": x["class"],
                        "ground_m": x["ground_m"], "level_m": x["level_m"], "water_mask": x["water_mask"],
                        "p_finite_adjacent_cells": pfinite, "f_finite_adjacent_cells": ffinite,
                        "runtime": x["runtime"], "physical": x["physical"], "visible": x["visible"]})

    risk_rows = read_rows(RISKS)
    snapshot_p = {}
    for line in NATIVE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("P;"):
            continue
        fields = line.split(";")
        snapshot_p[int(fields[1])] = {"ground": float(fields[2]), "sea": fields[3] == "true",
                                      "pond": fields[4] == "true", "no_fake": float(fields[5]),
                                      "depth": float(fields[6]), "sea_level": float(fields[7])}
    control_spec = [(1, "water_positive_pond_a"), (6, "water_positive_pond_b"),
                    (0, "dry_negative_a"), (4, "dry_negative_b")]
    controls = []
    for risk_id, role in control_spec:
        raw = risk_rows[risk_id]
        if int(raw[0]) != risk_id or risk_id not in snapshot_p:
            raise AssertionError(f"native control index missing or out of order: {risk_id}")
        sample = snapshot_p[risk_id]
        kind = int(raw[4])
        if role.startswith("water_positive"):
            if kind <= 0 or sample["sea"] or not sample["pond"] or sample["no_fake"] <= sample["ground"] + 0.03 or sample["depth"] <= 0.02:
                raise AssertionError(f"water-positive control did not pass pinned baseline: risk={risk_id}")
        else:
            if kind != 0 or sample["sea"] or sample["pond"] or sample["no_fake"] > sample["ground"] + 0.03 or sample["depth"] > 0.02:
                raise AssertionError(f"dry-negative control did not pass pinned baseline: risk={risk_id}")
        controls.append({"sample_id": f"C{risk_id:02d}_CONTROL", "role": role,
                         "group_id": f"CONTROL_RISK_{risk_id}", "risk_id": risk_id,
                         "class": kind, "x": float(raw[1]), "z": float(raw[2]),
                         "baseline": sample})

    # Exact compiled water-face containment and boundary clearance for each target center.
    index_module = load_face_index_builder()
    face_index = index_module.FaceRangeIndex(INDEX_RUN)
    manifest = json.loads(INDEX_MANIFEST.read_text(encoding="utf-8"))
    model_names = {int(m["model_id"]): m["basename"] for m in manifest["models"]}
    exact_face_context = {}
    for target in targets:
        row, col = target["row"], target["col"]
        x, z = target["xz_m"]
        for kind in ("physical", "visible"):
            hits = exact_face_hits(face_index, kind, row, col, x, z)
            prior = target[kind]["exactly_contains_sample_point"]
            prior_ids = {(f["object_id"], f["model_id"], f["face_id"]) for f in prior}
            current_ids = {(f["object_id"], f["model_id"], f["face_id"]) for f in hits}
            if prior_ids != current_ids:
                raise AssertionError(f"exact face set changed since anomaly classification at {(row, col)} {kind}")
            for hit in hits:
                hit["model_basename"] = model_names[hit["model_id"]]
            exact_face_context.setdefault(f"{row},{col}", {})[kind] = {
                "containment_count": len(hits),
                "min_barycentric_weight_to_edge": min((q["min_barycentric_weight"] for q in hits), default=None),
                "min_xz_edge_distance_m": min((q["min_edge_distance_m"] for q in hits), default=None),
                "faces": hits,
            }
    face_index.reverify()

    points = make_points(targets, controls)
    OUT.mkdir(parents=True, exist_ok=True)
    mission_dir = POINTS_CSV.parent
    mission_dir.mkdir(parents=True, exist_ok=True)
    fields = ["sample_id", "role", "group_id", "class", "row", "col", "ring_m", "dx_m", "dz_m", "x", "z"]
    with POINTS_CSV.open("w", newline="", encoding="utf-8") as fcsv:
        writer = csv.DictWriter(fcsv, fieldnames=fields, delimiter=";", lineterminator="\n")
        writer.writeheader()
        for item in points:
            writer.writerow({k: format(item[k], ".12g") if isinstance(item[k], float) else item[k] for k in fields})
    point_sha = sha(POINTS_CSV)

    mission_text = MISSION_SOURCE.read_text(encoding="utf-8")
    required_api = ("IsDedicatedServer()", "GetWorldName()", "SurfaceY(", "SurfaceIsSea(",
                    "SurfaceIsPond(", "GetWaterSurfaceHeightNoFakeWave(",
                    "GetWaterSurfaceHeightWithFakeWave(", "GetWaterDepth(", "SurfaceGetSeaLevel(",
                    "SurfaceGetSeaWaveCurrent(", "SurfaceGetSeaWaveMax(")
    forbidden_mutators = ("SetDate(", "SetTimeMultiplier(", "SetWeather(", "SetWind(", "SetRain(", "SetOvercast(")
    if any(token not in mission_text for token in required_api):
        raise AssertionError("mission is missing a required native readback API")
    if any(token in mission_text for token in forbidden_mutators):
        raise AssertionError("mission contains an environment/time mutation")
    mission_sha = sha(MISSION_SOURCE)
    lint = subprocess.run([sys.executable, str(VALIDATOR), str(MISSION_SOURCE)],
                          capture_output=True, text=True, check=False)
    try:
        lint_json = json.loads(lint.stdout)
    except Exception as exc:
        raise RuntimeError(f"validator output was not JSON: {lint.stdout[:1000]} {lint.stderr[:1000]}") from exc
    if (lint.returncode != 0 or lint_json.get("status") != "PASS" or
            lint_json.get("info", {}).get("files_scanned") != 1 or lint_json.get("errors")):
        raise AssertionError(f"mission lint failed: {lint_json}")
    if sha(MISSION_SOURCE) != mission_sha:
        raise RuntimeError("mission source changed during lint")
    NATIVE_LINT.write_text(json.dumps(lint_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    end = {str(path): sha(path) for path in PINS}
    if started != end:
        raise RuntimeError("pinned source readset changed during point preparation")
    selection = {
        "schema": "ev95.subcell-flag-probe-selection.v1",
        "status": "PREPARED_READ_ONLY_NO_MISSION_RUN",
        "source_readset_start": {str(path): digest for path, digest in started.items()},
        "source_readset_end": {str(path): digest for path, digest in end.items()},
        "producer_path": str(Path(__file__).resolve()), "producer_sha256": sha(Path(__file__).resolve()),
        "points_path": str(POINTS_CSV), "points_sha256": point_sha,
        "mission_source_path": str(MISSION_SOURCE),
        "mission_name": "BalticEV95SubcellFlagsV1.BalticTrial",
        "log_prefix": "baltic_ev95_subcell_flags_probe_20261010.log",
        "mission_source_sha256": mission_sha,
        "native_lint": {"path": str(NATIVE_LINT), "sha256": sha(NATIVE_LINT),
                         "validator_path": str(VALIDATOR), "validator_sha256": started[str(VALIDATOR)],
                         "status": lint_json["status"], "files_scanned": lint_json["info"]["files_scanned"]},
        "samples": {"anomaly_centers": 11, "class1_unknown": 6, "class3_below_all_physical_faces": 5,
                    "offsets_per_center": 24, "points_per_center": 25, "controls": 4, "total_unique_points": len(points),
                    "rings_m": [0.05, 0.25, 1.0], "directions_per_ring": 8,
                    "directions": [[int(a), int(b)] for a, b in itertools.product((-1, 0, 1), repeat=2) if (a, b) != (0, 0)]},
        "temporal_sampling": {"phases": 7, "nominal_elapsed_seconds": [0, 5, 10, 15, 20, 25, 30],
                              "sample_chunk_per_update": 32, "environment_mutated": False},
        "targets": targets, "controls": controls, "exact_compiled_face_context": exact_face_context,
        "index": {"manifest_path": str(INDEX_MANIFEST), "manifest_sha256": started[str(INDEX_MANIFEST)],
                  "status": manifest["status"], "water_object_count": manifest["object_count"],
                  "face_count": manifest["counts"]["faces"], "source_wrp_sha256": manifest["base_identity"]["wrp_source_sha256"],
                  "water_pbo_sha256": manifest["base_identity"]["water_pbo_sha256"]},
        "native_api_precedents": {"ev95_init_sha256": started[str(EV95_INIT)],
                                  "temporal_init_sha256": started[str(TEMPORAL_INIT)]},
        "limitations": ["The 30-second sample is a measured interval, not an envelope certificate.",
                        "No flag, scalar level, or NaN field alone proves a water polygon or visible rendering.",
                        "The index is the source-world static water-object set; it excludes nine non-water world objects.",
                        "The mission has not been staged or run."]
    }
    SELECTION.write_text(json.dumps(selection, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_out = {"schema": "ev95.subcell-flag-probe-preparation.v1", "status": "PREPARED_READ_ONLY_NO_RUN",
                    "selection_path": str(SELECTION), "selection_sha256": sha(SELECTION),
                    "points_path": str(POINTS_CSV), "points_sha256": point_sha,
                    "mission_source_path": str(MISSION_SOURCE), "mission_source_sha256": mission_sha,
                    "source_readset_start": selection["source_readset_start"],
                    "source_readset_end": selection["source_readset_end"],
                    "mission_name": selection["mission_name"], "log_prefix": selection["log_prefix"],
                    "native_lint_path": str(NATIVE_LINT), "native_lint_sha256": sha(NATIVE_LINT),
                    "validator_path": str(VALIDATOR), "validator_sha256": started[str(VALIDATOR)],
                    "points": len(points), "phases": 7, "dayz_run_executed": False}
    MANIFEST_OUT.write_text(json.dumps(manifest_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": selection["status"], "targets": len(targets), "controls": len(controls),
                      "points": len(points), "points_sha256": point_sha, "selection": str(SELECTION)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
