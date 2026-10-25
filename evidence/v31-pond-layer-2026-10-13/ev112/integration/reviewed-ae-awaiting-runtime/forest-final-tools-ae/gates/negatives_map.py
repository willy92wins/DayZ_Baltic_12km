"""Negative controls of the EV112 map-wide gates: each fixture is a copy of real records with one defect, and the gate
it targets must print FAIL (exit 1). A control 'passes' when its gate fails.

Usage: python -I negatives_map.py <records.json> <gate-rasters dir> <livonia-ev112-bands.json> <work dir> <region x0,z0,x1,z1>
         [--only n01,n02,...]
The records are cut to the region (G1/G4/G5 judge every instance, so a region is the same rule on fewer records); the
window gates (G2/G3, G8) judge the 1 km windows inside the region, G7 the bogs inside it.
  G1  n01 tree on a road axis; n02 bush in visible water; n03 tree in the engine sea band; n04 tree on a bridge;
      n05 tree on a kit piece; n06 tree in Narva; n21 the EV111 v1 fallen beech (geometry on the road strip);
      n30 tree inside an --exclude polygon (a dam site stand-in)
  G4  n12 every 50th instance lifted 0.30 m; n13 position = origin (bounding centre ignored); n14 a bush tilted 64 deg
  G5  n15 NaN; n16 skewed matrix; n17 an 'id' key; n18 missing model; n19 upper-case path
  G2  n07 every second tree removed; n22 interior conifers swapped for a model off the interior palette
  G3  n11 every tree and bush 0-25 m outside the texture removed (bare edge)
  G8  n40 the trees of the bog's forest-floor part reduced to the EV111 V2 open-bog density (40/ha); n41 synthetic
      clearings: 25 m discs emptied of trees on 2 % of the forest floor of each window; n42 sector border: everything
      outside one 1 km square removed (windows across its edge)
  G7  n43 the open bog filled with trees at 120/ha (no moss clearings); n44 wooded bog thinned to 40/ha; n45 bog pines
      swapped for Norway spruce
Writes <work dir>/negatives.json and prints one line per control."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gcfg  # noqa: E402
import glib  # noqa: E402
import recio  # noqa: E402

PY = sys.executable
T = gcfg.tool()
ap = argparse.ArgumentParser()
ap.add_argument("records")
ap.add_argument("rasters")
ap.add_argument("bands")
ap.add_argument("work")
ap.add_argument("region")
ap.add_argument("--only")
a = ap.parse_args()
W = Path(a.work)
W.mkdir(parents=True, exist_ok=True)
x0, z0, x1, z1 = [float(v) for v in a.region.split(",")]
models, midx, m, _ = recio.load_records(a.records, bbox=(x0, z0, x1, z1))
ref = json.loads(gcfg.REFERENCE.read_text(encoding="utf-8"))
mods = ref["models"]
fam = np.array([mods[models[i]]["family"] for i in midx])
rng = np.random.default_rng(7)
t = np.load(gcfg.TERRAIN)
H = t["heights"].astype(np.float64)
fp = np.load(gcfg.FOOTPRINT)
R = glib.Rasters(a.rasters)
wins = ";".join(f"{wx},{wz}" for wz in glib.WIN_X0 for wx in glib.WIN_X0 if wx >= x0 and wx + 1000 <= x1 and wz >= z0 and wz + 1000 <= z1)
only = set(a.only.split(",")) if a.only else None


def write(name, mo, mi, mm, extra_keys=None):
    p = W / f"{name}.json"
    if extra_keys is None:
        recio.write_records(p, mo, mi, mm)
    else:
        with open(p, "wb") as f:
            f.write(b"[\n")
            for k in range(len(mi)):
                rec = {"model": mo[mi[k]], "matrix": [float(v) for v in mm[k]]}
                if k in extra_keys:
                    rec.update(extra_keys[k])
                f.write((json.dumps(rec) + (",\n" if k + 1 < len(mi) else "\n")).encode("ascii"))
            f.write(b"]\n")
    return p


def moved(i, x, z):
    """Copy of record i with its position moved to (x, z) on the terrain (origin rule kept)."""
    mm = m[i].copy()
    M = mm[:9].reshape(3, 3).T
    bc = np.array(mods[models[midx[i]]]["bc"])
    h = T.tri_eval(H, np.array([x]), np.array([z]))[0][0]
    mm[9:12] = np.array([x, h, z]) + M @ bc
    return mm


def add(name, idx_src, x, z):
    mm = np.vstack([m, moved(idx_src, x, z)[None]])
    return write(name, models, np.r_[midx, midx[idx_src]], mm)


def gate(cmd):
    p = subprocess.run([PY, "-I", "-B", *map(str, cmd)], capture_output=True, text=True)
    last = [ln for ln in p.stdout.splitlines() if ln.strip()]
    return p.returncode, (last[-1] if last else p.stderr[-300:])


tree_i = int(np.flatnonzero(fam == "conifer")[0])
bush_i = int(np.flatnonzero(fam == "bush")[0])
G1 = lambda p, *ex: [HERE / "g1_map.py", p, W / "g1-tmp.json", *ex]  # noqa: E731
G45 = lambda p, g: [HERE / "g4g5_map.py", p, g]  # noqa: E731
G23 = lambda p: [HERE / "g2g3_map.py", p, a.rasters, a.bands, W / "g23-tmp.json", "--windows", wins]  # noqa: E731
G8 = lambda p: [HERE / "g8_agreement.py", p, a.rasters, a.bands, W / "g8-tmp.json", "--windows", wins]  # noqa: E731
G7 = lambda p: [HERE / "g7_map.py", p, a.rasters, W / "g7-tmp.json", "--livonia-bands", a.bands, "--bbox", a.region]  # noqa: E731
res = {}


def run(name, target, build, cmd):
    if only and name not in only:
        return
    p = build()
    rc, last = gate(cmd(p))
    if target in ("G2", "G3"):                 # g2g3_map judges both: credit the targeted gate's own verdict
        out_ = json.loads((W / "g23-tmp.json").read_text(encoding="utf-8"))["summary"][target]
        det = out_["verdict"] == "FAIL"
        last = f"{target}-map {out_['verdict']} ({out_['failed_windows']} windows fail)"
    else:
        det = rc == 1
    res[name] = {"gate": target, "rc": rc, "last": last, "detected": det}
    print(f"{name:5s} {target:3s} rc {rc} {'DETECTED' if det else 'MISSED'} | {last}", flush=True)


# ---- G1: points inside the region on each exclusion
from build_surface_v30 import road_chains  # noqa: E402
rp = next(np.asarray(c, float)[len(c) // 2] for c in road_chains() if len(c) > 3 and x0 < np.asarray(c, float)[len(c) // 2][0] < x1 and z0 < np.asarray(c, float)[len(c) // 2][1] < z1)
ws = R.big("wsea1m")
ii, jj = np.nonzero(ws[int(gcfg.MAP - z1):int(gcfg.MAP - z0), int(x0):int(x1)] == 1)
wpt = (x0 + jj[len(jj) // 2] + 0.5, z1 - ii[len(ii) // 2] - 0.5) if len(ii) else None
ii, jj = np.nonzero(ws[:, :] >= 2)
spt = (jj[len(jj) // 2] + 0.5, gcfg.MAP - ii[len(ii) // 2] - 0.5)
hulls, _ = T.object_hulls(gcfg.STAGE_WRP)
bh = next(h["hull"].mean(0) for h in hulls if h["kind"] == "bridge")
kh = next(h["hull"].mean(0) for h in hulls if h["kind"] == "kit")
nr, nc = np.nonzero(t["narva"])
npt = (6.0 * nc[len(nc) // 2], gcfg.ZTOP - 6.0 * nr[len(nr) // 2])
run("n01", "G1", lambda: add("n01", tree_i, *rp), G1)
if wpt:
    run("n02", "G1", lambda: add("n02", bush_i, *wpt), G1)
run("n03", "G1", lambda: add("n03", tree_i, *spt), G1)
run("n04", "G1", lambda: add("n04", tree_i, *bh), G1)
run("n05", "G1", lambda: add("n05", tree_i, *kh), G1)
run("n06", "G1", lambda: add("n06", tree_i, *npt), G1)
n21 = json.loads((gcfg.F111 / "scripts-v3r2/neg_fixtures/n21-fallen-beech-road.json").read_text(encoding="utf-8"))
n21r = n21[0] if isinstance(n21, list) else n21.get("record", n21)
run("n21", "G1", lambda: write("n21", sorted(set(models) | {n21r["model"]}), np.r_[[sorted(set(models) | {n21r["model"]}).index(models[i]) for i in midx],
                                                                                  [sorted(set(models) | {n21r["model"]}).index(n21r["model"])]],
                                     np.vstack([m, np.asarray(n21r["matrix"], float)[None]])), G1)
cx, cz = float(m[tree_i, 9]), float(m[tree_i, 11])
exf = W / "n30-exclude.json"
exf.write_text(json.dumps({"polygons": [{"name": "dam stand-in", "polygon_xz": [[cx - 20, cz - 20], [cx + 20, cz - 20], [cx + 20, cz + 20], [cx - 20, cz + 20]],
                                         "margin_m": 5.0}]}), encoding="utf-8")
run("n30", "G1", lambda: write("n30", models, midx, m), lambda p: G1(p, "--exclude", exf))
# ---- G4
def lifted():
    mm = m.copy()
    mm[::50, 10] += 0.30
    return write("n12", models, midx, mm)


def nobc():
    mm = m.copy()
    for k in range(0, len(mm), 50):
        M = mm[k, :9].reshape(3, 3).T
        mm[k, 9:12] -= M @ np.array(mods[models[midx[k]]]["bc"])
    return write("n13", models, midx, mm)


def steep():
    mm = m.copy()
    k = bush_i
    s = np.linalg.norm(mm[k, 0:3])
    th = np.radians(64)
    Rx = np.array([[1, 0, 0], [0, np.cos(th), -np.sin(th)], [0, np.sin(th), np.cos(th)]])
    M = Rx * s
    mm[k, :9] = M.T.ravel()
    return write("n14", models, midx, mm)


run("n12", "G4", lifted, lambda p: G45(p, "G4"))
run("n13", "G4", nobc, lambda p: G45(p, "G4"))
run("n14", "G4", steep, lambda p: G45(p, "G4"))
# ---- G5
def g5fix(name):
    mm, mo, mi, ek = m.copy(), list(models), midx.copy(), None
    if name == "n15":
        mm[3, 4] = np.nan
    elif name == "n16":
        mm[3, 1] += 0.2
    elif name == "n17":
        ek = {3: {"id": 1}}
    elif name == "n18":
        mo = mo + ["dz\\plants_bliss\\tree\\t_doesnotexist_summer.p3d"]
        mi[3] = len(mo) - 1
    elif name == "n19":
        mo = mo + [mo[mi[3]].upper()]
        mi[3] = len(mo) - 1
    return write(name, mo, mi, mm, ek)


for nm in ("n15", "n16", "n17", "n18", "n19"):
    run(nm, "G5", lambda nm=nm: g5fix(nm), lambda p: G45(p, "G5"))
# ---- G2 / G3
trees = np.isin(fam, ["conifer", "broadleaf"])
run("n07", "G2", lambda: write("n07", models, midx[~(trees & (np.cumsum(trees) % 2 == 0))], m[~(trees & (np.cumsum(trees) % 2 == 0))]), G23)


def offpal():
    interior = set(nm for nm, _ in ref["palette"]["interior"]["conifer"])
    off = next(nm for nm in sorted(mods) if mods[nm]["family"] == "conifer" and nm not in interior)
    mo = sorted(set(models) | {off})
    mi = np.array([mo.index(models[i]) for i in midx])
    mi[fam == "conifer"] = mo.index(off)
    return write("n22", mo, mi, m)


run("n22", "G2", offpal, G23)
rr = np.clip(np.floor(m[:, 11] / 5).astype(int), 0, glib.NB - 1)
cc = np.clip(np.floor(m[:, 9] / 5).astype(int), 0, glib.NB - 1)
tsd = R.tsd[rr, cc]
bare = np.isin(fam, ["conifer", "broadleaf", "bush"]) & (tsd < 0) & (tsd >= -25)
run("n11", "G3", lambda: write("n11", models, midx[~bare], m[~bare]), G23)
# ---- G8
bog1 = R.big("bog1m")
slot1 = R.big("slot1m")
pi = np.clip((gcfg.MAP - m[:, 11]).astype(int), 0, gcfg.MAP - 1)
pj = np.clip(m[:, 9].astype(int), 0, gcfg.MAP - 1)
inbog, onff = bog1[pi, pj], slot1[pi, pj] == 1
wood_trees = np.flatnonzero(trees & inbog & onff)
drop40 = wood_trees[rng.random(wood_trees.size) > 40.0 / 150.0]
keep40 = np.setdiff1d(np.arange(len(midx)), drop40)
run("n40", "G8", lambda: write("n40", models, midx[keep40], m[keep40]), G8)


def clearings():
    ff = R.tex_samp & ~R.water
    rr_, cc_ = np.nonzero(ff[int(z0 // 5):int(z1 // 5), int(x0 // 5):int(x1 // 5)])
    nd = int(0.02 * len(rr_) * 25 / (np.pi * 25 ** 2))
    pick = rng.choice(len(rr_), nd, replace=False)
    cxs, czs = x0 + (cc_[pick] + 0.5) * 5, z0 + (rr_[pick] + 0.5) * 5
    from scipy.spatial import cKDTree
    hit = cKDTree(np.c_[cxs, czs]).query(m[:, [9, 11]], distance_upper_bound=25.0)[0] < 25.0
    k = ~(hit & trees)
    return write("n41", models, midx[k], m[k])


run("n41", "G8", clearings, G8)
sq = (m[:, 9] >= x0 + 500) & (m[:, 9] < x0 + 1500) & (m[:, 11] >= z0 + 500) & (m[:, 11] < z0 + 1500)
run("n42", "G8", lambda: write("n42", models, midx[sq], m[sq]), G8)
# ---- G7
def open_fill():
    ob = (bog1[int(gcfg.MAP - z1):int(gcfg.MAP - z0), int(x0):int(x1)]) & (slot1[int(gcfg.MAP - z1):int(gcfg.MAP - z0), int(x0):int(x1)] != 1)
    ii_, jj_ = np.nonzero(ob)
    nadd = int(len(ii_) / 1e4 * 120)
    pk = rng.choice(len(ii_), nadd, replace=False)
    pine = next(i for i in range(len(midx)) if "pinussylvestris_1s" in models[midx[i]])
    new = np.array([moved(pine, x0 + jj_[k] + rng.random(), z1 - ii_[k] - rng.random()) for k in pk])
    return write("n43", models, np.r_[midx, np.full(nadd, midx[pine])], np.vstack([m, new]))


run("n43", "G7", open_fill, G7)
run("n44", "G7", lambda: write("n44", models, midx[keep40], m[keep40]), G7)


def spruce():
    sp = "dz\\plants_bliss\\tree\\t_piceaabies_2f_summer.p3d"
    mo = sorted(set(models) | {sp})
    mi = np.array([mo.index(models[i]) for i in midx])
    pines = np.array(["pinussylvestris" in models[i] for i in midx])
    mi[pines] = mo.index(sp)
    return write("n45", mo, mi, m)


run("n45", "G7", spruce, G7)
(W / "negatives.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(f"negatives detected {sum(v['detected'] for v in res.values())} / {len(res)}")
