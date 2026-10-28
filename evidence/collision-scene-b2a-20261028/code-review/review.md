**Veredicto: SOUND-with-fixes.** No encontré ningún falso CLEAR ni error aritmético en `collision_scene_b2a_ev112.py`. Los defectos son de informe y alcance, no de la prueba de separación.

**Qué verifiqué en código (tools/quality/collision_scene_b2a_ev112.py)**

- Geometry exacto float32(1e13), ≤1 LOD, ODOL completo y sin errores (`geometry_lod`, :42-48). Fire/View excluidos.
- Componentes incluyen todos los vértices de sus caras; caras y vértices sin componente van a grupos residuales (:51-83). El haya tiene 78 componentes y 78 grupos, es decir, 1804 caras cubiertas sin residual.
- Broadphase conservador en float64 con inflado sólo aritmético, sobre todas las poses por bloques de 65536, con la unión raw ∪ raw+bounding_center (:86-98, :360-366). Sin radio empírico.
- Separación: direcciones de hull sólo como candidatas; mínimo verificado contra todos los vértices con cota 64·eps más error de transformación; hull degenerada cae a ejes AABB y dentro queda INCONCLUSIVE (:101-135, :442-449).
- Rayos: todos los impactos por abanico, arista o vértice marcados AMBIGUOUS, verticales o degenerados INCONCLUSIVE, cuadriláteros condicionados, sin elegir altura (:150-187). hits.json conserva entradas sin altura (INCONCLUSIVE_VERTICAL_OR_DEGENERATE) y duplicados por componente.
- 90 estímulos = 10 centrales × 9; central float32 idéntico al original; H/B del result 2658 fijado; estados originales inmutables (:190-213, pins :303-304 y :417-419).
- Proxy desconocido o no vacío bloquea todo (`origin_state` :291-298); proxies recorridos en todos los LOD (:255-260). Los 7 proxies hallados son streambed de dz/water con geometry_resolution null y 0 vértices.
- Paquetes: prefijo+entry desde la tabla PBO normalizada, rutas duplicadas rechazadas, hash de cada PBO, payload WRP dentro del PBO comparado con el fichero (:216-241, :305-316). Catálogo 5509 cotejado por índice, nombre e instancias.
- Lector ODOL fijado por 3 hashes; `Proxy.model`, `selected_faces`, `selected_vertices`, `lod_end_ok` existen en odol_reader.py.

**Evidencia (R/collision-scene-b2a-20261028)**

- report.json: 5509/5509 decodificados, coverage_unknown vacío, 4 candidatos, 90 CLEAR_UNDER_FRAME_HYPOTHESES, 1106 contactos, 25.86 s / 520 MB. tests.log: 31 OK.
- points.json: 4185 pruebas, todas SEPARATED; ninguna POSSIBLE_OCCUPANCY ni INCONCLUSIVE; ningún margen < 0.1 m. Margen mínimo del tronco frente al origen bajo de 349: 1.58 m en z.
- Los 10 IDs están en un radio de ~2 m (x 8246.9–8248.0, z 8938.0–8939.0), por eso sólo 4 instancias son relevantes.
- Dato descriptivo fuerte que el informe no explota: para 349 central, el impacto superior del haya en marco raw es 25.928134 y el RV nativo midió rv_pos.y 25.928129 con el mismo shape; el kit cs_kit_118_0000 da impacto exactamente en B 8.044922. El motivo nativo del FAIL es "RV_height_identity_or_ray_position", es decir el rayo alto H+100 queda bloqueado por la copa, no el origen bajo. El marco raw+bounding_center produce 0 de 1106 contactos y sólo 360 pruebas whole_model (todas fuera de AABB).

**Bugs y fixes mínimos**

1. **Alcance incompleto (plan §5-6)**: no existe la salida "diferencias de impacto por 10 centrales". `run()` :404-416 sólo compara poses; report.json carece de comparación impactos vs rv_pos/bullet_pos. Contraejemplo: id 349 tiene 2 impactos de haya, 2 del kit y varios INCONCLUSIVE, pero ningún fichero los pone junto a 25.928129/26.062355 nativos. Fix: emitir `central-comparison.json` con todas las alturas por ID, marco, instancia y estado, más los valores nativos, sin selección; y añadir en report.json `contacts_by_frame` y `proofs_by_frame`. Mantener el texto "descriptivo, no certificación de marco".

2. **Informe induce a error sobre el segundo marco**: "contacts: 1106" sugiere que ambas hipótesis se ejercitaron contra caras; en plus_bounding_center ningún candidato cubre el XZ de los puntos (p. ej. kit 0000 z_max 8937.45 < 8938.498). El CLEAR de ese marco se apoya sólo en exclusión AABB, lo cual es válido pero debe declararse. Fix: desglose por marco en `limits`/report (misma línea que el fix 1).

3. **snapshot-pose-comparison.json engañoso** (:405-416): `nearest_candidate_instance` se busca sólo entre los 4 candidatos, así que árboles del snapshot a 15–48 m se asignan a 17228015 con delta 28–48 m. Un lector podría leerlo como desacuerdo de poses. Fix: buscar entre todas las instancias del mismo índice de modelo usando `order`/`starts`, informar coincidencias exactas (≈3e-7) y no coincidencias por separado.

4. **Comprobación de terreno no independiente**: `terrain_at_offset` del central 349 es 8.025211076407418, bit a bit igual a `expected.ground`, porque result 2658 usó el mismo `tri_h` sobre el mismo npz. La condición adjudicada "integrator-terrain" sólo es independiente para los 80 desplazados, y la identidad npz ↔ elevación del WRP compilado no se verifica (el lector OPRW no decodifica alturas). Impacto bajo: margen 2.0 m. Fix: añadir a `limits` que la holgura de terreno es relativa al npz fijado, no al terreno decodificado del WRP.

5. **Tests**: `test_unknown_proxy_blocks_clearance` sólo cubre hijo no vinculado; falta fixture de hijo con geometría no vacía que compruebe que `empty_proxy_tree` devuelve False y que `run` lo vuelca en `coverage_unknown`. Falta un test de `aabb_world` sobre la unión de ambos marcos. Menor; no afecta a la corrida.

**Lo que sigue siendo verdad y no cambia**: CLEAR_UNDER_FRAME_HYPOTHESES y OFFLINE_DIAGNOSTIC_ONLY no son PASS nativo ni autorización B2; Bullet, animación y dinámicos no están cubiertos (Bullet nativo 26.062 difiere 0.13 m del impacto Geometry); identidad vanilla de B1 no sellada; Original 47 FAIL / 21 inciertos intacto; las nueve regresiones abiertas siguen abiertas. No recalculé los SHA de inputs.json; leí los ficheros en las rutas indicadas.

FIN_REVISION