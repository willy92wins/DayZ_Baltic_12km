"""Kit probe points (HANDOFF step 7): the full-map v31 set (probe_points_map.py) on the given footprint plus the kit points
below, for the server probe (BalticBridgeProbeV2 / BalticKitProbeV1 log: P;id;ground;sea;pond;surface;depth;roadY;objects).
Every kit point carries site, piece(s), piece_kind(s), scale(s), roadway = the highest roadway-LOD face of all kit pieces there
(any texture), water_ext = the highest water_ext face (None when the point is off every flat run), ground = the terrain on its
native triangle, and expect:
  'wet'   water_ext - ground >= 0.10 (liquid control: the EV108 probe read water on water_ext faces),
  'test'  only a concrete_ext lip (or nothing) gives roadway - ground >= 0.10: engine water there is unverified,
  'dry'   control expected without water.
Kinds (any piece kind, scaled matrices, curves and slanted):
  kit_axis       three points on each piece's rung-midpoint centreline inside its water_ext flat run (25/50/75 %);
  kit_side       6 world m to either side of each piece's run midpoint, across the local centreline (dry control);
                 'of' = the kit_axis point, 'side' = -1 left / +1 right of the downstream direction;
  kit_confluence the same fixed lateral control, wet only inside a declared, built partner branch (<=1.8 m from its
                 continuous centreline and positively covered by that branch's actual water surface); other_site names it;
  kit_lip        at every joint (consecutive pieces by station), the arc midpoint of the concrete_ext lip of each of the two
                 plate ends that meet there (the lips of the two chain ends are buried by design and are not probed);
  kit_joint      the midpoint of the two plate-end centres of a joint (inside the overlap of the two plates);
  kit_joint_side 6 / 8 / 10 m (first geometrically dry one) to either side of the joint across the line between the two
                 lip points (dry control); 'of' = the kit_joint point;
  old_bed        wet vertices of the reference (EV107) bodies at the site seeds, kept only when farther than OLD_CLEAR from
                 every piece's continuous centreline, outside the kit's water sheets (no water-proxy face above the ground)
                 and outside the visible water of the given footprint (dry control: no pond there any more); at most 25
                 per site. v9 reach sites (sites.json entries with 'body'): the candidates are that site's body vertices,
                 not the whole wet component (which holds water this rollout keeps); every old_bed point names its site.
Geometry from streambed_kit_geometry_v31.json through streambed_kit_v31.py (KitSurface, rec_frame). EV108 version (14-10)
assumed straights at scale 1 with a hard-coded roadway height per model; the first v8 version (15-10) chose old_bed against
discrete axis markers, which let one control fall inside a sheet (review of 15-10, (8718, 11460)).
Usage: probe_points_kit.py <fp.npz> <terrain.npz> <lagoons.json> <kit-records.json> <ev107 terrain> <ev107 fp> <points.csv>
       <points.json> [sites.json]   (without sites.json: the seeds of kit-118 and kit-7)"""
import json, subprocess, sys
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.ndimage import label
sys.path.insert(0, str(Path(__file__).parent))
import streambed_kit_v31 as kit

MARGIN, SIDE, OLD_CLEAR = 0.10, 6.0, 6.0
fp, tp, lag, recp, t7, f7, csv_path, json_path = sys.argv[1:9]
site_list = json.load(open(sys.argv[9])) if len(sys.argv) > 9 else [dict(id="kit-118", seed=[8235, 9125]), dict(id="kit-7", seed=[8688, 11478])]
subprocess.run([sys.executable, "-I", str(Path(__file__).parent / "probe_points_map.py"), fp, tp, lag, csv_path, json_path], check=True, stdout=subprocess.DEVNULL)
pts = json.load(open(json_path))
models = kit.load_models()
recs = [r for r in json.load(open(recp)) if r["piece"] != "stones"]
surf = kit.KitSurface(recs, models)
H = np.load(tp)["heights"].astype(float)


def visible_plane(fp_path):
    """Vertex water plane of a footprint: the highest cell plane of the (up to) four cells around each vertex."""
    pl = np.load(fp_path)["plane"].astype(float)
    vp = np.full((pl.shape[0] + 1, pl.shape[1] + 1), -np.inf); cp = np.where(np.isfinite(pl), pl, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            vp[dr:dr + pl.shape[0], dc:dc + pl.shape[1]] = np.maximum(vp[dr:dr + pl.shape[0], dc:dc + pl.shape[1]], cp)
    return vp


def heights(q):
    q = np.asarray(q, float).reshape(-1, 2)
    road = surf.max_height(q, "road"); ext = surf.max_height(q, "road_ext"); water = surf.max_height(q, "water")
    ground = kit.tri_h(H, q[:, 0], q[:, 1])
    return road, ext, water, np.asarray(ground, float)


def expect_of(road, ext, ground):
    return "wet" if ext - ground >= MARGIN else "test"


def add(**kw):
    kw["id"] = len(pts); pts.append(kw); return kw


def kit_point(kind, q, **meta):
    road, ext, _, ground = heights(q)
    return add(kind=kind, **meta, x=float(q[0]), z=float(q[1]), roadway=float(road[0]),
               water_ext=float(ext[0]) if np.isfinite(ext[0]) else None, ground=float(ground[0]),
               expect=expect_of(road[0], ext[0], ground[0]))


def dry_point(kind, q, **meta):
    road, ext, water, ground = heights(q)
    return add(kind=kind, **meta, x=float(q[0]), z=float(q[1]), ground=float(ground[0]),
               kit_water=float(water[0]) if np.isfinite(water[0]) else None, expect="dry")


def arc_point(F, frac):
    """Point at fraction `frac` of the arc length of the polyline F (model frame, xz arc length)."""
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(F[:, [0, 2]], axis=0), axis=1))]
    v = frac * s[-1]; i = min(np.searchsorted(s, v, side="right") - 1, len(F) - 2)
    t = (v - s[i]) / max(s[i + 1] - s[i], 1e-9)
    return F[i] + t * (F[i + 1] - F[i]), F[i + 1] - F[i]


info = {}
for r in recs:
    g = models[kit.model_key(r["model"])]; R, T = kit.rec_frame(r)
    C = np.array(g["centre"]); fy = g["roadway_flat_y"]
    flat = np.nonzero(np.abs(C[:, 1] - fy) < 0.005)[0]
    meta = dict(site=r["site"], piece=r["piece"], piece_kind=kit.kind_of(r["model"]), scale=round(float(np.linalg.norm(R[:, 1])), 4))
    W = C @ R.T + T
    info[(r["site"], r["piece"])] = dict(rec=r, meta=meta, ends=(W[0, [0, 2]], W[-1, [0, 2]]),
                                         lips=((R @ arc_point(C[:flat[0] + 1], 0.5)[0] + T)[[0, 2]],
                                               (R @ arc_point(C[flat[-1]:], 0.5)[0] + T)[[0, 2]]),
                                         centroid=W[:, [0, 2]].mean(0), W=W[:, [0, 2]])
    F = C[flat[0]:flat[-1] + 1]
    for frac in (0.25, 0.5, 0.75):
        pm, dm = arc_point(F, frac)
        p = (R @ pm + T)[[0, 2]]
        a = kit_point("kit_axis", p, **meta)
        if frac == 0.5:
            d = (R @ dm)[[0, 2]]; d = -d / np.linalg.norm(d)              # downstream (model -Z) direction
            n = np.array([-d[1], d[0]])                                    # left of the downstream direction
            for sgn in (-1, 1):
                dry_point("kit_side", p - sgn * SIDE * n, **meta, of=a["id"], side=sgn)

# Approved EV112 amendment: preserve the fixed lateral location. A true branch
# crossing is a wet control; ordinary broad mouths and ponds remain dry controls.
linked = {}
for site in site_list:
    for end, relation in site.get("extend", {}).items():
        partner = relation.get("partner")
        if site.get("ends", {}).get(end) == "kit" and partner:
            linked.setdefault(site["id"], set()).add(partner)
            linked.setdefault(partner, set()).add(site["id"])
branch_surfaces, branch_segments = {}, {}
for sid in sorted({r["site"] for r in recs}):
    branch_surfaces[sid] = kit.KitSurface([r for r in recs if r["site"] == sid], models)
    branch_segments[sid] = np.vstack([np.c_[v["W"][:-1], v["W"][1:]] for key,v in info.items() if key[0] == sid])
for p in pts:
    if p["kind"] != "kit_side":
        continue
    q = np.array([p["x"], p["z"]])
    for other in sorted(linked.get(p["site"], ())):
        if other not in branch_surfaces:
            continue
        seg = branch_segments[other]; a,b = seg[:,:2],seg[:,2:]; ab=b-a
        t=np.clip(((q-a)*ab).sum(1)/np.maximum((ab*ab).sum(1),1e-12),0,1)
        distance=float(np.linalg.norm(q-(a+t[:,None]*ab),axis=1).min())
        if distance > 1.8:
            continue
        water=float(branch_surfaces[other].max_height(q.reshape(1,2),"water")[0])
        if np.isfinite(water) and water > p["ground"]:
            p.update(kind="kit_confluence",expect="wet",other_site=other,other_water=water,other_axis_distance=distance)
            break

new_vp = visible_plane(fp)
new_wet = np.isfinite(new_vp) & (H < new_vp)
joints_skipped_sides = 0
by_site = {}
for (sid, pc), v in info.items():
    by_site.setdefault(sid, []).append(v)
for sid, L in by_site.items():
    L.sort(key=lambda v: v["rec"]["station"][0])
    for a, b in zip(L[:-1], L[1:]):
        ia = int(np.argmin([np.linalg.norm(e - b["centroid"]) for e in a["ends"]]))
        ib = int(np.argmin([np.linalg.norm(e - a["centroid"]) for e in b["ends"]]))
        pair = dict(site=sid, pieces=[a["meta"]["piece"], b["meta"]["piece"]], piece_kinds=[a["meta"]["piece_kind"], b["meta"]["piece_kind"]],
                    scales=[a["meta"]["scale"], b["meta"]["scale"]])
        la = kit_point("kit_lip", a["lips"][ia], **a["meta"], end="downstream" if ia == 0 else "upstream", joint_with=b["meta"]["piece"])
        lb = kit_point("kit_lip", b["lips"][ib], **b["meta"], end="downstream" if ib == 0 else "upstream", joint_with=a["meta"]["piece"])
        q = 0.5 * (a["ends"][ia] + b["ends"][ib])
        j = kit_point("kit_joint", q, **pair, lips=[la["id"], lb["id"]])
        d = b["lips"][ib] - a["lips"][ia]; d = d / np.linalg.norm(d); n = np.array([-d[1], d[0]])
        for sgn in (-1, 1):
            for dist in (SIDE, SIDE + 2, SIDE + 4):
                s_ = q - sgn * dist * n
                road, ext, water, ground = heights(s_)
                rr, cc = int(round((kit.ZTOP - s_[1]) / 6)), int(round(s_[0] / 6))
                if not (water[0] > ground[0]) and not new_wet[rr - 1:rr + 2, cc - 1:cc + 2].any():
                    dry_point("kit_joint_side", s_, **pair, of=j["id"], side=sgn, distance=dist)
                    break
            else:
                joints_skipped_sides += 1

# old bed: EV107 wet vertices at the seeds, away from the continuous centrelines, the kit sheets and the new ponds
segs = np.vstack([np.c_[v["W"][:-1], v["W"][1:]] for v in info.values()])                    # (S, 4): a.x a.z b.x b.z


def axis_dist(Q):
    Q = np.asarray(Q, float).reshape(-1, 2); out = np.full(len(Q), np.inf)
    A, B = segs[:, :2], segs[:, 2:]; AB = B - A; L2 = np.maximum((AB * AB).sum(1), 1e-12)
    for k in range(0, len(Q), 256):
        q = Q[k:k + 256, None, :]
        t = np.clip(((q - A) * AB).sum(2) / L2, 0, 1)
        out[k:k + 256] = np.linalg.norm(q - (A + t[..., None] * AB), axis=2).min(1)
    return out


H7 = np.load(t7)["heights"].astype(float); vp7 = visible_plane(f7)
wet7 = np.isfinite(vp7) & (H7 < vp7)
lab, _ = label(wet7, np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]]))
rng = np.random.default_rng(7)
old_rejected = Counter()
built = {r["site"] for r in recs}
for site in site_list:
    if site["id"] not in built:
        continue
    if "body" in site:
        cells = np.array(site["body"], int).reshape(-1, 2)
        cells = cells[wet7[cells[:, 0], cells[:, 1]]]
        if not len(cells):
            continue
    else:
        sx, sz = site["seed"]
        r, c = int(round((kit.ZTOP - sz) / 6)), int(round(sx / 6))
        w = np.argwhere(wet7[r - 3:r + 4, c - 3:c + 4])[0] + (r - 3, c - 3)
        cells = np.argwhere(lab == lab[w[0], w[1]])
    Q = np.c_[6.0 * cells[:, 1], kit.ZTOP - 6.0 * cells[:, 0]]
    far = axis_dist(Q) > OLD_CLEAR
    _, _, water, ground = heights(Q)
    sheet = water > ground
    pond = new_wet[cells[:, 0], cells[:, 1]]
    old_rejected.update(near_axis=int((~far).sum()), in_sheet=int((far & sheet).sum()), in_pond=int((far & ~sheet & pond).sum()))
    ok = np.nonzero(far & ~sheet & ~pond)[0]
    for k in rng.choice(len(ok), size=min(25, len(ok)), replace=False):
        v = cells[ok[k]]
        add(kind="old_bed", site=site["id"], x=6.0 * v[1], z=kit.ZTOP - 6.0 * v[0], plane=float(vp7[v[0], v[1]]), ground=float(H[v[0], v[1]]), expect="dry")
from select_kit_probe_v31 import select as select_runtime
full_pts = pts
pts, sampling = select_runtime(full_pts, recs, 3000)
with open(json_path + ".full.json", "w", newline="\n") as f:
    json.dump(full_pts, f, indent=1)
with open(csv_path + ".full.csv", "w", newline="\n") as f:
    for p in full_pts:
        f.write(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n")
with open(json_path + ".sampling.json", "w", newline="\n") as f:
    json.dump(sampling, f, indent=1)
with open(csv_path, "w", newline="\n") as f:
    for p in pts:
        f.write(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n")
with open(json_path, "w", newline="\n") as f:
    json.dump(pts, f, indent=1)
print(len(pts), dict(Counter(p["kind"] for p in pts)), "expect", dict(Counter(p.get("expect") for p in pts if "expect" in p)),
      "joint sides skipped", joints_skipped_sides, "old_bed rejected", dict(old_rejected))
