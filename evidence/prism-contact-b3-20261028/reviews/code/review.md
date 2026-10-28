Revisión completa. Dictamen a continuación.

**Veredicto: SOUND-with-fixes.** La geometría, el parche de bytes, la protección de masa/caras/otros LOD y el consumidor independiente están bien ligados a las APIs reales. Hay un fallo de binding en la CLI del consumidor que impide ejecutarlo sobre el contrato real, y un riesgo de rechazo espurio en el autor. Ambos son ruidosos, no silenciosos, pero el primero es bloqueante.

**Bugs concretos con repro**

1. **Bloqueante. El consumidor exige `expect == 'dry'` para 700 y 723, pero 723 es `wet` en el original.** `verify_prism_contact_b3_ev112.py:183` requiere `all(v['expect'] == 'dry' for v in retained)`. En `R/dry-road-full-native-20261028/probe/result.json`, fila `rows[].id == 723`, `expected.expect` vale `"wet"` (línea 64078; también `states.water == "FAIL"`). La fila 700 sí es `dry` (línea 62146). Repro: ejecutar la CLI con el contrato real; sale `REJECTED_OFFLINE` con razón `original_controls_changed` antes de verificar nada. El plan fija los targets por `expected.XZ` originales de 700/723, no por su estado de agua, y la adjudicación dice que el agua no se cierra aquí. Fix: ligar los controles por id y XZ exactos (ya se hace con `c['targets'] == targets`), y comprobar `expect` por id (700 dry, 723 wet) o no comprobarlo. No baja ningún umbral geométrico.

2. **Riesgo. El autor exige grosor exacto con `==`, el consumidor tolera 1e-6.** `prism_contact_b3_ev112.py:34` requiere `p[b,1] - p[a,1] == 180/512` en float64 de valores float32; `verify_prism_contact_b3_ev112.py:36` tolera `1e-6`. La fuente d130 es la salida de `dry_road_mlod_ev112.py:66`, que suma un delta float64 a techo y base y empaqueta cada Y a float32 por separado. Las Y locales están alrededor de ±0,5 m (bed 7,22 y 6,92 frente a origen Y 7), de modo que techo y base caen con frecuencia en binadas distintas y el redondeo float32 puede romper la igualdad exacta en ~1e-8. Si ocurre, el autor falla con `prism_thickness` → `INCONCLUSIVE_AUTHOR`, sin candidato. No lo he podido ejecutar; es un repro potencial sobre el candidato real. Fix: alinear la guarda del autor con la del consumidor (`abs(...) <= 1e-6`). La base se reescribe desde el plano del techo (`:47`), así que el consumidor sigue verificando `base_plane_error` independientemente.

3. **Menor. Clasificación de errores no-ValueError como INCONCLUSO.** `np.linalg.solve` singular (`:112`, `:120`) o `next(...)` sin pareja (`:118`) lanzan `LinAlgError`/`StopIteration`, que `main` vuelca como `INCONCLUSIVE_CONSUMER`. Para una proyección degenerada debería ser rechazo. En la práctica `components()` ya rechaza antes (cierre, convexidad, emparejamiento vertical), así que no hay fallo silencioso.

4. **Menor. El autor no exige que `c['source']` esté en `pins`** (`prism_contact_b3_ev112.py:101-104`); el consumidor sí (`:177`). Como el consumidor reconstruye todo desde la fuente pinned, no hay vía de aceptación sin pin.

5. **Menor. Presupuesto de tiempo.** `meter.STARTED` se fija al importar el meter dentro de `main`, tras numpy/shapely/py3d; `dry_road_mlod_ev112.py:119` reasigna `STARTED`. Infracuenta segundos; no afecta a la geometría.

**Binding verificado contra las APIs reales**

- `review_compact_collision_v31.load` (`:16-21`) devuelve `header, lods, blobs` con `blobs[i]` como bytes exactos de cada LOD; el consumidor compara `blobs 0,2,3` byte a byte y el 1 con máscara. Correcto.
- Layout P3DM: `py3d/__init__.py:2752-2766` lee cabecera de 28 bytes, puntos `fff`+`<L` (16 bytes), normales `fff` (12). Los offsets `28+16*i` (XYZ, excluyendo flags) y `28+16*n+12*ni` del autor y la máscara del consumidor coinciden. `#Mass#`, selecciones y caras quedan tras los TAGG y están protegidos por `unauthorized_bytes_changed`.
- `Selection.points/faces` son dicts por identidad de objeto (`:1938-1939`); los índices via `id()` son correctos. `Face.read` acepta 3 o 4 vértices; ambos scripts exigen 3.
- `selected_components(..., contact_only=True)` (`overlap_stream_collision_v31.py:43-73`) selecciona por huella de 6 puntos en mundo; el consumidor reconstruye con el triángulo superior en local. Mismo conjunto salvo diferencias ~1e-12 en el umbral, y cualquier discrepancia aborta con `selection_mismatch` contra la lista del contrato, que incluye `Component1333`.
- `closed_component` y convención de winding: `add_component` (`compact_stream_collision_v31.py:98-105`) orienta normales hacia dentro con volumen firmado negativo; el consumidor exige `signed_volume < 0` y convexidad como `(p - t0)·n >= -1e-6` con n interior. Coherente. Techo = caras con `normal_y < -1e-10`, igual que `review_compact_collision_v31.py:104`.
- `overlay(bed, roof)` con límites por defecto ±0,02/0,01 heredados, más auto-overlay de la fuente a 1e-6. Bed y techo ambos en local (el review original suma origen a ambos; equivalente).
- `unique_assignment` exige que cada índice de normal pertenezca a exactamente una cara del modelo; esto garantiza que reescribir normales seleccionadas no toca ninguna cara no seleccionada.

**Criterios del plan y adjudicación**

- Homotecia 1+δ/r con δ=1/512, Y evaluada en el plano original en el XZ ya redondeado a float32, base = techo − 180/512. Mismos índices, 6/8, bbox exacto (`bbox_changed`). Sin Minkowski.
- Interior estricto local y mundial float32 (`contains` de shapely excluye borde), distancia firmada y ULP reportados, marco etiquetado como no certificado por el motor. No hay gate de 2 ULP; `assertLess(margin_ulps, 2)` en el test es una expectativa del fixture, no un umbral del consumidor. Recomiendo quitarlo o comentarlo para que no se lea como gate.
- Plano 1e-6 sin relajar; `predicted_float32_error_bound_m` reportado aparte.
- Normales seleccionadas recalculadas desde XYZ guardados, resto byte-exacto.
- No se infiere `ComponentNNNN-1`. No se usa `verify_dry_road_mlod_ev112`. Centroide base/techo no se usa como mutante.
- Fixtures: plano e inclinados con plano conocido, identidad rechazada por `no_strict_expansion`, cara invertida, cara retirada (la corrección de la selección hace que falle por `geometry_layout_changed`, correcto), normal, techo, masa ajena, Visual, Roadway, target extra, contracción, deformación no radial. Cumple la lista del plan.

**Qué no cubre esta revisión**

No he ejecutado nada. El fallo 1 está verificado por lectura del original; el riesgo 2 depende de los bytes reales de d130. Ninguna conclusión sobre compilación, motor, agua ni mapa; `OFFLINE_CANDIDATE_ONLY` sigue sin ser PASS de nada.

**Acción**

Corregir el fallo 1 (obligatorio) y alinear la guarda del autor (fallo 2) como la única corrección permitida por el plan; después ejecutar autor y consumidor sobre el candidato real.

FIN_REVISION