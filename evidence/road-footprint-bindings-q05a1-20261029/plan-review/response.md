## Veredicto: SOUND-with-fixes — CONVERGE condicionado

No apruebo medición, colocación ni reparación. Las 13 filas cuadran como datos guardados: 1 (`49/301`) + 6 (`71:370–375`) + 6 (`76:124–129`). Los frenos `measurement_ready=false`, `placement_ready=false`, `human_resolved=0`, `C1 NOT_REVIEWED` y “Q05A permanece fallido” evitan la falsa aprobación por volumen. Quedan correcciones previas obligatorias:

1. **Circularidad e integridad.** El integrador prepara la cápsula por selectores y luego “verifica” contra el mismo snapshot, en contexto compartido declarado en la sesión. Eso es autocontrol, no verificación independiente; no debe sustentar por sí solo la etiqueta `RECONCILED`. Además, “copiar hashes” no prueba las copias: hay que recomputar SHA-256 de cada fichero encapsulado y compararlo con `sha_recomputed`, distinguiéndolo del hash declarado por manifiesto. Copiar el hash junto al fichero sería circular.

2. **Campos y roles inventables.** `bindings.json` no contiene campo `role`, ni etiqueta `kit118`, ni `seco`, ni “tres modelos”. Publicar “identidad/estación/rol” exige citar la fuente guardada de cada rol; en caso contrario, `role=UNKNOWN`. `Kit118/76` presupone una asociación no visible en las filas; `49 seco` tensiona la propia regla de no inferir ausencia desde `instance_ids=[]`/`model_indices=[]`; y tres ficheros B0 `local-faces-0/1/2` no equivalen sin más a tres modelos.

3. **Medidas guardadas, no validadas.** Las filas traen `station_m` y `length_m`. Si se reproducen, deben marcarse como valores guardados no reconciliados geométricamente. La salida no puede “fijar longitud/tangente”, pero tampoco presentar estación/longitud como medición nueva ni como base de colocación.

4. **Cuenta y cápsula.** La sesión lista 21 entradas: 20 `OBSERVED_SAVED` y 1 `UNKNOWN` (B2 `contract.json`, “path absent”); `stop.json` dice `files_read=20`. El plan debe decir “20 leídas + 1 intentada/ausente”, no simplemente “20 fuentes”. La cápsula debe enumerar ficheros cerrados — idealmente `bindings`, `frozen-partial`, snapshot 4 y 7, `session-before-stop` y `stop` —; incluir las 20 fuentes reabriría interpretación B0/B2/B3/Q03B6 y desbordaría la consolidación. `frozen-partial.json` se invoca pero no se aporta a esta revisión: queda no auditado.

5. **Presupuestos.** 30 s de cápsula, 90 s de revisión y 120 s de entrega son topes `[DESIGN]`, no factibilidad probada; el lote guardado de 56,509 s no los valida. Su incumplimiento debe producir no-entrega, no informe degradado aprobado. Igual cautela con “localizar el esquema B2 por manifiesto”: presupone un manifiesto localizable no identificado en las fuentes aportadas.

Con esas cinco enmiendas, **CONVERGE** para una única entrega parcial `SAVED_BINDINGS_PARTIAL_RECONCILED`, entendida sólo como reconciliación documental autocontrolada de bytes guardados.
