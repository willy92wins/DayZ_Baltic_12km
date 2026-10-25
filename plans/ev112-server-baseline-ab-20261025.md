# EV112 — coste fijo de servidor frente a Chernarus

Unidad del punto5 de `ev112-performance-chernarus-20261024.md`. La petición viva
autoriza avanzar sin cliente mientras Guillermo no está. Codex ejecuta e integra;
Fable revisa el consumidor antes del ensayo. No se infiere FPS, carga de jugadores,
IA ni coste de una escena cliente desde esta medición.

[EXACT] La misión `missions/BalticTerrainPerf.BalticTrial/init.c` existente no
inicia Hive/CE y registra30s de calentamiento más120 ventanas de un segundo.
`tools/navigation/verify_terrain_perf.py:11` exige120 muestras, orden, tiempos,
inicio/final y mundo. `sample_server_process.ps1:14-24` identifica PID+creación
y mide CPU acumulada, working set y private bytes con reloj monotónico.
GetTickTime y GetTime están definidos en `P:/scripts/3_game/global/game.c:914,1534`.
OnUpdate mide delta de simulación, no duración CPU; FPS nativos headless siguen
sin una semántica validada para representar rendimiento real.

[DESIGN] Preparar seis misiones temporales equivalentes, con nombre/log únicos,
orden A-B-B-A-A-B: A=E con su navegación9 verificada; B=ChernarusPlus instalado.
Solo cambian mundo y nombre de archivo. Mismo ejecutable1.30, MCP, opciones y
configuración; sin cliente, CE ni IA. Todos los hashes de paquetes/misión/config
se fijan antes de medir. No correr compilación, navgenerator u otro trabajo pesado
propio durante el ensayo. Cualquier concurrencia externa detectada se informa.

El capturador host termina al observar END120 de su archivo único o a600s;
comprueba identidad en cada muestra. El consumidor exige intervalo host <=3s,
CPU finita/no decreciente y memoria positiva, lectura del marcador de calentamiento
(columns, escrito después de INIT) antes de S1 y cobertura hasta END120.
Ventana host: última lectura de ese marcador inmediatamente
antes de S1 hasta primera lectura END. Registrar incertidumbre de ambos extremos;
rechazar desajuste de duración >2,1s respecto a las120 ventanas del motor.
Cadencia objetivo500ms; no denominar perfecta a esta sincronización por muestreo.

Tres pasadas válidas por mundo; registrar razones de cualquier descarte. Comparar
CPU/segundo de pared, working set y private bytes sobre la ventana común. Informar
ratios y dispersión, definida antes de medir como (máximo-mínimo)/mediana entre
las tres pasadas del mismo mundo; >5% en cualquier mundo impide adjudicar el margen10% de RAM del
plan padre. CPU descriptiva: no inventar un presupuesto nuevo después de medir.
No calcular p95/p99 de frames a partir de OnUpdate ni FPS64. Si no hay navegación9
propia validada o el banco no está libre, conservar la preparación sin resultado.

Presupuesto: seis pasadas principales, una repetición motivada por evidencia
inválida. Pruebas previas del consumidor con log real existente y negativos:
mundo equivocado, falta de calentamiento/final, identidad cambiada, hueco, NaN,
CPU regresiva, memoria cero y cobertura host insuficiente. Una revisión de código
y una reparación de hallazgos antes de lanzar. Lease/lifecycle en cada run;
ningún cierre de sesiones ajenas.

Agregado automático: exige seis resultados completos en orden A-B-B-A-A-B,
identidades de proceso distintas, mismo ejecutable/configuración común y misión
normalizada idéntica, paquetes idénticos entre repeticiones del mismo mundo.
Compara las medianas de las tres pasadas por mundo. RAM >1,10 requiere además
dos excesos en los pares A1/B2, A4/B3, A5/B6 para FAIL; discrepancia o dispersión
alta queda INCONCLUSO. Cada resultado se vuelve a derivar de sus capturas y hashes.
CPU solo descriptiva. Una preparación sin seis pasadas nunca obtiene PASS.
