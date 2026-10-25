# Agua visible y perfiles de valle

La preview plana no se acepta: Guillermo informa reflejos sobre tierra, juntas de agua y cauces/taludes angulares. `user-images/` conserva las cuatro capturas; `frame-manifest.json` identifica las copias propias y sus hashes. No se ha promovido ningún parche de diagnóstico ni esta preview a base 1.0.

| Experimento | Hecho observado | Límite |
|---|---|---|
| Mar a -100 m | R1_far cargado pierde los parches; los estanques siguen visibles | Aísla participación del mar, no demuestra el mecanismo ni sirve de arreglo |
| waveAmplitude=0 | Persisten parches con valor leído 0 | Descartado como arreglo |
| Subdivision roughness=0 | Persisten parches con configuración leída | Descartado como arreglo |
| Cliente instrumentado | Misma configuración que servidor, puntos medidos secos, mar 0,65-0,85 m | Consultas físicas no son cota de la superficie dibujada |
| Near plane 0,07 / 1 / 0,07 m | Tres capturas por fase; parches en las tres fases | Descartado; `near-plane-repeat-record.json` y log. El intento anterior perdió la fase 1 por confundir substring con regex |
| StitchedWaterPilot | Desaparecen juntas de cuadrícula en R2/R3 oblicuo y bajo; repetición física 28 puntos x 62 muestras PASS en calma/tormenta | Altura nominal y presencia pond idénticas a flat en los 28 puntos; no implica smoothing resuelto ni extensión global |

Las capturas sea-away 1-3 carecen de texturas y no valen para comparación. La carpeta inicial near-plane/phase1 contiene una captura tardía de fase 2: la fase se determina por el log, nunca por el nombre. `near-plane/repeat2` es la serie completa posterior.

El piloto une solo el LOD visible de 538 modelos con alturas comunes en la malla nativa de 6 m. Roadway, memoria y propiedades pond quedan exactos; se compensa el centro ODOL en WRP. Desplazamiento visual máximo 0,342 m: su posible diferencia con la superficie física debe medirse. Compilación y comparación de geometría en `stitch-package.json`. Mundo desplegado 7d0a165d, agua 542bd4e8, terreno e0d35db0. No extendido aún al resto del agua.

El fallo de forma es independiente: `smooth_dry_relief_v30.py` excluye agua más 36 m y la reserva natural; los perfiladores antiguos trabajan sobre todo extremos de las aristas de orilla. La nueva petición de Guillermo exige transiciones curvas en todo el valle y en el relieve general. Carreteras, plataformas, puentes, fondo mínimo y corredores siguen siendo invariantes. El perímetro/biomas de reserva no son una prohibición de suavizar sus alturas naturales.

La regresión física está en `stitch-runtime-verification.json` y `stitch-vs-flat-physics.json`; run f20215b7 cerrado orderly_close, lease liberado y banco libre (`stitch-probe-lifecycle.json`).

Pendiente: nuevo perfil completo de valle, reparación demostrada de los parches, extensión global del agua continua; finales de río, lagos grandes y vistas restantes. Luego Terrain Builder y navmesh. Los veinte fallos no están cerrados. Los candidatos A/A1 de valle se retiraron por regresiones de contorno; ver la revisión de diseño del 09-10 en `../v30-valley-smoothing-2026-10-08/plan.md`.
