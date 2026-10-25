# DayZ_Baltic_12km - location map

Generated 2026-10-01 04:28 by `tools\gen-project-map.ps1`. Regenerate after moving files.
This answers WHERE things are. Current state lives in `HANDOFF.md`; do not duplicate it here.

## Anchors

| What | Path |
|---|---|
| Dev / docs | `C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev` |
| Tools | `C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\tools` |
| Plans | `C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\plans` |
| Reviews | `C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\reviews` |

## HANDOFF: cuánto leer

`HANDOFF.md`: el estado vigente está delimitado por `<!-- LIVE-STATE:START -->` y `<!-- LIVE-STATE:END -->`.

**Leerlo así:** hasta el marcador `LIVE-STATE:END`; no usar el antiguo límite fijo de15líneas. El resto es archivo histórico.

## Build / test entry points

- `build_foundation_package.ps1`
- `build_regional_water_assets.ps1`
- `build_static_shape_v2.ps1` - Copy only the compiled world subtree, never the junction-bearing project root.
- `rebuild-playtest.ps1`
- `sample_server_process.ps1`

## Docs in this project

- `HANDOFF.md` - 19 KB, touched 2026-10-01
- `product-spec.md` - 4 KB, touched 2026-09-30
- `README.md` - 3 KB, touched 2026-09-30
- `CLAUDE.md` - 2 KB, touched 2026-09-30
