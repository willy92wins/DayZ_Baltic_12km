**Veredicto: NEEDS-WORK.** Un bloqueador real en el capturador de logs; el resto del paquete es sólido con correcciones menores. No se autoriza RAM ni lanzamiento todavía.

**Bloqueador: capture_kit7_nav8load1_logs.ps1 está corrupto y no parsea**

El archivo sellado con hash `8d2bcb66…` en source-hashes.json es sintácticamente inválido. Anclas:

- `capture_kit7_nav8load1_logs.ps1:14` tiene `-match '^END;[0-9]+) {` sin comilla de cierre.
- `capture_kit7_nav8load1_logs.ps1:19` contiene `-notmatch '^END;[0-9]+@{pid=…` seguido del resto del script duplicado tres veces (líneas 28-62).

El patrón es el artefacto clásico de `-replace` en .NET: el reemplazo contenía `'^END;[0-9]+$'` y la secuencia `$'` se expandió como "texto posterior a la coincidencia". Comparado con el predecesor sano `capture_kit7_nav_log.ps1:14-19`, la intención era clara pero el resultado no ejecuta. Consecuencias:

- El orquestador lanzaría el servidor, ejecutaría el capture en background (`orchestrate_kit7_nav8load1_probe.js:29`), fallaría en el acto, cerraría la run en `finally` y consumiría el único intento autorizado sin datos.
- Los 13 flow tests y 8 command tests no lo detectaron porque mockean `cmd`; el `.ps1` nunca se interpretó. El sellador tampoco hace parse del script (`seal_kit7_nav8load1_probe.py:21-24` solo valida hashes y mocks).

Corrección: reescribir el capturador partiendo del predecesor, con un único bloque que exija `END;[0-9]+` en el log 607, luego valide el config log (`END;9` esperado, frescura por LastWrite ≥ creación del proceso), copie `config-runtime.log` y escriba `log-binding.json` con `config_sha256`, `config_source` y `config_source_last_write_utc` como espera `finish_kit7_nav8load1_probe.py:84-86`. Añadir al sellador un parse estático con `[System.Management.Automation.Language.Parser]::ParseFile` y rechazar si hay errores. Regenerar source-hashes.json tras la corrección.

**Lo que sí está bien**

- **Despliegue exacto**: `prepare_kit7_nav8load1_runtime.py:102-107` releé el PBO desplegado, exige que sólo `config.bin` difiera y que WRP/NM coincidan con el manifiesto; `deployment-parity.json` reporta 6826 entradas sin cambio. El config desplegado se redecodifica y pasa `verify_config_delta` (`:109-112`). `deployed-config.cpp:60` muestra `filterIsolatedIslandsOnLoad=1` y `:68` `filterIsolatedIslands="true"`.
- **Paridad de misión**: `prepare…:73-75` exige que la plantilla menos función y guard sea byte-idéntica a la base normalizada. El init.c en C:/temp lleva el UUID `4b29679b…` que coincide con runtime-preparation.json y con el path hardcodeado en `orchestrate…:3`. Las consultas CSV se verifican por hash (`:80`).
- **Guard sin falso PASS**: `init.c:41-45` exige tipo 0, texto "1", int/float 1 para los tres OnLoad numéricos y tipo 2/"true"/0 para GenParams; `init.c:80-86` escribe `FAIL;CONFIG` y `END;0`. Un `END;0` captura, pero `verify_kit7_nav_ev112.py` falla por conteo y el joint gate (`finish…:90`) exige ambos códigos 0 y ambos estados PASS. Config PASS aislado no autoriza nada.
- **Oráculo config**: `verify_nav8_load1_config_ev112.py:11-15` reutiliza `evaluate` con sus 9 controles y añade las exigencias de tipo nativo. Los 8 tests mutan el fixture literal del log real (`test_nav8_load1_config_ev112.py:6-7`) y el reemplazo de la fila 0 es unívoco en ese fixture.
- **Host binding**: PID y creación verificados en `orchestrate…:14,21-22` y `finish…:20-33`; ejecutable por SHA; 4 paquetes exactos; observer con handle retenido; cierre oficial con `validate_close` y una sola CLOSE_INTENT; RPT y script log ligados por UUID y ventana temporal (`finish…:65-73`).
- **Failure handling**: `finally` cierra sólo run propia y libera lease; sin prelease ni sondeo de ocupación; FIFO `on_busy=queue/wait 600/takeover=false` (`orchestrate…:10`). Presupuestos 60×5s≈300s arranque, 900s captura, 1200s observer.

**Fixes menores (no bloqueantes)**

1. `seal_kit7_nav8load1_probe.py:30` congela los inputs de `adjudication.json` más una lista explícita, pero no asegura que esa lista cubra todas las claves de source-hashes.json. Añadir aserción de superconjunto para que capture/finish/orquestador/oráculos queden congelados con certeza.
2. `finish…:57` escribe `identity-verification.json` con PASS_BOUND antes de ejecutar los consumidores. Es correcto como estado parcial, pero conviene que su `limits` diga explícitamente "joint pendiente" para no leerse como aceptación.
3. `init.c:8-16` tiene sangría irregular en los `paths.Insert`; cosmético, el validador estático pasa.
4. En PowerShell, `$rows[-1]` sobre un archivo de una sola línea devuelve el último carácter, no la línea. Es inofensivo con el regex `^END;[0-9]+$`, pero vale documentarlo o forzar `@(Get-Content …)`.

**Límites de esta revisión**

No se afirma causa del exceso de RAM ni promoción global; el A/B sigue siendo contra Chernarus y cualquier resultado concede sólo candidato local. El tipo nativo se exige en motor, no por inspección de bytes. El código queda aprobado para un único intento sólo cuando el capturador se repare, se parsee y se vuelva a sellar.

FIN_REVISION
