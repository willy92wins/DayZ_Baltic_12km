"""G2: visible-water width over the straights and curves, with the lips (method of scratchpad/wf-kit_lattice/measure_v8.py
outline_stats, lines 118-146, with the real geometry): cross-sections every 0.5 m along each straight/curve rung-midpoint
centreline over its WHOLE length (plate end to plate end, lips and joints included; only samples whose station falls outside
the wet span, i.e. on the buried outer lips of the two chain ends, are left out), lateral samples every 0.1 m stored from
-7 to +7 m (model x, scaled into the world), wet where the highest water-proxy LOD0 face of ANY piece lies above the terrain
on its native triangle. Width = the wet run through the centre x scale; edge outside the stone band when the run leaves
[-2.4, 3.0] stored (measure_v8.py line 55). Pass per site: p50 <= 4.0 m, std <= 1.0 m, out-of-band share <= 0.20.
Centre-dry sections are counted and printed (they carry no width). A section reaching the initial
window is remeasured out to +/-30 model metres; unresolved clipping fails. No clipped width enters statistics.
For slanted elbows only, use the flow normal over one native grid step (station +/-3m): a normal to a jagged
model lip can run longitudinally down the next 90-degree leg. Centres, spacing, every piece and all thresholds
remain unchanged. Diagnostic 98.0-1: the old 7.298m section follows the neighbouring leg; a deliberately
unburied broad sheet still fails the transverse check (median 5.25m), and zero coverage fails.
Usage: gate_g2_width.py [run_dir]"""
import json, os, sys, heapq
import numpy as np
sys.dont_write_bytecode = True; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gatelib as G
run = sys.argv[1] if len(sys.argv) > 1 else G.OUT
models, recs, rep, H, sites, pieces = G.load(run)
xs = np.round(np.arange(-7.0, 7.0001, 0.1), 3); i0 = len(xs) // 2
ok_all = bool(sites); out = {}
for sid, S in sites.items():
    P = pieces[sid]; V = np.array(S["lattice"]); span = S["wet_span"]
    W, n_dry, n_out, n, kinds, unmeasured, saturated, unresolved = [], 0, 0, 0, {}, [], 0, 0
    widest=[]; local_width=[]
    for p in P:
        C = p.centre_model; Rs, _ = G.resample(C, 0.5)
        seg = np.diff(C[:, [0, 2]], axis=0); s_ = np.r_[0, np.cumsum(np.linalg.norm(seg, axis=1))]
        _, sR = G.resample(C, 0.5)
        pts, meta = [], []
        for (mx, my, mz), sv in zip(Rs, sR):
            i = min(np.searchsorted(s_, sv, side="right") - 1, len(seg) - 1)
            d = seg[i] / np.linalg.norm(seg[i]); lat = np.array([d[1], -d[0]])
            pm = np.c_[mx + xs * lat[0], np.full(len(xs), my), mz + xs * lat[1]]
            pts.append(p.world(pm)[:, [0, 2]])
            meta.append(p.M[[0,2],:] @ np.array([lat[0],0.0,lat[1]]))
        pts = np.array(pts)                                            # (sections, 141, 2)
        if "slanted" in p.kind:
            centres = pts[:, i0, :]
            _, stations = G.project(V, centres)
            direction = G.at(V, stations+3)-G.at(V, stations-3)
            lengths = np.linalg.norm(direction,axis=1)
            if (lengths < 1e-9).any():
                unmeasured.append(dict(piece=p.rec["piece"],reason="undefined flow direction")); continue
            direction /= lengths[:,None]
            normal = np.c_[direction[:,1],-direction[:,0]]
            normal *= np.where(np.sum(normal*np.array(meta),axis=1) >= 0,1,-1)[:,None]
            pts = centres[:,None,:] + xs[None,:,None]*p.scale*normal[:,None,:]
        _, st = G.project(V, pts[:, i0, :])
        keep = (st >= span[0] - 1e-6) & (st <= span[1] + 1e-6)
        pts = pts[keep]; distance = sR[keep]*p.scale
        if not len(pts):
            unmeasured.append(dict(piece=p.rec["piece"],reason="no section in wet span"))
            continue
        flat = pts.reshape(-1, 2)
        wy = G.surface(P, flat, "water").reshape(pts.shape[:2])
        ty = G.terrain_y(H, flat[:, 0], flat[:, 1]).reshape(pts.shape[:2])
        wet = wy > ty
        k = p.kind.replace("_2", "")
        kd = kinds.setdefault(k, dict(samples=0, dry=0, w=[]))
        row_width = np.full(len(wet),np.nan); row_expanded=np.zeros(len(wet),bool)
        for row_idx,row in enumerate(wet):
            n += 1; kd["samples"] += 1
            if not row[i0]:
                n_dry += 1; kd["dry"] += 1; continue
            l = i0
            while l > 0 and row[l - 1]: l -= 1
            r = i0
            while r < len(xs) - 1 and row[r + 1]: r += 1
            edges = (xs[l],xs[r])
            if l == 0 or r == len(xs)-1:
                saturated += 1
                row_expanded[row_idx]=True
                wide_xs=np.round(np.arange(-30.0,30.0001,.1),3)
                centre=pts[row_idx,i0]
                lateral=(pts[row_idx,i0+1]-centre)/.1
                query=centre+wide_xs[:,None]*lateral
                wide_wet=G.surface(P,query,"water")>G.terrain_y(H,query[:,0],query[:,1])
                wl=wr=len(wide_xs)//2
                while wl>0 and wide_wet[wl-1]:wl-=1
                while wr<len(wide_xs)-1 and wide_wet[wr+1]:wr+=1
                if wl==0 or wr==len(wide_xs)-1:
                    unresolved+=1
                    continue
                edges=(wide_xs[wl],wide_xs[wr])
            w = (edges[1] - edges[0]) * p.scale; W.append(w); kd["w"].append(w)
            row_width[row_idx]=w
            example=(float(w),int(p.rec['piece']),row_idx,pts[row_idx,i0,:].round(3).tolist(),[float(x) for x in edges])
            if len(widest)<12:heapq.heappush(widest,example)
            else:heapq.heappushpop(widest,example)
            if edges[0] < -2.4 or edges[1] > 3.0:
                n_out += 1
        broad_runs=[]
        for mask,label in ((row_width>6,'over_6m'),(row_expanded,'expanded')):
            bounds=np.flatnonzero(np.diff(np.r_[False,mask,False])).reshape(-1,2)
            for a,b in bounds:
                length=float(distance[b-1]-distance[a])
                if length>=2:
                    broad_runs.append(dict(kind=label,length_m=round(length,3),start_section=int(a),end_section=int(b-1)))
        local_width.append(dict(piece=p.rec['piece'],kind=p.kind,width_p50=float(np.nanmedian(row_width)) if np.isfinite(row_width).any() else None,
                                broad_runs=broad_runs))
    W = np.array(W)
    if n == 0:
        out[sid] = dict(sections=0, note="no measured section", passed=False); ok_all = False; print(sid, json.dumps(out[sid])); continue
    if not len(W):
        out[sid] = dict(sections=n, centre_dry=n_dry, passed=False); ok_all = False; print(sid, json.dumps(out[sid])); continue
    p50, std, ob = float(np.percentile(W, 50)), float(W.std()), n_out / max(n - n_dry, 1)
    passed = p50 <= 4.0 and std <= 1.0 and ob <= 0.20 and not unmeasured and unresolved == 0; ok_all &= passed
    out[sid] = dict(sections=n, centre_dry=n_dry, width_p10_50_90=np.percentile(W, [10, 50, 90]).round(2).tolist(), width_std=round(std, 3),
                    edge_outside_band_share=round(ob, 6), unmeasured_pieces=unmeasured, expanded_sections=saturated, unresolved_sections=unresolved,
                    local_width=local_width,
                    widest=[dict(width_m=round(w,3),piece=piece,section=section,xz=xz,edges_model=edges) for w,piece,section,xz,edges in sorted(widest,reverse=True)],
                    by_kind={k: dict(samples=v["samples"], dry=v["dry"],
                    p10_50_90=np.percentile(v["w"], [10, 50, 90]).round(2).tolist() if v["w"] else None) for k, v in kinds.items()}, passed=passed)
    print(sid, json.dumps(out[sid]))
json.dump(out, open(run + "/gate-g2.json", "w"), indent=1)
print("G2", "PASS" if ok_all else "FAIL")
sys.exit(0 if ok_all else 1)
