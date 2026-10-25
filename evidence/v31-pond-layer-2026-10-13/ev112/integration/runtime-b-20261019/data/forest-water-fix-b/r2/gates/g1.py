"""G1: zero instances inside the exclusion margins (exact geometry at each instance's p3d origin).

Usage: python -I g1.py <records.json> [--json out.json]
Origin = position - M . bounding_centre (reference bc), scale s = |M column 0|. Margins (fixed before the first run):
  road     exact distance to the road chain polylines (verify_roads_v30.road_chains) >= 3.5 + clearance(family)
           conifer 2.09, broadleaf 1.08, bush 0.71, dead 1.99, reed 0.71 m
  water    no visible water in the disc of radius base_radius_plan * s + 0.25 m (reed 0.25 m): visible water =
           h < pond plane (footprint, per cell) or h < 0.75 m; exact minimum of the planar terrain over the disc
  sea      no engine sea band (h < 1.0 m in a cell outside the envelope) in the same disc
  bridge   distance to each bridge plan hull (visual bbox, staged EV110 WRP) >= crown_halfwidth * s + 1.0 m;
           distance to v31_bridge_cut / v31_bridge_fill cells >= the same
  kit      distance to each streambed kit plan hull >= base_radius_plan * s + 0.5 m; to v31_kit cells >= the same
  narva    distance to narva cells >= 6.0 m
  road_geometry (v2, EV111 review 1): no Geometry LOD face of a placed model (position + M . vertex, scale, yaw and tilt
           included) that reaches below 3.5 m above the planar terrain and is not fully buried (max > -0.05 m) may
           intersect the painted road strip (road chain polylines buffered 3.5 m, 32 segments per quarter circle).
           Checked for every instance whose WRP position lies within 3.5 m + its largest geometry vertex radius x s
           (+ 1 m) of an axis. Origin margins do not cover a 9.5 m fallen trunk (review 1: WRP 16867473).
Prints the count per category and PASS (all zero) or FAIL.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import shapely
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r"C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts")
sys.path.insert(0, r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\tools\terrain")
import gate_common as GC  # noqa: E402
import geom  # noqa: E402
from odol_reader import ODOL  # noqa: E402
from wrp0wzd import read as read_wrp  # noqa: E402

CLEAR = {"conifer": 2.09, "broadleaf": 1.08, "bush": 0.71, "dead": 1.99, "reed": 0.71}
BAND_H, BURIED, STRIP = 3.5, -0.05, 3.5


def road_geometry(names, m, H, models):
    """Indices whose band faces intersect the painted strip, and the smallest face-to-axis distance seen."""
    from verify_roads_v30 import road_chains
    lines = [shapely.LineString(np.asarray(c, float)) for c in road_chains() if len(c) >= 2]
    strip = shapely.buffer(shapely.multilinestrings(lines), STRIP, quad_segs=32)
    shapely.prepare(strip)
    net = shapely.multilinestrings(lines)
    A, B = geom.road_segments()
    geo = {}
    for nm in sorted(set(names)):
        od = ODOL.from_file("P:/DZ/" + nm[3:].replace("\\", "/"))
        lod = next((l for l in od.lods if 0.9e13 < l.resolution < 1.1e13 and l.vertices and l.faces), None)
        if lod is None:
            raise SystemExit(f"{nm}: no Geometry LOD")
        V = np.array([[v.x, v.y, v.z] for v in lod.vertices], float)
        geo[nm] = (V, [np.asarray(f.vertex_indices, int) for f in lod.faces], float(np.linalg.norm(V, axis=1).max()))
    s = np.linalg.norm(m[:, 0:3], axis=1)
    reach = STRIP + np.array([geo[nm][2] for nm in names]) * s + 1.0
    d = geom.seg_distance(m[:, 9], m[:, 11], A, B, float(reach.max()))
    bad, near, dmin = [], np.flatnonzero(d < reach), np.inf
    for i in near:
        V, faces, _ = geo[names[i]]
        W = V @ m[i, :9].reshape(3, 3) + m[i, 9:12]            # rows of the 3x3 = model axes: position + M . v
        gap = W[:, 1] - geom.h_at(H, W[:, 0], W[:, 2])
        polys = []
        for f in faces:
            if gap[f].min() < BAND_H and gap[f].max() > BURIED:
                xy = W[f][:, [0, 2]]
                pg = shapely.Polygon(xy) if len(f) >= 3 else None
                polys.append(pg if pg is not None and pg.is_valid and pg.area > 1e-8 else shapely.LineString(np.r_[xy, xy[:1]]))
        if not polys:
            continue
        if shapely.intersects(strip, np.array(polys, object)).any():
            bad.append(int(i))
        dmin = min(dmin, float(shapely.distance(net, shapely.geometrycollections(polys))))
    return np.array(bad, int), len(near), dmin


def run(records_path, out_json=None):
    ref = json.loads(GC.REFERENCE.read_text(encoding="utf-8"))
    models = ref["models"]
    recs = GC.load_records(records_path)
    t = np.load(GC.TERRAIN)
    fp = np.load(GC.FOOTPRINT)
    H = t["heights"].astype(np.float64)
    plane, env = fp["plane"], fp["env_plane"]
    m = np.array([r["matrix"] for r in recs], float)
    names = [r["model"] for r in recs]
    unknown = [nm for nm in names if nm not in models]
    if unknown:
        print(f"unknown models: {len(unknown)}")
        print("G1 FAIL")
        return False
    M = m[:, :9].reshape(-1, 3, 3).transpose(0, 2, 1)          # columns = axes
    bc = np.array([models[nm]["bc"] for nm in names])
    org = m[:, 9:12] - np.einsum("nij,nj->ni", M, bc)
    s = np.linalg.norm(M[:, :, 0], axis=1)
    x, z = org[:, 0], org[:, 2]
    fam = np.array([models[nm]["family"] for nm in names])
    base = np.array([models[nm]["base_radius_plan"] for nm in names]) * s
    crown = np.array([models[nm]["crown_halfwidth"] for nm in names]) * s
    viol = {}
    # roads
    A, B = geom.road_segments()
    need = 3.5 + np.array([CLEAR[f] for f in fam])
    d = geom.seg_distance(x, z, A, B, float(need.max()))
    viol["road"] = np.flatnonzero(d < need)
    # water and sea
    R = np.where(fam == "reed", 0.25, base + 0.25)
    pond = geom.disc_min(H, x, z, R, lambda r, c: plane[r, c])
    sealvl = geom.disc_min(H, x, z, R, lambda r, c: np.full(r.shape, 0.75))
    band = geom.disc_min(H, x, z, R, lambda r, c: np.where(np.isfinite(env[r, c]), np.nan, 1.0))
    viol["visible_water"] = np.flatnonzero((pond < 0) | (sealvl < 0))
    viol["sea"] = np.flatnonzero(band < 0)
    # bridges and kit objects of the staged base WRP
    w = read_wrp(GC.STAGE_WRP)
    boxes = {}
    bad_bridge, bad_kit = np.zeros(len(x), bool), np.zeros(len(x), bool)
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
        corners = np.array([[a, b, c] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])])
        P = corners @ om[:9].reshape(3, 3) + om[9:12]          # row-vector form of position + M . v (rows = axes)
        xz = P[:, [0, 2]]
        hull = xz[ConvexHull(xz).vertices]
        kind = "bridge" if "bridges" in nm.lower() else "kit"
        n_obj[kind] += 1
        near = (x > hull[:, 0].min() - 30) & (x < hull[:, 0].max() + 30) & (z > hull[:, 1].min() - 30) & (z < hull[:, 1].max() + 30)
        if not near.any():
            continue
        dd = geom.poly_distance(x[near], z[near], hull)
        lim = crown[near] + 1.0 if kind == "bridge" else base[near] + 0.5
        idx = np.flatnonzero(near)[dd < lim]
        (bad_bridge if kind == "bridge" else bad_kit)[idx] = True
    db = geom.flagged_cell_distance(t["v31_bridge_cut"] | t["v31_bridge_fill"], x, z, float((crown + 1.0).max()))
    bad_bridge |= db < crown + 1.0
    dk = geom.flagged_cell_distance(t["v31_kit"], x, z, float((base + 0.5).max()))
    bad_kit |= dk < base + 0.5
    viol["bridge"] = np.flatnonzero(bad_bridge)
    viol["kit"] = np.flatnonzero(bad_kit)
    dn = geom.flagged_cell_distance(t["narva"], x, z, 6.0)
    viol["narva"] = np.flatnonzero(dn < 6.0)
    viol["road_geometry"], n_geo, geo_min = road_geometry(names, m, H, models)
    ok = all(len(v) == 0 for v in viol.values())
    print(f"instances {len(recs)}; exclusion objects {n_obj}")
    for k, v in viol.items():
        ex = [{"i": int(i), "model": names[i].split(chr(92))[-1], "x": round(float(x[i]), 2), "z": round(float(z[i]), 2)} for i in v[:3]]
        print(f"  {k:14s} {len(v):6d} {'' if not len(v) else ex}")
    print(f"  min margins seen: road {float(np.min(d - need)):.3f} m over the limit; water disc min h-level "
          f"{float(np.min(np.minimum(pond, sealvl))):.3f} m; sea band {float(np.min(band)):.3f} m")
    print(f"  road geometry: {n_geo} instances near a road checked face by face; smallest band-face distance to an axis "
          f"{geo_min:.3f} m (strip {STRIP} m)")
    if out_json:
        Path(out_json).write_text(json.dumps({k: [int(i) for i in v] for k, v in viol.items()}) + "\n", encoding="utf-8")
    print(f"G1 {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("--json")
    a = ap.parse_args()
    sys.exit(0 if run(a.records, a.json) else 1)
