# Revisión independiente de la referencia nativa V2

**Veredicto: corrección de referencia coherente; no cambia los criterios nativos ni el snapshot.** La causa del `FAIL calibrated_height` original queda acotada a una lista de alturas esperadas que no se actualizó al regenerar el perfil de sonda.

`prepare_probe.py` recalcula los 1.212 `points` desde las alturas del candidato y actualiza `risks.csv` (líneas 133–158), pero su `reference.update` en líneas 208–235 no incluye `'points': points`; como `reference = dict(baseline)`, se serializa la lista vieja heredada del baseline. El verificador original compara cada fila `P` contra `ref['points'][i]['expected_ground']` con tolerancia de 0.001 m (`verify_native.py`, líneas 41–44), lo que explica el único error del informe V1.

La corrección V2, `prepare_native_reference_v2.py` SHA-256 `2dfcdf8b2d2d3b7acfd5124139c2180b3d479ba876f3902e5518298313555295`, reconstruye las 1.212 alturas de referencia desde `risks.csv` con un solve independiente del plano NW–SE. Comprueba identidad de índice, clase y X/Z; la diferencia máxima entre el plano calculado y CSV es `1.2121174e-7 m`. Los campos restantes de cada punto, incluidos los 1.205 valores `expected_water`, son idénticos al original. El recibo informa 11 puntos cuyo ground cambia frente al EV82 reconstruido. Las referencias no deben compararse altura-por-altura con un umbral más estricto que esa precisión de reconstrucción.

El diff de `verify_native.py` SHA `230d6540…e229` a `verify_native_v2.py` SHA `be9a531e…9f0c` solo cambia las rutas de referencia/salida y añade un negativo que muta una altura esperada para comprobar que `calibrated_height` la rechaza. La función `judge` y sus umbrales/criterios permanecen iguales: 2.048 filas de grilla, 4.194.304 vértices, 1.212 puntos, 1.205 sondas de agua y tolerancia de altura de 0.001 m.

| Evidencia | SHA-256 |
|---|---|
| Referencia V1 preservada (`native-reference.json`) | `8cb6f96d379d21878519fad70c9ac7a5ab8d789b5d33e48fdea4be7120598a5a` |
| FAIL V1 preservado (`native-verification.json`) | `dd97462b7ea6d7792e47963f386d975fa1ac9f79749cedf3375c8b70b0693031` |
| Referencia V2 | `f748ec16547b8a54150e2414c004c63d0f65cb9852537db2b558300fa857ff19` |
| Verificador V2 | `be9a531e9ca1fdd663ebe4064345f821b2fb185d0c2e0479522d834cc1689f0c` |
| Snapshot de runtime V1/V2 | `f69470851e82ce01f144a5530f1e28edf6541a3ef82cdf270bb20778103281c8` |
| Informe V2 | `native-verification-v2.json`, `PASS_COMPLETE_NATIVE_READBACK` |

La corrección no vuelve a ejecutar DayZ ni altera terreno/mission; V1 conserva `FAIL calibrated_height`, y V2 reevalúa el mismo snapshot con la lista recalculada. El PASS solo cubre esa lectura física y fase de ola; no demuestra el límite temporal de olas ni aceptación visual/render.
