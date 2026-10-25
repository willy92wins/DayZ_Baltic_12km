# ComparaciÃ³n con Chernarus: modelos y capturador, 24-10

**AuditorÃ­a binaria terminada; benchmark todavÃ­a INCONCLUSO.** No se midieron FPS,
frametimes, RAM/VRAM en juego ni capacidad multijugador. NingÃºn ajuste visual se
redujo para obtener mejores nÃºmeros.

Se leyeron estrictamente los 5.495 recursos distintos referenciados por Q y
Chernarus en las familias de agua, sin errores de parser, con finales de LOD e
Ã­ndices comprobados. Los 5.220 modelos de agua propia y los 35 del piloto tienen
un Ãºnico LOD visual. Los 11 modelos vanilla usados en Q tienen cuatro o cinco.
Chernarus usa 239 recursos de agua: 200 con un LOD, 30 con cinco y nueve con cuatro.
Un Ãºnico LOD no demuestra por sÃ­ solo un defecto: las lÃ¡minas tienen poca geometrÃ­a.

| Inventario ponderado por instancias, todo el mundo | Baltic Q | Chernarus Exp |
|---|---:|---:|
| TriÃ¡ngulos equivalentes visuales cercanos, familias vanilla de agua |130.093.772|46.351.753|
| TriÃ¡ngulos equivalentes del Ãºltimo LOD, mismas familias |154.199|338.359|
| TriÃ¡ngulos visuales de agua propia |710.918|â€”|
| TriÃ¡ngulos visuales del piloto |33.866|â€”|
| TriÃ¡ngulos de Geometry del piloto |264.480|â€”|

Son sumas de inventario a escala del mapa. No describen quÃ© queda visible,
quÃ© LOD selecciona el motor ni cuÃ¡ntos draw calls/coste de colisiÃ³n hay en una
escena. Las familias incluyen lechos y piedras. La reducciÃ³n de LOD vanilla
cambia radicalmente el total: hay que medir por escena antes de optimizar.
Prioridad de perfilado: cauces antiguos densos, piloto a media altura y transiciones
de LOD. Conservar agua/colisiÃ³n/aspecto y aislar una causa por ensayo.

El PBO Chernarus de **DayZ Exp en E:** tiene el mismo SHA256 que el cliente de C:
`ea868be8ca86200d3c2906ba5b932fafe04aed731276db75eca40cdbff6db75f`.
La comparaciÃ³n anterior usaba el contenido correcto tambiÃ©n para MCP130.

## InstrumentaciÃ³n preparada, no validada en juego

PresentMon 2.6.0 x64 portÃ¡til descargado de la
[publicaciÃ³n oficial](https://github.com/GameTechDev/PresentMon/releases/tag/v2.6.0).
SHA256 coincidente con el digest publicado:
`b2a706bc6ad475749e3b7e3409263aa1e6906d45bdcf993f6dbc0f660188f1af`.
Firma Authenticode vÃ¡lida de Intel Corporation; ejecutado Ãºnicamente `--help`.
Binario en `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018/performance-capture-20261024-d/`.
Sin instalaciÃ³n global, elevaciÃ³n ni captura de procesos ajenos.

`capture_presentmon_ev112.ps1` prepara 30s de calentamiento y 120s de captura,
PID+fecha+imagen verificados, sesiÃ³n ETW Ãºnica, RAM privada/residente y CPU de host.
No cambia foco, ajustes ni gestiona DayZ. Falta validarlo con un run propio: permisos
ETW, integridad de eventos, foco/pausa, escena, configuraciÃ³n y estabilidad.
No se ha ejecutado la captura. Solo sintaxis PowerShell verificada.

La traza detectó que el README mezcla nombres de métricas v2 con las columnas
por defecto. El lector se corrigió según el ejecutable firmado y
[CsvOutput.cpp de 2.6.0](https://github.com/GameTechDev/PresentMon/blob/v2.6.0/PresentMon/CsvOutput.cpp):
`CPUStartQPCTimeInMs` y `MsUntilDisplayed` (latencia, NA si no mostrado).
Los 357 frames en diez grupos de la traza pública coinciden exactamente con el
CSV dorado en intervalos de presentación y estado de visualización; sus
percentiles coinciden con un cálculo independiente. Los blobs descargados
coinciden con los hashes Git del tag. Esto prueba la reproducción offline, no
la captura ETW en vivo. `read_presentmon_ev112.py`
retiene tirones y frames no mostrados, rechaza PID/imagen ajenos, swapchains ambiguos,
reloj invÃ¡lido, unidades/duraciÃ³n incorrectas, valores invÃ¡lidos y ausencia de
frames mostrados. Tres mÃ©todos de prueba pasan: cadencia calculada a mano,
retenciÃ³n de un tirÃ³n y nueve corrupciones/contaminaciones rechazadas. El resultado
es descriptivo; nunca declara PASS del benchmark por un CSV estructuralmente vÃ¡lido.

## Bloqueo real

MCP130 continÃºa devolviendo `daemon_unavailable`. El arranque oficial finaliza por
plazo de migraciÃ³n de identidad; doctor ademÃ¡s informa diez slots de backup
preprune ocupados. No se ha aislado una causa Ãºnica. Bundle nativo y pins actuales
pasan. Los intentos de bootstrap terminaron; no se lanzÃ³ DayZ ni se adquiriÃ³ lease.
No se borraron backups, modificaron claves ni cerraron procesos ajenos.

La ocupaciÃ³n del banco no se puede certificar con session_status en este estado.
Reparar la infraestructura compartida antes de ejecutar el A/B del plan
`plans/ev112-performance-chernarus-20261024.md`. Foco/escenas y tres pasadas por mundo
siguen pendientes. El inventario no acredita el objetivo de 80â€“100 jugadores.

`MANIFEST.json` fija esta evidencia y las fuentes. AuditorÃ­a completa de 13,8MB en
el build; ruta y hash en `lod-audit-summary.json`. No commit/push: tarea global abierta.
