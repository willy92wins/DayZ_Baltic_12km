"""Road gate for terrain V30 with Codex's definition (tools/navigation/audit_dense_road_sections.py).

Geometry  tests/regional_foundation_roads_v6/reference.npz:xy indexed by evidence/.../road-grade-chains-v6.json.
Eligible  stations every 1 m farther than 48 m from water, 470 m from the Narva bridge centre and 18 m from both
          chain ends (junction aprons and wet crossings keep their own design, as in Codex's consumer).
Checks    cross  = spread of 17 lateral samples from -4 to +4 m        <= 3 cm
          grade  = centre grade between 1 m stations                  <= 6.5 %
          chord  = |h(s+3) - (h(s) + h(s+6)) / 2| on the centre line   <= 3 cm
Sampling  Codex's own waterway_common.sample (native NW-SE triangles), imported unchanged.
Usage: python verify_roads_v30.py <heights.asc | file.npz::key> <water.npz::key | v29> [--json out.json]
"""
import json
import hashlib
import os
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
sys.path.insert(0, os.path.join(R, "tools", "navigation"))
from waterway_common import sample  # noqa: E402

NARVA = np.array([2417.1428225906, 6889.8850822322])
LIMITS = {"cross_m": 0.03, "grade": 0.065, "chord_m": 0.03, "water_clear_m": 48.0, "narva_clear_m": 470.0, "end_margin_m": 18.0}


def load(spec):
    if spec.endswith(".asc"):
        with rasterio.open(spec) as ds:
            return ds.read(1).astype("float64")
    f, k = spec.split("::")
    return np.load(f)[k]


def road_chains():
    roads = np.load(os.path.join(R, "tests", "regional_foundation_roads_v6", "reference.npz"))["xy"]
    chains = json.load(open(os.path.join(R, "evidence", "regional-foundation-v1", "road-grade-chains-v6.json"), encoding="utf-8"))["chains"]
    return [roads[idx] for idx in chains]


def evaluate(h, water):
    wd = distance_transform_edt(~water) * 6
    tot = {"chains": 0, "samples": 0, "cross_fail": 0, "grade_fail": 0, "chord_fail": 0,
           "cross_max_m": 0.0, "grade_max": 0.0, "chord_max_m": 0.0, "worst": {}, "fail_list": []}
    offsets = np.arange(-4, 4.01, .5)
    for number, p in enumerate(road_chains()):
        if len(p) < 4:
            continue
        station = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
        s = np.linspace(0, station[-1], int(np.ceil(station[-1])) + 1)
        q = np.column_stack([np.interp(s, station, p[:, d]) for d in (0, 1)])
        tangent = np.gradient(q, axis=0)
        normal = np.column_stack([-tangent[:, 1], tangent[:, 0]]) / np.linalg.norm(tangent, axis=1)[:, None]
        rr = np.clip(np.rint((12282 - q[:, 1]) / 6).astype(int), 0, 2047)
        cc = np.clip(np.rint(q[:, 0] / 6).astype(int), 0, 2047)
        valid = (wd[rr, cc] > LIMITS["water_clear_m"]) & (np.linalg.norm(q - NARVA, axis=1) > LIMITS["narva_clear_m"]) \
            & (s > LIMITS["end_margin_m"]) & (s < station[-1] - LIMITS["end_margin_m"])
        if not valid.any():
            continue
        tot["chains"] += 1
        elev = np.array([sample(h, (q + normal * v)[:, 0] + 200000, (q + normal * v)[:, 1]) for v in offsets])
        cross = np.ptp(elev, axis=0)
        centre = elev[8]
        pairs = valid[:-1] & valid[1:]
        grade = np.abs(np.diff(centre) / np.diff(s))
        chord = np.abs(centre[3:-3] - (centre[:-6] + centre[6:]) / 2) if len(centre) > 6 else np.zeros(0)
        cvalid = valid[3:-3] & valid[:-6] & valid[6:] if len(centre) > 6 else np.zeros(0, bool)
        tot["samples"] += int(valid.sum())
        for name, arr, mask, lim in (("cross", cross, valid, LIMITS["cross_m"]), ("grade", grade, pairs, LIMITS["grade"]),
                                     ("chord", chord, cvalid, LIMITS["chord_m"])):
            if not mask.any():
                continue
            vals = arr[mask]
            tot[f"{name}_fail"] += int((vals > lim).sum())
            for i in np.flatnonzero(mask)[vals > lim][:50]:
                if len(tot["fail_list"]) < 400:
                    tot["fail_list"].append({"check": name, "chain": number, "station_m": round(float(s[i]), 1),
                                             "x": round(float(q[i, 0]), 1), "z": round(float(q[i, 1]), 1),
                                             "value": round(float(arr[i]), 4)})
            key = f"{name}_max" if name == "grade" else f"{name}_max_m"
            if vals.max() > tot[key]:
                tot[key] = float(vals.max())
                i = np.flatnonzero(mask)[int(np.argmax(vals))]
                tot["worst"][name] = {"chain": number, "station_m": float(s[i]), "x": round(float(q[i, 0]), 1),
                                      "z": round(float(q[i, 1]), 1), "value": round(float(vals.max()), 4)}
    tot["status"] = "PASS" if tot["cross_fail"] == tot["grade_fail"] == tot["chord_fail"] == 0 else "FAIL"
    tot["limits"] = LIMITS
    return tot


def main():
    h = load(sys.argv[1])
    if sys.argv[2] == "v29":
        ref = np.load(os.path.join(R, "tests", "regional_outline_smoothing_v33", "reference.npz"))
        water = ref["wet"] | ref["ocean"]
    else:
        water = load(sys.argv[2]).astype(bool)
    res = evaluate(h, water)
    terrain_path = Path(sys.argv[1].split('::')[0])
    water_path = Path(R) / 'tests/regional_outline_smoothing_v33/reference.npz' if sys.argv[2] == 'v29' else Path(sys.argv[2].split('::')[0])
    res['terrain_sha256'] = hashlib.sha256(terrain_path.read_bytes()).hexdigest()
    res['terrain_spec'] = sys.argv[1]
    res['water_spec'] = sys.argv[2]
    res['sources'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
        water_path, Path(__file__), Path(sample.__code__.co_filename),
        Path(R) / 'tests/regional_foundation_roads_v6/reference.npz',
        Path(R) / 'evidence/regional-foundation-v1/road-grade-chains-v6.json')}
    print(json.dumps({k: v for k, v in res.items() if k != "fail_list"}, indent=1))
    if "--json" in sys.argv:
        with open(sys.argv[sys.argv.index("--json") + 1], "wb") as f:
            f.write(json.dumps(res, indent=1).encode("utf-8"))


if __name__ == "__main__":
    main()
