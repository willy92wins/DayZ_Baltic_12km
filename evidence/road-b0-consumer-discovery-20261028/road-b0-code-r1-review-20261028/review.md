Revisión de la corrección R1 (prefijo, `accept_run_receipt`, driver), sin tocar código intacto ni pedir repetir A/R0.

**Veredicto: SOUND-with-fixes**

**Corrección del prefijo (road_consumer_discovery_ev112.py:19-21, 76; test:77-80)**
Correcto. El literal `DZ\structures\roads` coincide con el source-table de A y la identidad sigue atada al hash 34c1 (línea 75). El test cubre el caso real que falló (minúscula), truncado y None. Ninguna relajación.

**Aceptación de recibo (road_consumer_discovery_ev112.py:23-26; test:81-87)**
El contrato es correcto y estricto: rechaza stop_reason, tiempo, RSS, reporte con `error`, modelos distintos de 3, y par rc/status contradictorio (0+INCONCLUSIVE, 2+COMPLETE). El reporte del camino de excepción (línea 103) no trae `models`, luego nunca pasa. Observación menor: una clave ausente en el recibo produce KeyError en vez de ValueError; sigue siendo rechazo, no aceptación, así que no bloquea.

**Driver R1 (run_road_b0_execution_r1_20261028.py)**
La lectura del helper es la correcta: `run_tree` guarda el recibo y lanza RuntimeError por rc≠0, el driver captura sólo esa excepción (línea 17) y reconstruye el recibo desde `log.with_suffix('.receipt.json')` (línea 19). Fallo real sigue rechazado por líneas 20-24. Dos problemas de reuso de recibo:

- **Fix 1, línea 8.** El guard `already_started` comprueba `O` y `log` pero no `road-b0-execution-r1-driver-20261028.receipt.json` ni `road-b0-r1-driver-exception-20261028.json`. Si una ejecución abortada dejó el recibo y se borró el log, o si `run_tree` lanzara RuntimeError antes de escribir el recibo (fallo de spawn), la línea 19 leería un recibo ajeno y podría validarlo. Añadir ambos ficheros al assert de arranque.
- **Fix 2, línea 19.** Tras la excepción, atar el recibo a esta ejecución: comprobar que el recibo contiene el argv/salida `O` o el PID y create_time que `run_tree` observa, y que su mtime es posterior al inicio del driver. Sin esto, "recibo falso" por reuso no está excluido por el código, sólo por disciplina.

Secundario: las aserciones de línea 20-21 duplican las de `accept_run_receipt` (línea 24); inofensivo. El `completion.json` queda dentro de `O`, creado por el hijo con `exist_ok=False`; coherente.

**Cobertura de regresión (test:81-87)**
Falta el caso RSS>2GiB y el caso de reporte con 2 modelos (extracción truncada sin `error`). Ambos están contemplados por el código pero no demostrados. **Fix 3**: añadir dos líneas al mismo test.

**Alcance y contratos del plan**
- Una extracción, 120s/2GiB, sin reintentos: `already_started` y `exist_ok=False` lo garantizan dentro del driver. Cumplido.
- Sin cambios en helpers, sin WRP/build/deploy/DayZ: confirmado en las fuentes adjuntas.
- UNKNOWN de consumidor/pivote/ancho/cruces preservados (líneas 51-68, 94); no alterados por R1.
- R0 archivado y salida nueva: coherente con línea 7 del driver.

**Limitaciones fuera de R1 (no cuentan contra el veredicto)**
- Que `cat.require` lance ValueError y que `run_tree` mapee kill por timeout a `stop_reason` no None se asumen según el brief del helper sellado 914bef55; no verificables desde las fuentes adjuntas.
- Presupuesto de CfgConvert `min(60, …)` (línea 80) es diseño previo, no corrección.

**Resumen de fixes antes de ejecutar R1**
1. Driver línea 8: incluir `.receipt.json` y el JSON de excepción en el guard de arranque.
2. Driver línea 19: verificar que el recibo releído pertenece a esta ejecución (argv/PID/create_time o mtime>inicio).
3. Test línea 87: añadir casos RSS>2GiB y `models` de longitud 2.

Con 1 y 2 aplicados y la suite re-ejecutada, la corrección cierra el fallo demostrado sin relajar nada. Codex verifica y adjudica.

FIN_REVISION