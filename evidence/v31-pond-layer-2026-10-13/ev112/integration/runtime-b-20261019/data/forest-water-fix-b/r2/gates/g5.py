"""G5: records valid for stage_bridges_v31.py and the engine.

Usage: python -I g5.py <records.json>
Rule (fixed before the first run), every record:
  a) keys exactly {"model", "matrix"} (no "id": stage_bridges_v31.py:21 builds dict(id=..., **record));
  b) model: ASCII, lower case, backslashes, starts with "dz\\", ends ".p3d", no drive letter; P:/DZ/<path> exists and
     its SHA-256 equals the p3d measured for the Livonia reference (same model as measured);
  c) matrix: 12 finite numbers; columns X, Y, Z equal in length (|s_i - s| <= 1e-6 s), mutually orthogonal
     (|Xi . Xj| <= 1e-6 s^2), right-handed (det > 0); s within the model's Livonia scale range [q1, q99];
  d) ids: the base WRP's largest id + 1 .. + n (as stage_bridges assigns them) are unique, above every EV110 id and
     below 2^32; the base WRP ids themselves are unique.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\terrain")
import gate_common as GC  # noqa: E402
from wrp0wzd import read as read_wrp  # noqa: E402


def run(records_path):
    ref = json.loads(GC.REFERENCE.read_text(encoding="utf-8"))
    models = ref["models"]
    recs = json.loads(Path(records_path).read_text(encoding="ascii"))
    fails = {"keys": 0, "path_form": 0, "path_missing": 0, "p3d_sha": 0, "unknown_model": 0, "finite": 0, "orthonormal_scale": 0,
             "det": 0, "scale_range": 0}
    shas = {}
    for r in recs:
        if set(r) != {"model", "matrix"}:
            fails["keys"] += 1
            continue
        p = r["model"]
        if not (p.isascii() and p == p.lower() and p.startswith("dz\\") and p.endswith(".p3d") and "/" not in p and ":" not in p):
            fails["path_form"] += 1
        fp = Path("P:/DZ/" + p[3:].replace("\\", "/"))
        if p not in shas:
            shas[p] = hashlib.sha256(fp.read_bytes()).hexdigest() if fp.is_file() else None
        if shas[p] is None:
            fails["path_missing"] += 1
        elif p not in models:
            fails["unknown_model"] += 1
        elif shas[p] != models[p]["p3d_sha256"]:
            fails["p3d_sha"] += 1
        m = np.asarray(r["matrix"], float) if isinstance(r["matrix"], list) and len(r["matrix"]) == 12 else None
        if m is None or not np.isfinite(m).all():
            fails["finite"] += 1
            continue
        X, Y, Z = m[0:3], m[3:6], m[6:9]
        n = np.linalg.norm([X, Y, Z], axis=1)
        s = n.mean()
        if np.abs(n - s).max() > 1e-6 * s or max(abs(X @ Y), abs(X @ Z), abs(Y @ Z)) > 1e-6 * s * s:
            fails["orthonormal_scale"] += 1
        if np.linalg.det(np.stack([X, Y, Z], 1)) <= 0:
            fails["det"] += 1
        if p in models:
            q = models[p]["scale_q"]
            if not (q[0] - 1e-6 <= s <= q[-1] + 1e-6):
                fails["scale_range"] += 1
    w = read_wrp(GC.STAGE_WRP)
    ids = [o["id"] for o in w["objects"]]
    base_unique = len(set(ids)) == len(ids)
    mx = max(ids)
    new = np.arange(mx + 1, mx + 1 + len(recs), dtype=np.int64)
    ids_ok = base_unique and len(set(new.tolist()) | set(ids)) == len(ids) + len(recs) and (len(recs) == 0 or (new.min() > mx and new.max() < 2 ** 32))
    print(f"records {len(recs)}; models {len(shas)}; base WRP objects {len(ids)} ids {min(ids)}..{mx} unique {base_unique}; "
          f"new ids {mx + 1}..{mx + len(recs)}")
    for k, v in fails.items():
        print(f"  {k:18s} {v}")
    ok = len(recs) > 0 and all(v == 0 for v in fails.values()) and ids_ok
    print(f"  ids: {'ok' if ids_ok else 'BAD'}")
    print(f"G5 {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    a = ap.parse_args()
    sys.exit(0 if run(a.records) else 1)
