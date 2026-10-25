"""G1 map-wide: zero instances inside the exclusion margins (the EV111 r2 g1.py rules, every record of the map).

Usage: python -I g1_map.py <records.json> <out.json> [--exclude polygons.json]
Origin = position - M . bounding_centre (reference bc), s = |M column 0|. Margins (unchanged from r2 g1.py):
  road     exact distance to the road chain polylines >= 3.5 + clearance(family): conifer 2.09, broadleaf 1.08,
           bush 0.71, dead 1.99, reed 0.71 m (exact segment distance for every instance a 0.5 m axis sample places
           within reach + 0.3 m; the others are farther than the limit by construction)
  water    no visible water (h < pond plane or h < 0.75 m) in the disc base_radius_plan * s + 0.25 m (reed 0.25 m):
           exact minimum of the planar terrain over the disc (geom.disc_min)
  sea      no engine sea band (h < 1.0 m in a cell outside the envelope) in the same disc
  bridge   distance to each bridge plan hull (visual bbox, staged EV110 WRP) >= crown_halfwidth * s + 1.0 m, and to the
           v31_bridge_cut / v31_bridge_fill cells
  kit      kit pieces and kit stones: distance to each plan hull >= base_radius_plan * s + 0.5 m; to v31_kit cells
  narva    distance to narva cells >= 6.0 m
  extra    --exclude polygons (dam / causeway sites): distance >= margin_m + base_radius_plan * s
  road_geometry  no Geometry LOD face below 3.5 m above the terrain and not fully buried may intersect the painted
           strip (road polylines buffered 3.5 m), for every instance whose position lies within 3.5 m + its largest
           geometry vertex radius x s + 1 m of an axis.
Prints the count per category and PASS (all zero) or FAIL."""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import shapely
from scipy.spatial import ConvexHull, cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gcfg  # noqa: E402
import glib  # noqa: E402

sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
sys.path.insert(0, str(gcfg.TOOL_DIR.parent / "terrain"))
import geom  # noqa: E402  (r2 gates)
from odol_reader import ODOL  # noqa: E402
from wrp0wzd import read as read_wrp  # noqa: E402

CLEAR = {"conifer": 2.09, "broadleaf": 1.08, "bush": 0.71, "dead": 1.99, "reed": 0.71}
BAND_H, BURIED, STRIP = 3.5, -0.05, 3.5
CH = 200000


def chunked(fn, n, *arrs):
    out = np.empty(n)
    for s0 in range(0, n, CH):
        out[s0:s0 + CH] = fn(*[x_[s0:s0 + CH] for x_ in arrs])
    return out


def cells_near(mask, x, z, reach):
    """Exact distance to flagged cells, computed only where a flagged cell lies within reach + 9 m (cell lookup)."""
    cm = mask[:-1, :-1] | mask[1:, :-1] | mask[:-1, 1:] | mask[1:, 1:]
    from scipy import ndimage
    k = int(np.ceil((reach + 9.0) / 6.0))
    dil = ndimage.binary_dilation(cm, structure=np.ones((2 * k + 1, 2 * k + 1), bool))
    r = np.clip(np.floor((gcfg.ZTOP - z) / 6.0).astype(int), 0, gcfg.N - 2)
    c = np.clip(np.floor(x / 6.0).astype(int), 0, gcfg.N - 2)
    cand = np.flatnonzero(dil[r, c])
    d = np.full(len(x), np.inf)
    if cand.size:
        d[cand] = geom.flagged_cell_distance(mask, x[cand], z[cand], reach)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("out")
    ap.add_argument("--exclude")
    a = ap.parse_args()
    t0 = time.time()
    MR = glib.MapRecords(a.records)
    models = MR.ref["models"]
    t = np.load(gcfg.TERRAIN)
    fp = np.load(gcfg.FOOTPRINT)
    H = t["heights"].astype(np.float64)
    plane, env = fp["plane"], fp["env_plane"]
    m = MR.m
    names = MR.names
    if (~MR.known).any():
        print(f"unknown models: {int((~MR.known).sum())}")
        print("G1 FAIL")
        return 1
    M = m[:, :9].reshape(-1, 3, 3).transpose(0, 2, 1)
    bc = np.array([models[nm]["bc"] for nm in names])
    org = m[:, 9:12] - np.einsum("nij,nj->ni", M, bc)
    s = np.linalg.norm(M[:, :, 0], axis=1)
    x, z = org[:, 0], org[:, 2]
    fam = np.array([models[nm]["family"] for nm in names])
    base = np.array([models[nm]["base_radius_plan"] for nm in names]) * s
    crown = np.array([models[nm]["crown_halfwidth"] for nm in names]) * s
    n = len(x)
    viol = {}
    A_, B_ = geom.road_segments()
    need = 3.5 + np.array([CLEAR[f] for f in fam])
    samp = []
    for p, q in zip(A_, B_):
        L = float(np.hypot(*(q - p)))
        k_ = max(1, int(np.ceil(L / 0.5)))
        tt = np.arange(k_ + 1) / k_
        samp.append(p + tt[:, None] * (q - p))
    kd = cKDTree(np.vstack(samp))
    dap = kd.query(np.c_[x, z], distance_upper_bound=float(need.max()) + 1.0)[0]
    near = np.flatnonzero(dap < need + 0.3)
    d = np.full(n, np.inf)
    d[near] = geom.seg_distance(x[near], z[near], A_, B_, float(need.max()) + 0.5)
    viol["road"] = np.flatnonzero(d < need)
    R = np.where(fam == "reed", 0.25, base + 0.25)
    pond = chunked(lambda xx, zz, rr: geom.disc_min(H, xx, zz, rr, lambda r, c: plane[r, c]), n, x, z, R)
    sealvl = chunked(lambda xx, zz, rr: geom.disc_min(H, xx, zz, rr, lambda r, c: np.full(r.shape, 0.75)), n, x, z, R)
    band = chunked(lambda xx, zz, rr: geom.disc_min(H, xx, zz, rr, lambda r, c: np.where(np.isfinite(env[r, c]), np.nan, 1.0)), n, x, z, R)
    viol["visible_water"] = np.flatnonzero((pond < 0) | (sealvl < 0))
    viol["sea"] = np.flatnonzero(band < 0)
    w = read_wrp(gcfg.STAGE_WRP)
    boxes = {}
    bad_bridge, bad_kit = np.zeros(n, bool), np.zeros(n, bool)
    n_obj = {"bridge": 0, "kit": 0}
    for o in w["objects"]:
        nm = o["name"]
        if "baltic_water_v30" in nm:
            continue
        if nm not in boxes:
            mi = ODOL.from_file("P:/DZ/" + nm[3:].replace("\\", "/")).model_info
            boxes[nm] = ([mi.bbox_min_visual.x, mi.bbox_min_visual.y, mi.bbox_min_visual.z], [mi.bbox_max_visual.x, mi.bbox_max_visual.y, mi.bbox_max_visual.z])
        lo, hi = boxes[nm]
        om = np.asarray(o["matrix"], float)
        corners = np.array([[a_, b_, c_] for a_ in (lo[0], hi[0]) for b_ in (lo[1], hi[1]) for c_ in (lo[2], hi[2])])
        P = corners @ om[:9].reshape(3, 3) + om[9:12]
        xz = P[:, [0, 2]]
        hull = xz[ConvexHull(xz).vertices]
        kind = "bridge" if "bridges" in nm.lower() else "kit"
        n_obj[kind] += 1
        nr = np.flatnonzero((x > hull[:, 0].min() - 30) & (x < hull[:, 0].max() + 30) & (z > hull[:, 1].min() - 30) & (z < hull[:, 1].max() + 30))
        if not nr.size:
            continue
        dd = geom.poly_distance(x[nr], z[nr], hull)
        lim = crown[nr] + 1.0 if kind == "bridge" else base[nr] + 0.5
        (bad_bridge if kind == "bridge" else bad_kit)[nr[dd < lim]] = True
    db = cells_near(t["v31_bridge_cut"] | t["v31_bridge_fill"], x, z, float((crown + 1.0).max()))
    bad_bridge |= db < crown + 1.0
    dk = cells_near(t["v31_kit"], x, z, float((base + 0.5).max()))
    bad_kit |= dk < base + 0.5
    viol["bridge"] = np.flatnonzero(bad_bridge)
    viol["kit"] = np.flatnonzero(bad_kit)
    dn = cells_near(t["narva"], x, z, 6.0)
    viol["narva"] = np.flatnonzero(dn < 6.0)
    if a.exclude:
        bad = np.zeros(n, bool)
        for ex in json.loads(Path(a.exclude).read_text(encoding="utf-8"))["polygons"]:
            pg = np.asarray(ex["polygon_xz"], float)
            nr = np.flatnonzero((x > pg[:, 0].min() - 60) & (x < pg[:, 0].max() + 60) & (z > pg[:, 1].min() - 60) & (z < pg[:, 1].max() + 60))
            if nr.size:
                bad[nr[geom.poly_distance(x[nr], z[nr], pg) < float(ex["margin_m"]) + base[nr]]] = True
        viol["extra_exclusions"] = np.flatnonzero(bad)
    # road geometry (faces in the vehicle band against the painted strip)
    lines = [shapely.LineString(np.asarray(c_, float)) for c_ in geom_chains() if len(c_) >= 2]
    strip = shapely.buffer(shapely.multilinestrings(lines), STRIP, quad_segs=32)
    shapely.prepare(strip)
    net = shapely.multilinestrings(lines)
    geo = {}
    for nm in sorted(set(names.tolist())):
        od = ODOL.from_file("P:/DZ/" + nm[3:].replace("\\", "/"))
        lod = next((l_ for l_ in od.lods if 0.9e13 < l_.resolution < 1.1e13 and l_.vertices and l_.faces), None)
        if lod is None:
            raise SystemExit(f"{nm}: no Geometry LOD")
        V = np.array([[v.x, v.y, v.z] for v in lod.vertices], float)
        geo[nm] = (V, [np.asarray(f.vertex_indices, int) for f in lod.faces], float(np.linalg.norm(V, axis=1).max()))
    reach = STRIP + np.array([geo[nm][2] for nm in names]) * s + 1.0
    dpos = kd.query(np.c_[m[:, 9], m[:, 11]], distance_upper_bound=float(reach.max()) + 1.0)[0]
    cand = np.flatnonzero(dpos - 0.26 < reach)
    bad, n_geo, dmin = [], 0, np.inf
    for i in cand:
        V, faces, _ = geo[names[i]]
        W = V @ m[i, :9].reshape(3, 3) + m[i, 9:12]
        gap = W[:, 1] - geom.h_at(H, W[:, 0], W[:, 2])
        polys = []
        for f in faces:
            if gap[f].min() < BAND_H and gap[f].max() > BURIED:
                xy = W[f][:, [0, 2]]
                pg = shapely.Polygon(xy) if len(f) >= 3 else None
                polys.append(pg if pg is not None and pg.is_valid and pg.area > 1e-8 else shapely.LineString(np.r_[xy, xy[:1]]))
        if not polys:
            continue
        n_geo += 1
        if shapely.intersects(strip, np.array(polys, object)).any():
            bad.append(int(i))
        dmin = min(dmin, float(shapely.distance(net, shapely.geometrycollections(polys))))
    viol["road_geometry"] = np.array(bad, int)
    ok = all(len(v) == 0 for v in viol.values()) and n > 0 and MR.keys_ok.all()
    print(f"instances {n}; exclusion objects {n_obj}; {time.time() - t0:.0f} s")
    for k, v in viol.items():
        ex = [{"i": int(i), "model": names[i].split(chr(92))[-1], "x": round(float(x[i]), 2), "z": round(float(z[i]), 2)} for i in v[:3]]
        print(f"  {k:16s} {len(v):7d} {'' if not len(v) else ex}")
    fin = np.isfinite(d)
    print(f"  min margins seen: road {float(np.min((d - need)[fin])) if fin.any() else float('inf'):.3f} m over the limit; water disc "
          f"min h-level {float(np.min(np.minimum(pond, sealvl))):.3f} m; sea band {float(np.min(band)):.3f} m")
    print(f"  road geometry: {len(cand)} instances within reach, {n_geo} with faces in the band checked face by face; smallest "
          f"band-face distance to an axis {dmin:.3f} m (strip {STRIP} m)")
    Path(a.out).write_text(json.dumps({k: [int(i) for i in v] for k, v in viol.items()}) + "\n", encoding="utf-8")
    print(f"G1 {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def geom_chains():
    from verify_roads_v30 import road_chains
    return road_chains()


if __name__ == "__main__":
    sys.exit(main())
