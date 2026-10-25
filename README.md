# DayZ Baltic 12km — terreno y navegación

Mapa DayZ de 12,288 × 12,288 km que condensa la región báltica: golfo de
Finlandia, San Petersburgo con Kotlin y el Neva, Narva y la frontera, el Luga,
Peipus e Ilmen. Recorte aprobado por Guillermo el 29-09-2026. Se generó aquí
desde fuentes públicas; no depende del heightmap no entregado de Exta.

**Estado:** candidato de terreno V29 (`@DayZ_Baltic_RoadV29`) desplegado y probado
en el motor. La base no está aceptada: la auditoría del 02-10 encontró agua que falta,
un canal navegable uniforme, un satélite de maqueta desalineado y bordes rectos en el
relieve, y se van a rehacer agua y suelo. No hay edificios, vegetación colocada ni
carreteras físicas: el mapeado va después (P10).

- Estado vivo y siguiente paso: [HANDOFF.md](HANDOFF.md). Historia: [HANDOFF-history.md](HANDOFF-history.md).
- Producto y criterios: [product-spec.md](product-spec.md). Problemas: [bugs.md](bugs.md).
- Plan vigente: [plans/water-ground-rebuild-v1.md](plans/water-ground-rebuild-v1.md)
  (antecedente: [plans/v29-close-and-surface.md](plans/v29-close-and-surface.md)).
- Auditoría de agua y suelo: [evidence/v29-water-color-audit-2026-10-02](evidence/v29-water-color-audit-2026-10-02/summary.json).
- Desarrollo en `P:\DayZ_Baltic_12km_dev` (`subst` de `C:\Users\guill\OneDrive\Documentos\DayZ Projects`).
- Fuentes y atribuciones: [licenses/sources.md](licenses/sources.md).

## Repetición local

Python 3.12.14 aislado, con dependencias fijadas en `requirements.lock`. El entorno
está fuera de OneDrive y su intérprete base vive en la caché de runtimes de Codex
(`C:\Users\guill\.cache\codex-runtimes\codex-primary-runtime\dependencies\python`).
Hay copia de ambos en el checkpoint de E:\.

```powershell
& 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe' -X utf8 'P:\DayZ_Baltic_12km_dev\tools\run_pipeline.py'
```

Ejecutar solo en una copia de generación: reemplaza `derived/` y sincroniza `source/`.
Los retoques futuros deben vivir en capas separadas antes de regenerar. No
sobrescribir un `source/` editado a mano.

El comando no descarga. Usa los 21 originales fijados por SHA-256 en
`evidence/source-manifest.json`, guardados en
`C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\phase0\raw` (1,2 GiB) y
copiados al checkpoint de E:\. `--acquire` permite volver a adquirir fuentes, pero
una descarga nueva de OSM `latest` puede cambiar la instantánea y exige revisar el
manifiesto. Las rutas absolutas del manifiesto son de esta máquina.

`run_pipeline.py` produce la base de fase 0. El candidato V29 sale de encadenar los
solvers de `tools/navigation/` sobre intermedios fijados por hash en
`tests/regional_*`; todavía no hay un comando único desde las fuentes. El
checkpoint conserva esos intermedios.
