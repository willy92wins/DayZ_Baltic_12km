"""Worklist and sites file of the map-wide streambed kit rollout (streambed_kit_v31.py v9, reach mode), 17-10.

Guillermo, 15-10/17-10: the thin pond-layer streams look polygonal ('el rio al lado es totalmente poligonal', 015-16; 'lo
mismo con monticulos y rios por todo el mapa'); decision 'Kit en malla' for the whole map.
Source: the thin-stream census of EV109 (census.py of the thin_streams design, 16-10: 87 stems, 82.5 km, 2,745 segments of
30 m; stem vertices in course_<reach>.npz, metrics in census-reaches.csv / census-segments.csv). The census was measured on
EV109; the kit runs on EV107 (HANDOFF step 1). Both share the grid; they differ only around the ten EV109 bridges and
kit-118 / kit-7, which this builder handles explicitly (bridge zones, component sites).
Polygonal outline (the metric): wiggle = mean |d bank offset / ds| over both banks along the smoothed course (census.py: a
bank parallel to the course scores 0, a 45-degree single-vertex staircase 1). A stem is IN only when width p50 <= 6 m and its worst 30 m segment has
wiggle >= WIG_SEG (0.40, the census threshold of the 23.4 km 'escalera fina') or the whole stem has wiggle >= WIG_REACH
(0.25). Distance to the 015-16 bridge is reported without overriding this scope. Everything else is OUT with
its numbers (outline already along a triangle edge: wiggle < 0.25 and no segment >= 0.40).
Per stem vertex (EV107): blocked when within R_BRIDGE of a bridge site (sites-ev110.json + the 015-15 pilot: the bridge pass
cuts and seals up to 60 m along the water axis and needs the pond water there), within FROZEN_R of a reserve/platform/narva
or v31_bridge_cut vertex (a road on the stream), within SEA_R of an engine-sea vertex (terrain < 0.75 outside the
envelope), not wet in EV107, inside a component site's body (kit-118 / kit-7), or with a vertex of an envelope cell at
another level (plane outside the stem's range +- 0.05) with a corner within two vertex steps (the tool keeps its path one
step off that water and may not touch it). Runs of unblocked vertices of at least
MIN_LEN become reach sites ('<reach>-<k>'); shorter runs stay pond (reported).
End types (per run end): 'bridge' or 'sea' (the pond water beyond is kept; sill junction), 'road' (the kit stops short of
the road, the old water up to the road is removed: its stem vertices are added to the site body), 'pond' (the stem ends
against water this rollout keeps: wide water, an OUT stem, a short run: sill junction), 'kit' (the stem ends within KIT_R of
an earlier site's course: the course is extended straight to it and the tool trims the chain KK_CLEAR off its axis),
'natural' (dry beyond).
Body per site: the thin vertices (kit_candidates_v31.py:53 rule on EV107: wet, cls 5/6, no wet vertex farther than 1.5
vertices from dry land in its 7x7 window) reached from its run (and road-blocked) stem vertices by a breadth-first search
inside the thin component, at most BODY_STEPS steps, each vertex going to the nearest seed, where the stem vertices of the
water this rollout keeps (bridge zones, other-level and dry stretches, short runs, the streams left out) seed a 'keep' owner;
then every other wet blob of at
most ABSORB_MAX vertices touching a body (outside the bridge zones) joins it, since a kept blob in mid-reach would close the
channel with a sill (measured on EV107: 93 such vertices in 67 blobs of 1-4). The tool removes the pond cells
touching body vertices and keeps every other water (a review of 16-10 found that filling whole components destroyed
tributaries).
Order: component sites first, then mains (x.0) before branches, longer first.
Exclusions: an optional JSON {site id: reason} drops those runs after a gated run of the tool (a reach whose own gates fail
stays pond, with the reason in the worklist); their stem vertices then seed 'keep' like the other kept water.
Usage: kit_worklist_v31.py <census_dir> <terrain.npz> <footprint.npz> <envelope.npy> <bridge_sites.json> <component_sites.json>
       <out_sites.json> <out_worklist.json> [exclusions.json]
"""
import csv, json, math, sys
from collections import deque
import numpy as np
from scipy.ndimage import label, distance_transform_edt, maximum_filter, binary_dilation
from scipy.spatial import cKDTree

ZTOP = 12282.0
WIG_SEG, WIG_REACH = 0.40, 0.25
MAX_WIDTH_P50 = 6.0  # EV112 OT1: wider stems retain the pond layer.
FORCE_SITE, FORCE_R = "015-16", 30.0
PILOT_BRIDGES = {"015-15": (9091.0, 10305.0)}
R_BRIDGE, FROZEN_R, SEA_R, MIN_LEN, KIT_R, BODY_STEPS, POND_R = 75.0, 6.5, 12.0, 48.0, 30.0, 4, 12.0
ABSORB_MAX = 6
N8 = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc]


def xz(r, c):
    return np.array([6.0 * c, ZTOP - 6.0 * r])


def main():
    cdir, tpath, fpath, epath, bpath, cpath, out_sites, out_list = sys.argv[1:9]
    excl = json.load(open(sys.argv[9])) if len(sys.argv) > 9 else {}
    env = np.load(epath).astype(np.float64)
    z = np.load(tpath); H = z["heights"].astype(np.float64); cls = z["cls"]
    frozen = z["reserve"] | z["platform"] | z["narva"] | z["v31_bridge_cut"]
    pl = np.load(fpath)["plane"].astype(np.float64)
    vp = np.full(H.shape, -np.inf); cp = np.where(np.isfinite(pl), pl, -np.inf)
    for dr in (0, 1):
        for dc in (0, 1):
            vp[dr:dr + 2047, dc:dc + 2047] = np.maximum(vp[dr:dr + 2047, dc:dc + 2047], cp)
    wet = np.isfinite(vp) & (H < vp)
    thin = wet & (maximum_filter(distance_transform_edt(wet), size=7) <= 1.5) & np.isin(cls, (5, 6))
    tlab, _ = label(thin, np.ones((3, 3), bool))
    inc = np.zeros(H.shape, bool)
    for dr in (0, 1):
        for dc in (0, 1):
            inc[dr:dr + 2047, dc:dc + 2047] |= np.isfinite(pl)
    sea = (H < 0.75) & ~inc
    wlab, _ = label(wet, np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]]))
    comp_sites = json.load(open(cpath))
    comp_body = np.zeros(H.shape, bool)
    for s in comp_sites:
        sr, sc = int(round((ZTOP - s["seed"][1]) / 6)), int(round(s["seed"][0] / 6))
        w = np.argwhere(wet[sr - 3:sr + 4, sc - 3:sc + 4])
        rr, cc = w[np.argmin(np.hypot(w[:, 0] - 3, w[:, 1] - 3))] + (sr - 3, sc - 3)
        comp_body |= wlab == wlab[rr, cc]
    bridges = {b["id"]: (b["x"], b["z"]) for b in json.load(open(bpath))}
    bridges.update(PILOT_BRIDGES)
    BR = np.array(list(bridges.values())); BRid = list(bridges)
    fz = np.argwhere(frozen); ftree = cKDTree(np.c_[6.0 * fz[:, 1], ZTOP - 6.0 * fz[:, 0]])
    sv = np.argwhere(sea); stree = cKDTree(np.c_[6.0 * sv[:, 1], ZTOP - 6.0 * sv[:, 0]]) if len(sv) else None
    reaches = list(csv.DictReader(open(cdir + "/census-reaches.csv")))
    segs = list(csv.DictReader(open(cdir + "/census-segments.csv")))
    segmax = {}
    for g in segs:
        if g.get("wiggle"):
            segmax[g["reach"]] = max(segmax.get(g["reach"], 0.0), float(g["wiggle"]))
    fx, fzz = bridges[FORCE_SITE]
    stems, out_list_rows, out_stems = {}, [], {}
    for r in reaches:
        rid = r["reach"]; c = np.load(f"{cdir}/course_{rid}.npz")
        dmin = float(np.min(np.hypot(c["xs"] - fx, c["zs"] - fzz)))
        wig, wmax = float(r["wiggle"]), segmax.get(rid, 0.0)
        width = float(r["width_p50"])
        assert math.isfinite(width) and width >= 0, f"invalid census width: {rid}"
        reason = ("segment wiggle %.3f >= %.2f" % (wmax, WIG_SEG) if wmax >= WIG_SEG else
                  "stem wiggle %.3f >= %.2f" % (wig, WIG_REACH) if wig >= WIG_REACH else
                  None)
        if width > MAX_WIDTH_P50:
            reason = None
        excluded_reason = ("width p50 %.3f > %.2f m: retain pond" % (width, MAX_WIDTH_P50) if width > MAX_WIDTH_P50 else
                           "outline along a triangle edge: stem wiggle %.3f < %.2f and worst segment %.3f < %.2f" % (wig, WIG_REACH, wmax, WIG_SEG))
        row = dict(reach=rid, length_m=float(r["length_m"]), wiggle=wig, worst_segment_wiggle=wmax, width_p50=float(r["width_p50"]),
                   d_015_16_m=round(dmin, 1), selected=reason is not None, reason=reason or excluded_reason)
        out_list_rows.append(row)
        if reason:
            stems[rid] = np.c_[c["rr"], c["cc"]].astype(int)
        else:
            out_stems[rid] = np.c_[c["rr"], c["cc"]].astype(int)
    # orient upstream first (higher plane first; ties by terrain)
    for rid, S in stems.items():
        a, b = S[:10], S[-10:]
        ka = (np.mean(vp[a[:, 0], a[:, 1]]), np.mean(H[a[:, 0], a[:, 1]])); kb = (np.mean(vp[b[:, 0], b[:, 1]]), np.mean(H[b[:, 0], b[:, 1]]))
        if kb > ka:
            stems[rid] = S[::-1]
    order = sorted(stems, key=lambda k: (int(k.split(".")[1]) > 0, -len(stems[k]), k))
    # water of the OTHER selected stems is replaced by the kit: it never counts as 'another level' for a neighbour (a branch
    # meets its main at another plane); water around the stem's own course does
    zone = {}
    zcount = np.zeros((2047, 2047), np.int16)
    for k_, S_ in stems.items():
        z_ = np.zeros(H.shape, bool); z_[S_[:, 0], S_[:, 1]] = True
        z_ = binary_dilation(z_, np.ones((3, 3), bool), iterations=4)      # the water and its envelope rings
        zone[k_] = z_[:-1, :-1] | z_[:-1, 1:] | z_[1:, :-1] | z_[1:, 1:]
        zcount += zone[k_]
    # per-vertex blocking
    runs, blocked_log, keep_seed = [], {}, set()
    for rid in order:
        S = stems[rid]; P = np.array([xz(r, c) for r, c in S])
        dB = np.min(np.hypot(P[:, None, 0] - BR[None, :, 0], P[:, None, 1] - BR[None, :, 1]), 1)
        kB = np.argmin(np.hypot(P[:, None, 0] - BR[None, :, 0], P[:, None, 1] - BR[None, :, 1]), 1)
        dF = ftree.query(P)[0]; dS = stree.query(P)[0] if stree is not None else np.full(len(P), np.inf)
        why = np.full(len(S), "", object)
        why[~wet[S[:, 0], S[:, 1]]] = "dry107"
        why[comp_body[S[:, 0], S[:, 1]]] = "component"
        why[dS <= SEA_R] = "sea"
        why[dF <= FROZEN_R] = "road"
        why[dB <= R_BRIDGE] = "bridge"
        # envelope water at another level within two vertex steps: the kit would have to run beside a pond it may not
        # touch (third rollout: a reach beside a pond 1.25 m lower, margins down to -2.4 m); the reach stops there
        lo_, hi_ = float(np.min(vp[S[:, 0], S[:, 1]])) - 0.05, float(np.max(vp[S[:, 0], S[:, 1]])) + 0.05
        oth = np.isfinite(env) & ((env < lo_) | (env > hi_)) & ~((zcount - zone[rid]) > 0)
        hit = np.zeros(len(S), bool)
        for dr in (-3, -2, -1, 0, 1, 2):                           # cells with a corner within two vertex steps of v
            for dc in (-3, -2, -1, 0, 1, 2):
                a_, b_ = np.clip(S[:, 0] + dr, 0, 2046), np.clip(S[:, 1] + dc, 0, 2046)
                hit |= oth[a_, b_]
        why[hit & (why == "")] = "other_level"
        blocked_log[rid] = {k: int((why == k).sum()) for k in ("bridge", "road", "sea", "dry107", "component", "other_level")}
        keep_seed |= {tuple(int(x) for x in v) for v, w in zip(S, why) if w and w != "road"}
        i = 0
        while i < len(S):
            if why[i]:
                i += 1; continue
            j = i
            while j + 1 < len(S) and not why[j + 1]:
                j += 1
            L = float(np.sum(np.linalg.norm(np.diff(P[i:j + 1], axis=0), axis=1)))
            runs.append(dict(reach=rid, i0=i, i1=j, length=L, why_up=why[i - 1] if i > 0 else "end", why_dn=why[j + 1] if j + 1 < len(S) else "end",
                             bridge_up=BRid[kB[i - 1]] if i > 0 and why[i - 1] == "bridge" else None,
                             bridge_dn=BRid[kB[j + 1]] if j + 1 < len(S) and why[j + 1] == "bridge" else None))
            i = j + 1
    short = [r for r in runs if r["length"] < MIN_LEN]
    for r in short:                                                # a run too short for the kit stays pond
        keep_seed |= {tuple(int(x) for x in v) for v in stems[r["reach"]][r["i0"]:r["i1"] + 1]}
    for S_ in out_stems.values():                                  # streams left out keep their water
        keep_seed |= {tuple(int(x) for x in v) for v in S_}
    runs = [r for r in runs if r["length"] >= MIN_LEN]
    for k, r in enumerate(runs):
        r["id"] = f"{r['reach']}-{sum(1 for q in runs[:k] if q['reach'] == r['reach'])}"
    excluded = [dict(site=r["id"], length_m=round(r["length"], 1), reason=excl[r["id"]]) for r in runs if r["id"] in excl]
    for r in runs:
        if r["id"] in excl:
            keep_seed |= {tuple(int(x) for x in v) for v in stems[r["reach"]][r["i0"]:r["i1"] + 1]}
    runs = [r for r in runs if r["id"] not in excl]
    # road-blocked stem vertices go to the adjacent run's body (cut up to the road)
    claim_src = {}
    for r in runs:
        S = stems[r["reach"]]
        src = [tuple(v) for v in S[r["i0"]:r["i1"] + 1]]
        for side, step in (("up", -1), ("dn", 1)):
            if r["why_" + side] == "road":
                i = (r["i0"] if side == "up" else r["i1"]) + step
                S_ = stems[r["reach"]]
                while 0 <= i < len(S_):
                    v = tuple(S_[i])
                    if not (np.linalg.norm(xz(*v) - xz(*S_[i - step])) < 9) or not wet[v]:
                        break
                    P1 = xz(*v)
                    if ftree.query(P1)[0] > FROZEN_R:
                        break
                    src.append(v); i += step
        claim_src[r["id"]] = src
    # breadth-first body assignment inside thin components
    owner = {}
    dq = deque()
    for r in runs:
        for v in claim_src[r["id"]]:
            if v not in owner:
                owner[v] = (r["id"], 0); dq.append(v)
    # kept stem vertices seed the same search, so a thin vertex nearer to water this rollout keeps is not taken (the first
    # version took up to BODY_STEPS vertices of the bridge zones and of the streams left out: gaps of 20-120 m at the junctions)
    for v in sorted(keep_seed):
        if v not in owner:
            owner[v] = ("KEEP", 0); dq.append(v)
    while dq:
        v = dq.popleft(); sid, d = owner[v]
        if d >= BODY_STEPS:
            continue
        for dr, dc in N8:
            u = (v[0] + dr, v[1] + dc)
            if u in owner or not (0 <= u[0] < 2048 and 0 <= u[1] < 2048) or not thin[u] or comp_body[u]:
                continue
            if tlab[u] != tlab[v] and not wet[u]:
                continue
            owner[u] = (sid, d + 1); dq.append(u)
    body = {r["id"]: [] for r in runs}
    for v, (sid, _) in owner.items():
        if sid != "KEEP" and wet[v] and not comp_body[v]:
            body[sid].append([int(v[0]), int(v[1])])
    claimed = np.zeros(H.shape, bool)
    for sid, B in body.items():
        if B:
            Bv = np.array(B); claimed[Bv[:, 0], Bv[:, 1]] = True
    # small blobs of other wet vertices touching a body (a wet bank vertex of another class, a thin vertex one step beyond
    # the search) go to that body: kept, they would close the channel with a sill in mid-reach
    kept0 = wet & ~claimed & ~comp_body
    retained_seeds = {v for v in keep_seed if kept0[v]}
    klab, _ = label(kept0, np.ones((3, 3), bool)); ksize = np.bincount(klab.ravel())
    near_claim = binary_dilation(claimed, np.ones((3, 3), bool))
    absorbed = 0
    for k in np.unique(klab[kept0 & near_claim]):
        if ksize[k] > ABSORB_MAX:
            continue
        vv = np.argwhere(klab == k)
        if any(tuple(int(x) for x in v) in keep_seed for v in vv):
            continue  # Explicit retained-water seeds must never be absorbed into a replacement body.
        P_ = np.c_[6.0 * vv[:, 1], ZTOP - 6.0 * vv[:, 0]]
        if np.min(np.hypot(P_[:, None, 0] - BR[None, :, 0], P_[:, None, 1] - BR[None, :, 1])) <= R_BRIDGE:
            continue
        cand = []
        for a, b in vv:
            for dr, dc in N8:
                u = (int(a) + dr, int(b) + dc)
                if u in owner and claimed[u] and owner[u][0] != "KEEP":
                    cand.append(owner[u][0])
        if not cand:
            continue
        # Equal neighbour counts go to the lexicographically first site id,
        # independently of the hash seed in this process.
        sid = max(sorted(set(cand)), key=cand.count)
        for v in vv:
            body[sid].append([int(v[0]), int(v[1])]); claimed[v[0], v[1]] = True; absorbed += 1
    lost_seeds = sorted(v for v in retained_seeds if claimed[v])
    assert not lost_seeds, f"retained water absorbed into a kit body: {lost_seeds[:10]}"
    kept_wet = wet & ~claimed & ~comp_body
    kw = np.argwhere(kept_wet); ktree = cKDTree(np.c_[6.0 * kw[:, 1], ZTOP - 6.0 * kw[:, 0]])
    # end types
    courses = {}
    sites = []
    for r in runs:
        S = stems[r["reach"]][r["i0"]:r["i1"] + 1]
        P = np.array([xz(a, b) for a, b in S])
        ends = {}
        ext = {}
        for side, v in (("up", S[0]), ("dn", S[-1])):
            w = r["why_" + side]
            if w in ("bridge", "sea"):
                ends[side] = w
            elif w in ("road",):
                ends[side] = "road"
            elif w in ("dry107", "component", "other_level"):
                ends[side] = "pond"
            else:
                p = xz(*v)
                partner = None
                for q in sites:
                    Q = courses[q["id"]]
                    d = np.hypot(Q[:, 0] - p[0], Q[:, 1] - p[1]); k = int(np.argmin(d))
                    if d[k] <= KIT_R and (partner is None or d[k] < partner[1]):
                        partner = (q["id"], float(d[k]), Q[k])
                near_kept = ktree.query(p)[0] <= POND_R
                if partner is not None:
                    ends[side] = "kit"; ext[side] = dict(partner=partner[0], to=[round(float(partner[2][0]), 2), round(float(partner[2][1]), 2)], d_m=round(partner[1], 2))
                elif near_kept:
                    ends[side] = "pond"
                else:
                    ends[side] = "natural"
        courses[r["id"]] = P
        site = dict(id=r["id"], mode="reach", family="leaf", reach=r["reach"], stem=[[int(a), int(b)] for a, b in S],
                    end_causes={side: str(r["why_" + side]) for side in ("up", "dn")},
                    body=sorted(body[r["id"]]), ends=ends, extend=ext, length_m=round(r["length"], 1),
                    bridge={k: r["bridge_" + k] for k in ("up", "dn") if r["bridge_" + k]})
        sites.append(site)
    all_sites = [dict(s) for s in comp_sites] + sites
    with open(out_sites, "w", newline="\n") as f:
        json.dump(all_sites, f, separators=(",", ":"))
    thin_left = thin & ~claimed & ~comp_body
    rep = dict(schema="kit-worklist-v31.v1", params=dict(WIG_SEG=WIG_SEG, WIG_REACH=WIG_REACH, MAX_WIDTH_P50=MAX_WIDTH_P50, FORCE_SITE=FORCE_SITE, FORCE_R=FORCE_R,
               R_BRIDGE=R_BRIDGE, FROZEN_R=FROZEN_R, SEA_R=SEA_R, MIN_LEN=MIN_LEN, KIT_R=KIT_R, BODY_STEPS=BODY_STEPS, POND_R=POND_R, ABSORB_MAX=ABSORB_MAX),
               census_stems=len(reaches), census_km=round(sum(float(r["length_m"]) for r in reaches) / 1000, 2),
               selected_stems=len(stems), selected_km=round(sum(x["length_m"] for x in out_list_rows if x["selected"]) / 1000, 2),
               out_stems=[x for x in out_list_rows if not x["selected"]], in_stems=[x for x in out_list_rows if x["selected"]],
               blocked_vertices=blocked_log, sites=len(sites), site_km=round(sum(s["length_m"] for s in sites) / 1000, 2),
               short_runs_left_as_pond=[dict(reach=r["reach"], length_m=round(r["length"], 1), why=[r["why_up"], r["why_dn"]]) for r in short],
               excluded_by_gates=excluded,
               end_types={t: sum(1 for s in sites for e in s["ends"].values() if e == t) for t in ("natural", "pond", "road", "bridge", "sea", "kit")},
               body_vertices=int(claimed.sum()), absorbed_wet_blob_vertices=absorbed, thin_vertices=int(thin.sum()), thin_left_as_pond=int(thin_left.sum()),
               site_list=[dict(id=s["id"], length_m=s["length_m"], ends=s["ends"], extend=s["extend"], bridge=s["bridge"], body=len(s["body"])) for s in sites])
    with open(out_list, "w", newline="\n") as f:
        json.dump(rep, f, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k not in ("out_stems", "in_stems", "site_list", "blocked_vertices", "short_runs_left_as_pond")}, indent=1))
    print("OUT", [(x["reach"], x["length_m"], x["wiggle"], x["worst_segment_wiggle"]) for x in rep["out_stems"]])


if __name__ == "__main__":
    main()
