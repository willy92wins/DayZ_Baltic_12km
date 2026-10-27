**Veredicto: SOUND-with-fixes.** El código y el contrato son coherentes con el plan reconciliado; no encuentro falsos verdes ni defectos que impidan el único run. Dos ajustes menores, no bloqueantes.

**Verificado contra fuentes reales**

- `GetObjectsAtPosition` es círculo 2D (game.c:918-923), por lo que `Vector(x,0,z)` radio 40 en init.c:32 es correcto. La variante esfera es la 3D (game.c:930), no usada.
- `SurfaceRoadY(x,z)` sin tercer argumento usa LEGACY por defecto (game.c:1177). init.c:123,128,153 cumplen el contrato del plan.
- `SampleNavmeshPosition` deja el parámetro de salida intacto al fallar (aiworld.c:120). init.c:140-143 inicializa a cero y verify:86 exige `[0,0,0]` en el control NONE. Correcto.
- `FindPath` devuelve bool con waypoints incluyendo extremos (aiworld.c:95-98). `comparable` exige `count>=2` (verify:88), consistente.
- `GetShapeName` y `ModelToWorld` existen con las firmas asumidas (object.c:503,873).

**Anclaje**

- Orden de consultas idéntico entre init.c:83-93 e verify:47-51: índice par izquierda, impar derecha, 48 negativo con ancla 0 y q=-6 en ambos.
- Unicidad: init.c:97-107 cuenta solo objetos con modelo esperado y distancia 3D ≤0,05 (0.0025 al cuadrado); vecinos lejanos no son duplicados, como pide el plan. Falta o drift aborta sin sustitución.
- verify:57-59 ata expected al histórico (≤.011), actual al histórico (≤.05) y origin a actual. verify:60-66 comprueba ejes no degenerados y reconstruye rawStart/rawGoal desde origin+q·axisX+z·axisZ. Ejes 10 m / 0.1 en init.c:113-118 coherentes.
- Los 24 shapes de anchors.json ya están en minúsculas; init.c:100-102 baja el nombre actual y compara con el CSV literal.

**Parseo y comparación**

- Cabecera, UUID, 24/49, END;49, esquema de A(19)/Q(10)/P(7), cursor exacto al final (verify:95). Vectores `<x, y, z>` se parsean como en el log Nav12 real.
- Extremos: verify:75 exige `[rawX, road+.2, rawZ]`, igual que init.c:134-135. Endpoint XZ>2,1 y rutas no encontradas quedan no comparables pero con sus puntos preservados (verify:94).
- Umbral 0,801 aplicado a |NavY−RoadY| por waypoint; |RoadY−GroundY| registrado como discriminador y `raised_waypoints` solo informa cobertura. El test `test_height_equal_ground_road_still_fails` fija que RoadY=GroundY no exime. Correcto.
- `acceptance_eligible=False` siempre; los límites declaran la diferencia de fuente Y respecto a Baltic.

**Release / lifecycle**

- prepare.py:22 convierte la captura a `^END;[0-9]+$` y 300 s; los reemplazos de 607/900 solo afectan las líneas esperadas (líneas 6,14,16,18,24 del original). AbortProbe escribe END;<índice> y verify lo rechaza. La captura termina incluso con abort.
- finish.py: reemplazos `==4`→`==1` y `==607`→`==49` tocan únicamente las líneas 24-25 del original; la aserción de versión se sustituye por `version_state=='ok'`. Revalidación de inventario vanilla exacto (glob vs lista, hash por PBO) antes de host-identity.
- Host identity count 1 es consistente con Nav12 (4 = bridge + 3 PBO del extra_mod, ahora `extra_mods:[]`).
- Orchestrator: exige accepted.json ACCEPTED_AFTER_REVIEW y hashes congelados antes de lanzar, modo servidor, sin navmesh_data_server, ejecutable fijo, un solo paquete, cliente no iniciado.

**Defectos concretos (fixes menores)**

1. **verify:45 pierde la causa del abort.** Con `END;<n>` distinto de 49, el result.json solo dice `Incomplete capture`; la fila `FAIL;<name>;<reason>` (p. ej. ANCHOR_NOT_UNIQUE_OR_DRIFT y qué ancla) no se refleja. runtime.log sí la conserva, así que es diagnosticable, pero conviene incluir la última fila FAIL en `error` para que INCONCLUSO sea autoexplicativo.
2. **init.c:102 compara `expectedShape` sin ToLower.** Hoy es inocuo porque anchors.json está en minúsculas y congelado, pero verify:55 sí normaliza; asimetría de robustez. Fix de una línea: `expectedShape.ToLower();` tras init.c:88.

**Observaciones no bloqueantes**

- finish.py:20 y :30 repiten la misma aserción de `version_state`; inocuo.
- Si el control NONE falla, verify lanza y toda la captura queda INCONCLUSIVE_INVALID_CAPTURE sin `routes`. Es lo que lista el plan (línea 115) y el log crudo se preserva; lo señalo como decisión consciente, no defecto.
- `CloseFile` por tick en init.c garantiza que el log esté completo cuando la captura ve END.

**Recapitulación.** Código, contrato y pipeline de lanzamiento/consumo coinciden con el plan: anclaje estricto sin sustitución, parseo defensivo, 49 consultas preservadas, umbral 0,801 sin interpretación de imposibilidad, sin aceptación Baltic. Los dos fixes son opcionales y de bajo riesgo; si se aplican, hay que recalcular los hashes de init.c y verify antes de sellar deployment/frozen/accepted.