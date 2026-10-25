# Surface V30: satellite at 1 m/px and mask (2026-10-02)

Phase 4 of `plans/water-ground-rebuild-v1.md`, built by `tools/terrain/build_surface_v30.py` on terrain
V30 with the smooth coast and the shared plane rule (`tests/terrain_v30`, ASC `362550d1…`). Generated in about
105 s; output in `E:\DayZ-Baltic-Build\surface-v30e` (not versioned). Water is painted where the terrain lies
below the plane of its cell's piece. The offline views are rendered on this build (`coast_island` and `coast_spb`
show the smoothed sea coast).

## Layout kept from V29

- 32 × 32 tiles of 512 px at 1 m, 384 m step, 64 m overlap. Tile `aaa_bbb`: column `aaa` in x and row
  `bbb` from the north. Checked on the uvTransform of V29's materials (`P_005-020`, `P_010-010`).
- 4,560 of V29's 4,775 tile materials hold the four surfaces in a fixed order. That is Codex's
  "complete TerrainX channels" fix against black stains.
- The other 215 do not: 130 sea tiles have gravel only and 85 have two or three surfaces. Codex's
  review found this; Claude had checked only one tile's variants.
- `apply_surface_v30.py` rewrites all 215 from one full template, which first reproduces the 4,560
  byte for byte. Material names and the WRP material grid do not change.
- Mask colours as in V29: black `cp_gravel`, red `cp_conifer_common1`, green `cp_grass`, blue
  `cp_grass_tall`.

## Content per 1 m pixel

| Class | Rule | Surface and colour |
|---|---|---|
| Water | Terrain on the native triangles below the local water level, inside the cells covered by pieces, or below the sea. That is exactly where the engine shows water. | Gravel, with a dark bed that gets darker with depth. |
| Shore | Within 0.30 m above the level and 15 m of water. | Gravel, mud colour. |
| Road | Within 3.5 m of a graded chain centre line. | Gravel, light grey-brown. |
| Land | WorldCover 2021, majority-filtered over 5 × 5 vertices, with boundaries warped by ±6 m of smooth noise. | Forest: conifer, dark olive. Grassland and built-up: grass. Cropland, shrub and wetland: tall grass. Bare: gravel. |

- Built-up is grass with an olive-grey tint. Towns get buildings at mapping time.
- Tones come from Chernarus+ satellite tiles, decoded with DayZ Tools' ImageToPAA.
- Multi-octave value noise is added, plus row stripes on cropland.
- Shares of the 1 m pixels, overlaps included: conifer 61 %, gravel 25 % (mostly water beds), tall
  grass 8 %, grass 6 %.

## Files here

- `preview_sat.png` and `preview_mask.png`: the whole map at 16 m per pixel.
- `surface.json`: counts and palette.
- `offline-views/`: oblique views from `tools/terrain/render_view_v30.py`, a heightfield renderer with
  the V30 heights and these textures. **They are not engine captures**: no lighting model, water is a
  flat tint, colours are brightened ×1.9.
- `narva_bridge.jpg` shows the 480 m Narva zone. It keeps V29's blocky water and islands by
  requirement (identical to V29).

## Limits

- Still four surfaces, the V29 ones. More vanilla surfaces mean new materials with more stages and a
  mask encoding beyond four colours; that has not been tried.
- Narrow streams follow the 6 m vertex path and zigzag where they run diagonally.
- Not yet seen in the engine; in-game captures need the display on.
