"""Stage EV98: finish separating pond water from the engine sea on EV97.

Rule: no pond piece may lie over a wet vertex whose bed is below SEA_CLEAR, because the engine sea (0.75 +- 0.1,
fake wave up to ~+0.19) then draws under the pond and shows through as gray/wavy patches. Per water piece
(physical roadway footprint, cells whose centre lies inside it):
  * level < SEA_BAND_TOP (pond plane inside the sea band)            -> remove the piece; the water there is sea;
  * level - SEA_CLEAR >= MIN_DEPTH                                   -> raise the bed of its wet sub-clear corners
                                                                        to SEA_CLEAR (never reserve/platform);
  * otherwise (level too close to the clear floor)                   -> remove the piece.
Dry vertices are never edited. Inputs are hash-pinned; outputs go to a fresh folder.
"""
import collections, hashlib, json, re, shutil, sys, time
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon
from rasterio.features import rasterize
from affine import Affine

sys.path.insert(0, r"C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain")
sys.path.insert(0, r"C:/Users/guill/.claude/skills/dayz-p3d-debinarizer/scripts")
from wrp0wzd import read, write  # noqa: E402
from odol_reader import ODOL  # noqa: E402

EV97 = Path("E:/DayZ-Baltic-Build/v30-dry-relief-smoothing-20261011")
OUT = Path("E:/DayZ-Baltic-Build/v30-pond-sea-separation-20261011-b")
MODELS = Path("E:/DayZ-Baltic-Build/v30-global-contour-pass-20261009/package/water/temp/baltic_water_v30")
TREE = EV97 / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
PINS = {EV97 / "terrain-ev97.npz": "766cbd9905614be879236a4ae4d37c779681f69d141ecc684c7370cfed1754e1",
        TREE / "baltic_trial.wrp": "f227984c1f6780e84bb94090ad0f06a1cc4b77403867352fa5bf24b4f8530df0"}
SEA_BAND_TOP = 0.95
SEA_CLEAR = 1.0
MIN_DEPTH = 0.05
T = Affine(6, 0, 0, 0, -6, 12282)  # cell (r, c): x in [6c, 6c+6], z in [12282-6(r+1), 12282-6r]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    for p, h in PINS.items():
        assert sha(p) == h, p
    if OUT.exists():
        raise FileExistsError(OUT)
    OUT.mkdir(parents=True)
    t0 = time.time()
    z = np.load(EV97 / "terrain-ev97.npz")
    arrays = {k: z[k].copy() for k in z.files}
    H = arrays["heights"]
    W = arrays["water"] | (arrays["cls"] > 0)
    # Wet road-reserve vertices under the Narva bridge carry no road surface (the road is on the deck); Narva local
    # edits were authorized on 2026-10-08, so they may take the clear bed. Every other reserve/platform vertex stays.
    frozen = (arrays["reserve"] | arrays["platform"]) & ~(arrays["narva"] & W)
    wrp = read(TREE / "baltic_trial.wrp")
    assert np.array_equal(wrp["heights"], H[::-1])

    cache = {}
    H2 = H.copy()
    keep, removed, raised_by, stats = [], [], collections.Counter(), collections.Counter()
    blocked_frozen = []
    for o in wrp["objects"]:
        name = o["name"].lower()
        if not name.startswith("baltic_water_v30"):
            keep.append(o["bytes"])
            continue
        model = name.split("\\")[-1]
        if model not in cache:
            od = ODOL.from_file(str(MODELS / model))
            road = min(od.lods, key=lambda l: abs(l.resolution - 3e15))
            rv = np.array([(v.x, v.y, v.z) for v in road.vertices])
            poly = shapely.union_all([Polygon(rv[list(f.vertex_indices)][:, [0, 2]]) for f in road.faces])
            cache[model] = (float(rv[:, 1].mean()), poly)
        y_local, poly = cache[model]
        pos = np.array(o["matrix"][9:12])
        level = y_local + float(pos[1])
        fam = re.sub(r"_[0-9].*", "", model)
        if level < SEA_BAND_TOP:
            removed.append(dict(name=o["name"], level=round(level, 3), reason="sea_band"))
            stats["removed_sea_band_" + fam] += 1
            continue
        shape = shapely.affinity.translate(poly, pos[0], pos[2])
        x0, z0, x1, z1 = shape.bounds
        c0, c1 = max(0, int(np.floor(x0 / 6)) - 1), min(2047, int(np.ceil(x1 / 6)) + 1)
        r0, r1 = max(0, int(np.floor((12282 - z1) / 6)) - 1), min(2047, int(np.ceil((12282 - z0) / 6)) + 1)
        win = Affine(6, 0, 6 * c0, 0, -6, 12282 - 6 * r0)
        cells = rasterize([(shape, 1)], out_shape=(r1 - r0, c1 - c0), transform=win, fill=0, all_touched=False, dtype="uint8") > 0
        rr, cc = np.nonzero(cells)
        rr, cc = rr + r0, cc + c0
        if rr.size == 0:
            keep.append(o["bytes"])
            continue
        vr = np.concatenate([rr, rr, rr + 1, rr + 1])
        vc = np.concatenate([cc, cc + 1, cc, cc + 1])
        sub = W[vr, vc] & (H2[vr, vc] < SEA_CLEAR)
        if not sub.any():
            keep.append(o["bytes"])
            continue
        if level - SEA_CLEAR < MIN_DEPTH:
            removed.append(dict(name=o["name"], level=round(level, 3), reason="too_shallow_for_clear_bed",
                                sub_clear_vertices=int(sub.sum())))
            stats["removed_shallow_" + fam] += 1
            continue
        tr, tc = vr[sub], vc[sub]
        fz = frozen[tr, tc]
        if fz.any():
            blocked_frozen.append(dict(name=o["name"], level=round(level, 3), frozen_vertices=int(fz.sum())))
        tr, tc = tr[~fz], tc[~fz]
        H2[tr, tc] = np.float32(SEA_CLEAR)
        raised_by[fam] += int(len(set(zip(tr.tolist(), tc.tolist()))))
        keep.append(o["bytes"])

    # removed sea-band pieces: their wet vertices are sea now; keep metadata consistent for later tools
    changed = H2 != H
    assert not (changed & ~W).any(), "dry vertex edited"
    assert not (changed & frozen).any(), "frozen vertex edited"
    narva_exception = int((changed & arrays["reserve"] & arrays["narva"]).sum())
    tree = OUT / "stage/root/dayz_baltic_12km_dev/tb/narva_trial"
    shutil.copytree(TREE, tree)
    (tree / "baltic_trial.wrp").unlink()
    write(tree / "baltic_trial.wrp", wrp["header"], H2[::-1], wrp["materials"], keep, wrp["terminator"])
    back = read(tree / "baltic_trial.wrp")
    assert np.array_equal(back["heights"], H2[::-1]) and len(back["objects"]) == len(keep)
    arrays["heights"] = H2
    arrays["ev98_bed_raised"] = changed
    np.savez(OUT / "terrain-ev98.npz", **arrays)
    report = dict(schema="ev98-pond-sea-separation.v1", inputs={str(p): h for p, h in PINS.items()},
                  params=dict(SEA_BAND_TOP=SEA_BAND_TOP, SEA_CLEAR=SEA_CLEAR, MIN_DEPTH=MIN_DEPTH),
                  objects_before=len(wrp["objects"]), objects_after=len(keep), pieces_removed=len(removed),
                  removed_by=dict(stats), bed_raised_vertices=int(changed.sum()), raised_by_family=dict(raised_by),
                  pieces_with_frozen_sub_clear=len(blocked_frozen), narva_reserve_wet_raised=narva_exception, blocked_frozen=blocked_frozen,
                  removed=removed, wrp_sha256=sha(tree / "baltic_trial.wrp"),
                  terrain_sha256=sha(OUT / "terrain-ev98.npz"), seconds=round(time.time() - t0, 1))
    (OUT / "stage-report.json").write_text(json.dumps(report, indent=1))
    print({k: v for k, v in report.items() if k not in ("removed", "blocked_frozen", "inputs")})


if __name__ == "__main__":
    main()
