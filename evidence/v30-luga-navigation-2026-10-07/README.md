# Luga y navegación V12 — continuación del 07-10-2026

Encargo: «sigue con el plan». Base local `9e53b28`, mismo worktree de Claude. Sin subagentes, sin modificar v29-base ni publicar. [Plan congelado](plan.md).

## Smoothing del Luga: corrección probada, candidato rechazado

Los dos fallos anteriores tocaban celdas nativas con agua clase 2. Mantener inmóviles sus vértices de agua no bastaba: el piloto cambiaba vértices de tierra de las mismas caras y desplazaba el cruce. [Diagnóstico original](diagnosis.json).

`tools/terrain/limit_shore_faces_v30.py` conserva todos los vértices de las celdas que contienen agua ajena a la clase 3. La máscara sale de la clasificación V12; no de estaciones fallidas. Deshace 81 cambios del candidato 18-vector y deja 5.557 vértices modificados. No cambia sigma, niveles, clases ni añade superficie editable. Repite la protección frente a caras secas más inclinadas.

El verificador usa las cuatro esquinas de cada celda, independientemente de la dilatación del productor. Confirma metadatos, corredor congelado, exterior de la máscara y caras de agua ajena idénticos. Rechaza tanto el candidato anterior como un control que altera un vértice de lago. [Producción](scope-producer.json), [verificación](scope-verification.json).

| Conjunto fijado | Estaciones | Zigzag RMS antes → después | Cruces ausentes antes → después | Nuevos ausentes individuales |
|---|---:|---:|---:|---:|
| Original, paso 2 m | 13.197 | 0,6404 → 0,4563 m (−28,8 %) | 145 → 138 | 0 |
| Intercalado 1 m, independiente | 13.180 | 0,6401 → 0,4445 m (−30,6 %) | 144 → 141 | **2: FAIL** |

El percentil 90 de distancia al diseño baja de 2,375 a 2,125 m en ambos conjuntos. La mejora agregada no sustituye el límite local de ±8 m. Las nuevas estaciones fallidas son 5375 y 6730; se conservan sin excluirlas ni ampliar la puerta.

- **5375**, X 7702,875 / Z 2812,049: dos vértices secos bajan junto al lecho congelado. El cruce sobre la normal pasa de aproximadamente 5,31 a 8,94 m.
- **6730**, X 9464,735 / Z 2262,415: el perfil de una curva cambia también en sus cuatro vértices editables. El cruce sobre la normal pasa de aproximadamente 4,31 a 8,31 m.

Esas distancias son desplazamientos a lo largo de la normal de muestreo; no equivalen a una traslación perpendicular de toda la orilla ni a huecos de agua. El diagnóstico amplía la búsqueda únicamente para localizar el cruce; la aceptación sigue usando ±8 m y paso de 0,25 m. [Datos de las caras y perfiles](holdout-diagnosis.json), [figura](luga-holdout-fail.png).

Resultado: **FAIL, no integrado ni empaquetado**. Se agotó la corrección por mecanismo acordada para esta unidad. El siguiente paso requiere limitar el desplazamiento local del perfil en los contactos y curvas; no otro barrido de sigmas. Mantener los dos conjuntos de estaciones y revisar la sensibilidad de sus normales en los recodos antes de cambiar cualquier criterio.

Artefacto externo: `E:/DayZ-Baltic-Build/v30-luga-navigation-20261007/luga-scoped/terrain_inland.npz`, SHA256 `ee56a80296835cb3902c314fbaf9cdb3286d80832e0ae8a797e64c2693b28bc9`. Las estaciones completas y las máscaras están en esa carpeta de construcción y en el piloto anterior; los informes se conservan aquí.

## Navegación física

**PASS de los seis recorridos de lancha vacía**, con 1.648 muestras físicas. Salud 600 → 600 en todos; desvío máximo 3,325 m, menor que el límite de 7 m; todos los puntos intermedios visitados a menos de 0,734 m. El error máximo entre `SurfaceY` del motor y V12 es 0,00000137 m, inferior al límite de 0,002 m. Movimiento continuo con motor, marcha y hélice durante 98–108,5 s por caso. [Verificación completa](boat-verification.json), [log original](boat-runtime.log), [trayectorias](boat-trajectories.png).

[Referencia congelada](boat-reference.json): tres sectores, ida y vuelta, 820 m nominales en total. Aparición oeste/Narva: 130 m, mínimo nominal 1,575 m; Luga alto: 140 m, mínimo 2 m; Luga bajo: 140 m, mínimo 1 m. Puntos densos cada 0,5 m, rutas cada 4 m; coordenadas convertidas a float32 antes de congelarlas.

Se reutiliza la misión/autopiloto probado y el PBO de `@BalticBoatInputProbe`, sin editarlo. Solo cambian el nombre del log, el número de casos y las rutas. Una lancha vacía por caso, control de motor/timón y eliminación al acabar; ninguna posición impuesta durante la marcha. APIs reales leídas en `P:/scripts/3_game/vehicles/boat.c` (motor, marchas, hélice y combustible). La consulta de suelo usa la triangulación nativa independiente de `waterway_common.sample`.

Run propio `4e5cafa1-ae93-4cc7-8af8-85f8ad674971`, DayZDiag 1.29.163709, solo servidor. No se abrió cliente ni se tomó el foco. Lanzamiento público y adopción con lease; una caducidad durante lectura offline se recuperó adoptando el mismo run, sin reinicio. Final: cierre ordenado, línea de terminación del servidor confirmada, lease liberado, owner=null, runs=[], banco libre y cero comandos pendientes. [Lanzamiento](boat-launch.json), [ciclo de vida](boat-lifecycle.json).

Antes de lanzar se verificaron hashes desplegados: mundo V12 `f0813174…`, agua `07c5295f…`, controlador `c5414ffe…`; hashes completos en la referencia. La misión desplegada coincide byte a byte con `missions/BalticV12NavigationV1.BalticTrial`. El verificador conserva sus límites históricos: salud, continuidad, eje, puntos intermedios, controles, marcha/motor/hélice y suelo. Un control analítico conocido pasa; 18 alteraciones son rechazadas. [Controles del verificador](boat-verifier-controls.json).

Límite: seis recorridos de lancha vacía no aceptan todo el mapa, tripulación, anchura completa, giros ni el aspecto visual del agua baja. La profundidad registrada en la hélice no es el calado total del cauce. El arranque emite el diagnóstico `PluginConfigDebugProfile is not Registred` y avisos de configuración de misión/`pond`; no se afirma un arranque sin avisos.

## Estado que sigue vigente

La preview del relieve seco sigue en `@DayZ_Baltic_SmoothingPreview`, ya contrastada con V12 en dos poses y dos alturas leídas del motor: [evidencia anterior](../v30-smoothing-pilot-2026-10-07/README.md). No se mezcló con este Luga rechazado.

Teselas: la recuperación de textura sin foco y la aparición directa están documentadas en la sesión anterior; no hay prueba causal del foco ni aceptación completa cerca/media/lejos. Finales de río, agua baja/RIVER_80, lagos 269/170 y Terrain Builder/navmesh siguen abiertos. No se cambió material, textura ni configuración gráfica durante esta unidad.
