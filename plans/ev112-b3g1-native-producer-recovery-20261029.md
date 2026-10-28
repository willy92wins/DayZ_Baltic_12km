# B3G1 — recuperación del productor y su observación

Estado: REVISADO_PARA_IMPLEMENTAR_OFFLINE. Fable5.1 nativo67.328s adjudicado. Codex ejecutor/integrador autorizado.
Traza a B3G y P9/P10: esta unidad corrige la instrumentación para poder contrastar
ef229 frente a362ef4c2; no cambia mapa, puntos, low_y, agua ni tolerancias.

## Evidencia y mecanismo acotado

Run d4b28db9-f080-4a1c-85b4-c73faaee2e8e cerrado oficialmente y lease liberado.
El motor registró init.c:220 Formula too complex y Can't compile mission init
script a23:29:36Z. No se creó baltic_contact_b3g.log. La readiness del puente no
certifica la misión. No hubo muerte del proceso: se cerró orderly_close.
Además la continuidad del agente omitió heartbeat hasta caducar lease y agotó
captura180s; el deadline exacto no quedó persistido. Son fallos separados.
El candidato no se admitió. B3G R0 se conserva íntegro, no se reintenta.

Hallazgo adicional verificable: binding:42 exige float600.0 por type, pero una
petición MCP JSON con número600 se serializa como entero. Mismo valor semántico;
rechazar bool/string/NaN/599 sigue obligatorio. No reescribir recibo crudo R0.

## Plan de recuperación — [DESIGN]

1. Misión NUEVA BalticContactB3G1.BalticTrial. Dividir sólo la segunda asignación
   W (nueve valores concatenados) en tres asignaciones de tres valores. Header,
   orden de20campos, consultas y relojes permanecen. Fuente R0 archivada por SHA.
2. Adaptador nuevo de binding: guardar recibo raw intacto, validar número real
   finito==600 y no bool/string, normalizar sólo esa representación en copia
   para identity anterior. Funciones puras anteriores sin cambios. Añadir contrato
   de timestamps host: readyUTC/captureStart/deadline/end; deadline=ready+180s.
   El éxito requiere captura dentro de plazo y host antes/después, nunca un
   salvage tardío. La normalización no modifica la admisión solicitada.
3. Observación en un único exec asíncrono: heartbeat oficial cada<=20s mientras
   await de tools/host; persistir run/adoption/ready/deadline conforme llegan.
   Esperar server peer BOUND, version ok, fresco; globalreadycliente no aplica.
   Vigilar también archivo script fresco por PID/start/mtime y error de misión
   exacta. Parar inmediatamente al error, falta de archivo o deadline. No abrir
   otro puente ni cliente; no credenciales en disco. finally cierre/release/status.
4. NUEVOS directorios de admisión/recibos y manifiestos. Revalidar mismos hashes
   B3F/mundo/agua/vanilla y control original. Nuevo preparador sólo copias frescas
   y sello externo, sin ejecutar CLI R0. No consumir preparadores antiguos.

## Puertas y presupuesto antes de ejecutar

Planreview180s; code review180s sobre delta; suite120s/2GiB y lint>0archivos.
Tests negativos: cambio/campo W omitido u ordenado distinto, JSON600int/600float,
bool/string/599/NaN, ready sin misión compilada, error de otro run no imputado,
captura tardía, heartbeat fallido que aborta, finally aunque capture falle.
Tests de código no certifican Enforce. Sólo compilación real lo demuestra.

Preparación120s/2GiB; preflight oficial fresco con C:\ rutas canónicas, sin
ocupación consultada. Una pareja nueva por unidad: FIFO600s cada admisión,
readiness300s, captura180s, consumidores120s/2GiB. Control primero; si no hay
identidad/captura completas, candidato no arranca. No reintentos internos ni
relajación de umbrales. Gestionar sólo run propio exacto y retirarlo siempre.

Esta primera revisión autoriza implementar y probar offline el delta; el
coordinador y preparador deben estar revisados antes de la pareja nativa.
Resultado posible: instrumentación lista o fallo reproducido. Nunca PASS global.
Original47FAIL21inciertos, Nav8histórico607PASS, RAM y nueve regresiones abiertos.

Adjudicación: heartbeat concurrente sólo DESPUÉS de adopción exacta; durante FIFO el launcher gestiona su lease, sin preadquisición. La tarea concurrente debe ser awaitada y terminar en finally. readyUTC es primera observación host UTC de BOUND/versionok/poll<10s; persistir deadline=ready+180s entonces y comprobar error de misión antes de capturar. El normalizador acepta sólo int/float no bool finito==600, clave única; negativos string600.0 y600.0000001. Log filename/CreateCustomMission intactos. No certificar compilación de otras líneas por ausencia de primer error.
