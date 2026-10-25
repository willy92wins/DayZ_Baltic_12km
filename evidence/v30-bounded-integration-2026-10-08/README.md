# Baltic: preview combinada de smoothing, 08-10-2026

**Construida y leída en DayZ; revisión cruzada y aceptación final pendientes.** Continúa la petición de Guillermo de trabajar autónomamente sobre orillas, cauces y relieve. Base real `ae77c9f`, worktree `claude/codex-handoff-review-74f290`. No se sustituye v29-base ni los paquetes anteriores.

## Artefacto utilizable

`P:/Mods/@DayZ_Baltic_BoundedSmoothingPreview`:

- Mundo: `9768119eb687517957831f126156fb1707c954ebac76b6dc271d57bef33421aa`.
- Agua: `07c5295f112746d621e96324467b1d54fccc415a785c227feb245f59adff503f`, idéntica a V12.
- Terreno combinado: `E:/DayZ-Baltic-Build/v30-bounded-integration-20261008/combined/terrain_inland.npz`, SHA256 `a292b6c39ad5c4fa19936e5498dc0ddaa064ee6ce4ecdb3115a763a3f0bc57c1`.

Comparación íntegra de 6.827 entradas: cambia únicamente `baltic_trial.wrp`. Configuración, 4.775 materiales, 2.048 texturas y navmesh antigua exactos. Paquete contrastado contra el árbol compilado nuevo y despliegue contrastado por hash. [Recibos](reports/deploy-receipt.json), [diff completo](reports/pbo-diff.json), [contenido compilado](reports/pbo-verified.json).

## Luga y relieve

El mecanismo nuevo limita el delta de cada vértice a la mitad de su separación vertical original respecto a **todos** los planos de agua incidentes. No recibe las estaciones de aceptación. El redondeo float32 va hacia la altura original si el más cercano cruzaría el límite exacto; después se mantiene el guard de caras secas. No se alteran sigma, clases, niveles ni excepciones geográficas.

La primera ejecución detectó dos redondeos que excedían el límite: se corrigió el redondeo, sin aumentar tolerancias ni generar un candidato intermedio. 1.347 vértices acotados, 594 redondeados hacia dentro, 5.557 cambios finales de orilla; cero caras restauradas en el último guard.

| Prueba congelada | V12 | Nuevo |
|---|---:|---:|
| Zigzag RMS, 13.197 estaciones originales | 0,640431 m | 0,497219 m (−22,36 %) |
| Zigzag RMS, 13.180 estaciones intercaladas | 0,640131 m | 0,486893 m (−23,94 %) |
| p90 del desplazamiento, ambos conjuntos | 2,375 m | 2,125 m |
| Nuevas estaciones sin cruce individual | — | 0 en ambos |

Todos los sectores oeste/centro/este pasan por separado. Hay 140 estaciones sin cruce heredadas en cada conjunto: no se interpreta como cobertura total ni como huecos físicos. Negativos: el candidato anterior viola la cota; una edición de cara ajena se rechaza; V12 sin smoothing no acredita mejora. [Verificación](reports/verification-r2-margin-verification.json), [cruces medidos](figures/shore-crossings.png).

El relieve seco conserva el candidato ya probado: curvatura local −21,02 %, altas −10,21 %, llanos −25,92 %; delta local ≤1 m y cambio regional de 180 m ≤0,066013 m. Cambia 2.494.070 vértices. La composición no comparte vértices **ni celdas nativas** entre los dos cambios. Todos los soportes de los 1.714.505 probes de orilla quedan idénticos al candidato de orillas. Carreteras: **77.381 estaciones PASS, resultado idéntico a V12**. [Integración](reports/combined-verification.json).

Puertas generales: **FAIL heredado idéntico a V12**, no PASS global. Permanecen un vértice de calado, 21 esquinas de piezas y la comparación histórica de Narva contra V29. Se verificó la identidad exacta de los fallos de calado/esquinas, además de los recuentos. La primera llamada vial usó por error la máscara histórica `v29`: se conserva `roads-combined.json` como diagnóstico descartado; la aceptación usa la máscara de agua V12 congelada, como la prueba anterior.

## Render y alturas

[Comparativa de tres distancias](figures/render-tres-distancias.png), [datos y comprobaciones](render-comparison.json). Misma misión de aparición directa (6081,4966), matrices exactas, viewport real 1920×1080 y mediodía leído en ambos runs. FOV solicitado 1,1955505 rad; no hay lectura nativa de FOV. Distancia de cámara al punto observado: 71 / 284 / 1.134 m.

V12 `24eed80e-9172-4790-aaee-7b35881e1cea`: 121 muestras de ventana, todas con foco. Preview `13e8ac2f-21a1-4ba2-8c36-34cd60e26564`: 208, todas con foco. Registro desde antes del lanzamiento, muestreo aproximadamente cada 1,3 s; máximos huecos 2,74 / 1,36 s. No se tomó el foco por script. La primera sonda seguía al servidor porque usa el mismo ejecutable; ese run se cerró ordenadamente y se repitió con selección por el argumento real `-connect=127.0.0.1`.

Cerca y media: ROI seca con índice de bloques planos azulados 0 en ambos paquetes. Lejos: **0,2396 / 0,2370**, por encima del umbral histórico 0,2, aunque se ven patrones de textura. La aceptación a larga distancia queda **INCONCLUSA**; no se adapta el umbral al resultado. No confundir igualdad entre paquetes, niebla, mipmaps y ausencia de textura; tampoco un fotograma estático con proceso colgado. El fallo gris intermitente previo no queda resuelto ni atribuido causalmente al foco.

Alturas leídas exactamente iguales a la fuente nueva: (6060,8346)=58,361595; (6324,8190)=17,653690; orilla (9492,2076)=3,6440885 m. Cada una rechaza la altura V12 anterior. La consulta submarina (10290,3918) devuelve `fresh_water_ext`, 3,15 m: es agua, no prueba del fondo; `MCPBridge.c:1355` usa `SurfaceGetType`. Vista remota del Luga texturizada antes/después de acercar al jugador, cámara idéntica; no reproduce la demora anterior.

## Navegación del combinado

**6/6 PASS**, 1.649 muestras físicas y 820 m nominales en los tres sectores, ida y vuelta. Salud 600 constante; desvío máximo 3,356 m frente a 7 m; distancia máxima a puntos intermedios 0,861 m frente a 7 m; error máximo del suelo contra el ASC nuevo 0,00000142 m frente a 0,002 m. Movimiento continuo con motor/marcha/hélice durante 98–108,5 s por caso. [Verificación](boat-verification.json), [log original](boat-runtime.log).

Mismo controlador, misma misión y seis rutas/criterios congelados. Dos sectores tienen celdas próximas editadas (8 y 2); por eso se repitió la prueba. Referencia [boat-reference.json](boat-reference.json). El consumidor es el mismo V2 ya contrastado con un positivo y 18 negativos en la unidad anterior; no se cambió para esta ejecución. Alcance: lancha vacía, sectores seleccionados; no giros completos, tripulación, anchura entera ni todo el mapa.

Run `56c5303a-c4c5-47e4-8b0b-f449987f94da`, DayZDiag 1.29.163709, servidor solo. Cierre ordenado confirmado, lease liberado, ambos MCP ven banco libre. Una caducidad de lease durante análisis offline se recuperó adoptando el mismo run, sin reiniciar. [Ciclo de vida](lifecycle.json).

## Revisión, límites y continuación

La revisión de otra familia está pendiente. El control automático **rechazó ejecutar Claude CLI** porque suponía enviar archivos privados a Anthropic sin autorización explícita para ese destino. El usuario recibió una pregunta con los archivos de [review-brief.txt](review-brief.txt); no se ejecutó ni se buscó otro canal. El candidato queda disponible para revisión, sin promoción a base aceptada. La revisión del commit congelado está prevista por `workflow.md`, sección 4.

No se han cambiado las decisiones de nivel: tramos bajos/Narva, finales que requieren estrechar el río, RIVER_80, lagos 269/170 y aceptación visual siguen el orden y las decisiones pendientes de `HANDOFF.md` y `plans/v30-rumbo-agua-1.0.md`. Terrain Builder y navmesh nueva dependen de congelar esa geometría; la navmesh incluida no valida estos cambios. Esta unidad no declara terminada la base 1.0.

Código nuevo: `tools/terrain/bound_shore_margin_v30.py`. Productores y consumidores de esta unidad quedan junto a este documento; los NPZ y temporales grandes permanecen en E:, con rutas/huellas en [artifact-locations.json](artifact-locations.json). No borrar carpetas de construcción con junctions.
