# Carga acotada de IA: medición completa

Run ea48bc79-7b0d-47dd-b6b1-a959662c253a, DayZDiag1.29.163709,
PBO fd2c7023 y misión60e4716a. Cliente y servidor locales, sin CE ni población
regional. Ryzen7800X3D/64GB/RTX3090; hardware.json del baseline identifica el host.
Contrato anterior al run: `../ai-load-reference-v1.json` y plan terrain-ai-load.

Las cuatro fases0/25/100/0 completaron25s de calentamiento y60s medidos cada una.
En todas las muestras cargadas, todos los actores seguían vivos y con mind>=1.
Con100, media31.47 actores desplazándose>0.1m desde la muestra anterior; salud
mínima88, no bajas. Desplazamiento máximo del objetivo0.822m. No se controló
posición/velocidad de la IA tras crearla.

| Fase | Residente servidor, mediana | Privada servidor | CPU servidor, % de un núcleo lógico |
|---|---:|---:|---:|
|0 inicial|1629.91MiB|1958.16–1961.33MiB|16.82|
|25 activos|1637.89MiB|1963.04–1963.70MiB|16.24|
|100 activos|1645.31MiB|1973.26–1974.18MiB|4.00|
|0 final|1645.82MiB|1977.12–1977.25MiB|0.43|

CPU no monotónica: no usar esta secuencia para afirmar que100 cuesta menos que25,
ni derivar un coste por infectado. No se controló/registró foco de la ventana,
temperatura, frecuencias o políticas de throttle del cliente. El comienzo y el
final sin IA no son equivalentes en recursos ya cargados. No se aisló el mecanismo
de la variación. Las cifras son observaciones del proceso, no un benchmark causal.

335 muestras host por proceso, identidad PID+creación estable; unión por el último
marcador de fase observado, incertidumbre de hasta un intervalo host. La fase100
tuvo máximo timeslice12ms; el máximo de todas fue17ms y no hubo timeslices>50ms.
OnUpdate no se publica como FPS. Memoria final algo mayor puede incluir cachés;
esta secuencia no demuestra fuga. Medianas cliente2236/2324/2366/2362MiB, sin
FPS de render acreditados. No había ciudades, loot, persistencia ni100 conexiones.

No se ha aplicado ninguna reducción de calidad: estos datos no localizan un
cuello de botella atribuible al terreno. Los costes sirven como primer registro
reproducible, conservando las condiciones y sus límites.

`verification.json` = PASS_BOUNDED_ACTIVE_AI_MEASUREMENT, no PASS80–100jugadores.
Logf2459094. Limpieza de actores completada por misión; cierre posterior MCP
forced_kill, exit_metrics_valid=false, lease none/caja libre/0 pendientes.
`cleanup.json`. Los logsRPT conservan avisos conocidos; no se afirma arranque limpio.
