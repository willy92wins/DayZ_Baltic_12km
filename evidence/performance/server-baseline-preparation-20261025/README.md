# EV112 — preparación del A/B de servidor vacío

**PREPARADO, NO EJECUTADO.** 184 tests pasan. Capturador host probado sobre un
proceso PowerShell propio, con PID/creación incorrectos y escritor exclusivo:
continúa registrando CPU/RAM ante el bloqueo y termina en END. Esa prueba no
mide DayZ ni demuestra rendimiento de Baltic.

Fable5.1 revisó código y fixes, SOUND-with-fixes. Se resolvieron mundo real,
identidades obligatorias, cadencia500ms, timeout600s, CPU nula, captura bloqueada,
fecha anterior al arranque y vínculo del nombre de log con la misión.
El agregador revalida capturas/hashes, seis procesos y logs distintos, configuración
idéntica, misión canónica y paquetes estables por mundo. Tests incluyen presupuesto,
dispersión, exceso no reproducido, cambios de condiciones y negativos de captura.
El caller aún debe probar el stack realmente cargado y la identidad del run.

Orden A-B-B-A-A-B: A=E con navegación9 aceptada, B=ChernarusPlus instalado.
Tres pasadas por mundo, calentamiento30s y120 ventanas útiles; sin CE/IA/jugadores/
cliente. Dispersión congelada=(máximo-mínimo)/mediana, límite5%; RAM1,10 y exceso
reproducible en dos pares para FAIL. CPU descriptiva. No hay FPS cliente, VRAM,
capacidad multijugador ni resultado A/B en esta unidad.

Seis misiones V2 preparadas, aún sin lanzar. V1 no se usa. Las credenciales/config
privada no se publican: únicamente se fijarán sus hashes al medir. El primer
snapshot debe preceder al arranque y los archivos deben conservarse hasta validar.
Cualquier repetición requiere nueva misión/log. MANIFEST.json fija estos artefactos.

Tests.log normaliza UTF-8/LF; tests-raw.log.gz conserva el registro original.
El script smoke conserva sus bytes exactos en .ps1.gz; la copia legible recorta
solo las lineas vacias finales.
