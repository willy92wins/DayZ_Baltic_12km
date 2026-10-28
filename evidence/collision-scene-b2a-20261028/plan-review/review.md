**Veredicto: SOUND-with-fixes.** La unidad está bien acotada (no reetiqueta, no toca mundo, cobertura explícita, hulls como superconjunto), y el presupuesto es viable: el censo anterior leyó 5443 modelos completos en 39 s / 272 MB (`deployed-surface-prototypes-20261028/report.json:3,21-22`). Hay un hueco de corrección que puede fabricar separaciones falsas y varios huecos de trazabilidad. Ninguno exige otra arquitectura.

## Hallazgos

**1. [ALTA] El marco de los vértices ODOL respecto a la traslación WRP no está verificado; una separación CLEAR puede ser falsa por un desplazamiento de metros.**
- Plan línea 25-26 y 68-76 asumen `vertices @ R + t` como pose completa. Esa convención sólo se ha usado en `deployed_surface_inventory_ev112.py:82-85` para prototipos, cuyo propio estado es `PROTOTYPES_ONLY_NOT_WORLD_OVERLAY` (report.json:2,15). Nunca se ha superpuesto geometría en mundo ni comprobado contra nada nativo. `extract()` lee `bounding_center` pero no lo aplica a los vértices (`:168-170`); sólo lo usa como hipótesis para proxies.
- Contraejemplo reproducible con datos ya cerrados: en el snapshot B1 del punto 700 (`water-query-b1-native-20261028/observations.json:740-745`) la instancia `t_fagussylvatica_3fb_summer` tiene GetPosition Y=18.889 con suelo ≈8.0 (:2925). Si la traslación WRP de esa fila coincide con 18.889, el origen del objeto está ~10.9 m sobre el suelo, lo que es coherente con vértices ODOL centrados en `bounding_center` (base del tronco en Y≈−10.9 en modelo). Si los vértices Geometry decodificados del árbol tienen Y_min≈0 en vez de ≈−10.9, aplicar `@R+t` elevará el sólido 11 m y el origen bajo (max(H,B)+2 ≈ 10.0 m) quedará "libre" por un artefacto. El plan no contiene ninguna comprobación que distinga ambos casos.
- Mínimo fix: en el paso 2 añadir una verificación por modelo decodificado: bounds de vértices Geometry frente a `ModelInfo.bbox_min/bbox_max` y `lod.b_min/b_max/b_center` (`odol_reader.py:475-476,488,660-662`) bajo las dos convenciones (vértices tal cual; vértices + bounding_center). Para el árbol, comprobar además que Y_min(modelo)+t_y ≈ suelo (8.0±pendiente) con la fila WRP cuya traslación coincida con el GetPosition 18.889 de B1. Si la convención queda sin resolver para un modelo, construir las envolventes bajo ambas y exigir separación frente a la unión; de lo contrario POSSIBLE_OCCUPANCY. No cambia tolerancias físicas.

**2. [MEDIA] Trazabilidad del hecho "tres rayos altos a 17–19 m sobre B".**
- Plan línea 15-16 no cita fuente y `inputs.json` no la incluye. La fuente es `dry-road-full-native-diagnosis-20261028/report.json:852-968` (IDs 349, 350, 1425; `rv_delta_to_expected` 17.88, 16.67, 19.05; `bed` 8.045/7.982/8.025). El rango real es 16.7–19.0 m, no 17–19. "B" no se define en el plan; en la fuente es el campo `bed`. Además Bullet reportó la misma forma (`bullet_shape`, :867,892,967), no sólo RV; el plan sólo dice "rayos altos" sin consumidor.
- Impacto: el origen bajo `max(H,B)+2` depende de B; sin fuente fijada el ejecutor podría tomar otro B (por ejemplo el de B1) y violar la línea 55.
- Mínimo fix: fijar en Entradas la ruta y hash del report de diagnóstico, definir B=`bed` de esa fuente para los 5 fallidos, y declarar de dónde salen H y B para los 5 positivos (no aparecen en ese report; verificar que el result original 2658 los contiene antes de generar los 90 puntos). Corregir "17–19" a "16.7–19.0".

**3. [MEDIA] "Snapshot B1 de objetos" (línea 81) sólo existe para 2 de los 10 centrales.**
- B1 observó 115 puntos (`observations.json:6`). Entre los 10 IDs sólo 700 y 723 tienen registro con lista de objetos (:2903, :3641); 349/350/1425/348/311/701/725/1426 no aparecen en observations.json.
- Mínimo fix: declarar que la comparación descriptiva contra B1 se limita a 700/723 y que para el resto el único referente nativo es `rv_height`/`bullet_shape` del report de diagnóstico.

**4. [MEDIA] Modelos sin binding: falta regla de cobertura por origen.**
- El WRP tiene 5509 nombres (`deployed-world-geometry-discovery-20261028/report.json:4`); el censo anterior resolvió 5443 (`deployed-surface-prototypes-20261028/report.json:3`). Quedan 66 nombres cuya geometría no se leyó. Plan línea 45-46 dice "cobertura incompleta", pero sin bounds no hay broadphase posible, así que no se puede decidir si afectan a un origen.
- Mínimo fix: resolver los 66 desde PBOs vanilla instalados (línea 40 ya lo pide; cuantificarlo). Para los que sigan sin resolver, emitir por origen la distancia de la instancia no resuelta más cercana y marcar COVERAGE_UNKNOWN si esa distancia es menor que el mayor radio decodificado entre todos los modelos resueltos multiplicado por la escala máxima de su matriz; documentar que ese umbral es cota empírica, no prueba. No inventar extensión cero.

**5. [BAJA] Proxies: nombrar los marcos "documentados".**
- Línea 64-67 habla de "todos los marcos documentados" sin listarlos. Existen exactamente dos: la `Matrix4P` del proxy en el LOD (`odol_reader.py:33-44`) aplicada directamente, y la hipótesis del censo "vértices + centro del hijo, luego matriz" (`deployed_surface_inventory_ev112.py:88-92,192`). El LOD Geometry del haya instalada tiene 0 proxies (tree-source report :54), pero el censo encontró 65 caras de proxy condicional en otros modelos (:8).
- Mínimo fix: enumerar esos dos marcos y definir la envolvente como unión de ambas hulls; proxies con hijo no resuelto => COVERAGE_UNKNOWN para la instancia.

**6. [BAJA] Selección del LOD Geometry no existe en código previo.**
- `select_lods` (`deployed_surface_inventory_ev112.py:131-137`) sólo elige visual y Roadway. Geometry es resolución 1e13 (índice 4 del árbol, 1058 vértices / 1804 caras, report :50-56). Fire Geometry (1e15) y View Geometry (6e15) deben excluirse porque RaycastRV usa `ObjIntersectGeom` (`init.c:124`).
- Mínimo fix: constante GEOMETRY con comparación float32 exacta, exigir ≤1 LOD Geometry; modelo sin Geometry y sin proxies = vacío declarado, nunca libre implícito. Para componentes usar `NamedSelection.selected_faces/selected_vertices` (`odol_reader.py:254,258`), ya verificados en el árbol (78 componentes).

**7. [BAJA] Degeneraciones y float32.**
- Línea 75: "degeneración => INCONCLUSIVE". Un componente plano (hull sin volumen) lejos del punto hace que qhull falle y el origen quede INCONCLUSIVE sin motivo. Fix: si la hull falla, usar la AABB mundial del componente como superconjunto; INCONCLUSIVE sólo si el punto cae dentro o en margen de esa AABB.
- Línea 51: ±0.005 m en float32 a X≈8247 tiene ulp ≈0.001 m; el desplazamiento real será ≈0.00488 o 0.00586. Declarar los valores float32 efectivos en el informe, no los nominales.

**8. [BAJA] Lector fuera del worktree.**
- `odol_reader.py` vive en `C:/temp/moto_lanes/review_g3/tools/` y su hash está fijado sólo en tree-source report :164. La línea 104-105 exige Python del worktree. Fix: copiar o fijar hash `fa0d74b6…` en Entradas y ejecutar con `-I` pasando la ruta como argumento.

## Lo que está bien
- Separación estática sin equivalencia Bullet: correcto; RV usa Geometry (`init.c:124`), Bullet usa capa BUILDING (`:135`); el plan sólo compara descriptivamente.
- Broadphase contra todos los 2 578 398 objetos sin filtro de 40 m: viable con el lector OPRW ya validado (`package_visual_forest_ev112.py:29-75`, ancla id 16787372 verificada).
- Vegetación incluida: los 72 tipos son los `vegetation_not_inspected` del catálogo anterior (model-catalog.json, 72 ocurrencias); el plan debe tratarlos como mínimo, no como lista cerrada, porque ese catálogo nació de la selección espacial del puente.
- Árbol instalado ODOL56: el lector lo mapea a layout 54 (`odol_reader.py:1013-1014`) y los 8 LODs cierran `end_ok` (tree-source report). Usar `plants_bliss.pbo` de8c3d0d… por prefijo+entry como fija el plan.
- 90 estímulos y 10 centrales intactos, sin reetiquetado, sin tocar tolerancias.

## Resumen
El plan es ejecutable tal cual en cobertura y broadphase, pero el hallazgo 1 debe incorporarse antes de implementar: sin la comprobación de marco (bbox/bounding_center y base del árbol frente a GetPosition 18.889 de B1), cualquier CLEAR_OF_RESOLVED_STATIC_GEOMETRY podría ser un artefacto de 11 m. Los hallazgos 2-4 son correcciones de texto y de reglas de cobertura; 5-8 son precisiones de implementación.

FIN_REVISION