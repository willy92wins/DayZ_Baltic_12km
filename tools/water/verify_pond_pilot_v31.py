"""Pond layer v31 pilot, step S11 (subset): compiled coverage of the staged WRP against footprint.npz.

For every cell in the window plus a MARGIN-tile frame, two sample points (centroids of the native triangles) are tested
against the compiled roadway triangles (record position + ODOL vertices) of every water record near the window.
Counts per sample: new p31 cover, old cover. Gates: new cover == footprint exactly (each sample covered once), no
sample covered by both a new and an old record, no footprint sample in the frame left uncovered, and compiled roadway
heights == band level, compiled visual heights == F at the cell corners (|d| <= 1e-4).
Usage: verify_pond_pilot_v31.py <stage_report.json> <footprint.npz> <wrp> <water_temp_dir> <out.json>
"""
import json, sys
import numpy as np
from shapely import STRtree, points as shp_points
from shapely.geometry import Polygon
sys.path[:0] = [r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts",
                r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\tools\terrain"]
from odol_reader import ODOL
from wrp0wzd import read

PREFIX, ZTOP, MARGIN = "baltic_water_v30\\", 12282, 2


def lod_tris(lod, pos):
    v = np.array([(p.x, p.y, p.z) for p in lod.vertices]) + pos
    out = []
    for f in lod.faces:
        idx = list(f.vertex_indices)
        out.append(v[idx])
    return out


def main():
    rep_path, fp_path, wrp, temp, out = sys.argv[1:6]
    rep = json.load(open(rep_path))
    wx0, wx1, wz0, wz1 = rep["window"]
    fx0, fx1, fz0, fz1 = wx0 - 48 * MARGIN, wx1 + 48 * MARGIN, wz0 - 48 * MARGIN, wz1 + 48 * MARGIN
    fp = np.load(fp_path); plane, field = fp["plane"].astype(float), fp["field"]
    added = {a["id"] for a in rep["added_list"]}
    w = read(wrp)
    cache, polys, kinds, info = {}, [], [], []
    vis_err = road_err = 0.0
    for o in w["objects"]:
        if not o["name"].startswith(PREFIX):
            continue
        pos = np.array(o["matrix"][9:12])
        if not (fx0 - 60 <= pos[0] <= fx1 + 60 and fz0 - 60 <= pos[2] <= fz1 + 60):
            continue
        name = o["name"][len(PREFIX):]
        if name not in cache:
            od = ODOL.from_file(f"{temp}/{name}"); bc = od.model_info.bounding_center
            cache[name] = (od, np.array([bc.x, bc.y, bc.z]))
        od, bc = cache[name]
        road = min(od.lods, key=lambda l: abs(l.resolution - 3e15))
        for t in lod_tris(road, pos):
            polys.append(Polygon(t[:, [0, 2]])); kinds.append(o["id"] in added); info.append(o["id"])
            if o["id"] in added:
                road_err = max(road_err, float(np.abs(t[:, 1] - round(t[:, 1].mean() / 0.025) * 0.025).max()))
        if o["id"] in added:
            vis = min(od.lods, key=lambda l: abs(l.resolution - 1))
            for t in lod_tris(vis, pos):
                for x, y, z in t:
                    c = int(round(x / 6)); r = int(round((ZTOP - z) / 6))
                    # the vertex is a corner of some footprint cell; compare against any incident cell's F at that corner
                    best = 9.0
                    for (dr, dc, k) in ((0, 0, 0), (0, -1, 1), (-1, 0, 2), (-1, -1, 3)):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < 2047 and 0 <= cc < 2047 and np.isfinite(plane[rr, cc]):
                            best = min(best, abs(field[rr, cc, k] - y))
                    vis_err = max(vis_err, best)
    tree = STRtree(polys)
    kinds = np.array(kinds)
    r0, r1 = int((ZTOP - fz1) / 6), int((ZTOP - fz0) / 6); c0, c1 = int(fx0 / 6), int(fx1 / 6)
    R, C = np.mgrid[r0:r1, c0:c1]
    sx = np.stack([6 * C + 4, 6 * C + 2], -1).astype(float)          # centroid of A (NW,NE,SE) and B (NW,SE,SW)
    sz = np.stack([ZTOP - 6 * R - 2, ZTOP - 6 * R - 4], -1).astype(float)
    pts = shp_points(sx.ravel(), sz.ravel())
    pi, ti = tree.query(pts, predicate="within")
    newc = np.bincount(pi[kinds[ti]], minlength=len(pts)).reshape(sx.shape)
    oldc = np.bincount(pi[~kinds[ti]], minlength=len(pts)).reshape(sx.shape)
    inwin = ((6 * C >= wx0) & (6 * C + 6 <= wx1) & (ZTOP - 6 * R - 6 >= wz0) & (ZTOP - 6 * R <= wz1))[..., None].repeat(2, -1)
    want = np.isfinite(plane[r0:r1, c0:c1])[..., None].repeat(2, -1)
    res = dict(window=rep["window"], frame_tiles=MARGIN, samples=int(sx.size), new_records_checked=len(added),
               new_cover_eq_footprint_in_window=int(((newc > 0) != (want & inwin)).sum()),
               new_cover_multiple=int((newc > 1).sum()), new_cover_outside_window=int(((newc > 0) & ~inwin).sum()),
               overlap_new_old=int(((newc > 0) & (oldc > 0)).sum()),
               footprint_uncovered_in_frame=int((want & ~inwin & (oldc == 0)).sum()),
               old_cover_samples_in_window=int(((oldc > 0) & inwin).sum()),
               max_roadway_level_err_m=road_err, max_visual_vs_field_err_m=vis_err)
    res["pass"] = bool(res["new_cover_eq_footprint_in_window"] == 0 and res["new_cover_multiple"] == 0 and res["overlap_new_old"] == 0
                   and res["new_cover_outside_window"] == 0 and road_err <= 1e-4 and vis_err <= 1e-4)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
