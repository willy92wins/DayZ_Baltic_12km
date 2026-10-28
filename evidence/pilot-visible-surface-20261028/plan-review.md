Tengo todo lo necesario; redacto el veredicto.

**Veredicto: SOUND-with-fixes.** El plan es viable, no toca alturas ni compila, y su marco (categorías relativas al terreno fuente, sin pedir validación visual para cerrar el censo) es correcto. Hay cinco fixes mínimos antes de código y varias observaciones.

**Hechos comprobados**

- `deployed_surface_inventory_ev112.py:154-155` sólo conserva caras Roadway y caras Visual con material de agua. El lecho Visual (`streambed_leaf_long_straight.rvmat`) no está en los 539009 prototipos. El plan acierta al exigir relectura; `extract()` ya recorre todos los LOD, así que el cambio es añadir un `kind` para el material de lecho, no un lector nuevo.
- En la fuente, Roadway lecho y Visual lecho usan los mismos `bflat,bt` (`continuous_stream_pilot_v31.py:372` y `:383`). La equivalencia que el plan quiere enumerar es cierta por construcción en MLOD; lo que falta probar es que el ODOL la conserve. Correcto no asumirlo.
- CAP: 8 filas fuera del NPZ sólo en `start==0` y en el último chunk (`:345-362`), desplazadas por la tangente del extremo con mezcla `smoothstep(d/8)`. Las juntas entre chunks comparten fila exacta, no se solapan.
- Firmas de LOD en la fuente: Visual 0, Geometry 1e13, Memory 1e15, Roadway 3e15 (`:367-384`). Lector MLOD existente con esquema de 4 LOD en `screen_shapes_ev112.py:93` y lectura de triángulos en `audit_stream_visibility_ev112.py`. No hace falta inventar fuentes vanilla.
- Terreno fuente: `road_surface_overlay_ev112.py:240-242` ya verifica `terrain-buried.npz` byte‑exacto contra el WRP editable. Etiqueta "relativo a terreno fuente exacto" sostenible.
- Agua nominal: plano por celda en `footprint.npz` 084171b0, POND si finito, SEA en otro caso (`:279`); el 0.75 aparece como nivel de mar en `water_constraint_diagnostic_ev112.py:202`. Coherente con el plan.
- Sitios: el directorio fuente contiene 139 `cs_kit_7_*`, 26 `cs_kit_118_*`, 9 `cs_65p0_0_*`, 27 `cs_131p0_0_*` = 201. Los 62 SIN_CANDIDATO son exactamente kit118 + los dos cauces cortos.

**Fixes mínimos**

1. **kit118 está fuera de los 139 por construcción.** El candidato 1e85c73f cubre sólo kit_7. El plan dice "no prometer que arregla kit118"; debe decir que no puede tocarlo, y que los 6 cortes de carretera 76 caen íntegramente en SIN_CANDIDATO. Nombrar los cuatro sitios con sus recuentos (139/26/9/27) en lugar de "ambos cauces".
2. **Consumir la exposición Roadway ya publicada antes de medir el Visual.** `pilot-road-overlaps.json` tiene estado PILOT_ROADWAY_OVER_REFERENCE_ROAD_NOT_VISUAL_EXPOSURE_PROOF y `exposure()` (`road_surface_overlay_ev112.py:127-137`) ya clasifica EXPOSED/BURIED/CONTACT a lo largo de la arista. Dado que Roadway lecho ≡ Visual lecho en fuente, ese resultado sobre las aristas 124‑129 es la primera prueba a reproducir: si el ODOL conserva la equivalencia, la categoría del Visual sobre el eje queda determinada sin medir de nuevo. El plan debe declararlo como control positivo, no ignorarlo.
3. **Definir "superficie efectiva" con oclusión por agua Visual del piloto.** Lecho sobre H pero bajo la lámina de agua Visual (W) no es saliente visible. El plan la "conserva" pero no la usa en la categoría. Añadir APARENTE_BAJO_AGUA_PILOTO como categoría separada, evaluada contra el agua Visual real, no contra W nominal del campo.
4. **Cita de corredor.** `verify_roads_v30.py` define ±4 m en `:6` y `offsets` en `:56`, no `:59`. Además ese gate muestrea 17 puntos a 0,5 m; el corredor del plan es continuo. Decirlo para que nadie herede su muestreo.
5. **Extremos analíticos: exigir prueba de planaridad.** B−H y B−W son lineales por sub‑polígono sólo si cada cara de lecho es un triángulo plano; `strip_faces` (`:150-153`) emite triángulos, pero el ODOL puede retriangular. El consumidor debe comprobar triángulo por triángulo que la cara es plana antes de tomar extremos en vértices; si no, INCONCLUSO para esa cara.

**Observaciones sin bloqueo**

- **Costo.** ~201 modelos × ≤39 columnas × ≤21 filas × 2 ≈ 3×10⁵ triángulos de lecho de ≤1 m contra caras nativas de 6 m: ≤4 cortes por triángulo. Cabe holgado en 600 s/2 GiB con partición por modelo; el preflight de 120 s basta para contar caras y hashes.
- **Degeneraciones a cubrir en fixtures:** triángulos de área ~0 en el cap de extremos (half=2.25·0.015 en agua, `:322`), pliegues de cinta en curva pese al límite `apron>4` (`:293`), y filas CAP que retroceden sobre el cuerpo si la tangente del extremo no es colineal con el eje. El plan lista "piezas superpuestas"; añadir estas tres concretas.
- **Roadway como Visual.** El plan lo prohíbe correctamente. Con fix 2, Roadway se usa sólo como control de equivalencia, nunca como sustituto.
- **Condiciones para la siguiente reparación.** La tabla debe separar: (a) lecho seco expuesto fuera de posiciones fijas → reparable por Y seca; (b) CAP expuesto → requiere decisión nueva porque el plan aplazado congela las 8 filas; (c) agua Visual sobre carretera → cruce, no reparación de lecho. Hoy el plan mezcla (b) con "posiciones fijas" sin señalar que su reparación exige reabrir una protección.
- No se afirma exposición visual ni causa de kit118; correcto. La cercanía 14,6 m de eje no identifica la captura.

FIN_REVISION
