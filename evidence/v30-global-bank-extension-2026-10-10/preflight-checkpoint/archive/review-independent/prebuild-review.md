# EV93 prebuild review — 2026-10-10

**Dictamen:** READY FOR READ-ONLY BUILD. No blocking source-contract defect found in the reviewed builder or consumer draft. This is not a result from built shards and does not establish correct coverage until the consumer runs on a COMPLETE manifest.

## Frozen inputs

- Plan: `E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/plan.md` — SHA256 `ccc018a9e1cc8a51b075a91905b1cbe7d3cdaf72040e51992f2ac55db8ad7e82`.
- Builder final: `E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/ev93-face-index/build_face_index.py` — SHA256 `d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e`. This supersedes the earlier pre-fix builder SHA `adf6785eb31ebdf1e488788b48be721dde85fe89c4521f58244894e8061dbe83`.
- Independent consumer draft: `E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/review-independent/verify_face_index.py` — final reviewed-prebuild SHA256 `7524ff2cc0621e230fcccf49a3c7cd6255eba9949c522f54415fa47c834bfac6`.

## Revisión

- El builder fija sus fuentes aprobadas antes de leer entradas, verifica identidad WRP/bounds/PBO/OPRW y revalida hashes al terminar (`build_face_index.py:58-63, 233-246, 247-255, 286-300, 337-356`). La salida se restringe a la carpeta de índice revisada y tiene límites de 10 min y 2 GiB (`:25-35, 233-236`). La cota de bytes incluye los arrays persistidos (`:214-220, 337-356`); no es una cota de memoria total del proceso.
- La selección conserva las dos resoluciones LOD exactas y cada cara triangular. Una revisión detectó que las caras XZ colineales podían descartarse por `Polygon.is_valid`; el fix final retiene las de área cero con plano sentinel y no filtra áreas pequeñas positivas (`:174-211`, `:322-335`). La triangulación del terreno queda fijada NW-SE (`:242-246`). Los rangos son bbox cerrado e inclusivo; el código declara que el recorte exacto se hace después (`:66-103`).
- El guard ODOL 54/55 no es una suposición universal: el censo del WRP B actual encontró 13,128 modelos únicos, todos ODOL v55, y hashes iguales a la tabla bounds. Eso valida únicamente este set de entrada. El builder rechaza otras versiones (`:417-424`).
- El consumidor compila y `--fixtures-only` pasa siete casos: bbox multi-celda, contacto exacto con borde de grid, split NW-SE, fuera de mapa, degenerada, rango omitido negativo y exposición arriba/enterrada. Sus fixtures no sustituyen la prueba sobre shards reales. En producción importa el builder fijado solo para ejercitar su API de consulta; enumeración y oráculos de fuente/rango/exposición se reconstruyen en el consumidor.
- El consumidor vuelve a enumerar objetos/caras desde WRP y ODOL, compara claves y geometría cara por cara, contrasta `query_cell`/`query_window` del API real con su propia búsqueda por rangos y luego compara exposición estática con recorte por los triángulos nativos (`verify_face_index.py:330-390` y continuación). Al final vuelve a verificar los shards y los hashes de entrada.

## Límites que siguen abiertos

- Esta revisión no ejecutó el builder ni el consumidor sobre un índice COMPLETE; queda pendiente contrastar el manifest y shards reales.
- La exposición compara geometría estática de ODOL/WRP frente al terreno B. No mide oleaje, composición dinámica ni render in-game.
- El límite de 2 GiB cubre bytes del índice, no el pico de RAM del lector ni del consumidor. `FaceRangeIndex` carga todos los shards a memoria (`build_face_index.py:114-128`); comprobar uso real después de conocer tamaño/conteos del índice. No es bloqueo para crear el índice.
- El consumidor usa `ev87.compiled_objects` para cargar el inventario de ODOL de mapa completo. La presión de memoria de esa fase tampoco se ha medido en esta prebuild review.

## Verificación ejecutada

Con `C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe`:

- `verify_face_index.py --fixtures-only` → PASS, 7/7 fixtures.
- `python -m py_compile verify_face_index.py` → PASS.
- El auditor no ejecutó el builder ni cargó shards.
