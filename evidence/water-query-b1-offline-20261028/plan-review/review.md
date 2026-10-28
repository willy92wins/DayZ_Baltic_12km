Tengo lo necesario: plan B1, padre, APIs reales en game.c, productor 2658, consumidor 2658, report A y dos filas de selected-points (292 positivo, 524 fallo seco). No requiero más lecturas.

## Veredicto: SOUND-with-fixes

El plan es implementable como misión diagnóstica y consumidor. No autoriza lanzamiento, no reetiqueta, conserva los 115 IDs y no convierte W>max(H,B) en expectativa. Hay tres huecos de diseño que, sin corregir, permitirían declarar CAPTURE_COMPLETE_DIAGNOSTIC_ONLY sin poder distinguir H3 ni detectar deriva de geometría desplegada. Ninguno exige nueva meta; son columnas, invariantes y un estado.

## Hechos verificados

- `P:/scripts/3_Game/global/game.c:1196-1202` coincide con el plan: SurfaceIsSea, SurfaceIsPond, GetWaterDepth(vector), y ambas GetWaterSurfaceHeight documentadas como "nearest water or object surface under a point, ignoring land". La declaración no acredita linking; el plan ya lo reconoce en la línea 111.
- `missions/BalticVisualProbeV1.BalticTrial/init.c:104-116` hace la primera carga WRP, espera 100 ms y recarga en el fotograma de consulta. El plan lo conserva (líneas 32-33).
- Report A: 43 fallos de agua con bed_delta 0.0 en los 43; 47 positivos; 68 unión; producto INCONCLUSIVE_PRODUCT_REFERENCE; tree_geometry NOT_EVALUATED. El aplazamiento de B2 es correcto.
- ID 524 en selected-points: ground 6.835, effective_bed 6.951, water_ext 6.824, expect dry, FAIL de agua con depth>0 en H+0.01. Este dato es la razón de que el hueco 1 sea decisivo.

## Hallazgos

**1. NEEDS-FIX. Sin columna de clase de superficie, H3 no es contrastable.** Plan líneas 66-68 y 86-88. El plan registra nfHigh/nfLow/fakeHigh/fakeLow y residuos, pero no define contra qué se compara cada valor devuelto. En 524 el lecho B=6.951 está 0.127 m sobre la lámina W=6.824 y 0.116 m sobre H; si la función devuelve el objeto del kit, surface≈B y depth desde H+0.01 sale ≈0.106, compatible con el residuo dry/FAIL 0.12-0.16 del report A. Sin una clasificación preregistrada, el consumidor mostraría filas pero nadie podría decir si "surface" es agua o lecho, y el estado CAPTURE_COMPLETE quedaría declarado con la pregunta central abierta.
Corrección mínima: columna `surface_class` por cada una de las cuatro consultas, con bandas fijadas antes de medir y no exclusivas: |v−Wref|≤0.05 → WATER_REF; |v−B|≤0.03 → BED_OBJECT; |v−H|≤0.01 → GROUND; dos o más → AMBIGUOUS; ninguna → OTHER. Las bandas reutilizan las tolerancias ya existentes y no las relajan. Además, registrar los GetShapeName de los objetos devueltos por GetObjectsAtPosition en radio 2 m alrededor del punto, como ya hace el productor 2658 con los impactos en `init.c:126-130`. Sin objetos nuevos ni rayos.

**2. NEEDS-FIX. Deriva de Ground/Roadway no puede quedar en INCONCLUSIVE.** Plan líneas 93-96. Si Ground difiere de A más de 0.01 o Roadway decisiva más de 0.03, el contenido desplegado no es el que A proyectó y las columnas de agua pierden su vínculo. El texto actual deja esa situación caer en "confusor/cobertura física abierta", que conserva el diagnóstico como usable.
Corrección mínima: añadir estado `REFERENCE_MISMATCH` o incluirlo en INVALID_EVIDENCE; cualquier ID con Ground o Roadway decisiva fuera de banda invalida el run completo para uso diagnóstico, no sólo la fila. Añadir el negativo correspondiente a la lista de la línea 105.

**3. NEEDS-FIX. Faltan invariantes entre rondas.** Plan líneas 55-59. Tres rondas sólo aportan información si se exige que H, Roadway, sea, pond, cuenta de objetos y los ecos de coordenadas sean idénticos entre rondas para el mismo ID; cualquier diferencia debe marcarse como confusor explícito y bloquear CAPTURE_COMPLETE. Hoy el consumidor sólo exige IDs/rondas exactos y relojes no decrecientes. Las columnas de agua sí pueden variar entre rondas; ésa es la variación temporal que se quiere observar.

**4. Fix menor. Testigo de fase de oleaje.** Plan línea 57. GetTime() es entero en ms y será igual antes y después dentro de un fotograma; esa igualdad es necesaria pero no demuestra que el fake wave no haya cambiado de fase. Registrar SurfaceGetSeaWaveCurrent() antes y después de las consultas (`game.c:1195`) y conservar ambos valores. Si difieren, el grupo queda INCONCLUSIVE como ya prevé la línea 90.

**5. Fix menor. Controles positivos sin predicción preregistrada.** Plan líneas 43-45 y 54. Los 47 positivos son todos vértices del kit. Para separar "agua" de "objeto" hacen falta dos clases de control que ya existen en los datos: puntos con water_ext null y lecho presente, como 292, donde H3 predice surface≈B y las demás predicen valor no finito u OTHER; y las tres referencias marinas sin objeto, donde todas predicen WATER. Añadir a las referencias marinas, en el mismo fotograma, WithFakeWave y depth desde nivel+0.25, no sólo NoFakeWave desde y=100 como en `init.c:150-152`. Escribir en el plan la tabla hipótesis×clase de control×resultado esperado antes de implementar.

**6. Fix menor. Origen S+2 sumergido.** Plan línea 66. Si en algún ID Wref>S+2, el origen bajo queda bajo el agua y el valor no es comparable con el alto. Preregistrar esa condición como columna `low_origin_submerged` en lugar de interpretarla a posteriori.

**7. Fix de documentación.** Plan línea 26 cita SurfaceRoadY3D(float,float,RoadSurfaceDetection); la firma real en `game.c:1178` es (float x, float y, float z, rsd). Corregir el [EXACT].

**8. Fix menor. Vínculo CSV→A.** Plan líneas 74-75. Hashear el CSV no demuestra que sus filas provengan de A. El preparador debe generar el CSV desde selected-points y el consumidor comprobar fila a fila que ID, x, z serializados float32 coinciden con A y que la expectativa original se copia sin cambio.

## Lo que está bien y debe quedarse

- Orígenes Y0/Y1/Y2 y S=max(H,B) como estímulos sin reclasificación (líneas 63-65). Para los 41 mojados con B>W, Y1 queda sobre la lámina y una profundidad positiva ahí falsaría "agua=water_ext" sin tocar etiquetas.
- Prohibición de usar las consultas bajas como rayos de aceptación (línea 67).
- Informe original siempre FAIL, producto INCONCLUSIVE, B2 pendiente, nunca mapa PASS (línea 96-97). Ningún estado del plan autoriza cambios de generador.
- Presupuesto: 345 puntos a dos fotogramas más 100 ms caben en 180 s con margen.
- Lista de negativos de la línea 105-109, ampliada con los de los hallazgos 2 y 3.

## Impacto si se implementa sin los fixes

Se obtendría una captura válida de esquema que no puede separar objeto de agua ni detectar contenido desplegado distinto de A. Con los fixes 1-3, B1 responde a H1/H2/H3 en términos de clases preregistradas y deja B2 exactamente donde el plan lo sitúa.

FIN_REVISION