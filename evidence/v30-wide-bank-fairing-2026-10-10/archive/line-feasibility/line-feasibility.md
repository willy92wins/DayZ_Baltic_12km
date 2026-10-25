# EV88-Q: factibilidad analítica de la interpolación B→Q

**Veredicto: no existe ningún intervalo de ancho positivo de `α∈(0,1)` que cumpla juntas las cuatro puertas de forma congeladas.** Esto no prueba que el perfil deseado sea físicamente imposible: prueba que la recta entre B y el Q rechazado no satisface simultáneamente esas heurísticas. No se generó ni aceptó una variante.

## Anclas

- Plan congelado: `plan.md`, SHA-256 `50a94dac1a15580c6299426678399ca80caf49835ba98a79946ded688a8a47ad`.
- B, SHA-256 `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`.
- Q rechazado, preservado, SHA-256 `cce4cd0c2f71355c6d8a110804b52570644e496055ada9ef17d07b4cb60c455c`.
- Tau near-flat congelado: `0.024040603637695314 m`; núcleo analizado: filas `[834,847)`, columnas `[364,377)`.
- El derivador enumera 490 breakpoints de igualdades/umbrales pertinentes y evalúa por separado cada breakpoint y cada tramo abierto. No usa una malla de alphas.

## Resultado por puerta

| Puerta | Conjunto de α que pasa |
|---|---|
| Reducción de prominencia de ambos perfiles focales ≥25%, sin depresión | `[0.2311671129494325, 1]` |
| Sin nuevas ventanas 2×2 con span `≤ tau` | `[0, 0.010198783062144338]` y `(0.9499850382009432, 0.9958592725061418]` |
| Extremos axiales emparejados según contrato | `[0, 0.7723378669496158]` |
| Máxima prominencia por cada fila/columna no empeora | solo `α=0` |
| **Intersección** | **vacía** |

En el primer alpha que alcanza la meta focal (`α≈0.2311671`), las prominencias pasan de `1.8323015→1.3557010 m` Este-Oeste y `1.7872882→1.3404661 m` Norte-Sur. Ya aparecen cuatro ventanas near-flat nuevas; ejemplos (fila,columna): `(837,373)`, `(839,374)`, `(840,374)`, `(842,375)`. A `α=0.5` hay cinco ventanas nuevas.

La puerta de perfiles por fila/columna es más restrictiva en esta interpolación: Q aumenta una prominencia desde cualquier `α>0`. En `α=0.2311671`, por ejemplo, fila 835 sube `0.0052382→0.0119883 m` (+`0.0067502 m`), fila 836 sube `0.0052603→0.0103834 m` (+`0.0051230 m`), y columna 376 sube `0.0002694→0.0005505 m`. Cerca de cero también hay excesos positivos, pero diminutos (a `α=10⁻⁶`: fila 837 +`1.69e-8 m`, columna 376 +`5.56e-9 m`); la obstrucción en el alpha focal es milimétrica, no solo redondeo.

En la banda donde near-flat vuelve a pasar (`α≈0.95`), la puerta de extremos falla además: aparecen extremos H sin pareja B admisible, incluidos `(834,368)`, `(835,369)` y `(840,372)` en ese punto de control. El extremo Q también falla varias puertas.

## Límite de la conclusión

La puerta de extremos y la de prominencia por fila/columna están descritas en el plan como heurísticas explícitas de forma, no invariantes físicos del agua. Por eso el resultado localiza la incompatibilidad entre los objetivos de forma de este piloto y la dirección Q; no demuestra que el perfil sea “natural” o antinatural, ni habilita relajar criterios. Este análisis no comprueba protección, corredor, agua, cruces, ángulos, energía, float32, cobertura ODOL ni motor; no selecciona alpha.

## Reproducción

- Derivador: [derive_line_intervals.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/line-feasibility/derive_line_intervals.py), SHA-256 `E8B4AC0591A4C5C65D226380860F811A784AB47C86CD5AAD113A361E78E89A9F`.
- Salida analítica: [line-intervals.json](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/line-feasibility/line-intervals.json), SHA-256 `CEDAC17B44180543699BC5BCB65B2B3ED0B87FCFE5509524971571402324556B`.
- Inspección ejecutada con `C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe`; el estado resultó `COMPLETE_ANALYTIC_LINE_DECOMPOSITION`, 490 breakpoints, intersección vacía.
