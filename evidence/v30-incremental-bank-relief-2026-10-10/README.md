# EV82-B: integración y límites

Estado vigente: geometría, superficie, paquete y lectura nativa completa verificados. Revisión independiente del PBO y de la evidencia nativa sin fallo bloqueante. No es aceptación de la base 1.0 ni del aspecto del agua.

## Corrección de mecanismo

EV81, calculado desde EV79, perdió mejoras EV80. EV82 usa EV80 como terreno inicial y referencia angular; EV79 mantiene el presupuesto acumulado de ±2 m, máscaras y suelo. EV82-A se rechazó por dos ángulos de referencia apenas superiores a 30°: el autor usaba un clasificador más estrecho que el consumidor y omitía protegerlos. EV82-B alinea solo las dos clasificaciones con el contrato existente. No relaja el límite de la propuesta ni el consumidor. El fixture reproduce ambas omisiones y su rechazo corregido.

## Evidencia ya verificada por root

- Consumidor independiente: 38/38 puertas, 3046 cambios frente a EV80, 4091 acumulados frente a EV79; 4329 nodos recorridos. Terreno `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`.
- Energía de aristas incidentes: −13,5023 % frente a EV80. Quiebros mixtos >30°: 3384→2597. Sin nuevos >30°, sin máximos de sector peores. El banco seco redistribuye curvatura: su media cuadrática aumenta 1,38947688→1,42257046; el p99 apenas baja. No afirmar mejora uniforme.
- Exposición real sobre modelos compilados: 11825 caras físicas y 16705 visibles en 1806 celdas; 0 m² ganados/perdidos. El WRP conserva exactamente 18033 objetos, materiales y cabecera del anterior.
- Comparación de 390924 píxeles de entrada afectados: 0 cambios mojados, 784 cambios de clasificación de orilla. Superficie regenerada: 462 teselas, 562 intactas por huella de entrada, 2324 solapes exactos. Los 2426 píxeles mojados no-grava tras compresión se restringen a la banda de borde; interior no-grava 0.
- Distribución creada: `P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1`. Mundo `b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c`; agua idéntica `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`. OPRW `3b12b21d554c6ab75d76c43b5ba902c9a1d49a26516bdd14b16f1a6048ba2539`. 91 PAA y WRP cambiados; 6735/6827 entradas intactas. 728 mips nuevos PASS con controles negativos y cuatro decodificaciones nativas aisladas.
- Preparador de prueba corregido en revisión root: ya no sobreescribe el verificador nativo reforzado. Guarda identidad de verificador y exige todas las puertas del consumidor antes de escribir misión. Misión preparada y validada: un archivo Enforce real, 4194304 vértices, 1212 puntos y 1205 planos; los 1212 puntos conservan altura prevista, pero el censo completo sí incluye los cambios nuevos.

## Límites y continuación

Lectura nativa terminada en 24,308 s, run `2d06c106-f70d-48ae-aff5-ab17fb42c8f9`: 4194304 vértices, 1212 puntos, 1205 planos; máximo error 1,52588e−5 m y siete controles negativos rechazados. En esta fase de mar: 0 flags secos nominales/dinámicos, 25 flags ausentes sobre clase de diseño mojada y 339 escalares sin flag. Frente a EV80 hay dos A y 275 Q nuevos; todos recaen sobre alturas intactas. No se interpreta la variación de fase como reparación. Snapshot `c0effbbcf0200bd916a691e94d44546bc573dc30a7c275b8049a8ad64b2863a2`.

Servidor cerrado por lifecycle guard con terminación orderly; lease liberado y banco libre. RPT conserva stack PluginItemDiagnostic, una instancia MCPPollCallback declarada como fuga al cerrar y errores de recursos: no se declara limpio. Los estados PREPARED de native-reference/native-scripts-provenance describen la preparación original y permanecen inmutables; native-verification, runtime-rpt-identity y lifecycle-close acreditan la ejecución posterior.

El diagnóstico de facetas incluye sus protecciones y grados de libertad. Una selección vacía de un detector de picos no demuestra ausencia de elevaciones piramidales; root rechazó la figura vacía y pidió perfiles residuales representativos y un discriminador local de factibilidad. No se autoriza otra variante global bajo el plan EV82-B.

Tres vértices que conservan los picos/escalones de los perfiles, (1146,1002), (2196,1566) y (2196,1572), están fijados por `wet_support`; el segundo además es agua y `other_fixed`. Sus alturas EV79/EV80/B son idénticas. Sus pendientes locales máximas son 30,494/32,459/32,459°. Repetir el selector seco no puede repararlos. El próximo diagnóstico estudia la factibilidad de cambios conjuntos manteniendo los contornos físicos y visibles, sin cambiar todavía geometría ni niveles. La única propuesta local encontrada en otro punto (5538,3918), +0,091957 m, pasa seis caras/doce bisagras pero mejora solo 0,953 % local y no se ha aplicado; no justifica otro recorrido a ciegas.

Rectángulos grises, agua aparente sobre tierra, contornos mojados y finales no quedan resueltos por estas pruebas. No hay run cliente pendiente de foco. EV68 y las excepciones de niveles no se promueven. Terrain Builder y navmesh final siguen después de congelar geometría.


Diagnóstico residual: `residual-review/residual-diagnosis.md`. Revisión independiente: `review-luna/review.md`, `compiled-package-review.md` y `native-evidence-review.md`. EV80 permanece disponible para rollback. No hay aceptación visual ni push.
