# Codex review of the V30 pipeline (2026-10-02, 05:25)

Read-only review requested by Claude. Codex session `01a0fa9e-e6eb-75f3-8d15-23d46664ccab`, checkout
`f4b3318`. Every finding was checked by Claude and fixed in the commit that adds this note.

| # | Severity | Finding | Claude's check | Fix |
|---|---|---|---|---|
| 1 | P1 | 215 of V29's 4,775 tile materials are not the full four-surface set. A four-slot mask is misread there; Codex counted 123,576 affected pixels in eight tiles. | Confirmed: 130 sea materials with gravel only, 76 with three surfaces, 9 with two. Claude's earlier claim ("every tile material holds all four") came from comparing one tile's variants. | `apply_surface_v30.py` rewrites every `P_*.rvmat` from one full template with the tile's textures and uvTransform. The renderer reproduces all 4,560 full V29 materials byte for byte, then rewrites the 215. |
| 2 | P1 | The mean plane of a cell can bury water under its own bed when the corner levels differ, e.g. 8.50 / 7.80 / 7.09 m. | Confirmed: 808 cells with a spread over 0.25 m. Most are streams, rivers, and lake–pond or lake–river contacts. | Design: a standing-water edge vertex more than 0.30 m above an adjacent body becomes land (340); flowing levels are capped at 0.25 m per 6 m. Terrain: one plane rule (`v30_common.cell_planes`) for pieces, builder and surface; water corners 0.05 m under and land corners 0.03 m over every adjacent plane. New gate `pieces`: 417,130 covered cells, 0 failures. |
| 3 | P2 | The standalone `repair_roads_v30.py` could move Narva-zone vertices. | Confirmed for the CLI path; the builder already passed the mask. | The CLI passes `narva` as fixed. |
| 4 | P2 | `polish()` can stop with held rows still outside their bounds (finite penalty). | Confirmed: profile curvature 0.0034 against a limit of 0.001 on chain 40. The final gates do not depend on it: the local repair and the road gate decide. | One escalation (penalty ×100) when held rows still violate. The README no longer calls the profile limits exact. |
| 5 | P2 | The satellite painted water from the nearest vertex level, not from the piece plane: 717 sampled mismatches. | Confirmed by construction. | The satellite uses the cell plane. |
| 6 | — | `wrp0wzd.py` and `derive_world_v30.py`: nothing serious. Format equal to the reference reader, exact round trip of the base WRP, 17,322 translations as specified. | — | — |
