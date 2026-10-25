Revisión completada sobre el código real y la evidencia. La cadena R → 15 fallos → S3 → medición independiente está trazada por hashes y es coherente. Los hallazgos son mayoritariamente de cobertura de tests y de límites de confianza, no de mecánica rota.

## Verificado como correcto

- Interpolación nativa NW-SE, derivadas direccionales y familia de rupturas diagonales (x+z múltiplo de 6) en `audit_road_mesh_edges_ev112.py:14-40` son matemáticamente correctas y coherentes con `repair_roads_v30.bary`.
- Rechazos de 0 muestras, NaN, forma y `expect` desconocido implementados y cubiertos por tests; baseline-repros.json documenta los tres falsos PASS originales.
- Cadena de evidencia: R `d3d41a8…` → 15 fallos (`failure_count: 15`) → productor S3 exige ese sha y el sha del inventario → S3 `5cfe6a7…` → independent-mesh PASS sobre el mismo sha, misma cobertura `405173…`, 77559 secciones = 77559 muestras legacy.
- Márgenes del reparador (.0295/.064) son más estrictos que los límites, no relajados. Candidato S3 mueve 56 vértices, rango ±8 cm, 0 aristas regresadas.

## Findings

1. **Cobertura "congelada" tautológica.** `tools/terrain/review_visual_roads_ev112.py:35-36` usa como referencia el hash de cobertura del baseline calculado con la misma máscara. El hash depende solo de geometría + estaciones válidas, no del terreno, así que `coverage_matches_reference` es True por construcción. Repro: cambiar water1m.npy y ejecutar; sigue True. Arreglo: aceptar `--expected-coverage` y comparar con la constante `405173842d…` como hace el audit.

2. **Test de rupturas diagonales no ejercita diagonales.** `tests/test_road_mesh_edges.py:9` usa (1,12281)→(11,12271): x+z = 12282 constante, cae en `abs(v-u)<1e-12` y la familia diagonal se omite. Solo verifica el cruce x=6. Arreglo: segmento (1,12281)→(11,12281) y exigir el punto (7,12281).

3. **Orientación del triángulo nativo no cubierta.** Todos los tests en `tests/test_road_mesh_edges.py:13-33` usan planos o campos solo en x, invariantes ante NW-SE vs NE-SW. Arreglo: silla H con a=e=0, b=d=1 muestreada en el centro de celda; esperar 0 (NW-SE) y no 1.

4. **Caminos grade/chord del juez sin positivo.** `tests/test_qc_false_passes.py:40-44` solo prueba `cross_fail`. El mapeo de estación del chord (`verify_roads_v30.py:105,114`, desplazamiento +3) y `grade_fail` nunca se ejercitan. Arreglo: rampa a lo largo de la cadena (10 %/m) y un bache puntual, comprobando `station_m` del `fail_list`.

5. **Lógica de estaciones triplicada con divergencias.** `audit_road_mesh_edges_ev112.py:56` reimplementa exclusiones con 48/470/18 literales en vez de `LIMITS`; `repair_road_mesh_edges_ev112.py:36` indexa con `rint` sin clip (envuelve negativo en silencio) donde el juez clipa y `native()` lanza. Arreglo mínimo: en el audit, `assert crosscount==old['samples']` y usar `legacy.LIMITS`; en el reparador, clipar como el juez.

6. **S3 no fija `platform` ni islas.** `repair_road_mesh_edges_ev112.py:73-76` fija narva/estanque/orilla/H<.9/registros/kits/01545, pero `review_continuous_stream_pilot_v31.py:98` trata `reserve|platform|narva` como congelados. Reserva debe ser libre para carreteras; `platform` no. Hipótesis, no demostrado que alguno de los 56 vértices lo toque. Arreglo: añadir `data['platform']` a `fixed` y reportar `(changed&platform).sum()`.

7. **Extremos originales confiados al autor.** `tools/water/audit_stream_visibility_ev112.py:72` y `review_continuous_stream_pilot_v31.py:68` toman `original_raw_endpoints` de author-report.json. El segundo ya carga el kit-report congelado para el eje pero no para los extremos. Un autor podría acortar el tramo húmedo obligatorio. Arreglo: asertar igualdad con los extremos del kit-report congelado.

8. **Recuento de componentes contra afirmación del autor.** `tools/water/verify_compiled_stream_pilot_v31.py:65` compara ODOL con `inst['collision_components']` (author-report) en vez del MLOD ya cargado en `raw`. Arreglo: `len(raw.lods[1].selections)`.

9. **Índices de LOD fijos y pliegues solo del lecho.** `review_continuous_stream_pilot_v31.py:48` asume lods[0/1/3]; el binario selecciona por resolución. Falla cerrado si el orden difiere, pero inconsistente. Además `:37-43` mide pliegues solo en `bed`, no en `z['water']`. Arreglo: seleccionar por resolución y repetir el test de áreas sobre la rejilla de agua.

10. **KeyError escapa del juez de sonda.** `tools/water/eval_visual_probe_v31.py:82,101,109` acceden `p[key]`, `p['bed']`, `p['kind']`; `main:122` solo captura Assertion/Value/IndexError. Un punto `sea`/`ground` con `collision_pilot` y sin `bed` produce traceback sin informe `FAIL_INVALID_EVIDENCE`. Arreglo: añadir `KeyError` al except y exigir `bed` finito cuando `collision_pilot`.

11. **Calibración ignora rayos nativos sin impacto.** `eval_visual_probe_v31.py:62` solo valida cuando `rv or bullet`; un rayo spawn_native que falla ambos se descarta en silencio y basta `len(margins)>=3` de 289. Arreglo: exigir fracción mínima de impactos o fallar si hay fallos nativos.

12. **Consumidor de bosque aborta en vez de informar.** `tools/vegetation/review_visual_forest_support_v31.py:91` asserta finitud tras calcular `bad_support`; un soporte no finito produce traceback sin JSON. `:123` `gap[selected].max()` revienta si no hay árboles. Arreglo: emitir `status: FAIL_INVALID_EVIDENCE` con recuento de no finitos y guardar `selected` vacío. La convención matriz traspuesta/origen (`:66,70`) no tiene test ni prueba de motor.

## Veredicto

**SOUND-with-fixes.** Ninguna tolerancia relajada ni falso PASS demostrado en el código entregado. Los findings 1, 2, 3 y 4 son falsa cobertura demostrada; 6 a 12 son riesgos o endurecimientos. S3 sigue siendo candidato no integrado; bosque no es PASS.

## LO_NO_VERIFICADO

- `waterway_common.sample` (fuera de rutas): convención de triángulo y el offset x+200000 en `verify_roads_v30.py:89`. Solo evidencia circunstancial de coincidencia con NW-SE (S3 cae exactamente en el margen .0295 en ambos consumidores).
- `despike_v31`, `census_creases_v31`, `geom.disc_min`, `tri_h`, `height`, py3d, odol_reader externo no promovido: semántica asumida por lectura de llamadas.
- Contenido de author-report.json y kit-report.json; causa del soporte no finito en R.
- Si algún vértice cambiado de S3 toca `platform`; los 3 vértices con etiqueta legacy de agua descansan en water1m staged + plano + H>.9.
- Convención WRP traslación = origen + centro de bounding; no prueba motor.
- Hashes de `verify_roads_v30.py` registrados bajo ruta C:\OneDrive y P:\ se asumen el mismo fichero vía subst.
- No ejecuté tests ni scripts.

END_IMPLEMENTATION_REVIEW