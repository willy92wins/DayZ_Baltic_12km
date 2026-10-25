"""G11 (EV112): roads, bridges, sea and kept water around the rollout. Needs G6's bury-work (the footprint of the output).
  a) roads    no kit face (roadway LOD or water-proxy LOD0, every piece) stands above the terrain anywhere inside a native
              triangle with a reserve/platform/narva/v31_bridge_cut vertex: each piece's faces rasterised at 0.25 m, highest
              face per pixel, compared with the terrain on its native triangle (no kit piece on a road platform);
  b) bridges  every kit piece (its whole plan) at least 60 m from each bridge site of sites-ev110.json and the 015-15 pilot (the
              bridge pass cuts and seals up to 60 m along the water axis and needs the pond water there);
  c) sea      no kit water face above an engine-sea point (terrain < 0.75 m in a cell of no output envelope cell);
  d) kept     every wet vertex of the input (EV107 terrain below the EV107 vertex plane) that is in no site's body (reach sites:
              the body list of the sites file; component sites: the whole wet component at the seed) is still wet in the
              output footprint (bury-work fp0: terrain below the highest incident footprint plane), and every input envelope
              cell touching such a vertex is still an envelope cell with the same plane: streams left out, wide water and the
              bridge zones keep their water (a review of 16-10 found that filling whole components destroyed tributaries).
              Declared exception (the tool's seat corridor): a kept cell may be removed only when it lies in a built site's
              corridor, i.e. a vertex of it within 6.01 m of a reach site's lattice path (component sites: its centre within
              CUT_Q = 10 m, v8's rule); a kept vertex may dry only when every incident input envelope cell it lost is such a
              corridor cell. Both are counted and printed; any other loss FAILs;
  e) junctions: every declared pond/bridge/sea/kit end must reach its receptor with no continuous dry gap >6m.
              Evaluate exact linear heights on native triangles, split at grid/diagonal and water-face boundaries.
              Missing receptors, missing footprint and zero measured junctions fail closed.
Pass: a) b) c) d) e) hold. Usage: gate_g11_junctions.py [run_dir] [sites.json]   (default sites: the chain's)"""
import glob, json, os, sys
from collections import defaultdict
import numpy as np
from scipy.ndimage import label
from scipy.spatial import cKDTree
sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
run = sys.argv[1] if len(sys.argv) > 1 else G.OUT
spath = sys.argv[2] if len(sys.argv) > 2 else G.chain()["args"][5]
spath = spath if os.path.isabs(spath) else G.B + "/" + spath
models, recs, rep, H, sites, pieces = G.load(run)
z0 = np.load(G.B + "/bridges/terrain-ev107.npz"); H0 = z0["heights"].astype(np.float64)
frozen = z0["reserve"] | z0["platform"] | z0["narva"] | z0["v31_bridge_cut"]
ftri = frozen[:-1, :-1] | frozen[:-1, 1:] | frozen[1:, :-1] | frozen[1:, 1:]
env1 = np.load(run + "/envelope-ev108.npy").astype(np.float64); env0 = np.load(G.B + "/bridges/envelope-ev107.npy").astype(np.float64)
PX = 0.25
fails = defaultdict(list); res = {}


def vplane(pl):
    vp = np.full((pl.shape[0] + 1, pl.shape[1] + 1), -np.inf); cp = np.where(np.isfinite(pl), pl, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            vp[dr:dr + pl.shape[0], dc:dc + pl.shape[1]] = np.maximum(vp[dr:dr + pl.shape[0], dc:dc + pl.shape[1]], cp)
    return vp


def raster(p, tris):
    lo = p.lo - 0.5; hi = p.hi + 0.5
    nx, nz = int(np.ceil((hi[0] - lo[0]) / PX)), int(np.ceil((hi[1] - lo[1]) / PX))
    W = np.full((nz, nx), -np.inf)
    for t in tris:
        a, b, c = t[:, [0, 2]]
        tlo = np.minimum(np.minimum(a, b), c); thi = np.maximum(np.maximum(a, b), c)
        i0, i1 = int(np.floor((tlo[0] - lo[0]) / PX)), int(np.ceil((thi[0] - lo[0]) / PX))
        j0, j1 = int(np.floor((tlo[1] - lo[1]) / PX)), int(np.ceil((thi[1] - lo[1]) / PX))
        X, Z = np.meshgrid(lo[0] + (np.arange(i0, i1) + 0.5) * PX, lo[1] + (np.arange(j0, j1) + 0.5) * PX)
        v0, v1 = b - a, c - a; den = v0[0] * v1[1] - v0[1] * v1[0]
        if abs(den) < 1e-12:
            continue
        dx, dz = X - a[0], Z - a[1]
        u = (dx * v1[1] - dz * v1[0]) / den; v = (v0[0] * dz - v0[1] * dx) / den
        ins = (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
        y = t[0, 1] + u * (t[1, 1] - t[0, 1]) + v * (t[2, 1] - t[0, 1])
        blk = W[j0:j1, i0:i1]; W[j0:j1, i0:i1] = np.where(ins, np.maximum(blk, y), blk)
    jj, ii = np.nonzero(np.isfinite(W))
    return lo[0] + (ii + 0.5) * PX, lo[1] + (jj + 0.5) * PX, W[jj, ii]


# a) roads, c) sea
inc1 = np.zeros(H.shape, bool)
for dr in (0, 1):
    for dc in (0, 1):
        inc1[dr:dr + 2047, dc:dc + 2047] |= np.isfinite(env1)
sea_cell = np.zeros((2047, 2047), bool)
seav = (H < 0.75) & ~inc1
sea_cell = seav[:-1, :-1] | seav[:-1, 1:] | seav[1:, :-1] | seav[1:, 1:]
road_px = defaultdict(int); sea_px = defaultdict(int); road_worst = {}
for sid, P in pieces.items():
    for p in P:
        x, zz, y = raster(p, np.concatenate([p.road, p.water]) if len(p.water) else p.road)
        c = np.clip(np.floor(x / 6.0).astype(int), 0, 2046); r = np.clip(np.floor((G.ZTOP - zz) / 6.0).astype(int), 0, 2046)
        g = G.terrain_y(H, x, zz)
        m = ftri[r, c] & (y > g)
        if m.any():
            road_px[sid] += int(m.sum()); road_worst[sid] = max(road_worst.get(sid, 0.0), float((y - g)[m].max()))
        xw, zw, yw = raster(p, p.water) if len(p.water) else (np.zeros(0), np.zeros(0), np.zeros(0))
        if len(xw):
            cw = np.clip(np.floor(xw / 6.0).astype(int), 0, 2046); rw = np.clip(np.floor((G.ZTOP - zw) / 6.0).astype(int), 0, 2046)
            ms = sea_cell[rw, cw] & (yw > G.terrain_y(H, xw, zw))
            sea_px[sid] += int(ms.sum())
for sid in road_px:
    fails["road_platform"].append([sid, road_px[sid], round(road_worst[sid], 3)])
for sid, n in sea_px.items():
    if n:
        fails["over_engine_sea"].append([sid, n])
res["road_pixels_by_site"] = dict(road_px); res["road_worst_m"] = road_worst
# b) bridges
bsites = {b["id"]: (b["x"], b["z"]) for b in json.load(open(G.WT + "/evidence/v31-pond-layer-2026-10-13/bridges/ev110/sites-ev110.json"))}
bsites["015-15"] = (9091.0, 10305.0)
BR = np.array(list(bsites.values())); bid = list(bsites)
bmin = {}
for sid, P in pieces.items():
    for p in P:
        allv = np.vstack([p.road.reshape(-1, 3), p.water.reshape(-1, 3)])[:, [0, 2]]
        d = np.min(np.hypot(allv[:, None, 0] - BR[None, :, 0], allv[:, None, 1] - BR[None, :, 1]), axis=0)
        k = int(np.argmin(d))
        if sid not in bmin or d[k] < bmin[sid][1]:
            bmin[sid] = (bid[k], float(d[k]))
res["nearest_bridge_by_site"] = {k: [v[0], round(v[1], 1)] for k, v in bmin.items()}
for sid, (b, d) in bmin.items():
    if d < 60.0:
        fails["bridge_clearance"].append([sid, b, round(d, 1)])
# d) kept water
fps = sorted(glob.glob(run + "/bury-work/fp*/footprint.npz"), key=lambda p: int(p.replace("\\", "/").split("/fp")[-1].split("/")[0]))
fp0 = np.load(G.B + "/bridges/fp-ev107/footprint.npz")
vp0 = vplane(fp0["plane"].astype(np.float64)); wet0 = np.isfinite(vp0) & (H0 < vp0)
lab, _ = label(wet0, np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]]))
claimed = np.zeros(H.shape, bool)
for s in json.load(open(spath)):
    if s.get("mode", "component") == "reach":
        b = np.array(s["body"], int).reshape(-1, 2); claimed[b[:, 0], b[:, 1]] = True
    else:
        sr, sc = int(round((G.ZTOP - s["seed"][1]) / 6)), int(round(s["seed"][0] / 6))
        w = np.argwhere(wet0[sr - 3:sr + 4, sc - 3:sc + 4])
        rr, cc = w[np.argmin(np.hypot(w[:, 0] - 3, w[:, 1] - 3))] + (sr - 3, sc - 3)
        claimed |= lab == lab[rr, cc]
kept = wet0 & ~claimed
# corridor cells of the built sites (gate's own distances)
corr = np.zeros((2047, 2047), bool)
for sid, s_ in sites.items():
    V = np.array(s_["lattice"]); reach_mode = s_.get("mode") == "reach"
    R = 6.01 if reach_mode else 10.0
    for a, b in zip(V[:-1], V[1:]):
        lo_, hi_ = np.minimum(a, b) - R - 9, np.maximum(a, b) + R + 9
        ra, rb = max(int((G.ZTOP - hi_[1]) / 6), 0), min(int((G.ZTOP - lo_[1]) / 6) + 1, 2046)
        ca, cb = max(int(lo_[0] / 6), 0), min(int(hi_[0] / 6) + 1, 2046)
        RR, CC = np.mgrid[ra:rb + 1, ca:cb + 1]; ab = b - a
        if reach_mode:                                             # any vertex of the cell within R
            Pv = np.c_[6.0 * CC.ravel(), G.ZTOP - 6.0 * RR.ravel()]
            t = np.clip(((Pv - a) @ ab) / (ab @ ab), 0, 1); dv = np.linalg.norm(Pv - (a + t[:, None] * ab), axis=1).reshape(RR.shape)
            near = dv <= R
            cells = near[:-1, :-1] | near[:-1, 1:] | near[1:, :-1] | near[1:, 1:]
            corr[ra:rb, ca:cb] |= cells
        else:                                                      # cell centre within CUT_Q
            Pc = np.c_[6.0 * CC[:-1, :-1].ravel() + 3, G.ZTOP - 6.0 * RR[:-1, :-1].ravel() - 3]
            t = np.clip(((Pc - a) @ ab) / (ab @ ab), 0, 1); dc_ = np.linalg.norm(Pc - (a + t[:, None] * ab), axis=1).reshape(RR[:-1, :-1].shape)
            corr[ra:rb, ca:cb] |= dc_ <= R
if fps:
    vp1 = vplane(np.load(fps[-1])["plane"].astype(np.float64)); wet1 = np.isfinite(vp1) & (H < vp1)
    kc = (kept[:-1, :-1] | kept[:-1, 1:] | kept[1:, :-1] | kept[1:, 1:]) & np.isfinite(env0)
    changed = kc & ~(np.isfinite(env1) & (env1 == env0))
    res.update(kept_envelope_cells=int(kc.sum()), kept_envelope_cells_changed=int(changed.sum()),
               kept_envelope_cells_changed_in_corridor=int((changed & corr).sum()))
    if (changed & ~corr).any():
        fails["kept_envelope_changed_outside_corridor"].append([[6 * int(c) + 3, round(G.ZTOP - 6 * int(r) - 3, 1)] for r, c in np.argwhere(changed & ~corr)[:10]])
    lost = kept & ~wet1
    gone = np.isfinite(env0) & ~np.isfinite(env1)
    gone_nc = gone & ~corr
    inc_bad = np.zeros(H.shape, bool)
    for dr in (0, 1):
        for dc in (0, 1):
            inc_bad[dr:dr + 2047, dc:dc + 2047] |= gone_nc
    lost_bad = lost & inc_bad
    # a lost vertex none of whose lost cells is outside the corridor: allowed only if it lost at least one corridor cell
    inc_corr = np.zeros(H.shape, bool)
    for dr in (0, 1):
        for dc in (0, 1):
            inc_corr[dr:dr + 2047, dc:dc + 2047] |= gone & corr
    lost_unexplained = lost & ~inc_bad & ~inc_corr
    res.update(footprint=fps[-1], kept_wet_vertices=int(kept.sum()), kept_wet_lost=int(lost.sum()),
               kept_wet_lost_in_corridor=int((lost & inc_corr & ~inc_bad).sum()),
               kept_lost_bad_xz=[[6 * int(c), round(G.ZTOP - 6 * int(r), 1)] for r, c in np.argwhere(lost_bad | lost_unexplained)[:20]])
    if lost_bad.any() or lost_unexplained.any():
        fails["kept_water_lost"].append(int((lost_bad | lost_unexplained).sum()))
else:
    fails["no_footprint_run_G6_first"].append(run)
# e) continuous native-triangle junction gate (EV112 OT1b)
from junction_native import dry_gap
kw = np.argwhere(kept & wet1) if fps else np.zeros((0, 2), int)
ktree = cKDTree(np.c_[6.0 * kw[:, 1], G.ZTOP - 6.0 * kw[:, 0]]) if len(kw) else None
lines = {sid: np.array(s["lattice"]) for sid, s in sites.items()}
junctions = []
all_pieces = [p for pp in pieces.values() for p in pp]
final_plane = np.load(fps[-1])["plane"] if fps else None
for sid, s in sites.items():
    if s.get("mode") != "reach" or not s.get("ends"):
        continue
    V = lines[sid]
    for side, st in (("up", s["wet_span"][0]), ("dn", s["wet_span"][1])):
        typ = s["ends"].get(side)
        if typ in (None, "natural", "road"):
            continue
        E = G.at(V, [st])[0]
        K = None
        if typ == "kit":
            partner = (s.get("extend") or {}).get(side, {}).get("partner")
            if partner in lines:
                _, station = G.project(lines[partner], E.reshape(1,2))
                station = np.clip(station,0,np.linalg.norm(np.diff(lines[partner],axis=0),axis=1).sum())
                K = G.at(lines[partner], station)[0]
            d = float(np.linalg.norm(K-E)) if K is not None else None
        else:
            if ktree is not None:
                d, ki = ktree.query(E); K = ktree.data[ki]
                d = float(d)
            else:
                d = None
        row = dict(site=sid, end=side, type=typ, wet_end_xz=E.round(1).tolist(), distance_m=round(d, 2) if d is not None else None)
        if K is None or final_plane is None:
            row["passed"] = False
        else:
            cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V, axis=0), axis=1))]
            inner = np.clip(st+(12 if side == "up" else -12), s["wet_span"][0], s["wet_span"][1])
            stops = np.sort(np.r_[inner, cum[(cum>min(st,inner)) & (cum<max(st,inner))], st])
            if side == "up":
                stops = stops[::-1]
            path = np.vstack([G.at(V, stops), K])
            row.update(dry_gap(path, H, final_plane, all_pieces))
            row["target_xz"] = K.tolist()
            row["passed"] = bool(row["wet_m"] > 0 and row["max_dry_m"] <= 6.0+1e-6)
        junctions.append(row)
        if not row["passed"]:
            fails["junction_dry_gap_or_missing_target"].append(row)
if not junctions:
    fails["zero_junction_coverage"].append(0)
ds = [j["distance_m"] for j in junctions if j["distance_m"] is not None]
res.update(junctions=junctions, junction_distance_p50_p90_max=np.percentile(ds, [50, 90, 100]).round(2).tolist() if ds else None,
           failures={k: dict(n=len(v), first=v[:10]) for k, v in fails.items()})
res["passed"] = not fails
print(json.dumps({k: v for k, v in res.items() if k not in ("junctions", "nearest_bridge_by_site")}))
json.dump(res, open(run + "/gate-g11.json", "w"), indent=1)
print("G11", "PASS" if res["passed"] else "FAIL")
sys.exit(0 if res["passed"] else 1)
