IMPORTANT PROCESS NOTE: write the complete files FIRST, in one pass, then stop. Keep internal deliberation focused.
The receiver re-runs every changed tool with its DEFAULTS and compares sha256 against archived outputs: with the
defaults, terrain/water/image outputs must be byte-identical to today's. Change nothing that the task does not ask for.
Code and comments in English; keep the style of the surrounding code (comment density, naming, idiom).
Output: one fenced block per changed or new file, each preceded by the line `FILE: <repo-relative path>`, whole file.
Coordinates: game metres, x east, z north; the vertex grid is N = 2048 vertices every 6 m, row r at z = 12282 - 6r,
column c at x = 6c (tools/terrain/v30_common.py).

# Task P3: external outline and low-water banks in tools/terrain/profile_inland_v30.py, and the matching gate in
# tools/terrain/verify_terrain_v30.py
Measured problem (06-10): the shore pass computes each component's outline from the 6 m CLASS raster (lines 151-164:
EDT of the component, Gaussian, clamp); a long straight row of the raster stays straight after smoothing, so the visible
waterline of rivers follows grid rows. A smoothed VECTOR outline of the design exists as a signed-distance field
(npz key 'sd', float32 N x N, metres, negative inside water, NaN where undefined, sign set by the class). Second
problem: very low water (level about 1.0 m) has its bank vertices held at the 1.40 m land floor, so the crossing of
the water plane can only fall near the wet vertex.
1. `--outline-sd PATH` and `--outline-sd-classes` (comma list of class codes, default "2,5,7"). Without --outline-sd
   the tool behaves exactly as today. With it: main() loads np.load(path)['sd'] as float64 once and passes it through
   the args namespace (the selftest builds an argparse.Namespace without it: read it with getattr(a, 'ext_sd', None)).
   In profile(), per component window, after the raster sd (lines 163-164) and once Lw and wat_cls are known (lines
   166-169; you may compute them earlier, results must not change): at every window vertex where the external value is
   finite AND its sign agrees with the input class (ext < 0 on a vertex of this component B, ext > 0 on a land vertex
   lw0) AND the relevant class is in the list (for a B vertex its own class cls0w, for a land vertex wat_cls, the class
   of the nearest component vertex), sd takes the external value. Everything after (bandm, crossing edges, edge
   records, targets) uses the combined sd.
2. `--low-water-bank` (flag) and `--low-water-bank-min M` (default 1.0). Without the flag: today's behaviour. With
   it: a LAND vertex that this component forces (forced & lw0, after line 191) and whose floor today comes from the
   1.40 m land floor rather than from the water (near_lv + G['freeboard_m'] < floor, the arrays of lines 109-115)
   gets the per-vertex floor max(near_lv + freeboard, pmax, M) + EPS instead of lfloor; NaN pmax counts as absent
   (use np.fmax like line 115). Only those vertices; every other land vertex keeps lfloor. Use this per-vertex floor
   in the clamp of line 196 and in `broke` (line 199). Keep a mask of the vertices this rule relaxed (over all
   components) for the report and the gates.
3. Gates (lines 251-253): gate_counts (tools/terrain/profile_rivers_v30.py:82, excerpt below) counts land under 1.40 m
   as 'land_floor' failures. With --low-water-bank, compute the AFTER counts on a copy of h2 where the relaxed
   vertices that stand at or above their own relaxed floor are lifted to G['land_floor_m'], so only true failures
   count; then the existing assert (after <= before) must hold. Report 'low_water_bank': {'vertices': relaxed vertices
   below 1.40 in the output, 'below_own_floor': count below their own floor (expected 0)} under 'vertices'.
4. The report 'params' must stay JSON-serialisable: Paths as str, never the array.
5. `--selftest` must still pass unchanged. Update the module docstring (steps 2 and 3, the gates and Usage).
6. tools/terrain/verify_terrain_v30.py (argv-based): add `--low-water-bank-min M` (default absent = today's output
   byte for byte). With it, a land vertex counted by the land_floor gate (line 73: same mask) that is 8-adjacent to an
   inland water vertex (classes 2, 3, 5, 6, 7 with level > 0.80) whose level + 0.05 < 1.40 (use the highest such
   adjacent level) passes that gate when h >= max(level + 0.05, M) - 1e-6; count those vertices and their failures
   under out["land_floor"]["low_water_bank"] = {"vertices": n, "fail": f}; "fail" of land_floor then counts the other
   vertices below 1.40 plus f.

### tools/terrain/profile_rivers_v30.py, lines 76-111 (read only, for reference)
```python
  76|         out[c] = {'edges': int(m.sum()), 'no_crossing': int((m & ~ok).sum()),
  77|                   **({q: round(float(np.percentile(vv, p)), 3)
  78|                       for q, p in (('p50', 50), ('p90', 90), ('p99', 99))} if vv.size else {})}
  79|     return out
  80| 
  81| 
  82| def gate_counts(h, cls, level, beach, narva600, planes):
  83|     """water_depth, banks, land/beach floor, pieces and slope counts exactly as verify_terrain_v30.py computes them."""
  84|     water = cls > 0
  85|     land = ~water
  86|     dist, idx = ndimage.distance_transform_edt(land, sampling=6.0, return_indices=True)
  87|     near_lv = level[idx[0], idx[1]]
  88|     with np.errstate(invalid='ignore'):
  89|         wd = int((water & ~narva600 & (level - h < G['depth_min_m'])).sum())
  90|         banks = int((land & (dist <= G['bank_radius_m']) & ~narva600 & (h < near_lv + G['freeboard_m'])).sum())
  91|     lf = int((land & ~narva600 & ~beach & (h < G['land_floor_m'] - 1e-6)).sum())
  92|     bf = int((beach & (h < G['beach_floor_m'] - 1e-6)).sum())
  93|     n = h.shape[0]
  94|     czone = narva600[:-1, :-1] | narva600[:-1, 1:] | narva600[1:, :-1] | narva600[1:, 1:]
  95|     pw = pl = 0
  96|     for dr in (0, 1):
  97|         for dc in (0, 1):
  98|             hc = h[dr:dr + n - 1, dc:dc + n - 1]
  99|             wc = water[dr:dr + n - 1, dc:dc + n - 1]
 100|             ok = np.isfinite(planes) & ~czone
 101|             with np.errstate(invalid='ignore'):
 102|                 pw += int((ok & wc & (hc > planes - PIECE_DEPTH)).sum())
 103|                 pl += int((ok & ~wc & (hc < planes)).sum())
 104|     nwd, new, nsw, nse = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
 105|     ang = np.r_[np.degrees(np.arctan(np.hypot((new - nwd) / 6.0, (nse - new) / 6.0))).ravel(),
 106|                 np.degrees(np.arctan(np.hypot((nsw - nwd) / 6.0, (nse - nsw) / 6.0))).ravel()]
 107|     lnw, lne, lsw, lse = land[:-1, :-1], land[:-1, 1:], land[1:, :-1], land[1:, 1:]
 108|     mland = np.r_[(lnw & lne & lse).ravel(), (lnw & lsw & lse).ravel()]
 109|     sl = int((mland & (ang > 35.01)).sum())
 110|     return {'water_depth': wd, 'banks': banks, 'land_floor': lf, 'beach_floor': bf, 'slopes': sl, 'pieces': pw + pl}
 111| 
```

# The files to change (full listings)

### tools/terrain/profile_inland_v30.py (full file, 398 lines)
```python
   1| """Standing and flowing inland water shores V30 on one smoothed outline per component, and the inland-bed floor.
   2| 
   3| The water of every inland body is drawn per 6 m cell at a plane (v30_common.cell_planes); standing water (lakes,
   4| ponds) sits at a flat centimetre level, a flowing body (navigable reach, river, stream) descends in 0.025 m plane
   5| steps. The visible shore is where the native terrain (6 m grid, NW-SE diagonals) crosses those planes.
   6| profile_lakes_v30.py and profile_rivers_v30.py fixed the same per kind of water, but each froze everything within
   7| 22 m of the other kind, so wetlands where ponds, lakes and rivers interleave kept the 6 m staircase. This tool
   8| profiles both kinds in one pass, component by component, each with per-vertex levels:
   9| 1. Components in one id space: standing bodies by centimetre level (relevel_bodies_v30.label_bodies, 8-connected,
  10|    bodies under 4 vertices left unlabelled), flowing bodies 8-connected above the 0.80 m plane cut, offset past the
  11|    standing ids; components under --min-vertices are not profiled.
  12| 2. Outline: signed distance to the component (negative inside), Gaussian-smoothed (--sigma m) and clamped so the
  13|    zero line moves at most --max-shift; then the exact distance to its zero contour, signed by the smoothed field.
  14| 3. Profile: a vertex ending a native edge (east, south, NW-SE diagonal) whose ends lie on opposite sides of the
  15|    outline takes Lw + --slope * sd, where Lw is the level of the nearest component vertex. The side of a vertex is
  16|    its INPUT class, never the sign of sd, so no class or level changes and the cell planes, and with them the
  17|    existing water pieces, stay valid: water is capped at min(level - 0.10, plane - 0.02), land at
  18|    max(nearest level + 0.05, plane, land floor) (1.40 m, 0.80 m on the beach); each move capped (--max-raise-water
  19|    on water, --max-raise on land, --max-lower down); a vertex whose capped target still breaks its gate keeps its
  20|    height. A land vertex edited by several components keeps the MAXIMUM of their targets, so it stays above every
  21|    water it borders; a water vertex is edited only by its own component.
  22| 4. Edits that make a land face steeper than 35 degrees (or than it was) are undone.
  23| 5. Bed floor (--bed-floor F): every lake, pond, river and stream vertex of a profiled component outside the exact
  24|    corridors, the Narva zone, the map border and the vanilla reach cells rises to min(F, level - --bed-min-depth,
  25|    gate cap). Navigable reaches keep their depth (Guillermo, 05-10).
  26| Fixed for the shore profile: platforms, reserves, the exact 24 m navigable and delta corridor vertices (only those,
  27| so the channel edges stay free), the Narva zone and the map border, the sea and the delta, low inland water at or
  28| below the 0.80 m plane cut (drawn by the engine sea), unlabelled standing water, the vertices of the vanilla channel
  29| reaches (<channels>/axes.json removed cells), components below --min-vertices, and every vertex within
  30| --band + --max-shift + 6 m of any of those. A vertex near two components is NOT fixed any more, so shores where a
  31| lake or pond touches a river or stream are profiled (Guillermo, 06-10); the nature envelope is not fixed either,
  32| its reserve stays the same while the drawing of its shores changes.
  33| No class or level changes, so the cell planes and the existing water pieces stay valid: no water tile is rebuilt.
  34| Usage: profile_inland_v30.py --terrain IN.npz --out OUTDIR --channels FITDIR [--slope 0.15] [--band 12]
  35|                              [--sigma 12] [--max-shift 4] [--min-vertices 4] [--max-raise 2.0]
  36|                              [--max-raise-water 6.0] [--max-lower 1.5] [--bed-floor F] [--bed-min-depth 0.30]
  37|                              [--narva-radius 620] [--sea-cut 0.51]
  38|        profile_inland_v30.py --selftest
  39| """
  40| import argparse
  41| import json
  42| import sys
  43| import time
  44| from pathlib import Path
  45| 
  46| import numpy as np
  47| import shapely
  48| from scipy import ndimage
  49| 
  50| sys.path.insert(0, str(Path(__file__).resolve().parent))
  51| from v30_common import N, cell_planes, grid_xz, vertex_plane_bounds  # noqa: E402
  52| from finish_shores_v30 import discard_steeper_land_faces, protect_corridors  # noqa: E402
  53| from profile_coast_v30 import EDGES, NARVA, SEA_CLASSES, sha  # noqa: E402
  54| from profile_lakes_v30 import G, EPS, window_lines  # noqa: E402
  55| from relevel_bodies_v30 import label_bodies  # noqa: E402
  56| from profile_rivers_v30 import PIECE_DEPTH, gate_counts, same_level  # noqa: E402
  57| 
  58| FLOWING = (3, 5, 6)
  59| STANDING = (2, 7)
  60| INLAND = STANDING + FLOWING
  61| 
  62| 
  63| def edge_offsets(h, edges):
  64|     """Distance (m) along each recorded native edge between the terrain crossing of the local level Lw and the
  65|     outline crossing, per water-end class; edges whose terrain no longer crosses Lw are counted apart."""
  66|     ra, ca, rb, cb, tstar, length, lv, k = edges
  67|     out = {}
  68|     for c in INLAND:
  69|         out[c] = {'edges': 0}
  70|     if ra.size == 0:
  71|         return out
  72|     ha, hb = h[ra, ca] - lv, h[rb, cb] - lv
  73|     ok = ha * hb < 0
  74|     t = np.where(ok, ha / np.where(ok, ha - hb, 1.0), np.nan)
  75|     v = np.abs(t - tstar) * length
  76|     for c in INLAND:
  77|         m = k == c
  78|         vv = v[m & ok]
  79|         out[c] = {'edges': int(m.sum()), 'no_crossing': int((m & ~ok).sum()),
  80|                   **({q: round(float(np.percentile(vv, p)), 3)
  81|                       for q, p in (('p50', 50), ('p90', 90), ('p99', 99))} if vv.size else {})}
  82|     return out
  83| 
  84| 
  85| def profile(t, corridor, reach_vertices, a):
  86|     """The whole method on the terrain arrays t; returns (output arrays, masks, report without inputs)."""
  87|     h0 = t['heights'].astype(np.float64)
  88|     cls0 = t['cls'].copy()
  89|     level0 = t['level'].astype(np.float64)
  90|     x, z = grid_xz()
  91|     flow0 = np.isin(cls0, FLOWING)
  92|     stand0 = np.isin(cls0, STANDING)
  93|     land0 = cls0 == 0
  94|     low = np.isin(cls0, INLAND) & (level0 <= G['plane_cut_m'])
  95|     sids = label_bodies(cls0, level0)
  96|     n_standing = int(sids.max())
  97|     flab, n_flowing = ndimage.label(flow0 & ~low, structure=np.ones((3, 3), bool))
  98|     ids = sids.copy()
  99|     fm = flab > 0
 100|     ids[fm] = (flab[fm] + n_standing).astype(np.int32)
 101|     n_comp = n_standing + n_flowing
 102|     narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= a.narva_radius
 103|     narva600 = np.hypot(x - NARVA[0], z - NARVA[1]) <= G['narva_zone_excluded_m']
 104|     border = (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
 105| 
 106|     # per-vertex gate fields from the input; exact for the output because no class or level changes
 107|     planes = cell_planes(cls0, level0, sea_cut=a.sea_cut)
 108|     pmin, pmax = vertex_plane_bounds(planes)
 109|     dist, idx = ndimage.distance_transform_edt(land0, sampling=6.0, return_indices=True)
 110|     near_lv = level0[idx[0], idx[1]]
 111|     wcap = level0 - G['depth_min_m'] - EPS
 112|     pm = np.isfinite(pmin)
 113|     wcap[pm] = np.minimum(wcap[pm], pmin[pm] - PIECE_DEPTH - EPS)
 114|     floor = np.where(t['beach'], G['beach_floor_m'], G['land_floor_m'])
 115|     lfloor = np.fmax(near_lv + G['freeboard_m'], np.fmax(pmax, floor)) + EPS
 116| 
 117|     reach = a.band + a.max_shift + 6.0
 118|     rv = int(np.ceil(reach / 6.0))
 119|     yy, xx = np.mgrid[-rv:rv + 1, -rv:rv + 1]
 120|     disc = np.hypot(yy, xx) * 6.0 <= reach
 121|     objs = ndimage.find_objects(ids)
 122|     sizes = np.bincount(ids.ravel(), minlength=n_comp + 1)
 123|     small = (ids > 0) & (sizes[ids] < a.min_vertices)
 124|     loose = stand0 & (sids == 0) & ~low
 125|     other = (np.isin(cls0, SEA_CLASSES) | low | reach_vertices | loose | small)
 126|     near_other = ndimage.distance_transform_edt(~other) * 6.0 <= reach if other.any() else np.zeros((N, N), bool)
 127|     fixed = t['platform'] | t['reserve'] | corridor | narva | border | other | near_other
 128| 
 129|     h1 = h0.copy()
 130|     land_max = np.full((N, N), -np.inf)
 131|     land_set = np.zeros((N, N), bool)
 132|     land_n = np.zeros((N, N), np.uint8)
 133|     masks = {k: np.zeros((N, N), bool) for k in ('band', 'forced', 'editable')}
 134|     counts = dict(profiled=0, skipped_no_outline=0, forced_at_cap=0, kept_by_gate=0)
 135|     profiled = np.zeros(n_comp + 1, bool)
 136|     per_class = {k: dict(forced=0, changed=0) for k in INLAND}
 137|     rows = []
 138|     e_ra, e_ca, e_rb, e_cb, e_tstar, e_len, e_lv, e_k = ([] for _ in range(8))
 139|     g = int(np.ceil((reach + 3 * a.sigma + 12.0) / 6.0))
 140|     for i, sl in enumerate(objs, 1):
 141|         if sl is None or sizes[i] < a.min_vertices:
 142|             continue
 143|         r0, r1 = max(sl[0].start - g, 0), min(sl[0].stop + g, N)
 144|         c0, c1 = max(sl[1].start - g, 0), min(sl[1].stop + g, N)
 145|         W = (slice(r0, r1), slice(c0, c1))
 146|         B = ids[W] == i
 147|         nb = int(B.sum())
 148|         hw0 = h0[W]
 149|         cls0w, level0w = cls0[W], level0[W]
 150|         lw0 = land0[W]
 151|         base = np.where(B, -ndimage.distance_transform_edt(B), ndimage.distance_transform_edt(~B)) * 6.0
 152|         smooth = ndimage.gaussian_filter(base, a.sigma / 6.0)
 153|         smooth = np.clip(smooth, base - a.max_shift, base + a.max_shift)
 154|         near = np.abs(base) <= a.band + a.max_shift + 9.0
 155|         lines = window_lines(smooth, near, r0, c0)
 156|         if not lines:
 157|             counts['skipped_no_outline'] += 1
 158|             continue
 159|         segs = np.concatenate([np.stack([ln[:-1], ln[1:]], axis=1) for ln in lines])
 160|         tree = shapely.STRtree(shapely.linestrings(segs))
 161|         xw, zw = x[W], z[W]
 162|         _, d = tree.query_nearest(shapely.points(xw[near], zw[near]), return_distance=True, all_matches=False)
 163|         sd = np.full(B.shape, np.nan)
 164|         sd[near] = np.where(smooth[near] < 0, -d, d)
 165|         bandm = near & np.isfinite(sd) & (np.abs(sd) <= a.band)
 166|         # local level: the level of the nearest component vertex, for the profile target and the metric
 167|         _, j = ndimage.distance_transform_edt(~B, return_indices=True)
 168|         Lw = level0w[j[0], j[1]]
 169|         wat_cls = cls0w[j[0], j[1]]
 170|         edit = bandm & (B | lw0) & ~fixed[W]
 171|         ends = B | lw0
 172|         nr, nc = B.shape
 173|         forced = np.zeros(B.shape, bool)
 174|         for dr, dc in EDGES:
 175|             sa, sb = sd[:nr - dr, :nc - dc], sd[dr:, dc:]
 176|             with np.errstate(invalid='ignore'):
 177|                 cross = (np.isfinite(sa) & np.isfinite(sb) & (sa * sb < 0)
 178|                          & ends[:nr - dr, :nc - dc] & ends[dr:, dc:])
 179|             forced[:nr - dr, :nc - dc] |= cross
 180|             forced[dr:, dc:] |= cross
 181|             ra, ca = np.nonzero(cross)
 182|             sac, sbc = sa[cross], sb[cross]
 183|             e_ra.append(ra + r0)
 184|             e_ca.append(ca + c0)
 185|             e_rb.append(ra + r0 + dr)
 186|             e_cb.append(ca + c0 + dc)
 187|             e_tstar.append(np.abs(sac) / (np.abs(sac) + np.abs(sbc)))
 188|             e_len.append(np.full(ra.size, 6.0 * (2 ** 0.5 if dr and dc else 1.0)))
 189|             e_lv.append(Lw[:nr - dr, :nc - dc][cross])
 190|             e_k.append(wat_cls[:nr - dr, :nc - dc][cross])
 191|         forced &= edit
 192|         # side = input class: water capped at its own gate, land held over its own floor
 193|         with np.errstate(invalid='ignore'):
 194|             want = np.where(forced, Lw + a.slope * np.nan_to_num(sd), hw0)
 195|             want = np.where(B, np.minimum(want, wcap[W]), want)
 196|             want = np.where(lw0, np.maximum(want, lfloor[W]), want)
 197|             raise_cap = np.where(B, a.max_raise_water, a.max_raise)
 198|             want_c = np.clip(want, hw0 - a.max_lower, hw0 + raise_cap)
 199|             broke = (B & (want_c > wcap[W])) | (lw0 & (want_c < lfloor[W]))
 200|         want_f = np.where(broke, hw0, want_c)
 201|         # water is edited by its own component only; land keeps the maximum over every component that moves it (a
 202|         # component that leaves a vertex where it was must not undo another component's lowering)
 203|         em = edit & B
 204|         lm = edit & lw0 & (want_f != hw0)
 205|         hv = h1[W]
 206|         hv[em] = want_f[em]
 207|         land_max[W][lm] = np.fmax(land_max[W][lm], want_f[lm])
 208|         land_set[W] |= lm
 209|         land_n[W] += lm
 210|         diff = edit & (want_f != hw0)
 211|         attr = np.where(B, cls0w, wat_cls)
 212|         masks['band'][W] |= bandm
 213|         masks['forced'][W] |= forced
 214|         masks['editable'][W] |= edit
 215|         counts['profiled'] += 1
 216|         profiled[i] = True
 217|         counts['forced_at_cap'] += int((edit & forced & (want_c != want) & ~broke).sum())
 218|         counts['kept_by_gate'] += int((edit & forced & broke).sum())
 219|         for k in INLAND:
 220|             per_class[k]['forced'] += int((forced & (attr == k)).sum())
 221|             per_class[k]['changed'] += int((diff & (attr == k)).sum())
 222|         rows.append(dict(id=i, vertices=nb,
 223|                          cls_counts={k: int((B & (cls0w == k)).sum()) for k in INLAND},
 224|                          level_min=round(float(level0w[B].min()), 3),
 225|                          level_max=round(float(level0w[B].max()), 3),
 226|                          changed=int(diff.sum())))
 227|     h1[land_set] = land_max[land_set]
 228| 
 229|     # undo steepened land faces; nothing else about classes or levels ever moved
 230|     h2, faces = discard_steeper_land_faces(h1, h0, cls0)
 231|     h2 = h2.astype('float32').astype(np.float64)
 232| 
 233|     # bed floor on lakes, ponds, rivers and streams of profiled components; navigable reaches keep their depth;
 234|     # may act inside fixed (the only place a fixed vertex may change), never lowers anything
 235|     bed = np.zeros((N, N), bool)
 236|     if a.bed_floor is not None:
 237|         body = (profiled[ids] & (ids > 0) & np.isin(cls0, (2, 5, 6, 7)) & ~corridor & ~narva & ~border
 238|                 & ~reach_vertices & (level0 > G['plane_cut_m']))
 239|         with np.errstate(invalid='ignore'):
 240|             need = np.minimum(np.minimum(a.bed_floor, level0 - a.bed_min_depth), wcap)
 241|         bed = body & np.isfinite(need) & (h2 < need)
 242|         h2[bed] = need[bed]
 243|         h2 = h2.astype('float32').astype(np.float64)
 244| 
 245|     h0f = h0.astype('float32').astype(np.float64)
 246|     changed = h2 != h0f
 247|     assert np.array_equal(cls0, t['cls']), 'class changed'
 248|     assert same_level(level0.astype(t['level'].dtype), t['level']), 'level changed'
 249|     assert not np.any(changed & fixed & ~bed), 'protected height changed'
 250| 
 251|     gb = gate_counts(h0, cls0, level0, t['beach'], narva600, planes)
 252|     ga = gate_counts(h2, cls0, level0, t['beach'], narva600, planes)
 253|     assert all(ga[k] <= gb[k] for k in ga), (gb, ga)
 254| 
 255|     edges = tuple(np.concatenate(v) if v else np.array([]) for v in (e_ra, e_ca, e_rb, e_cb, e_tstar, e_len, e_lv, e_k))
 256|     ob, oa = edge_offsets(h0, edges), edge_offsets(h2, edges)
 257|     rows.sort(key=lambda r: -r['vertices'])
 258|     d = h2 - h0
 259|     rep = {
 260|         'components': {'standing': n_standing, 'flowing': n_flowing, 'profiled': counts['profiled'],
 261|                        'skipped_small': int((sizes[1:n_comp + 1] < a.min_vertices).sum()),
 262|                        'skipped_no_outline': counts['skipped_no_outline'],
 263|                        'land_vertices_edited_by_two_or_more': int((land_n >= 2).sum())},
 264|         'vertices': {'band': int(masks['band'].sum()), 'editable': int(masks['editable'].sum()),
 265|                      'forced': int(masks['forced'].sum()), 'changed': int(changed.sum()),
 266|                      'forced_at_move_cap': counts['forced_at_cap'], 'kept_by_gate': counts['kept_by_gate'],
 267|                      'bed_raised': int(bed.sum()), 'face_recovery': faces},
 268|         'by_class': {k: {'forced': per_class[k]['forced'], 'changed': per_class[k]['changed'],
 269|                          'bed_raised': int((bed & (cls0 == k)).sum()),
 270|                          'crossing_offset_m_vs_smoothed_outline': {'before': ob[k], 'after': oa[k]}}
 271|                      for k in (2, 3, 5, 6, 7)},
 272|         'gates': {k: {'before': gb[k], 'after': ga[k]} for k in gb},
 273|         'bed_below_0p85': {k: {'before': int(((cls0 == k) & (level0 > G['plane_cut_m']) & (h0 < 0.85)).sum()),
 274|                                'after': int(((cls0 == k) & (level0 > G['plane_cut_m']) & (h2 < 0.85)).sum())}
 275|                            for k in (2, 3, 5, 6, 7)},
 276|         'largest_components': rows[:10],
 277|         'change_m': {'raise_max': round(float(d.max()), 3), 'lower_max': round(float(-d.min()), 3)}}
 278|     return out_arrays(t, h2), dict(masks, changed=changed, bed_raised=bed), rep
 279| 
 280| 
 281| def out_arrays(t, h2):
 282|     out = dict(t)
 283|     out['heights'] = h2.astype(t['heights'].dtype)
 284|     return out
 285| 
 286| 
 287| def selftest():
 288|     n = N
 289|     h = np.full((n, n), 4.6, np.float32)
 290|     cls = np.zeros((n, n), np.uint8)
 291|     level = np.full((n, n), np.nan, np.float32)
 292|     r, c = np.mgrid[0:n, 0:n]
 293|     cc = 1000 + (r - 800) // 7
 294|     river = (r >= 800) & (r <= 1100) & (c >= cc - 1) & (c <= cc + 1)
 295|     cls[river] = 5
 296|     level[river] = (4.0 - 0.004 * (r - 800))[river]
 297|     h[river] = level[river] - 0.6
 298|     cc950 = 1000 + (950 - 800) // 7
 299|     stream = (r == 950) & (c >= cc950 + 2) & (c <= cc950 + 80)
 300|     cls[stream] = 6
 301|     level[stream] = (3.4 + 0.003 * (c - cc950 - 2))[stream]
 302|     h[stream] = level[stream] - 0.25
 303|     cc1100 = 1000 + (1100 - 800) // 7
 304|     lake = (r >= 1101) & (r <= 1115) & (c >= cc1100 - 7) & (c <= cc1100 + 7)
 305|     cls[lake], level[lake], h[lake] = 2, 2.75, 2.0
 306|     nav = (r >= 1300) & (r <= 1305) & (c >= 900) & (c <= 1300)
 307|     cls[nav], level[nav], h[nav] = 3, 3.0, -0.5
 308|     corridor = (r >= 1301) & (r <= 1304) & (c >= 900) & (c <= 1300)
 309|     lowr = (r >= 300) & (r <= 305) & (c >= 300) & (c <= 400)
 310|     cls[lowr], level[lowr], h[lowr] = 3, 0.7, 0.0
 311|     lake_a = (np.maximum(abs(r - 1540), abs(c - 640)) <= 40) & (abs(r - 1540) + abs(c - 640) <= 60)
 312|     island = np.maximum(abs(r - 1545), abs(c - 637)) <= 6
 313|     lake_a &= ~island
 314|     cls[lake_a], level[lake_a], h[lake_a] = 2, 4.0, 3.0
 315|     cc900 = 1000 + (900 - 800) // 7
 316|     pond = (r >= 898) & (r <= 902) & (c >= cc900 + 4) & (c <= cc900 + 8)
 317|     cls[pond], level[pond], h[pond] = 7, 3.0, 2.6
 318|     zero = np.zeros((n, n), bool)
 319|     t = dict(heights=h, cls=cls, level=level, platform=zero, reserve=zero, narva=zero, water=cls > 0, beach=zero)
 320|     a = argparse.Namespace(slope=0.15, band=12.0, sigma=12.0, max_shift=4.0, min_vertices=4, max_raise=2.0,
 321|                            max_raise_water=6.0, max_lower=1.5, bed_floor=None, bed_min_depth=0.30,
 322|                            narva_radius=620.0, sea_cut=0.51)
 323|     out, masks, rep = profile(t, corridor, zero, a)
 324|     assert all(v['before'] == 0 and v['after'] == 0 for v in rep['gates'].values()), rep['gates']
 325|     assert np.array_equal(out['cls'], cls) and same_level(out['level'], level), 'class or level changed'
 326|     assert np.array_equal(out['heights'][corridor], h[corridor]), 'corridor changed'
 327|     R = a.band + a.max_shift + 6.0
 328|     keep = ndimage.distance_transform_edt(~lowr) * 6.0 <= R
 329|     assert not np.any(masks['changed'] & keep), 'change near the low reach'
 330|     between = (cls == 0) & (r >= 898) & (r <= 902) & (c >= cc900 + 2) & (c <= cc900 + 3)
 331|     assert np.any(masks['changed'][between]), 'river-pond contact not profiled'
 332|     wm = river | pond
 333|     assert not np.any(out['heights'][wm] > level[wm].astype(np.float64) - 0.10), 'water above its level - 0.10'
 334|     for k in (2, 3, 5):
 335|         obk = rep['by_class'][k]['crossing_offset_m_vs_smoothed_outline']['before']
 336|         oak = rep['by_class'][k]['crossing_offset_m_vs_smoothed_outline']['after']
 337|         assert oak['p90'] < obk['p90'], (k, obk, oak)
 338|     assert np.any((out['cls'] == 0) & island), 'island lost'
 339|     a.bed_floor = 3.5
 340|     out2, _, _ = profile(t, corridor, zero, a)
 341|     wk = np.isin(out2['cls'], (2, 5, 6, 7))
 342|     lim = np.minimum(3.5, out2['level'][wk].astype(np.float64) - 0.30)
 343|     assert np.all(out2['heights'][wk] >= lim - 1e-5), float(out2['heights'][wk].min())
 344|     assert np.array_equal(out2['heights'][corridor], h[corridor]), 'corridor changed by the bed floor'
 345|     print('SELFTEST PASS')
 346| 
 347| 
 348| def main():
 349|     if '--selftest' in sys.argv:
 350|         selftest()
 351|         return
 352|     ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
 353|     ap.add_argument('--terrain', type=Path, required=True)
 354|     ap.add_argument('--out', type=Path, required=True)
 355|     ap.add_argument('--channels', type=Path, default=None)
 356|     ap.add_argument('--slope', type=float, default=0.15)
 357|     ap.add_argument('--band', type=float, default=12.0)
 358|     ap.add_argument('--sigma', type=float, default=12.0)
 359|     ap.add_argument('--max-shift', type=float, default=4.0)
 360|     ap.add_argument('--min-vertices', type=int, default=4)
 361|     ap.add_argument('--max-raise', type=float, default=2.0)
 362|     ap.add_argument('--max-raise-water', type=float, default=6.0)
 363|     ap.add_argument('--max-lower', type=float, default=1.5)
 364|     ap.add_argument('--bed-floor', type=float, default=None)
 365|     ap.add_argument('--bed-min-depth', type=float, default=0.30)
 366|     ap.add_argument('--narva-radius', type=float, default=620.0)
 367|     ap.add_argument('--sea-cut', type=float, default=0.51)
 368|     a = ap.parse_args()
 369|     if a.channels is None:
 370|         ap.error('--channels is required')
 371|     assert not a.out.exists(), 'fresh output required'
 372|     t0 = time.time()
 373|     t = dict(np.load(a.terrain))
 374|     planes = cell_planes(t['cls'], t['level'], sea_cut=a.sea_cut)
 375|     corridor, _, _, _ = protect_corridors(planes)   # the exact corridor faces, not their one-vertex margin
 376|     axes = json.loads((a.channels / 'axes.json').read_text(encoding='utf-8'))
 377|     reach_vertices = np.zeros((N, N), bool)
 378|     for reach in axes.values():
 379|         for r, c in reach['removed_cells']:
 380|             reach_vertices[r:r + 2, c:c + 2] = True
 381|     out, masks, rep = profile(t, corridor, reach_vertices, a)
 382|     a.out.mkdir(parents=True)
 383|     np.savez_compressed(a.out / 'terrain_inland.npz', **out)
 384|     np.savez_compressed(a.out / 'masks.npz', **masks)
 385|     rep = {'status': 'BUILT_PENDING_GATES_AND_ENGINE_VIEWS',
 386|            'params': {k: v for k, v in vars(a).items() if k not in ('terrain', 'out', 'channels')},
 387|            **rep,
 388|            'inputs': {str(p): sha(p) for p in (a.terrain, a.channels / 'axes.json', Path(__file__))},
 389|            'output_sha256': sha(a.out / 'terrain_inland.npz'), 'seconds': round(time.time() - t0, 1),
 390|            'limits': ['Only heights change: classes, levels and the vanilla reach vertices stay as they are.',
 391|                       'Water pieces stay valid (no class or level change); gates and engine views decide acceptance.']}
 392|     (a.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
 393|     print(json.dumps({k: v for k, v in rep.items() if k != 'inputs'}, indent=1))
 394| 
 395| 
 396| if __name__ == '__main__':
 397|     main()
 398| 
```

### tools/terrain/verify_terrain_v30.py (full file, 112 lines)
```python
   1| """Offline gates for terrain V30 other than roads (roads: verify_roads_v30.py).
   2| 
   3| water_depth  every water vertex at least 0.10 m below its level (sea 0.75 m), Narva zone excluded (V29 exact)
   4| banks        every land vertex within 8.5 m of water at least 0.05 m above the nearest water level (shores are
   5|              slopes from the smooth outline; the plane edge must still lie under land)
   6| land_floor   every land vertex >= 1.40 m (the sea, 0.5-1.0 m with tide, never floods land), except the beach strip
   7|              along the smoothed coast (terrain mask 'beach'), which must stay >= 0.80 m
   8| slopes       land triangles (all three corners land) <= 35 degrees (+0.01 for float32: V29 itself is capped at
   9|              35.000x in the Narva zone); triangles touching water reported, not gated
  10| bed_floor    no vertex below -12.0 m, V29's deepest sea floor (a bed is cut, never dug as a pit)
  11| pieces       every cell a pond piece covers (v30_common.cell_planes): water corners >= 0.02 m under the plane, land
  12|              corners >= 0.00 m over it, outside the 600 m Narva zone
  13| narva        heights within 480 m of the bridge centre identical to V29 (ASC ed6cdaa5)
  14| Usage: verify_terrain_v30.py <terrain.npz> [--json out.json] [--sea-cut 0.80]  (pond planes above the sea cut)
  15| """
  16| import json
  17| import hashlib
  18| import os
  19| import sys
  20| from pathlib import Path
  21| 
  22| import numpy as np
  23| import rasterio
  24| from scipy.ndimage import distance_transform_edt
  25| 
  26| sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  27| from v30_common import cell_planes  # noqa: E402
  28| 
  29| R = r"C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev"
  30| NARVA = (2417.1428225906, 6889.8850822322)
  31| G = {"depth_min_m": 0.10, "bank_radius_m": 8.5, "bank_min_m": 0.05, "land_floor_m": 1.40, "beach_floor_m": 0.80, "slope_max_deg": 35.0, "slope_tol_deg": 0.01, "bed_floor_m": -12.0,
  32|      "narva_radius_m": 480.0, "narva_zone_excluded_m": 600.0}
  33| 
  34| 
  35| def main():
  36|     t = np.load(sys.argv[1])
  37|     h = t["heights"].astype(float)
  38|     cls, level = t["cls"], t["level"].astype(float)
  39|     water = cls > 0
  40|     n = h.shape[0]
  41|     c, r = np.meshgrid(np.arange(n), np.arange(n))
  42|     dn = np.hypot(c * 6.0 - NARVA[0], 12282 - r * 6.0 - NARVA[1])
  43|     out = {}
  44|     zone = dn <= G["narva_zone_excluded_m"]
  45|     m = water & ~zone
  46|     depth = level[m] - h[m]
  47|     out["water_depth"] = {"vertices": int(m.sum()), "fail": int((depth < G["depth_min_m"]).sum()),
  48|                           "min_m": round(float(depth.min()), 3),
  49|                           "by_class_fail": {int(k): int(((level - h) < G["depth_min_m"])[m & (cls == k)].sum()) for k in range(1, 8)}}
  50|     dist, idx = distance_transform_edt(~water, sampling=6.0, return_indices=True)
  51|     near_lv = level[idx[0], idx[1]]
  52|     b = (~water) & (dist <= G["bank_radius_m"]) & ~zone
  53|     over = h[b] - near_lv[b]
  54|     out["banks"] = {"vertices": int(b.sum()), "fail": int((over < G["bank_min_m"]).sum()), "min_m": round(float(over.min()), 3)}
  55|     land = ~water
  56|     sea_cut = float(sys.argv[sys.argv.index("--sea-cut") + 1]) if "--sea-cut" in sys.argv else 0.80
  57|     plane = cell_planes(cls, level, sea_cut=sea_cut)
  58|     czone = zone[:-1, :-1] | zone[:-1, 1:] | zone[1:, :-1] | zone[1:, 1:]
  59|     pw = pl = 0
  60|     for dr in (0, 1):
  61|         for dc in (0, 1):
  62|             hc = h[dr:dr + n - 1, dc:dc + n - 1]
  63|             wc = water[dr:dr + n - 1, dc:dc + n - 1]
  64|             ok = np.isfinite(plane) & ~czone
  65|             with np.errstate(invalid="ignore"):
  66|                 pw += int((ok & wc & (hc > plane - 0.02)).sum())
  67|                 pl += int((ok & ~wc & (hc < plane)).sum())
  68|     out["pieces"] = {"cells": int((np.isfinite(plane) & ~czone).sum()), "water_corner_fail": pw, "land_corner_fail": pl,
  69|                      "fail": pw + pl}
  70|     out["bed_floor"] = {"fail": int((h < G["bed_floor_m"] - 1e-6).sum()), "min_m": round(float(h.min()), 3)}
  71|     beach = t["beach"] if "beach" in t.files else np.zeros_like(land)
  72|     inland = land & ~zone & ~beach
  73|     out["land_floor"] = {"vertices": int(inland.sum()), "fail": int((h[inland] < G["land_floor_m"] - 1e-6).sum()),
  74|                          "min_m": round(float(h[inland].min()), 3),
  75|                          "beach_vertices": int(beach.sum()),
  76|                          "beach_fail": int((h[beach] < G["beach_floor_m"] - 1e-6).sum())}
  77|     nw, ne, sw, se = h[:-1, :-1], h[:-1, 1:], h[1:, :-1], h[1:, 1:]
  78|     au = np.degrees(np.arctan(np.hypot((ne - nw) / 6, (se - ne) / 6)))
  79|     al = np.degrees(np.arctan(np.hypot((sw - nw) / 6, (se - sw) / 6)))
  80|     lnw, lne, lsw, lse = land[:-1, :-1], land[:-1, 1:], land[1:, :-1], land[1:, 1:]
  81|     mu, ml = lnw & lne & lse, lnw & lsw & lse
  82|     su, sl = (lnw | lne | lse) & ~mu, (lnw | lsw | lse) & ~ml
  83|     land_ang = np.r_[au[mu], al[ml]]
  84|     shore_ang = np.r_[au[su], al[sl]]
  85|     out["slopes"] = {"land_triangles": int(land_ang.size), "fail": int((land_ang > G["slope_max_deg"] + G["slope_tol_deg"]).sum()),
  86|                      "within_tolerance": int(((land_ang > G["slope_max_deg"]) & (land_ang <= G["slope_max_deg"] + G["slope_tol_deg"])).sum()),
  87|                      "max_deg": round(float(land_ang.max()), 2),
  88|                      "shore_triangles_over_35": int((shore_ang > G["slope_max_deg"]).sum()),
  89|                      "shore_max_deg": round(float(shore_ang.max()), 2)}
  90|     with rasterio.open(os.path.join(R, "tests", "regional_road_network_v29", "baltic_road_network_v29.asc")) as ds:
  91|         v29 = ds.read(1).astype("float32")
  92|     nz = dn <= G["narva_radius_m"]
  93|     out["narva"] = {"vertices": int(nz.sum()), "identical": bool(np.array_equal(t["heights"][nz], v29[nz])),
  94|                     "max_diff_m": float(np.abs(t["heights"][nz] - v29[nz]).max())}
  95|     gates = [out["water_depth"]["fail"], out["banks"]["fail"], out["land_floor"]["fail"], out["land_floor"]["beach_fail"],
  96|              out["slopes"]["fail"], out["pieces"]["fail"],
  97|              out["bed_floor"]["fail"]]
  98|     out["status"] = "PASS" if all(g == 0 for g in gates) and out["narva"]["identical"] else "FAIL"
  99|     out["limits"] = dict(G, sea_cut_m=sea_cut)
 100|     out['terrain_sha256'] = hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()
 101|     out['sources'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
 102|         Path(__file__), Path(cell_planes.__code__.co_filename),
 103|         Path(R) / 'tests/regional_road_network_v29/baltic_road_network_v29.asc')}
 104|     print(json.dumps(out, indent=1))
 105|     if "--json" in sys.argv:
 106|         with open(sys.argv[sys.argv.index("--json") + 1], "wb") as f:
 107|             f.write(json.dumps(out, indent=1).encode("utf-8"))
 108| 
 109| 
 110| if __name__ == "__main__":
 111|     main()
 112| 
```

# Reminder
# Task P3: external outline and low-water banks in tools/terrain/profile_inland_v30.py, and the matching gate in
# tools/terrain/verify_terrain_v30.py
Measured problem (06-10): the shore pass computes each component's outline from the 6 m CLASS raster (lines 151-164:
EDT of the component, Gaussian, clamp); a long straight row of the raster stays straight after smoothing, so the visible
waterline of rivers follows grid rows. A smoothed VECTOR outline of the design exists as a signed-distance field
(npz key 'sd', float32 N x N, metres, negative inside water, NaN where undefined, sign set by the class). Second
problem: very low water (level about 1.0 m) has its bank vertices held at the 1.40 m land floor, so the crossing of
the water plane can only fall near the wet vertex.
1. `--outline-sd PATH` and `--outline-sd-classes` (comma list of class codes, default "2,5,7"). Without --outline-sd
   the tool behaves exactly as today. With it: main() loads np.load(path)['sd'] as float64 once and passes it through
   the args namespace (the selftest builds an argparse.Namespace without it: read it with getattr(a, 'ext_sd', None)).
   In profile(), per component window, after the raster sd (lines 163-164) and once Lw and wat_cls are known (lines
   166-169; you may compute them earlier, results must not change): at every window vertex where the external value is
   finite AND its sign agrees with the input class (ext < 0 on a vertex of this component B, ext > 0 on a land vertex
   lw0) AND the relevant class is in the list (for a B vertex its own class cls0w, for a land vertex wat_cls, the class
   of the nearest component vertex), sd takes the external value. Everything after (bandm, crossing edges, edge
   records, targets) uses the combined sd.
2. `--low-water-bank` (flag) and `--low-water-bank-min M` (default 1.0). Without the flag: today's behaviour. With
   it: a LAND vertex that this component forces (forced & lw0, after line 191) and whose floor today comes from the
   1.40 m land floor rather than from the water (near_lv + G['freeboard_m'] < floor, the arrays of lines 109-115)
   gets the per-vertex floor max(near_lv + freeboard, pmax, M) + EPS instead of lfloor; NaN pmax counts as absent
   (use np.fmax like line 115). Only those vertices; every other land vertex keeps lfloor. Use this per-vertex floor
   in the clamp of line 196 and in `broke` (line 199). Keep a mask of the vertices this rule relaxed (over all
   components) for the report and the gates.
3. Gates (lines 251-253): gate_counts (tools/terrain/profile_rivers_v30.py:82, excerpt below) counts land under 1.40 m
   as 'land_floor' failures. With --low-water-bank, compute the AFTER counts on a copy of h2 where the relaxed
   vertices that stand at or above their own relaxed floor are lifted to G['land_floor_m'], so only true failures
   count; then the existing assert (after <= before) must hold. Report 'low_water_bank': {'vertices': relaxed vertices
   below 1.40 in the output, 'below_own_floor': count below their own floor (expected 0)} under 'vertices'.
4. The report 'params' must stay JSON-serialisable: Paths as str, never the array.
5. `--selftest` must still pass unchanged. Update the module docstring (steps 2 and 3, the gates and Usage).
6. tools/terrain/verify_terrain_v30.py (argv-based): add `--low-water-bank-min M` (default absent = today's output
   byte for byte). With it, a land vertex counted by the land_floor gate (line 73: same mask) that is 8-adjacent to an
   inland water vertex (classes 2, 3, 5, 6, 7 with level > 0.80) whose level + 0.05 < 1.40 (use the highest such
   adjacent level) passes that gate when h >= max(level + 0.05, M) - 1e-6; count those vertices and their failures
   under out["land_floor"]["low_water_bank"] = {"vertices": n, "fail": f}; "fail" of land_floor then counts the other
   vertices below 1.40 plus f.

Write the whole files now.
