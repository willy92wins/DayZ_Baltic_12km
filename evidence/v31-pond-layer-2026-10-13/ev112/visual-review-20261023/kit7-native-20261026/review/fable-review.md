**Veredicto: SOUND-with-fixes.** No encuentro ninguna vía concreta de falsa aceptación en el consumidor ni en la preparación. Los hallazgos son de endurecimiento y documentación, acotados a esta unidad.

## Lo que se sostiene (con evidencia)

- **Mapeo nativo de coordenadas y triángulos.** `tri_h` usa diagonal NW-SE con `ZTOP = 12282` (`tools/water/streambed_kit_v31.py:175,270-277`), igual a 2047·6. Los centroides con offset (4,2) caen en fc=4/6 > fr=2/6 (triángulo nw-ne-se) y (2,4) en fc<fr (nw-sw-se), coincidiendo con las esquinas elegidas en `native_height_probe_ev112.py:43-47`. La convención fila 0 = norte queda ligada al WRP real por la aserción `terrain == H[::-1]` en `review_visual_forest_support_v31.py:39`, que el preparador de frontera ejecuta sobre el mismo npz kit7.
- **Ligadura de contenido de alturas.** El `after` (hash 815ef8…, `prepare_kit7_native_data.py:40`) es el mismo npz que el stage-report declara y que `forest_arrays` compara byte a byte contra la elevación del WRP fuente. El total 3430 se cruza con `stage-report.json:22`.
- **Identidad de cobertura.** `verify_coverage` exige conjunto exacto de vértices cambiados y ambos triángulos de cada celda incidente, IDs secuenciales, coordenadas que nombran el punto declarado, y expectativa igual a `tri_h` con atol 1e-9. Omisión, duplicado y deriva de coordenada/altura se rechazan (`:64-90`). `parse` exige UUID canónico, recuento exacto, IDs en orden y reloj monótono (`eval_forest_boundary_probe_v31.py:10-31`).
- **Fail-closed.** Salida distinta de 0 salvo `NATIVE_HEIGHT_SAMPLE_PASS`; salida existente bloquea; nada en `judge` tolera filas ausentes.
- **Frontera.** IDs exactos contra `boundary_pending.ids` (3727), registros y puntos idénticos a F, paquetes kit7, UUID nuevo, estado `BOUNDARY_PREPARED_NOT_RUN` y `native_result_inherited=False` (`prepare:34-37`). El `SAMPLED_BOUNDARY_CLEAR` de F no se hereda.
- **Sin operar DayZ.** Solo un subprocess Python con `-I`; escribe en cuatro rutas nuevas aseguradas inexistentes (`prepare:26`). API escalar e `init.c` con 128/frame sin cambios (hash 69fd65… coincide con F).
- **Sustancia de tests.** El positivo analítico codifica a mano los 6 triángulos que contienen el vértice (4,5); comprobé que el conjunto es correcto (celdas (3,4) ambos, (3,5) solo t1, (4,4) solo t0, (4,5) ambos). Los negativos ejercitan rutas reales del consumidor.

## Hallazgos a corregir

1. **Puertas desactivables por `-O`** (`prepare_kit7_native_data.py:15-53`). Todo el gating es `assert`. Reproducción: ejecutar con `python -O -I` y un `accepted.json` con estado distinto; la línea 15 no falla y la preparación continúa. Corrección: añadir al inicio `if sys.flags.optimize: raise SystemExit(...)` o convertir las aserciones críticas a `raise`.
2. **Oráculos usados antes de ligarse** (`prepare:16-17` vs `:41,46`). `streambed_kit_v31.py` y `eval_forest_boundary_probe_v31.py` no están en `required`, pero se importan y usan en la línea 41; su hash se registra después, en la 46. Añadirlos a `required`. No es falsa aceptación porque la sonda nativa sigue siendo el oráculo final.
3. **Procedencia de la tolerancia** (`plans/ev112-kit7-native-data-unit-20261026.md:5`). Cita `eval_visual_probe_v31.py:108`, que es la tolerancia xz del rayo de colisión. La puerta de suelo nativo de 1 cm está en la línea 88. El valor es correcto; la cita no.
4. **Test de no-finito no ejercita esa rama** (`tests/test_native_height_probe_ev112.py:66`). Reemplazar `P;1;` por `P;1;nan;` produce 7 campos y dispara el error de esquema. Sustituir el campo de altura manteniendo 6 campos.
5. **Estado parcial en fallo** (`prepare:27-28` antes de `:32-48`). Si una puerta posterior falla, quedan creados `O`, el mod en `P:/Mods` y las dos misiones, y la línea 26 bloquea el reintento. Documentar la limpieza manual. Sin riesgo de ejecución: ningún perfil de servidor referencia el mod nuevo.
6. **Opcional.** `verify_binding` no exige que `mission/init.c` tenga el mismo hash que el `init.c` del repo; hoy lo garantiza `copyfile`. Añadir una clave explícita en el manifiesto cerraría esa dependencia del preparador.

## Límites de esta revisión

- No ejecuté nada; no puedo afirmar que los nueve tests pasan, solo que su lógica es sustantiva.
- No inspeccioné el contenido de los npz ni decodifiqué alturas del WRP compilado; la sonda nativa es la única evidencia de ello.
- La resolución del float impreso por Enforce se asume en torno a 6 cifras significativas, suficiente a 1 cm para alturas de este mapa; la puerta de frontera a 5 mm con el mismo productor ya pasó.
- Esta revisión no acepta runtime, navegación, agua, colisión ni verificador de identidad de host.
