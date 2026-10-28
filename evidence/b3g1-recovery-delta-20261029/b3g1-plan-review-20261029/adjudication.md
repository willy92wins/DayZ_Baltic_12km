# B3G1 — adjudicación del plan

Fable5.1 nativo67.328s, completo, sin tools/denials y entradas intactas.
1. Aceptado dividir expresión como hipótesis, no compilación probada. Las otras
   líneas no quedan certificadas por no ser el primer error. Log filename y
   CreateCustomMission se conservan; misma nueva misión en ambos brazos.
2. Aceptado normalizar únicamente wait_for_box_s con int/float finito==600,
   excluyendo bool y strings. Añadir negativos string600.0 y600.0000001.
3. Aceptado heartbeat concurrente después de adopción y timestamps persistidos.
   Corrección a la revisión: FIFO del lanzamiento no tiene lease nuestro; el
   launcher oficial lo gestiona. No se debe preadquirir ni mandar heartbeat de
   un token anterior durante admisión. La tarea heartbeat comienza tras adoptar
   exactamente el run devuelto y termina sólo después del cierre/release.
   functions.exec admite awaits y setTimeout; una tarea concurrente puede vivir
   mientras se esperan tools, pero debe ser awaitada para no perderse al salir.
   La implementación específica seguirá pendiente de code review y negativos.
4. readyUTC = primera observación host UTC de server peer BOUND/versionok/poll<10s;
   persistir entonces deadline=ready+180s. Revisar error fresco de misión exacta
   antes de la captura. La readiness sola no prueba compilación.

Autorizado implementar offline; no nueva admisión hasta preparador/coordinador
revisados. No se repiten B3G R0 ni sus scripts. Umbrales físicos intactos.
