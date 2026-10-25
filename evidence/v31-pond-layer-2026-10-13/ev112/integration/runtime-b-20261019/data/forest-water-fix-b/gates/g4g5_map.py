"""G4 (vertical placement) and G5 (record validity), map-wide, with the EV111 r2 rules (g4.py, g5.py).

Usage: python -I g4g5_map.py <records.json> <G4|G5> [--terrain terrain.npz]
G4, every instance: a) the original p3d origin (position - M . bounding_centre) on the planar terrain within 0.005 m,
   with the JSON doubles and with the matrix rounded to float32 as the WRP stores it (Livonia: -2..+2 mm, no sink);
   b) conifer, broadleaf, bush: largest terrain drop under the trunk disc (trunk_radius * s, exact planar minimum,
   geom.disc_min) <= depth of the visual model below its origin + 0.01 m; c) tilt <= the model's Livonia tilt p99
   + 0.01 deg. --terrain judges the same records on another terrain (vertical placement depends on it: on the EV112
   final terrain the placer must run again).
G5, every record: a) keys exactly {"model", "matrix"}; b) model path ASCII lower case with backslashes, 'dz\\...p3d', no
   drive, P:/DZ file exists with the sha256 of the Livonia reference; c) 12 finite numbers, columns equal length within
   1e-6, orthogonal within 1e-6 s^2, det > 0, scale within the model's Livonia [q1, q99]; d) the ids stage_bridges
   assigns (base WRP max id + 1 ... + n) unique, above every base id, below 2^32."""
import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gcfg  # noqa: E402
import glib  # noqa: E402
import geom  # noqa: E402

sys.path.insert(0, str(gcfg.TOOL_DIR.parent / "terrain"))
from wrp0wzd import read as read_wrp  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("records")
ap.add_argument("gate", choices=["G4", "G5"])
ap.add_argument("--terrain", default=str(gcfg.TERRAIN))
a = ap.parse_args()
MR = glib.MapRecords(a.records)
models = MR.ref["models"]
names = MR.names
m = MR.m
n = len(names)
if a.gate == "G4":
    if (~MR.known).any():
        print("unknown models")
        print("G4 FAIL")
        sys.exit(1)
    H = np.load(a.terrain)["heights"].astype(np.float64)
    bc = np.array([models[nm]["bc"] for nm in names])
    bad = 0
    for label, mm in (("float64", m), ("float32", m.astype(np.float32).astype(np.float64))):
        M = mm[:, :9].reshape(-1, 3, 3).transpose(0, 2, 1)
        org = mm[:, 9:12] - np.einsum("nij,nj->ni", M, bc)
        dy = org[:, 1] - geom.h_at(H, org[:, 0], org[:, 2])
        nb = int((np.abs(dy) > 0.005).sum())
        bad += nb
        print(f"  a) {label}: origin - terrain p0/p1/p50/p99/p100 = {np.round(np.percentile(dy, [0, 1, 50, 99, 100]), 5).tolist()} m; |dy| > 0.005: {nb}")
    M = m[:, :9].reshape(-1, 3, 3).transpose(0, 2, 1)
    org = m[:, 9:12] - np.einsum("nij,nj->ni", M, bc)
    s = np.linalg.norm(M[:, :, 0], axis=1)
    fam = np.array([models[nm]["family"] for nm in names])
    sel = np.flatnonzero(np.isin(fam, ["conifer", "broadleaf", "bush"]))
    tr = np.array([models[nm]["trunk_radius"] for nm in names]) * s
    embed = np.array([-min(models[nm]["visual_bottom_local"], 0.0) for nm in names]) * s
    gap = np.empty(sel.size)
    for s0 in range(0, sel.size, 200000):
        k = sel[s0:s0 + 200000]
        hmin = geom.disc_min(H, org[k, 0], org[k, 2], tr[k], lambda r, c: np.zeros(r.shape))
        gap[s0:s0 + 200000] = geom.h_at(H, org[k, 0], org[k, 2]) - hmin - embed[k]
    nb = int((gap > 0.01).sum())
    print(f"  b) trunk drop - embed depth p50/p99/max = {np.round(np.percentile(gap, [50, 99, 100]), 4).tolist()} m over {sel.size} trees and bushes; > 0.01 m: {nb}")
    Y = M[:, :, 1] / s[:, None]
    tilt = np.degrees(np.arccos(np.clip(Y[:, 1], -1, 1)))
    tmax = np.array([models[nm]["tilt_q"][-1] for nm in names]) + 0.01
    nt = int((tilt > tmax).sum())
    print(f"  c) tilt p50/p99/max = {np.round(np.percentile(tilt, [50, 99, 100]), 3).tolist()} deg; above the model's Livonia p99: {nt}")
    ok = bad == 0 and nb == 0 and nt == 0 and n > 0
    print(f"G4 {'PASS' if ok else 'FAIL'}")
    sys.exit(0 if ok else 1)
fails = {"keys": int((~MR.keys_ok).sum()), "path_form": 0, "path_missing": 0, "p3d_sha": 0, "unknown_model": 0, "finite": 0,
         "orthonormal_scale": 0, "det": 0, "scale_range": 0}
cnt = np.bincount(np.where(MR.midx < len(MR.models), MR.midx, len(MR.models)), minlength=len(MR.models) + 1)
for j, p in enumerate(MR.models):
    c = int(cnt[j])
    if not (p.isascii() and p == p.lower() and p.startswith("dz\\") and p.endswith(".p3d") and "/" not in p and ":" not in p):
        fails["path_form"] += c
    fp = Path("P:/DZ/" + p[3:].replace("\\", "/"))
    if not fp.is_file():
        fails["path_missing"] += c
    elif p not in models:
        fails["unknown_model"] += c
    elif hashlib.sha256(fp.read_bytes()).hexdigest() != models[p]["p3d_sha256"]:
        fails["p3d_sha"] += c
fails["unknown_model"] += int(cnt[-1])
fin = np.isfinite(m).all(1)
fails["finite"] = int((~fin).sum())
X, Y, Z = m[:, 0:3], m[:, 3:6], m[:, 6:9]
nrm = np.stack([np.linalg.norm(X, axis=1), np.linalg.norm(Y, axis=1), np.linalg.norm(Z, axis=1)], 1)
s = nrm.mean(1)
dots = np.max(np.abs(np.stack([(X * Y).sum(1), (X * Z).sum(1), (Y * Z).sum(1)], 1)), 1)
bad_o = (np.abs(nrm - s[:, None]).max(1) > 1e-6 * s) | (dots > 1e-6 * s * s)
fails["orthonormal_scale"] = int((bad_o & fin).sum())
det = np.linalg.det(np.where(fin[:, None, None], np.stack([X, Y, Z], 2), np.eye(3)[None]))
fails["det"] = int(((det <= 0) & fin).sum())
q1 = np.array([models[p]["scale_q"][0] if p in models else -np.inf for p in MR.models] + [-np.inf])
q99 = np.array([models[p]["scale_q"][-1] if p in models else np.inf for p in MR.models] + [np.inf])
mi = np.where(MR.midx < len(MR.models), MR.midx, len(MR.models))
fails["scale_range"] = int((fin & ((s < q1[mi] - 1e-6) | (s > q99[mi] + 1e-6))).sum())
w = read_wrp(gcfg.STAGE_WRP)
ids = [o["id"] for o in w["objects"]]
base_unique = len(set(ids)) == len(ids)
mx = max(ids)
ids_ok = base_unique and n > 0 and mx + n < 2 ** 32
print(f"records {n}; models {len(MR.models)}; base WRP objects {len(ids)} ids {min(ids)}..{mx} unique {base_unique}; new ids {mx + 1}..{mx + n}")
for k, v in fails.items():
    print(f"  {k:18s} {v}")
ok = n > 0 and all(v == 0 for v in fails.values()) and ids_ok
print(f"  ids: {'ok' if ids_ok else 'BAD'}")
print(f"G5 {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
