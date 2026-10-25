"""G4: vertical placement.

Usage: python -I g4.py <records.json>
Rule (fixed before the first run), every instance:
  a) Livonia sink: the original p3d origin (position - M . bounding_centre) lies on the planar EV110 terrain:
     |origin_y - h(origin_x, origin_z)| <= 0.005 m, both with the JSON doubles and with the matrix rounded to float32
     as the WRP stores it. Livonia: origin - terrain p1..p99 = -2..+2 mm over 1,046,594 conifers, no extra sink.
  b) No floating base on slopes (conifer, broadleaf, bush): the largest terrain drop under the trunk circle
     (trunk_radius * s around the origin, exact minimum of the planar terrain over the disc) must not exceed the depth
     the visual model reaches below its origin (-visual_bottom_local * s) + 0.01 m. Dead wood and reeds lie or bend
     and follow rule a) only.
  c) Tilt within the model's Livonia tilt range (<= tilt_q p99 + 0.01 deg).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate_common as GC  # noqa: E402
import geom  # noqa: E402


def run(records_path):
    ref = json.loads(GC.REFERENCE.read_text(encoding="utf-8"))
    models = ref["models"]
    recs = GC.load_records(records_path)
    H = np.load(GC.TERRAIN)["heights"].astype(np.float64)
    names = [r["model"] for r in recs]
    if any(nm not in models for nm in names):
        print("unknown models")
        print("G4 FAIL")
        return False
    bc = np.array([models[nm]["bc"] for nm in names])
    res = {}
    for label, m in (("float64", np.array([r["matrix"] for r in recs], float)),
                     ("float32", np.array([r["matrix"] for r in recs], np.float32).astype(np.float64))):
        M = m[:, :9].reshape(-1, 3, 3).transpose(0, 2, 1)
        org = m[:, 9:12] - np.einsum("nij,nj->ni", M, bc)
        dy = org[:, 1] - geom.h_at(H, org[:, 0], org[:, 2])
        res[label] = dy
        print(f"  a) {label}: origin - terrain p0/p1/p50/p99/p100 = {np.round(np.percentile(dy, [0, 1, 50, 99, 100]), 5).tolist()} m; "
              f"|dy| > 0.005: {int((np.abs(dy) > 0.005).sum())}")
    m = np.array([r["matrix"] for r in recs], float)
    M = m[:, :9].reshape(-1, 3, 3).transpose(0, 2, 1)
    org = m[:, 9:12] - np.einsum("nij,nj->ni", M, bc)
    s = np.linalg.norm(M[:, :, 0], axis=1)
    fam = np.array([models[nm]["family"] for nm in names])
    sel = np.isin(fam, ["conifer", "broadleaf", "bush"])
    tr = np.array([models[nm]["trunk_radius"] for nm in names]) * s
    embed = np.array([-min(models[nm]["visual_bottom_local"], 0.0) for nm in names]) * s
    hmin = geom.disc_min(H, org[sel, 0], org[sel, 2], tr[sel], lambda r, c: np.zeros(r.shape))
    drop = geom.h_at(H, org[sel, 0], org[sel, 2]) - hmin
    gap = drop - embed[sel]
    nb = int((gap > 0.01).sum())
    print(f"  b) trunk drop - embed depth p50/p99/max = {np.round(np.percentile(gap, [50, 99, 100]), 4).tolist()} m over {int(sel.sum())} "
          f"trees and bushes; > 0.01 m: {nb}")
    Y = M[:, :, 1] / s[:, None]
    tilt = np.degrees(np.arccos(np.clip(Y[:, 1], -1, 1)))
    tmax = np.array([models[nm]["tilt_q"][-1] for nm in names]) + 0.01
    nt = int((tilt > tmax).sum())
    print(f"  c) tilt p50/p99/max = {np.round(np.percentile(tilt, [50, 99, 100]), 3).tolist()} deg; above the model's Livonia p99: {nt}")
    ok = all(int((np.abs(v) > 0.005).sum()) == 0 for v in res.values()) and nb == 0 and nt == 0
    print(f"G4 {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    a = ap.parse_args()
    sys.exit(0 if run(a.records) else 1)
