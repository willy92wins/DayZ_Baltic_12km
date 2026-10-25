```
FINDING 1 | severity: CRITICAL
WHERE: profile_river_mouths_v30.py:51
EVID: "d = dijkstra(g, directed=False, indices=idx[seeds & mask], min_only=True)"
SCENARIO: Any terrain with at least one qualifying mouth component (pond vertices cls=5, level 0.55–0.70,
8-adjacent to cls=1 sea and to cls=5 level 0.90). scipy.sparse.csgraph.dijkstra's documented signature is
dijkstra(csgraph, directed=True, indices=None, unweighted=False, return_predecessors=True, min_only=False),
i.e. it returns a (dist, predecessors) tuple by default, also with min_only=True. `out[rr, cc] = d` then assigns
a (2, n) array into a shape-(n,) target -> ValueError: could not broadcast input array from shape (2,n) into
shape (n,). The tool dies on the first processed component, before writing terrain_mouths.npz or report.json;
it can never produce output.
FIX: d = dijkstra(g, directed=False, indices=idx[seeds & mask], min_only=True, return_predecessors=False)
(or unpack: d, _ = dijkstra(...)).
```

```
FINDING 2 | severity: HIGH
WHERE: profile_river_mouths_v30.py:102
EVID: "new_h[move] = target[move]"
SCENARIO: Bed drops up to 0.30 m are possible (h <= level_old - 0.10 <= 0.70 since the component's level <= 0.80;
target = min(new_level-0.10, pmin-0.0501) can be 0.40-0.45). Take a legal input bank triangle (two cls=0 corners,
one cls=5 corner w with old level 0.79, h=0.69, land corner at 4.89 m -> face atan(4.20/6) = 34.9 deg <= 35, legal).
The ramp assigns new_level[w]=0.51 near the sea side, target = 0.41, so w drops 0.28 m -> leg 4.48/6 -> 36.8 deg:
the "land triangles <= 35 degrees" gate is broken. Tool 2 contains no face check and no face metric; if
fit_shore_crossings_v30 runs afterwards, discard_steeper_land_faces treats tool 2's output as `original`, so the
ceiling becomes max(36.8, 35)+1e-4 and the violation is permanently preserved. Nothing reports it.
FIX: After the bed pass, run the same face guard as tool 1 (revert drops that push any land face past 35 deg
relative to the input) or cap the per-vertex drop; report reverted count.
```

```
FINDING 3 | severity: MEDIUM
WHERE: profile_river_mouths_v30.py:99
EVID: "need = changed_level & (h > target + 1e-9)"
SCENARIO: The tool raises component levels up to 0.80 but only ever touches WET beds; the bank gate
"land within 8.5 m of water >= nearest water level + 0.05" is never re-evaluated. For non-beach land the 1.40 m
floor dominates (0.80+0.05=0.85 < 1.40), but on the beach mask the floor is 0.80: a beach land vertex b (cls=0,
beach=True) at h=0.80, 6 m from a component vertex whose level rises 0.55 -> 0.78 (lagoon side near the first
planes), now requires h_b >= 0.83 and stays at 0.80. Old state was legal (0.80 >= 0.60). Tool 1 lists beach in
`fixed`, so the follow-up fitter can never lift b either -> the gate is broken in the final candidate and no
report field shows it.
FIX: After computing new_level, recompute the bank bound (EDT to wet, nearest level + 0.05, 0.80 floor on beach)
and lift or flag land vertices within 8.5 m; refuse raises that break it.
```

```
FINDING 4 | severity: LOW
WHERE: fit_shore_crossings_v30.py:174
EVID: "no_raise = wet & (w['groove'] | guard)"
SCENARIO: The docstring (lines 13-14) promises "groove vertices and wet vertices within 24 m ... never rise",
but the code intersects groove with wet. If water_v30.npz's `groove` mask contains any dry (cls==0) shoulder
vertex that is the land end of a fitted wet-land edge (dw<=0, dl>=0), the crossing equation can raise it
(ub = hv + 0.6, no ceiling applied) although the protection says it must never rise. Conditional on groove
containing dry vertices.
FIX: no_raise = w['groove'] | (wet & guard)  — drop the wet qualifier for groove vertices, per the docstring.
```

PREMISE
The per-edge condition "terrain interpolated at t* equals W" is the correct *local* condition — on a wet-land edge the visible waterline is exactly where the linear terrain crosses the plane. But it is only applied where sd flips sign (dw<=0, dl>=0): wet-land edges lying fully inside or fully outside the designed outline still produce visible crossings that are neither fitted nor measured, so the shoreline there keeps the 6 m grid signature and no metric notices. Second, W = max plane of the edge's cells: with 25 mm banding the two adjacent cells usually differ, so the fit pins the crossing to the higher plane and the lower cell's visible line stays up to one band off the outline — a systematic jag heights-only editing cannot remove. Third, the condition is structurally infeasible at t*≈0/1 (outline through a vertex): it then demands the wet vertex itself ≈ W while the bounds force <= level−0.101 and W ≈ level, so residuals at the ends are by construction, not solver failure (offset_limits correctly attributes them, but "every edge can meet the outline" is false).

LO QUE NO PUDE VERIFICAR
- Finding 1 rests on the documented scipy default `return_predecessors=True` for dijkstra (incl. with min_only=True); I cannot execute scipy here to confirm on the pinned version — the one-line fix is harmless either way.
- v30_common internals (grid_xz, tri_sample, N), engine_water_model.Piece.box ordering / visual() return, and axes.json 'removed_cells' schema — channel_surface's r/c mapping from the piece box is unverifiable.
- finish_shores_v30: records(), PARAMS['iterations_max'], and whether finish_shores builds corridors from pre- or post-channel-removal planes. Tool 1 calls protect_corridors(planes) BEFORE channel_surface() deletes removed reach cells (line 114 vs 117), so its fixed set may diverge from finish_shores'.
- water_v30.npz fields (sd, sd_sea, groove — especially whether groove contains dry vertices, on which Finding 4 depends) and terrain npz fields platform/reserve/narva/beach; heights dtype (a float64 input would trip the `changed & fixed` assert purely via the float32 cast; float32 assumed).
- Which wet bound the acceptance checker applies to planeless, sea-shown water: strict "level − 0.10" (0.40 at the ramp's sea end) or the tidal-coast rule "wet <= 0.45" that tool 2's 0.45 target (and tool 1's doc line "wet <= 0.45") assumes. Tool 2's knowingly-reported blocked beds (level lowered, height kept) fall under the same ambiguity and are at least surfaced in beds_blocked_by_protection.
- SHALLOW/DRY fixture schemas, the 13 SHALLOW_IDS, and corridor geojson availability; solver runtime on 2048x2048 with ~10⁵ variables under lsq_linear/TRF.