"""Pond layer v31, step S11 (exact): every compiled p31 triangle against footprint.npz.

For each added record (stage report): compiled ODOL roadway and visual triangles + record position. Each roadway triangle
must be one native half-cell, A = (NW, NE, SE) or B = (NW, SE, SW), with |dXZ| <= TOL from the 6 m grid and y == band
level; each visual triangle the same half-cell with y == F at its corners. Gates: every footprint half-cell covered exactly
once by the roadway and once by the visual, nothing outside the footprint, no level error > TOL.
Every model must parse with no LOD error and hold exactly one visual LOD (resolution 1.0) and exactly one roadway LOD
(resolution 3e15, relative 1e-6); a model that does not is listed in model_errors, adds no triangles and fails the run
(the nearest-resolution pick used before accepted a model whose roadway LOD was missing). Exit 0 only on pass.
Usage: verify_pond_exact_v31.py <stage_report.json> <footprint.npz> <water_temp_dir> <out.json> [--window x0 x1 z0 z1]
"""
import json, sys
import numpy as np
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
from odol_reader import ODOL

ZTOP, TOL = 12282, 1e-3
RES_VIS, RES_ROAD = 1.0, 3e15


def pick_lods(od):
    """(roadway, visual) LODs of one model, or a reason string."""
    if getattr(od, "lod_errors", None):
        return f"LOD read errors {od.lod_errors}"
    if any(l is None for l in od.lods):
        return "a LOD did not parse"
    road = [l for l in od.lods if abs(l.resolution - RES_ROAD) <= RES_ROAD * 1e-6]
    vis = [l for l in od.lods if abs(l.resolution - RES_VIS) <= 1e-6]
    if len(road) != 1 or len(vis) != 1:
        return f"needs exactly one roadway (3e15) and one visual (1.0) LOD, has {len(road)} and {len(vis)}; resolutions {od.resolutions}"
    return road[0], vis[0]


def lod_tris(lod):
    v = np.array([(p.x, p.y, p.z) for p in lod.vertices])
    return np.array([v[list(f.vertex_indices)] for f in lod.faces])


def classify(t):
    """(r, c, kind, corner indices per vertex) of a world triangle on the native grid, or None."""
    xs, zs = t[:, 0], t[:, 2]
    c0, r0 = int(np.floor(xs.min() / 6 + 1e-6)), int(np.floor((ZTOP - zs.max()) / 6 + 1e-6))
    gx, gz = (xs - 6 * c0) / 6, ((ZTOP - 6 * r0) - zs) / 6
    if np.abs(gx - np.rint(gx)).max() * 6 > TOL or np.abs(gz - np.rint(gz)).max() * 6 > TOL:
        return None
    pts = {(int(round(a)), int(round(b))) for a, b in zip(gx, gz)}           # (dc, dr) in {0,1}
    corner = {(0, 0): 0, (1, 0): 1, (0, 1): 2, (1, 1): 3}                    # NW, NE, SW, SE
    if pts == {(0, 0), (1, 0), (1, 1)}:
        kind = 0
    elif pts == {(0, 0), (1, 1), (0, 1)}:
        kind = 1
    else:
        return None
    idx = [corner[(int(round(a)), int(round(b)))] for a, b in zip(gx, gz)]
    return r0, c0, kind, idx


def main():
    rep_path, fp_path, temp, out = sys.argv[1:5]
    win = [float(v) for v in sys.argv[6:10]] if len(sys.argv) > 5 and sys.argv[5] == "--window" else None
    rep = json.load(open(rep_path))
    fp = np.load(fp_path); plane, field = fp["plane"].astype(float), fp["field"]
    road_cnt = np.zeros(plane.shape + (2,), np.int32); vis_cnt = np.zeros_like(road_cnt)
    cache, bad_tri, lvl_err, vis_err, model_errors = {}, 0, 0.0, 0.0, {}
    for a in rep["added_list"]:
        name = a["model"]
        if name not in cache:
            try:
                got = pick_lods(ODOL.from_file(f"{temp}/{name}"))
            except Exception as e:                      # unreadable model: fail closed, keep going to list them all
                got = f"read failed: {type(e).__name__}: {e}"
            if isinstance(got, str):
                model_errors[name] = got
                cache[name] = None
            else:
                cache[name] = (lod_tris(got[0]), lod_tris(got[1]))
        if cache[name] is None:
            continue
        rt, vt = cache[name]
        pos = np.array(a["position"])
        for tris, cnt, visual in ((rt, road_cnt, False), (vt, vis_cnt, True)):
            for t in tris + pos:
                k = classify(t)
                if k is None:
                    bad_tri += 1; continue
                r, c, kind, idx = k
                if not (0 <= r < 2047 and 0 <= c < 2047) or not np.isfinite(plane[r, c]):
                    bad_tri += 1; continue
                cnt[r, c, kind] += 1
                if visual:
                    vis_err = max(vis_err, float(np.abs(t[:, 1] - field[r, c, idx]).max()))
                else:
                    lvl_err = max(lvl_err, float(np.abs(t[:, 1] - plane[r, c]).max()))
    want = np.isfinite(plane)
    if win:
        x0, x1, z0, z1 = win
        R, C = np.mgrid[0:2047, 0:2047]
        want &= (6 * C >= x0) & (6 * C + 6 <= x1) & (ZTOP - 6 * R - 6 >= z0) & (ZTOP - 6 * R <= z1)
    w2 = np.repeat(want[..., None], 2, -1)
    res = dict(records=len(rep["added_list"]), models=len(cache), footprint_half_cells=int(w2.sum()),
               triangles_off_grid_or_outside=bad_tri,
               roadway_missing=int((w2 & (road_cnt == 0)).sum()), roadway_multiple=int((road_cnt > 1).sum()),
               roadway_outside=int((~w2 & (road_cnt > 0)).sum()),
               visual_missing=int((w2 & (vis_cnt == 0)).sum()), visual_multiple=int((vis_cnt > 1).sum()),
               visual_outside=int((~w2 & (vis_cnt > 0)).sum()),
               max_roadway_level_err_m=lvl_err, max_visual_field_err_m=vis_err,
               model_errors=len(model_errors), model_error_list=dict(sorted(model_errors.items())[:20]))
    res["pass"] = bool(all(res[k] == 0 for k in ("triangles_off_grid_or_outside", "roadway_missing", "roadway_multiple", "roadway_outside",
                                                  "visual_missing", "visual_multiple", "visual_outside", "model_errors"))
                       and lvl_err <= TOL and vis_err <= TOL)
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res, indent=1))
    sys.exit(0 if res["pass"] else 1)


if __name__ == "__main__":
    main()
