Ya tengo todas las fuentes, las misiones preparadas, la config del servidor y la evidencia del nombre real de mundo. Redacto el veredicto.

**Veredicto: SOUND-with-fixes.** No encontré ningún falso PASS ni error de atribución en el código actual. Hay un riesgo de robustez en el capturador que conviene corregir antes de lanzar, y tres refuerzos opcionales.

**Verificado como correcto**

- **Mundo real.** `missions/BalticTerrainPerf.BalticTrial/init.c:25-27,39` usa GetWorldName con guard en minúsculas y cabecera del motor. El nombre real de Chernarus es `chernarusplus` en minúsculas, evidenciado en `E:\DayZ-Baltic-Build\vanilla-water-survey-v1\survey.log:1`, y el consumidor compara sin distinguir mayúsculas en `tools/performance/read_server_baseline_ev112.py:22`. Las seis misiones V2 en C:\temp difieren del canon solo en guard y nombre de log, en las líneas 27, 33 y 64.
- **Sincronización.** Cadencia 500 ms, intervalo aceptado 0,4 a 3 s, tope 600 s y 1201 filas son coherentes. La ventana host va de la última lectura de columns antes de S;1 hasta END, exige adyacencia y tolera 2,1 s. El delta CPU nulo se rechaza en la línea 55.
- **Agregador.** Índices Baltic (0,3,4) y Chernarus (1,2,5) coinciden con A-B-B-A-A-B, y zip produce los pares A1/B2, A4/B3, A5/B6 del plan. Dispersión (max-min)/mediana, umbral 5 %, escalera PASS, FAIL con dos excesos, INCONCLUSO en el resto, CPU solo descriptiva. Cada resultado se rederiva de las capturas y hashes en `load_pass`.
- **Config común.** `C:\temp\DayZ_MCP_130_dev\_server\serverDZ.cfg:10` fija template y la misión se elige con -mission= según los RPT previos, así que la exigencia de config idéntica en `compare_server_baseline_ev112.py:84-85` es satisfacible. La línea de comando y el stack -mod no se vinculan: límite documentado en el docstring de bind, no bug.

**Fix recomendado antes de lanzar**

- **Bloqueo de fichero aborta la pasada.** `tools/performance/capture_server_baseline_ev112.ps1:23` abre el log del motor con ErrorActionPreference Stop. Si Enforce mantiene el fichero sin FILE_SHARE_READ durante su OpenFile/CloseFile por segundo, una IOException mata el capturador y se pierde la pasada con un presupuesto de una sola repetición. No hay evidencia en ninguna dirección: el smoke usó un escritor PowerShell. Fix: envolver la lectura del tail en try/catch de IOException y dejar engine_last_line vacío para esa muestra. El consumidor ya tolera marcadores vacíos y solo rechaza si el vacío cae justo antes de S;1. Es riesgo de robustez, no falso PASS.

**Refuerzos opcionales**

- **Vínculo misión ↔ log del motor.** `compare_server_baseline_ev112.py:58` canonicaliza el nombre único del log pero no exige que `artifacts.engine` se llame igual ni que los seis nombres sean distintos. Un check de un par de líneas cierra el vínculo misión-proceso sin depender del caller.
- **Orden temporal del snapshot.** `bind_server_baseline_ev112.py:17-25` no registra cuándo se preparó; un snapshot hecho tras la pasada superaría `finish`. Añadir prepared_utc y exigir que preceda a start_utc. Límite declarado, no bug.
- **Huecos de test.** Sin caso para INCONCLUSIVE_PAIRED_EXCESS, para "Common conditions changed" y "World packages changed" del main de compare, ni para guard de mundo equivocado en conditions_identity.

**Operativo**

- Una repetición debe usar un directorio y nombre de log nuevos. Con un log viejo completo, el capturador vería END en la muestra 0 y pararía. Falla cerrado, pero quema la repetición.
- En `C:\temp\DayZ_MCP_130_dev\mpmissions` conviven directorios V1 obsoletos, por ejemplo BalticAB01_e3bb83b26d5c, junto a los V2 de missions.json. Lanzar uno equivocado fallaría cerrado en conditions_identity, pero conviene borrarlos.

No se emite aceptación de motor ni benchmark. Ninguna pasada A/B ha ocurrido.
