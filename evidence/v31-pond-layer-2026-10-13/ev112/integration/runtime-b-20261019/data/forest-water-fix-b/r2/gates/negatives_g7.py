"""Negative controls for G7 (bog): each mutated record set must make g7_bog.py print FAIL (exit 1).

Usage: python -I negatives_g7.py <records.json> <instances.npy> <v2 records.json> <work_dir> [--free-m D]
  n23-v2-birch-bog       the v2 pilot as it is: OSM wetland at forest density with the riparian (birch) mix
  n24-bog-birch-swap     every bog-palette pine swapped for the birch of the same size and form (origin kept)
  n25-dense-bog          three extra copies of every bog-core tree, 3-5 m away (forest density in the bog)
  n26-no-moss-clearings  the bog-core trees moved to uniform random positions over the bog core (same count)
  n27-no-transition      the rim trees (0-25 m into the bog) thinned to the core density (a cut, not a gradient)
  n28-tall-pines         bog-palette pines at the model's Livonia scale p90 (origin kept)
  n29-v1-closed-rims     (r2, with --v1 R) the EV111 v1 pilot as it is: moss clearings closed by the 25 m transition, so
                         the whole bog has < 30 % tree-free patches (EV111 review 1)
The bog core and rim come from instances.npy (bd, bogpal, written by the placer) for the mutations only; G7 recomputes
everything from the records.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate_common as GC  # noqa: E402

PY = sys.executable
recs_path, inst_path, v2_path, work = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
free = sys.argv[sys.argv.index("--free-m") + 1] if "--free-m" in sys.argv else None
work.mkdir(parents=True, exist_ok=True)
recs = GC.load_records(recs_path)
inst = np.load(inst_path)
assert len(recs) == len(inst)
ref = json.loads(GC.REFERENCE.read_text(encoding="utf-8"))
models = ref["models"]
secs = json.loads(GC.SECTORS.read_text(encoding="utf-8"))["sectors"]
H = np.load(GC.TERRAIN)["heights"].astype(np.float64)
rng = np.random.default_rng(16)
fam = np.array([models[r["model"]]["family"] for r in recs])
tree = np.isin(fam, ["conifer", "broadleaf"])
pine = np.array([(models[r["model"]]["genus"] or "") == "pinussylvestris" for r in recs])
bd = inst["bd"].astype(float)
core = bd >= 25.0
rim = (bd >= 0) & (bd < 25.0)
bogpal = inst["bogpal"].astype(bool)


def mat(r):
    m = np.asarray(r["matrix"], float)
    return m[:9].reshape(3, 3).T, m[9:12]


def rec(model, M, T):
    return {"model": model, "matrix": [float(a) for a in (*M[:, 0], *M[:, 1], *M[:, 2], *T)]}


def write(name, rs):
    p = work / f"{name}.json"
    p.write_text(json.dumps(rs) + "\n", encoding="ascii")
    return p


controls = [("n23-v2-birch-bog", v2_path)]
if "--v1" in sys.argv:
    controls.append(("n29-v1-closed-rims", Path(sys.argv[sys.argv.index("--v1") + 1])))
# n24: pine -> birch of the same size and form
BIRCH = {(1, True): "t_betulapendulae_1s", (1, False): "t_betulapendulae_1s", (2, True): "t_betulapendulae_2s",
         (2, False): "t_betulapendulae_2f", (3, True): "t_betulapendulae_3s", (3, False): "t_betulapendulae_3f"}
sw, n24 = [dict(r) for r in recs], 0
for k in np.flatnonzero(pine & bogpal):
    old = models[recs[k]["model"]]
    new = "dz\\plants_bliss\\tree\\" + BIRCH[(old["size"], bool(old["solitary"]))] + "_summer.p3d"
    assert new in models, new
    M, T = mat(recs[k])
    org = T - M @ np.array(old["bc"])
    sw[k] = rec(new, M, org + M @ np.array(models[new]["bc"]))
    n24 += 1
controls.append(("n24-bog-birch-swap", write("n24-bog-birch-swap", sw)))
# n25: three copies of each bog-core tree 3-5 m away, origin on the terrain
dense = list(recs)
for k in np.flatnonzero(core & tree):
    M, T = mat(recs[k])
    bc = np.array(models[recs[k]["model"]]["bc"])
    org = T - M @ bc
    for _ in range(3):
        a, d = rng.uniform(0, 2 * np.pi), rng.uniform(3, 5)
        x, z = org[0] + d * np.cos(a), org[2] + d * np.sin(a)
        o2 = np.array([x, GC.h_planar(H, np.array([x]), np.array([z]))[0], z])
        dense.append(rec(recs[k]["model"], M, o2 + M @ bc))
controls.append(("n25-dense-bog", write("n25-dense-bog", dense)))
# n26: bog-core trees at uniform random positions over the bog core of their sector (1 m pixels, bd >= 25 m)
moved = [dict(r) for r in recs]
zone_area = {}
for si, sec in enumerate(secs):
    poly = np.asarray(sec["polygon_xz"], float)
    x0, z0 = int(np.floor(poly[:, 0].min())), int(np.floor(poly[:, 1].min()))
    x1, z1 = int(np.ceil(poly[:, 0].max())), int(np.ceil(poly[:, 1].max()))
    pad = 110
    Xp, Zp = np.meshgrid(x0 - pad + np.arange(x1 - x0 + 2 * pad) + 0.5, z1 + pad - np.arange(z1 - z0 + 2 * pad) - 0.5)
    bp = GC.wetland_fraction(Xp, Zp) >= 0.5
    bdp = ndimage.distance_transform_edt(bp) - 0.5
    sl = (slice(pad, pad + z1 - z0), slice(pad, pad + x1 - x0))
    cm = bp[sl] & (bdp[sl] >= 25.0) & GC.in_poly(Xp[sl], Zp[sl], poly)
    cx, cz = Xp[sl][cm], Zp[sl][cm]
    ip = GC.in_poly(Xp[sl], Zp[sl], poly) & bp[sl]
    zone_area[si] = {"core": int(cm.sum()), "rim_out": int((ip & (bdp[sl] < 12.5)).sum()),
                     "rim_in": int((ip & (bdp[sl] >= 12.5) & (bdp[sl] < 25.0)).sum())}
    idx = np.flatnonzero(core & tree & (inst["sector"] == si))
    if not len(idx) or not len(cx):
        continue
    pick = rng.integers(0, len(cx), len(idx))
    for k, j in zip(idx, pick):
        M, T = mat(recs[k])
        bc = np.array(models[recs[k]["model"]]["bc"])
        x, z = cx[j] + rng.uniform(-0.5, 0.5), cz[j] + rng.uniform(-0.5, 0.5)
        o2 = np.array([x, GC.h_planar(H, np.array([x]), np.array([z]))[0], z])
        moved[k] = rec(recs[k]["model"], M, o2 + M @ bc)
controls.append(("n26-no-moss-clearings", write("n26-no-moss-clearings", moved)))
# n27: rim trees thinned to the core tree density of their sector (zone areas in 1 m bog pixels of the polygon)
keep = np.ones(len(recs), bool)
for si in range(len(secs)):
    s = inst["sector"] == si
    if si not in zone_area or zone_area[si]["core"] == 0:
        continue
    d_core = int((core & tree & s).sum()) / zone_area[si]["core"]
    for (lo, hi), key in (((0.0, 12.5), "rim_out"), ((12.5, 25.0), "rim_in")):
        b = s & tree & (bd >= lo) & (bd < hi)
        p = min(1.0, d_core * zone_area[si][key] / max(1, int(b.sum())))
        keep[np.flatnonzero(b)] = rng.random(int(b.sum())) < p
controls.append(("n27-no-transition", write("n27-no-transition", [r for k, r in enumerate(recs) if keep[k]])))
# n28: bog pines at their Livonia p90 scale
tall = [dict(r) for r in recs]
for k in np.flatnonzero(pine & bogpal):
    m = models[recs[k]["model"]]
    M, T = mat(recs[k])
    s0 = float(np.linalg.norm(M[:, 0]))
    s1 = float(np.interp(90, m["scale_levels"], m["scale_q"]))
    org = T - M @ np.array(m["bc"])
    M2 = M * (s1 / s0)
    tall[k] = rec(recs[k]["model"], M2, org + M2 @ np.array(m["bc"]))
controls.append(("n28-tall-pines", write("n28-tall-pines", tall)))
print(f"n24 swapped {n24}; n25 added {len(dense) - len(recs)}; n27 kept {int(keep.sum())} of {len(recs)}")
res = []
for name, path in controls:
    args = [PY, "-I", str(HERE / "g7_bog.py"), str(path)] + (["--free-m", free] if free else [])
    p = subprocess.run(args, capture_output=True, text=True)
    last = [ln for ln in p.stdout.strip().splitlines() if ln.startswith("G7")]
    verdict = last[-1].split()[-1] if last else "ERROR"
    fails = [ln.split()[0] for ln in p.stdout.splitlines() if ln.strip().endswith("FAIL") and not ln.startswith(("G7", "  A-", "  B-"))]
    ok = verdict == "FAIL" and p.returncode == 1
    res.append({"control": name, "gate": "G7", "expected": "FAIL", "observed": verdict, "rc": p.returncode, "as_expected": ok,
                "failed_metrics": fails})
    (work / f"{name}-g7.log").write_text(p.stdout + p.stderr, encoding="utf-8")
    print(f"{name:24s} G7 expected FAIL observed {verdict} rc {p.returncode} -> {'OK' if ok else 'NOT DETECTED'}; failed: {sorted(set(fails))}")
(work / "negatives_g7.json").write_text(json.dumps({"controls": res}, indent=1) + "\n", encoding="utf-8")
print("NEGATIVES G7 " + ("ALL DETECTED" if all(r["as_expected"] for r in res) else "SOME NOT DETECTED"))
