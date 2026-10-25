IMPORTANT PROCESS NOTE: write the complete files FIRST, in one pass, then stop. Keep internal deliberation focused.
The receiver re-runs every changed tool with its DEFAULTS and compares sha256 against archived outputs: with the
defaults, terrain/water/image outputs must be byte-identical to today's. Change nothing that the task does not ask for.
Code and comments in English; keep the style of the surrounding code (comment density, naming, idiom).
Output: one fenced block per changed or new file, each preceded by the line `FILE: <repo-relative path>`, whole file.
Coordinates: game metres, x east, z north; the vertex grid is N = 2048 vertices every 6 m, row r at z = 12282 - 6r,
column c at x = 6c (tools/terrain/v30_common.py).

# Task P4: per-class shore slope in tools/terrain/profile_inland_v30.py
Guillermo, 06-10: rivers and lakes look flat; more depth, with the shore outline of the design kept exactly. Today
every forced vertex (one end of a native edge that crosses the outline) takes Lw + --slope * sd (line 241), one slope
(0.15 m per m) for every class, so a river vertex 4 m inside the outline sits 0.60 m under the water and the land
vertex 2 m outside 0.30 m over it. Raising the slope on BOTH sides of the outline keeps the crossing exactly on the
outline (the profile still passes through Lw at sd = 0) and deepens the water: rivers about 1 m at the centre
(slope 0.25), streams about 0.4 m (slope 0.20), lakes and ponds 1 m at 6 m from the shore (slope 0.167). The land
vertex next to the water rises in proportion; nothing farther from the outline changes.

1. Two new options (argparse in main(), lines 409-428):
   - `--slope-by-class SPEC`, default "" (today's behaviour: every class uses --slope). SPEC is comma-separated
     "class:slope" pairs, e.g. "2:0.167,5:0.25,6:0.2,7:0.167" (classes: 2 lake, 5 river, 6 stream, 7 pond). Parse it in
     main() into a dict {int class: float slope} stored as a.slope_by_class.
   - `--slope-ref D`, metres, default 4.0.
2. In profile(), replace the single slope at line 241 by a per-vertex slope `s`:
   - k = the class that decides the vertex: cls0w on the component (B), wat_cls on land; that is the expression
     `np.where(B, cls0w, wat_cls)` that line 258 computes as `attr`: compute it before line 241 and reuse it at 258;
   - s_class = a.slope_by_class.get(k, a.slope) per vertex (vectorise it with a lookup table over the uint8 class);
   - where s_class > a.slope and a.bed_floor is not None:
         s = clip((Lw - a.bed_floor) / a.slope_ref, a.slope, s_class)
     elsewhere s = s_class. A forced water vertex at most --slope-ref inside the outline then stays above the bed floor,
     so the floor does not clip it and the crossing stays on the outline; low water keeps today's slope (never
     gentler than --slope).
   - want = np.where(forced, Lw + s * np.nan_to_num(sd), hw0)
   With an empty SPEC, s equals a.slope everywhere and terrain_inland.npz and masks.npz must be byte-identical to
   today's (the receiver checks the sha256 against the v10b run). The report may gain the new params.
3. profile() must read the new fields with getattr(a, 'slope_by_class', {}) and getattr(a, 'slope_ref', 4.0): the
   selftest builds its own argparse.Namespace (line 377) without them and must keep passing unchanged.
4. Report: rep['forced_water_depth_m_p50'] = {class: median(level - height) of the forced water vertices of that
   class after the pass} for classes 2, 5, 6, 7 present (rounded to 3 decimals). main() already copies the params.
5. Selftest: after the existing checks, run profile() once more with a.slope_by_class = {5: 0.25} (bed_floor None):
   classes and levels unchanged, every gate count 0 before and after, and the median depth of the forced river
   vertices deeper than in the first run (print both).
6. Docstring: point 3 describes the per-class slope and --slope-ref; add both options to the Usage line.

# The file to change

### tools/terrain/profile_inland_v30.py (full file, 464 lines)
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
  14|    With --outline-sd PATH the smoothed vector outline of the design, given as a signed-distance field (npz key
  15|    'sd', metres, negative inside water, NaN where undefined), replaces the raster field wherever its sign agrees
  16|    with the input class (negative on the component, positive on land) and the class is one of
  17|    --outline-sd-classes, so a straight raster row no longer keeps the waterline on a grid row.
  18| 3. Profile: a vertex ending a native edge (east, south, NW-SE diagonal) whose ends lie on opposite sides of the
  19|    outline takes Lw + --slope * sd, where Lw is the level of the nearest component vertex. The side of a vertex is
  20|    its INPUT class, never the sign of sd, so no class or level changes and the cell planes, and with them the
  21|    existing water pieces, stay valid: water is capped at min(level - 0.10, plane - 0.02), land at
  22|    max(nearest level + 0.05, plane, land floor) (1.40 m, 0.80 m on the beach); each move capped (--max-raise-water
  23|    on water, --max-raise on land, --max-lower down); a vertex whose capped target still breaks its gate keeps its
  24|    height. With --low-water-bank a land vertex the component forces whose floor comes from the 1.40 m land floor
  25|    rather than from the water (its water level + 0.05 under it; the water level is the highest among its inland-water
  26|    8-neighbours, at least the nearest one) is held at max(water level + 0.05, plane, --low-water-bank-min) instead, so the crossing of a very low water plane
  27|    (level about 1.0 m) falls between the wet vertex and the bank. A land vertex edited by several components keeps
  28|    the MAXIMUM of their targets, so it stays above every water it borders; a water vertex is edited only by its
  29|    own component.
  30| 4. Edits that make a land face steeper than 35 degrees (or than it was) are undone.
  31| 5. Bed floor (--bed-floor F): every lake, pond, river and stream vertex of a profiled component outside the exact
  32|    corridors, the Narva zone, the map border and the vanilla reach cells rises to min(F, level - --bed-min-depth,
  33|    gate cap). Navigable reaches keep their depth (Guillermo, 05-10).
  34| 6. Gates: water depth, banks, land/beach floor, pieces and slopes are counted on the input and on the output
  35|    (profile_rivers_v30.gate_counts) and the output counts must not exceed the input ones; with --low-water-bank
  36|    the relaxed bank vertices standing at or above their own relaxed floor are lifted to the 1.40 m land floor for
  37|    the output count, and 'low_water_bank' under 'vertices' reports the relaxed vertices below 1.40 m and below
  38|    their own relaxed floor.
  39| Fixed for the shore profile: platforms, reserves, the exact 24 m navigable and delta corridor vertices (only those,
  40| so the channel edges stay free), the Narva zone and the map border, the sea and the delta, low inland water at or
  41| below the 0.80 m plane cut (drawn by the engine sea), unlabelled standing water, the vertices of the vanilla channel
  42| reaches (<channels>/axes.json removed cells), components below --min-vertices, and every vertex within
  43| --band + --max-shift + 6 m of any of those. A vertex near two components is NOT fixed any more, so shores where a
  44| lake or pond touches a river or stream are profiled (Guillermo, 06-10); the nature envelope is not fixed either,
  45| its reserve stays the same while the drawing of its shores changes.
  46| No class or level changes, so the cell planes and the existing water pieces stay valid: no water tile is rebuilt.
  47| Usage: profile_inland_v30.py --terrain IN.npz --out OUTDIR --channels FITDIR [--slope 0.15] [--band 12]
  48|                              [--sigma 12] [--max-shift 4] [--min-vertices 4] [--max-raise 2.0]
  49|                              [--max-raise-water 6.0] [--max-lower 1.5] [--bed-floor F] [--bed-min-depth 0.30]
  50|                              [--outline-sd PATH] [--outline-sd-classes 2,5,7] [--low-water-bank]
  51|                              [--low-water-bank-min 1.0] [--narva-radius 620] [--sea-cut 0.51]
  52|        profile_inland_v30.py --selftest
  53| """
  54| import argparse
  55| import json
  56| import sys
  57| import time
  58| from pathlib import Path
  59| 
  60| import numpy as np
  61| import shapely
  62| from scipy import ndimage
  63| 
  64| sys.path.insert(0, str(Path(__file__).resolve().parent))
  65| from v30_common import N, cell_planes, grid_xz, vertex_plane_bounds  # noqa: E402
  66| from finish_shores_v30 import discard_steeper_land_faces, protect_corridors  # noqa: E402
  67| from profile_coast_v30 import EDGES, NARVA, SEA_CLASSES, sha  # noqa: E402
  68| from profile_lakes_v30 import G, EPS, window_lines  # noqa: E402
  69| from relevel_bodies_v30 import label_bodies  # noqa: E402
  70| from profile_rivers_v30 import PIECE_DEPTH, gate_counts, same_level  # noqa: E402
  71| 
  72| FLOWING = (3, 5, 6)
  73| STANDING = (2, 7)
  74| INLAND = STANDING + FLOWING
  75| 
  76| 
  77| def edge_offsets(h, edges):
  78|     """Distance (m) along each recorded native edge between the terrain crossing of the local level Lw and the
  79|     outline crossing, per water-end class; edges whose terrain no longer crosses Lw are counted apart."""
  80|     ra, ca, rb, cb, tstar, length, lv, k = edges
  81|     out = {}
  82|     for c in INLAND:
  83|         out[c] = {'edges': 0}
  84|     if ra.size == 0:
  85|         return out
  86|     ha, hb = h[ra, ca] - lv, h[rb, cb] - lv
  87|     ok = ha * hb < 0
  88|     t = np.where(ok, ha / np.where(ok, ha - hb, 1.0), np.nan)
  89|     v = np.abs(t - tstar) * length
  90|     for c in INLAND:
  91|         m = k == c
  92|         vv = v[m & ok]
  93|         out[c] = {'edges': int(m.sum()), 'no_crossing': int((m & ~ok).sum()),
  94|                   **({q: round(float(np.percentile(vv, p)), 3)
  95|                       for q, p in (('p50', 50), ('p90', 90), ('p99', 99))} if vv.size else {})}
  96|     return out
  97| 
  98| 
  99| def profile(t, corridor, reach_vertices, a):
 100|     """The whole method on the terrain arrays t; returns (output arrays, masks, report without inputs)."""
 101|     h0 = t['heights'].astype(np.float64)
 102|     cls0 = t['cls'].copy()
 103|     level0 = t['level'].astype(np.float64)
 104|     x, z = grid_xz()
 105|     flow0 = np.isin(cls0, FLOWING)
 106|     stand0 = np.isin(cls0, STANDING)
 107|     land0 = cls0 == 0
 108|     low = np.isin(cls0, INLAND) & (level0 <= G['plane_cut_m'])
 109|     sids = label_bodies(cls0, level0)
 110|     n_standing = int(sids.max())
 111|     flab, n_flowing = ndimage.label(flow0 & ~low, structure=np.ones((3, 3), bool))
 112|     ids = sids.copy()
 113|     fm = flab > 0
 114|     ids[fm] = (flab[fm] + n_standing).astype(np.int32)
 115|     n_comp = n_standing + n_flowing
 116|     narva = np.hypot(x - NARVA[0], z - NARVA[1]) <= a.narva_radius
 117|     narva600 = np.hypot(x - NARVA[0], z - NARVA[1]) <= G['narva_zone_excluded_m']
 118|     border = (x < 12) | (z < 12) | (x > 12270) | (z > 12270)
 119| 
 120|     # per-vertex gate fields from the input; exact for the output because no class or level changes
 121|     planes = cell_planes(cls0, level0, sea_cut=a.sea_cut)
 122|     pmin, pmax = vertex_plane_bounds(planes)
 123|     dist, idx = ndimage.distance_transform_edt(land0, sampling=6.0, return_indices=True)
 124|     near_lv = level0[idx[0], idx[1]]
 125|     wcap = level0 - G['depth_min_m'] - EPS
 126|     pm = np.isfinite(pmin)
 127|     wcap[pm] = np.minimum(wcap[pm], pmin[pm] - PIECE_DEPTH - EPS)
 128|     floor = np.where(t['beach'], G['beach_floor_m'], G['land_floor_m'])
 129|     lfloor = np.fmax(near_lv + G['freeboard_m'], np.fmax(pmax, floor)) + EPS
 130|     lwb = getattr(a, 'low_water_bank', False)
 131|     if lwb:
 132|         # level a relaxed bank vertex must clear: the highest level among its 8-neighbours that are inland water over
 133|         # the plane cut (as verify_terrain_v30.py --low-water-bank-min checks it), at least the nearest level
 134|         iw = np.isin(cls0, (2, 3, 5, 6, 7)) & (np.nan_to_num(level0, nan=-np.inf) > G['plane_cut_m'])
 135|         pad = np.pad(np.where(iw, level0, -np.inf), 1, constant_values=-np.inf)
 136|         adj = np.full((N, N), -np.inf)
 137|         for dr in (0, 1, 2):
 138|             for dc in (0, 1, 2):
 139|                 if (dr, dc) != (1, 1):
 140|                     adj = np.fmax(adj, pad[dr:dr + N, dc:dc + N])
 141|         bank_lv = np.fmax(near_lv, adj)
 142| 
 143|     reach = a.band + a.max_shift + 6.0
 144|     rv = int(np.ceil(reach / 6.0))
 145|     yy, xx = np.mgrid[-rv:rv + 1, -rv:rv + 1]
 146|     disc = np.hypot(yy, xx) * 6.0 <= reach
 147|     objs = ndimage.find_objects(ids)
 148|     sizes = np.bincount(ids.ravel(), minlength=n_comp + 1)
 149|     small = (ids > 0) & (sizes[ids] < a.min_vertices)
 150|     loose = stand0 & (sids == 0) & ~low
 151|     other = (np.isin(cls0, SEA_CLASSES) | low | reach_vertices | loose | small)
 152|     near_other = ndimage.distance_transform_edt(~other) * 6.0 <= reach if other.any() else np.zeros((N, N), bool)
 153|     fixed = t['platform'] | t['reserve'] | corridor | narva | border | other | near_other
 154| 
 155|     h1 = h0.copy()
 156|     land_max = np.full((N, N), -np.inf)
 157|     land_set = np.zeros((N, N), bool)
 158|     land_n = np.zeros((N, N), np.uint8)
 159|     relaxed = np.zeros((N, N), bool)
 160|     masks = {k: np.zeros((N, N), bool) for k in ('band', 'forced', 'editable')}
 161|     counts = dict(profiled=0, skipped_no_outline=0, forced_at_cap=0, kept_by_gate=0)
 162|     profiled = np.zeros(n_comp + 1, bool)
 163|     per_class = {k: dict(forced=0, changed=0) for k in INLAND}
 164|     rows = []
 165|     e_ra, e_ca, e_rb, e_cb, e_tstar, e_len, e_lv, e_k = ([] for _ in range(8))
 166|     g = int(np.ceil((reach + 3 * a.sigma + 12.0) / 6.0))
 167|     for i, sl in enumerate(objs, 1):
 168|         if sl is None or sizes[i] < a.min_vertices:
 169|             continue
 170|         r0, r1 = max(sl[0].start - g, 0), min(sl[0].stop + g, N)
 171|         c0, c1 = max(sl[1].start - g, 0), min(sl[1].stop + g, N)
 172|         W = (slice(r0, r1), slice(c0, c1))
 173|         B = ids[W] == i
 174|         nb = int(B.sum())
 175|         hw0 = h0[W]
 176|         cls0w, level0w = cls0[W], level0[W]
 177|         lw0 = land0[W]
 178|         base = np.where(B, -ndimage.distance_transform_edt(B), ndimage.distance_transform_edt(~B)) * 6.0
 179|         smooth = ndimage.gaussian_filter(base, a.sigma / 6.0)
 180|         smooth = np.clip(smooth, base - a.max_shift, base + a.max_shift)
 181|         near = np.abs(base) <= a.band + a.max_shift + 9.0
 182|         lines = window_lines(smooth, near, r0, c0)
 183|         if not lines:
 184|             counts['skipped_no_outline'] += 1
 185|             continue
 186|         segs = np.concatenate([np.stack([ln[:-1], ln[1:]], axis=1) for ln in lines])
 187|         tree = shapely.STRtree(shapely.linestrings(segs))
 188|         xw, zw = x[W], z[W]
 189|         _, d = tree.query_nearest(shapely.points(xw[near], zw[near]), return_distance=True, all_matches=False)
 190|         sd = np.full(B.shape, np.nan)
 191|         sd[near] = np.where(smooth[near] < 0, -d, d)
 192|         # local level: the level of the nearest component vertex, for the profile target and the metric
 193|         _, j = ndimage.distance_transform_edt(~B, return_indices=True)
 194|         Lw = level0w[j[0], j[1]]
 195|         wat_cls = cls0w[j[0], j[1]]
 196|         # external outline of the design: where its sign agrees with the input class (negative on the component,
 197|         # positive on land) and the class is in the list, it replaces the raster signed distance
 198|         ext = getattr(a, 'ext_sd', None)
 199|         if ext is not None:
 200|             ew = ext[W]
 201|             with np.errstate(invalid='ignore'):
 202|                 usew = ((B & np.isfinite(ew) & (ew < 0) & np.isin(cls0w, a.outline_sd_classes))
 203|                         | (lw0 & np.isfinite(ew) & (ew > 0) & np.isin(wat_cls, a.outline_sd_classes)))
 204|             sd = np.where(usew, ew, sd)
 205|         bandm = near & np.isfinite(sd) & (np.abs(sd) <= a.band)
 206|         edit = bandm & (B | lw0) & ~fixed[W]
 207|         ends = B | lw0
 208|         nr, nc = B.shape
 209|         forced = np.zeros(B.shape, bool)
 210|         for dr, dc in EDGES:
 211|             sa, sb = sd[:nr - dr, :nc - dc], sd[dr:, dc:]
 212|             with np.errstate(invalid='ignore'):
 213|                 cross = (np.isfinite(sa) & np.isfinite(sb) & (sa * sb < 0)
 214|                          & ends[:nr - dr, :nc - dc] & ends[dr:, dc:])
 215|             forced[:nr - dr, :nc - dc] |= cross
 216|             forced[dr:, dc:] |= cross
 217|             ra, ca = np.nonzero(cross)
 218|             sac, sbc = sa[cross], sb[cross]
 219|             e_ra.append(ra + r0)
 220|             e_ca.append(ca + c0)
 221|             e_rb.append(ra + r0 + dr)
 222|             e_cb.append(ca + c0 + dc)
 223|             e_tstar.append(np.abs(sac) / (np.abs(sac) + np.abs(sbc)))
 224|             e_len.append(np.full(ra.size, 6.0 * (2 ** 0.5 if dr and dc else 1.0)))
 225|             e_lv.append(Lw[:nr - dr, :nc - dc][cross])
 226|             e_k.append(wat_cls[:nr - dr, :nc - dc][cross])
 227|         forced &= edit
 228|         # very low water: the bank vertices this component forces, whose floor comes from the 1.40 m land floor
 229|         # rather than from the water, are held over a relaxed per-vertex floor so the plane crossing can fall
 230|         # between the wet vertex and the bank
 231|         lw_floor = lfloor[W]
 232|         if lwb:
 233|             cand = lw0 & forced & (bank_lv[W] + G['freeboard_m'] < floor[W])
 234|             if cand.any():
 235|                 vf = np.fmax(np.fmax(bank_lv[W] + G['freeboard_m'], pmax[W]), a.low_water_bank_min) + EPS
 236|                 cand &= vf < lw_floor
 237|                 lw_floor = np.where(cand, vf, lw_floor)
 238|                 relaxed[W] |= cand
 239|         # side = input class: water capped at its own gate, land held over its own floor
 240|         with np.errstate(invalid='ignore'):
 241|             want = np.where(forced, Lw + a.slope * np.nan_to_num(sd), hw0)
 242|             want = np.where(B, np.minimum(want, wcap[W]), want)
 243|             want = np.where(lw0, np.maximum(want, lw_floor), want)
 244|             raise_cap = np.where(B, a.max_raise_water, a.max_raise)
 245|             want_c = np.clip(want, hw0 - a.max_lower, hw0 + raise_cap)
 246|             broke = (B & (want_c > wcap[W])) | (lw0 & (want_c < lw_floor))
 247|         want_f = np.where(broke, hw0, want_c)
 248|         # water is edited by its own component only; land keeps the maximum over every component that moves it (a
 249|         # component that leaves a vertex where it was must not undo another component's lowering)
 250|         em = edit & B
 251|         lm = edit & lw0 & (want_f != hw0)
 252|         hv = h1[W]
 253|         hv[em] = want_f[em]
 254|         land_max[W][lm] = np.fmax(land_max[W][lm], want_f[lm])
 255|         land_set[W] |= lm
 256|         land_n[W] += lm
 257|         diff = edit & (want_f != hw0)
 258|         attr = np.where(B, cls0w, wat_cls)
 259|         masks['band'][W] |= bandm
 260|         masks['forced'][W] |= forced
 261|         masks['editable'][W] |= edit
 262|         counts['profiled'] += 1
 263|         profiled[i] = True
 264|         counts['forced_at_cap'] += int((edit & forced & (want_c != want) & ~broke).sum())
 265|         counts['kept_by_gate'] += int((edit & forced & broke).sum())
 266|         for k in INLAND:
 267|             per_class[k]['forced'] += int((forced & (attr == k)).sum())
 268|             per_class[k]['changed'] += int((diff & (attr == k)).sum())
 269|         rows.append(dict(id=i, vertices=nb,
 270|                          cls_counts={k: int((B & (cls0w == k)).sum()) for k in INLAND},
 271|                          level_min=round(float(level0w[B].min()), 3),
 272|                          level_max=round(float(level0w[B].max()), 3),
 273|                          changed=int(diff.sum())))
 274|     h1[land_set] = land_max[land_set]
 275| 
 276|     # undo steepened land faces; nothing else about classes or levels ever moved
 277|     h2, faces = discard_steeper_land_faces(h1, h0, cls0)
 278|     h2 = h2.astype('float32').astype(np.float64)
 279| 
 280|     # bed floor on lakes, ponds, rivers and streams of profiled components; navigable reaches keep their depth;
 281|     # may act inside fixed (the only place a fixed vertex may change), never lowers anything
 282|     bed = np.zeros((N, N), bool)
 283|     if a.bed_floor is not None:
 284|         body = (profiled[ids] & (ids > 0) & np.isin(cls0, (2, 5, 6, 7)) & ~corridor & ~narva & ~border
 285|                 & ~reach_vertices & (level0 > G['plane_cut_m']))
 286|         with np.errstate(invalid='ignore'):
 287|             need = np.minimum(np.minimum(a.bed_floor, level0 - a.bed_min_depth), wcap)
 288|         bed = body & np.isfinite(need) & (h2 < need)
 289|         h2[bed] = need[bed]
 290|         h2 = h2.astype('float32').astype(np.float64)
 291| 
 292|     h0f = h0.astype('float32').astype(np.float64)
 293|     changed = h2 != h0f
 294|     assert np.array_equal(cls0, t['cls']), 'class changed'
 295|     assert same_level(level0.astype(t['level'].dtype), t['level']), 'level changed'
 296|     assert not np.any(changed & fixed & ~bed), 'protected height changed'
 297| 
 298|     gb = gate_counts(h0, cls0, level0, t['beach'], narva600, planes)
 299|     ga = gate_counts(h2, cls0, level0, t['beach'], narva600, planes)
 300|     if lwb:
 301|         # the verifier with --low-water-bank-min passes a relaxed bank vertex standing at or above its own relaxed
 302|         # floor; for the land floor count only, lift those to the land floor so only true failures count
 303|         vf_all = np.fmax(np.fmax(bank_lv + G['freeboard_m'], pmax), a.low_water_bank_min) + EPS
 304|         hg = h2.copy()
 305|         hg[relaxed & (h2 >= vf_all - 1e-6)] = G['land_floor_m']
 306|         ga['land_floor'] = gate_counts(hg, cls0, level0, t['beach'], narva600, planes)['land_floor']
 307|     assert all(ga[k] <= gb[k] for k in ga), (gb, ga)
 308| 
 309|     edges = tuple(np.concatenate(v) if v else np.array([]) for v in (e_ra, e_ca, e_rb, e_cb, e_tstar, e_len, e_lv, e_k))
 310|     ob, oa = edge_offsets(h0, edges), edge_offsets(h2, edges)
 311|     rows.sort(key=lambda r: -r['vertices'])
 312|     d = h2 - h0
 313|     rep = {
 314|         'components': {'standing': n_standing, 'flowing': n_flowing, 'profiled': counts['profiled'],
 315|                        'skipped_small': int((sizes[1:n_comp + 1] < a.min_vertices).sum()),
 316|                        'skipped_no_outline': counts['skipped_no_outline'],
 317|                        'land_vertices_edited_by_two_or_more': int((land_n >= 2).sum())},
 318|         'vertices': {'band': int(masks['band'].sum()), 'editable': int(masks['editable'].sum()),
 319|                      'forced': int(masks['forced'].sum()), 'changed': int(changed.sum()),
 320|                      'forced_at_move_cap': counts['forced_at_cap'], 'kept_by_gate': counts['kept_by_gate'],
 321|                      'bed_raised': int(bed.sum()), 'face_recovery': faces,
 322|                      **({'low_water_bank': {'vertices': int((relaxed & (h2 < G['land_floor_m'] - 1e-6)).sum()),
 323|                                             'below_own_floor': int((relaxed & (h2 < vf_all - 1e-6)).sum())}}
 324|                         if lwb else {})},
 325|         'by_class': {k: {'forced': per_class[k]['forced'], 'changed': per_class[k]['changed'],
 326|                          'bed_raised': int((bed & (cls0 == k)).sum()),
 327|                          'crossing_offset_m_vs_smoothed_outline': {'before': ob[k], 'after': oa[k]}}
 328|                      for k in (2, 3, 5, 6, 7)},
 329|         'gates': {k: {'before': gb[k], 'after': ga[k]} for k in gb},
 330|         'bed_below_0p85': {k: {'before': int(((cls0 == k) & (level0 > G['plane_cut_m']) & (h0 < 0.85)).sum()),
 331|                                'after': int(((cls0 == k) & (level0 > G['plane_cut_m']) & (h2 < 0.85)).sum())}
 332|                            for k in (2, 3, 5, 6, 7)},
 333|         'largest_components': rows[:10],
 334|         'change_m': {'raise_max': round(float(d.max()), 3), 'lower_max': round(float(-d.min()), 3)}}
 335|     return out_arrays(t, h2), dict(masks, changed=changed, bed_raised=bed), rep
 336| 
 337| 
 338| def out_arrays(t, h2):
 339|     out = dict(t)
 340|     out['heights'] = h2.astype(t['heights'].dtype)
 341|     return out
 342| 
 343| 
 344| def selftest():
 345|     n = N
 346|     h = np.full((n, n), 4.6, np.float32)
 347|     cls = np.zeros((n, n), np.uint8)
 348|     level = np.full((n, n), np.nan, np.float32)
 349|     r, c = np.mgrid[0:n, 0:n]
 350|     cc = 1000 + (r - 800) // 7
 351|     river = (r >= 800) & (r <= 1100) & (c >= cc - 1) & (c <= cc + 1)
 352|     cls[river] = 5
 353|     level[river] = (4.0 - 0.004 * (r - 800))[river]
 354|     h[river] = level[river] - 0.6
 355|     cc950 = 1000 + (950 - 800) // 7
 356|     stream = (r == 950) & (c >= cc950 + 2) & (c <= cc950 + 80)
 357|     cls[stream] = 6
 358|     level[stream] = (3.4 + 0.003 * (c - cc950 - 2))[stream]
 359|     h[stream] = level[stream] - 0.25
 360|     cc1100 = 1000 + (1100 - 800) // 7
 361|     lake = (r >= 1101) & (r <= 1115) & (c >= cc1100 - 7) & (c <= cc1100 + 7)
 362|     cls[lake], level[lake], h[lake] = 2, 2.75, 2.0
 363|     nav = (r >= 1300) & (r <= 1305) & (c >= 900) & (c <= 1300)
 364|     cls[nav], level[nav], h[nav] = 3, 3.0, -0.5
 365|     corridor = (r >= 1301) & (r <= 1304) & (c >= 900) & (c <= 1300)
 366|     lowr = (r >= 300) & (r <= 305) & (c >= 300) & (c <= 400)
 367|     cls[lowr], level[lowr], h[lowr] = 3, 0.7, 0.0
 368|     lake_a = (np.maximum(abs(r - 1540), abs(c - 640)) <= 40) & (abs(r - 1540) + abs(c - 640) <= 60)
 369|     island = np.maximum(abs(r - 1545), abs(c - 637)) <= 6
 370|     lake_a &= ~island
 371|     cls[lake_a], level[lake_a], h[lake_a] = 2, 4.0, 3.0
 372|     cc900 = 1000 + (900 - 800) // 7
 373|     pond = (r >= 898) & (r <= 902) & (c >= cc900 + 4) & (c <= cc900 + 8)
 374|     cls[pond], level[pond], h[pond] = 7, 3.0, 2.6
 375|     zero = np.zeros((n, n), bool)
 376|     t = dict(heights=h, cls=cls, level=level, platform=zero, reserve=zero, narva=zero, water=cls > 0, beach=zero)
 377|     a = argparse.Namespace(slope=0.15, band=12.0, sigma=12.0, max_shift=4.0, min_vertices=4, max_raise=2.0,
 378|                            max_raise_water=6.0, max_lower=1.5, bed_floor=None, bed_min_depth=0.30,
 379|                            narva_radius=620.0, sea_cut=0.51)
 380|     out, masks, rep = profile(t, corridor, zero, a)
 381|     assert all(v['before'] == 0 and v['after'] == 0 for v in rep['gates'].values()), rep['gates']
 382|     assert np.array_equal(out['cls'], cls) and same_level(out['level'], level), 'class or level changed'
 383|     assert np.array_equal(out['heights'][corridor], h[corridor]), 'corridor changed'
 384|     R = a.band + a.max_shift + 6.0
 385|     keep = ndimage.distance_transform_edt(~lowr) * 6.0 <= R
 386|     assert not np.any(masks['changed'] & keep), 'change near the low reach'
 387|     between = (cls == 0) & (r >= 898) & (r <= 902) & (c >= cc900 + 2) & (c <= cc900 + 3)
 388|     assert np.any(masks['changed'][between]), 'river-pond contact not profiled'
 389|     wm = river | pond
 390|     assert not np.any(out['heights'][wm] > level[wm].astype(np.float64) - 0.10), 'water above its level - 0.10'
 391|     for k in (2, 3, 5):
 392|         obk = rep['by_class'][k]['crossing_offset_m_vs_smoothed_outline']['before']
 393|         oak = rep['by_class'][k]['crossing_offset_m_vs_smoothed_outline']['after']
 394|         assert oak['p90'] < obk['p90'], (k, obk, oak)
 395|     assert np.any((out['cls'] == 0) & island), 'island lost'
 396|     a.bed_floor = 3.5
 397|     out2, _, _ = profile(t, corridor, zero, a)
 398|     wk = np.isin(out2['cls'], (2, 5, 6, 7))
 399|     lim = np.minimum(3.5, out2['level'][wk].astype(np.float64) - 0.30)
 400|     assert np.all(out2['heights'][wk] >= lim - 1e-5), float(out2['heights'][wk].min())
 401|     assert np.array_equal(out2['heights'][corridor], h[corridor]), 'corridor changed by the bed floor'
 402|     print('SELFTEST PASS')
 403| 
 404| 
 405| def main():
 406|     if '--selftest' in sys.argv:
 407|         selftest()
 408|         return
 409|     ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
 410|     ap.add_argument('--terrain', type=Path, required=True)
 411|     ap.add_argument('--out', type=Path, required=True)
 412|     ap.add_argument('--channels', type=Path, default=None)
 413|     ap.add_argument('--slope', type=float, default=0.15)
 414|     ap.add_argument('--band', type=float, default=12.0)
 415|     ap.add_argument('--sigma', type=float, default=12.0)
 416|     ap.add_argument('--max-shift', type=float, default=4.0)
 417|     ap.add_argument('--min-vertices', type=int, default=4)
 418|     ap.add_argument('--max-raise', type=float, default=2.0)
 419|     ap.add_argument('--max-raise-water', type=float, default=6.0)
 420|     ap.add_argument('--max-lower', type=float, default=1.5)
 421|     ap.add_argument('--bed-floor', type=float, default=None)
 422|     ap.add_argument('--bed-min-depth', type=float, default=0.30)
 423|     ap.add_argument('--outline-sd', type=Path, default=None)
 424|     ap.add_argument('--outline-sd-classes', default='2,5,7')
 425|     ap.add_argument('--low-water-bank', action='store_true')
 426|     ap.add_argument('--low-water-bank-min', type=float, default=1.0)
 427|     ap.add_argument('--narva-radius', type=float, default=620.0)
 428|     ap.add_argument('--sea-cut', type=float, default=0.51)
 429|     a = ap.parse_args()
 430|     if a.channels is None:
 431|         ap.error('--channels is required')
 432|     assert not a.out.exists(), 'fresh output required'
 433|     a.outline_sd_classes = tuple(int(s) for s in a.outline_sd_classes.split(','))
 434|     if a.outline_sd is not None:
 435|         with np.load(a.outline_sd) as z:
 436|             a.ext_sd = z['sd'].astype(np.float64)
 437|     t0 = time.time()
 438|     t = dict(np.load(a.terrain))
 439|     planes = cell_planes(t['cls'], t['level'], sea_cut=a.sea_cut)
 440|     corridor, _, _, _ = protect_corridors(planes)   # the exact corridor faces, not their one-vertex margin
 441|     axes = json.loads((a.channels / 'axes.json').read_text(encoding='utf-8'))
 442|     reach_vertices = np.zeros((N, N), bool)
 443|     for reach in axes.values():
 444|         for r, c in reach['removed_cells']:
 445|             reach_vertices[r:r + 2, c:c + 2] = True
 446|     out, masks, rep = profile(t, corridor, reach_vertices, a)
 447|     a.out.mkdir(parents=True)
 448|     np.savez_compressed(a.out / 'terrain_inland.npz', **out)
 449|     np.savez_compressed(a.out / 'masks.npz', **masks)
 450|     rep = {'status': 'BUILT_PENDING_GATES_AND_ENGINE_VIEWS',
 451|            'params': {k: (str(v) if isinstance(v, Path) else v)
 452|                       for k, v in vars(a).items() if k not in ('terrain', 'out', 'channels', 'ext_sd')},
 453|            **rep,
 454|            'inputs': {str(p): sha(p) for p in (a.terrain, a.channels / 'axes.json', Path(__file__))},
 455|            'output_sha256': sha(a.out / 'terrain_inland.npz'), 'seconds': round(time.time() - t0, 1),
 456|            'limits': ['Only heights change: classes, levels and the vanilla reach vertices stay as they are.',
 457|                       'Water pieces stay valid (no class or level change); gates and engine views decide acceptance.']}
 458|     (a.out / 'report.json').write_text(json.dumps(rep, indent=1) + '\n', encoding='utf-8')
 459|     print(json.dumps({k: v for k, v in rep.items() if k != 'inputs'}, indent=1))
 460| 
 461| 
 462| if __name__ == '__main__':
 463|     main()
 464| 
```

# Reminder
Task P4: --slope-by-class SPEC and --slope-ref D in tools/terrain/profile_inland_v30.py; per-vertex slope from the
deciding class (attr), clipped to (Lw - bed_floor) / slope_ref but never below --slope; getattr defaults so the old
selftest passes; report forced_water_depth_m_p50; one more selftest run with {5: 0.25}. Empty SPEC = byte-identical
outputs. Write the whole file now.
