# Terrain V30: offline build and gates (2026-10-02)

Phase 2 of `plans/water-ground-rebuild-v1.md`. Built by Claude during the autonomous run.

## What it is

- Relief V30 (mix approved by Guillermo) with dimples filled, V29 water the new design drops filled,
  valley envelopes beside rivers, streams and navigable reaches, re-graded roads, carved water beds,
  smooth shores and coast, and the Narva bridge zone identical to V29 within 480 m.
- Output, not versioned (`tests/terrain_v30/`): `baltic_terrain_v30.asc` (SHA-256 `362550d1…`),
  `terrain_v30.npz` (heights and masks), `water_v30.npz`, `build_v30.json`.
- Reproduce from the repo root:
  1. `tools/terrain/build_v30_water.py tests/water_v3 tests/terrain_v30`
  2. `tools/terrain/build_v30.py tests/terrain_v30 tests/terrain_v30`
  3. the two gates below.
  The build is deterministic: a scratch run and the repo run gave identical heights.

## Roads

The first version gave every platform vertex the height of the nearest 1 m station. At a 6 % grade
that is a step of up to 3 cm, the whole cross-section budget. The road step now works as follows:

- Profiles are one quadratic programme over 107,206 stations and 124 chains, solved with an ADMM
  in OSQP's form plus an exact active-set polish.
- Constraints, met approximately by the solver (Codex's review found a curvature row at 0.0034 against
  0.001 after the polish; the local repair and the road gate below are the guarantee):
  - grade ≤ 5.8 %, and lower in bends (0.002·radius; 0.0005·radius below 16 m);
  - curvature ≤ 0.001 per m;
  - dry floor;
  - equal heights, within 2 mm, between each station and the nearest station of every other chain
    within 25 m, where their platforms touch.
- Platforms interpolate the profile every 12.5 cm.
- A final local repair re-solves the few vertices left outside a margin below the gate limits:
  37 stations, at most 11 cm.

## Shores

A water outline rasterised on 6 m vertices gives a staircase shore whatever the vector looks like.
That was the "square" water of V29.

- Heights near inland water (lakes, navigable reaches, delta, rivers, streams, ponds) follow the
  signed distance to the smooth vector outline, out to 12 m:
  - inside, level − max(0.10, 0.12·d), down to 1.2 m;
  - on land, level + 0.06 + 0.12·d.
  The triangulated shoreline (terrain = water level) then follows the outline.
- River and stream centre lines get 4-connected vertex grooves, so a 3–6 m stream stays continuous
  between vertices.
- Vertices only touched by a narrow polygon become land: 16,786.
- One plane per 6 m cell (`v30_common.cell_planes`, shared by pieces, builder and surface):
  - a standing-water edge vertex more than 0.30 m above an adjacent body becomes land (340);
  - flowing levels are capped at 0.25 m per 6 m;
  - water corners lie 0.05 m under every adjacent plane and land corners 0.03 m over it.
  This follows Codex's review, in `codex-review.md`.
- Sea coast: Codex's ocean mask is a 6 m staircase. The new coast is its 0.5 contour after a 9 m
  Gaussian. Within 12 m of it:
  - sea bed at 0.75 − max(0.15, 0.15·d);
  - beach at 0.85 + 0.15·d up to the 1.40 m dry floor, reached 3.7 m inland. The tide wets that
    strip: 2,681 vertices.
  - 1,661 land vertices became sea and 388 sea vertices became land.
- The Narva zone keeps V29.
- Roads keep their ground: within 9 m of a road station, a vertex that was dry in V29 stays
  land. Where a station runs on such ground, the whole carriageway (6.5 m) stays land. That
  keeps the sea causeway west of St Petersburg and roads beside widened or new rivers:
  757 vertices and 1,268 causeway stations. Without data, causeway profiles follow V29's
  height. Crossings that V29 already had in water stay water (bridge or ford reserves).

## Gates

| Gate | Result |
|---|---|
| Roads, Codex's definition (`verify_roads_v30.py`) | PASS: 100 chains, 76,536 stations, 0 failures. Cross ≤ 2.74 cm, grade ≤ 6.25 %, chord ≤ 2.48 cm. |
| Same gate on V29 (positive control) | PASS: 88,452 stations. |
| Water depth (every water vertex ≥ 0.10 m below its level) | PASS, minimum 0.15 m. |
| Banks (land within 8.5 m of water ≥ level + 0.05 m) | PASS, minimum 0.06 m. |
| Pieces: every covered cell's water corners ≥ 0.02 m under its plane and land corners over it (outside the Narva zone) | PASS, 416,633 cells. |
| Land floor ≥ 1.40 m; beach strip ≥ 0.80 m | PASS; the beach strip has 2,681 vertices. |
| Bed floor ≥ −12.0 m | PASS. Negative control: an uncapped sea cut (−480 m) failed on 601,940 vertices; an unbounded shore rule (−76 m) failed on 182,432. |
| Land slopes ≤ 35° | PASS. 17 triangles at 35.000x° inside the Narva zone, which is V29 itself (0.01° tolerance). |
| Narva zone identical to V29 (480 m) | PASS, 20,109 vertices, difference 0. |

The gate results are in `roads-gate.json`, `terrain-gate.json` and `roads-gate-v29-positive-control.json`.

## Limits

- Narrow streams still follow the 6 m vertex path: grooves zigzag where a stream runs diagonally.
- Shore triangles, those touching water, are reported but not gated. Many exceed 35°: these are
  underwater steps down to deep lake or sea beds.
- Overpasses without a shared OSM node are at grade: both roads are forced to one height. Bridges
  over them are left for mapping.
- Offline only. Engine checks are in `evidence/v30-preview-ingame-2026-10-02/`.
