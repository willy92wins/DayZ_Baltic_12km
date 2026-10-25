"""Negative controls for G1-G5: each mutated record set must make its gate print FAIL (exit 1).

Usage: python -I negatives.py <records.json> <instances.npy> <work_dir>
Writes the mutated records under work_dir and prints one line per control: name, gate, expected FAIL, observed.
v2 (EV111 review 1): n10/n11 follow the texture-distance edge (instances.npy dt); n21 = the v1 fallen beech that crossed
the road strip with its Geometry LOD (WRP 16867473, fixture neg_fixtures/n21-fallen-beech-road.json); n22 = every
conifer in the canopy interior swapped for a conifer of the same size and form absent from the Livonia interior
reference (review 1 species_negative.py). n20 (placer without edge rules, several seeds) runs in neg_tools/run_n20.py.
n09 (trees moved to uniform random positions in the sector box) is a structure-against-texture control: it is counted
on G3 (texture-relative edge bins); its G2 and G1 verdicts are recorded as informative (G2 rebuilds its canopy
contexts from the moved trees and judges per context, so it sees little of it).
v3 (EV111 bog, strict G2/G3): n09 is counted on G2 again, as in v1: with the strict contract restored G2 rejects it
(dense rule, riparian density, broadleaf spacing), while G3 no longer can: a uniform scatter leaves no canopy edge to
judge (edge context 0.4-0.5 ha, below the 5 ha minimum) and, with the bog left out, few texture bins outside the forest
floor; its G3 and G1 verdicts are recorded as informative.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate_common as GC  # noqa: E402
import geom  # noqa: E402

PY = sys.executable
recs_path, inst_path, work = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
work.mkdir(parents=True, exist_ok=True)
recs = GC.load_records(recs_path)
inst = np.load(inst_path)
ref = json.loads(GC.REFERENCE.read_text(encoding="utf-8"))
models = ref["models"]
t = np.load(GC.TERRAIN)
fp = np.load(GC.FOOTPRINT)
H = t["heights"].astype(np.float64)
secs = {s["name"]: s for s in json.loads(GC.SECTORS.read_text(encoding="utf-8"))["sectors"]}
B = np.asarray(secs["B-bosque-carretera-agua"]["polygon_xz"], float)
CON = "dz\\plants_bliss\\tree\\t_piceaabies_3f_summer.p3d"
BUSH = "dz\\plants_bliss\\bush\\b_betulanana_1s_summer.p3d"
ROSA = "dz\\plants_bliss\\bush\\b_rosacanina_1s_summer.p3d"
for nm in (CON, BUSH, ROSA):
    assert nm in models, nm


def rec_at(model, x, z):
    h = float(geom.h_at(H, np.array([x]), np.array([z]))[0])
    bc = np.array(models[model]["bc"], float)
    T = np.array([x, h, z]) + bc
    return {"model": model, "matrix": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, *map(float, T)]}


def inside_B(x, z):
    return GC.in_poly(np.array([x]), np.array([z]), B)[0]


# ---- locate test sites from the inputs
A_, _ = geom.road_segments()
road_pt = next(p for p in A_ if inside_B(*p))
xs, zs = np.meshgrid(np.arange(B[:, 0].min(), B[:, 0].max(), 1.0) + 0.5, np.arange(B[:, 1].min(), B[:, 1].max(), 1.0) + 0.5)
h1 = geom.h_at(H, xs, zs)
rr = np.clip(np.floor((GC.ZTOP - zs) / 6).astype(int), 0, GC.N - 2)
cc = np.clip(np.floor(xs / 6).astype(int), 0, GC.N - 2)
pl = fp["plane"][rr, cc]
wet = np.isfinite(pl) & (h1 < np.nan_to_num(pl, nan=-1e9) - 0.2)
wi = np.argwhere(wet)[0]
water_pt = (float(xs[tuple(wi)]), float(zs[tuple(wi)]))
cm = (H[:-1, :-1] < 0.5) & (H[1:, :-1] < 0.5) & (H[:-1, 1:] < 0.5) & (H[1:, 1:] < 0.5) & ~np.isfinite(fp["env_plane"])
sr, sc = np.argwhere(cm)[len(np.argwhere(cm)) // 2]
sea_pt = (6.0 * sc + 3.0, GC.ZTOP - 6.0 * sr - 3.0)
sys.path.insert(0, r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\terrain")
from wrp0wzd import read as read_wrp  # noqa: E402
objs = read_wrp(GC.STAGE_WRP)["objects"]
bridge = min((o for o in objs if "bridges" in o["name"]), key=lambda o: abs(o["matrix"][9] - 8575) + abs(o["matrix"][11] - 7003))
bridge_pt = (bridge["matrix"][9], bridge["matrix"][11])
kit = next(o for o in objs if "streambed" in o["name"])
kit_pt = (kit["matrix"][9], kit["matrix"][11])
nr, nc = np.argwhere(t["narva"])[0]
narva_pt = (6.0 * nc, GC.ZTOP - 6.0 * nr)
# steepest upper triangle on the map; the bush goes on its incentre, 1.757 m from the legs (rosacanina: trunk 1.17 m,
# embed 0.39 m -> its base floats above ~19 deg)
dc_ = H[:-1, 1:] - H[:-1, :-1]
dr_ = H[1:, 1:] - H[:-1, 1:]
tsl = np.degrees(np.arctan(np.hypot(dc_, dr_) / 6.0))
steep = np.unravel_index(np.argmax(tsl), tsl.shape)
steep_pt = (6.0 * steep[1] + 6.0 - 1.757, GC.ZTOP - 6.0 * steep[0] - 1.757)
sites = {"road": road_pt.tolist(), "water": water_pt, "sea": sea_pt, "bridge": bridge_pt, "kit": kit_pt, "narva": narva_pt,
         "steep": steep_pt, "steep_slope_deg": float(tsl[steep])}
print("sites", json.dumps(sites))

trees = np.isin(inst["fam"], [0, 1])
controls = []


def write(name, rs):
    p = work / f"{name}.json"
    p.write_text(json.dumps(rs) + "\n", encoding="ascii")
    return p


controls.append(("n01-road-tree", "g1", write("n01-road-tree", recs + [rec_at(CON, *sites["road"])])))
controls.append(("n02-water-bush", "g1", write("n02-water-bush", recs + [rec_at(BUSH, *sites["water"])])))
controls.append(("n03-sea-tree", "g1", write("n03-sea-tree", recs + [rec_at(CON, *sites["sea"])])))
controls.append(("n04-bridge-tree", "g1", write("n04-bridge-tree", recs + [rec_at(CON, *sites["bridge"])])))
controls.append(("n05-kit-tree", "g1", write("n05-kit-tree", recs + [rec_at(CON, *sites["kit"])])))
controls.append(("n06-narva-tree", "g1", write("n06-narva-tree", recs + [rec_at(CON, *sites["narva"])])))
# G2: half the trees, no broadleaf, trees moved to random positions
half = [r for k, r in enumerate(recs) if not (trees[k] and k % 2)]
controls.append(("n07-half-trees", "g2", write("n07-half-trees", half)))
controls.append(("n08-no-broadleaf", "g2", write("n08-no-broadleaf", [r for k, r in enumerate(recs) if inst["fam"][k] != 1])))
rng = np.random.default_rng(7)
pois = []
for k, r in enumerate(recs):
    if trees[k]:
        m = list(r["matrix"])
        sec = list(secs.values())[int(inst["sector"][k])]
        pp = np.asarray(sec["polygon_xz"], float)
        m[9] = float(rng.uniform(pp[:, 0].min(), pp[:, 0].max()))
        m[11] = float(rng.uniform(pp[:, 1].min(), pp[:, 1].max()))
        r = {"model": r["model"], "matrix": m}
    pois.append(r)
p09 = write("n09-poisson-trees", pois)
controls += [("n09-poisson-trees", "g2", p09), ("n09-poisson-trees (info)", "g3", p09), ("n09-poisson-trees (info)", "g1", p09)]
# G3: no bushes along the texture edge (-40..15 m); a bare edge (no trees nor bushes in the 25 m outside the texture)
RIP = 4                                                     # forest_v31.CLASSES.index("riparian")
dt_, cl_, fa_ = inst["dt"], inst["cls"], inst["fam"]
controls.append(("n10-no-edge-bushes", "g3", write("n10-no-edge-bushes", [r for k, r in enumerate(recs)
                                                                          if not (fa_[k] == 2 and -40 <= dt_[k] < 15 and cl_[k] != RIP)])))
controls.append(("n11-bare-edge", "g3", write("n11-bare-edge", [r for k, r in enumerate(recs)
                                                                if not (fa_[k] in (0, 1, 2) and -25 <= dt_[k] < 0 and cl_[k] != RIP)])))
# G4: lifted records, bounding centre ignored, bush on the steepest slope
lift = [dict(r, matrix=r["matrix"][:10] + [r["matrix"][10] + 0.30] + r["matrix"][11:]) if k % 1000 == 0 else r for k, r in enumerate(recs)]
controls.append(("n12-lifted", "g4", write("n12-lifted", lift)))
nobc = []
for k, r in enumerate(recs):
    if trees[k] and k % 500 == 0:
        m = np.asarray(r["matrix"], float)
        M = m[:9].reshape(3, 3).T
        org = m[9:12] - M @ np.array(models[r["model"]]["bc"])
        r = {"model": r["model"], "matrix": [*m[:9].tolist(), *org.tolist()]}
    nobc.append(r)
controls.append(("n13-no-bounding-centre", "g4", write("n13-no-bounding-centre", nobc)))
controls.append(("n14-steep-bush", "g4", write("n14-steep-bush", recs + [rec_at(ROSA, *sites["steep"])])))
# G5: NaN, skewed axes, an id key, a missing model, an upper-case path
nan = [dict(r) for r in recs]; nan[0] = dict(nan[0], matrix=[float("nan")] + nan[0]["matrix"][1:])
skew = [dict(r) for r in recs]; skew[1] = dict(skew[1], matrix=[a * 1.1 for a in skew[1]["matrix"][:3]] + skew[1]["matrix"][3:])
idk = [dict(r) for r in recs]; idk[2] = dict(idk[2], id=1)
miss = [dict(r) for r in recs]; miss[3] = dict(miss[3], model="dz\\plants_bliss\\tree\\t_piceaabies_9z_summer.p3d")
upper = [dict(r) for r in recs]; upper[4] = dict(upper[4], model=upper[4]["model"][:3] + upper[4]["model"][3:].upper())
controls += [("n15-nan", "g5", write("n15-nan", nan).with_suffix(".json")), ("n16-skew", "g5", write("n16-skew", skew)),
             ("n17-id-key", "g5", write("n17-id-key", idk)), ("n18-missing-model", "g5", write("n18-missing-model", miss)),
             ("n19-upper-case-path", "g5", write("n19-upper-case-path", upper))]
# G1: the v1 fallen beech whose trunk crossed the road strip (origin 8.49 m from the axis, trunk at 1.05 m)
fx = json.loads((HERE.parent / "neg_fixtures/n21-fallen-beech-road.json").read_text(encoding="utf-8"))
controls.append(("n21-fallen-trunk-on-road", "g1", write("n21-fallen-trunk-on-road", recs + [fx["record"]])))
# G2: interior conifers swapped for conifers outside the Livonia interior reference (same size and form)
plane_ = fp["plane"]
sw = [dict(r) for r in recs]
Pm = np.array([r["matrix"][9:12] for r in recs])
n_sw = 0
for sec in secs.values():
    _, cx = GC.sector_measure(recs, ref, sec, H, plane_)
    ins = GC.in_poly(Pm[:, 0], Pm[:, 2], np.asarray(sec["polygon_xz"], float))
    for k in np.flatnonzero(ins):
        row, col = int((Pm[k, 2] - cx["z0"]) // 5), int((Pm[k, 0] - cx["x0"]) // 5)
        if cx["ctx"][row, col] != 0 or models[recs[k]["model"]]["family"] != "conifer":
            continue
        old = models[recs[k]["model"]]
        alt = sorted(nm for nm, v in models.items() if v["family"] == "conifer" and v["size"] == old["size"]
                     and v["solitary"] == old["solitary"] and nm not in ref["species_reference"]["interior"]["conifer"])
        if alt:
            sw[k] = dict(sw[k], model=alt[0])
            n_sw += 1
print("n22 swapped", n_sw)
controls.append(("n22-off-palette-species", "g2", write("n22-off-palette-species", sw)))
# ---- run
res = []
for name, gate, path in controls:
    args = [PY, "-I", str(HERE / ("g2_g3.py" if gate in ("g2", "g3") else gate + ".py")), str(path)]
    if gate in ("g2", "g3"):
        args += [gate.upper(), "--dense", "A-reserva"]
    p = subprocess.run(args, capture_output=True, text=True)
    last = [ln for ln in p.stdout.strip().splitlines() if ln.startswith(("G1", "G2", "G3", "G4", "G5"))]
    verdict = last[-1].split()[-1] if last else "ERROR"
    ok = verdict == "FAIL" and p.returncode == 1
    counted = "(info)" not in name
    res.append({"control": name, "gate": gate.upper(), "expected": "FAIL" if counted else "informative", "observed": verdict,
                "rc": p.returncode, "as_expected": ok, "counted": counted})
    (work / f"{name.split()[0]}-{gate}.log").write_text(p.stdout + p.stderr, encoding="utf-8")
    print(f"{name:26s} {gate.upper()} expected {'FAIL' if counted else 'info'} observed {verdict} rc {p.returncode} -> "
          f"{('OK' if ok else 'NOT DETECTED') if counted else 'informative'}")
(work / "negatives.json").write_text(json.dumps({"sites": sites, "controls": res}, indent=1) + "\n", encoding="utf-8")
print("NEGATIVES " + ("ALL DETECTED" if all(r["as_expected"] for r in res if r["counted"]) else "SOME NOT DETECTED"))
