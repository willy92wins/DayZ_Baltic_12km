# Observador automático temporal de agua

Petición viva: continuar la versión básica y resolver la inundación. Extiende únicamente la instrumentación de `narva-water-clearance.md` (P2/P4/P8); no crea otro candidato de terreno.

## Discriminador y presupuesto

F10 no cargó `BuldozerModule` en la sesión 17:34, aunque el usuario confirmó la tecla. Escape automático tampoco mostró menú; Alt+F4 cerró el visor normalmente a las 17:59:29. TB quedó sin respuesta. No repetir esas pulsaciones como si fueran pruebas del agua. La consola Enforce depende de `DEVELOPER`, ausente de los defines registrados; no se cambian scripts vanilla para habilitarla.

[DESIGN] Un addon temporal, guardado fuera del addon del mapa, añade un observador a `MissionGameplay` solo con `BULDOZER` y `DIAG_DEVELOPER`. Imprime un marcador al construir la misión y, tras diez segundos acumulados en `OnUpdate`, escribe una sola vez las mismas 441 consultas del observador basal. No modifica mundo, jugador, red ni configuración de agua. Rechaza sobrescribir un log existente. No necesita F10.

Datos: superficie/agua local del visor; sin RPC ni SyncVars. Guardas de compilación impiden ejecución en un servidor/juego normal. El retraso no demuestra por sí mismo que TB haya enviado el terreno: la comparación contra el ASC guardado debe rechazar alturas que no correspondan.

Presupuesto: una carga del addon y una lectura. Si no aparece el marcador, diagnosticar carga de módulos; si aparece marcador sin salida, diagnosticar ciclo de misión. Si hay salida inválida o alturas de otro terreno, INCONCLUSO. No elevar más tierra por un fallo del observador.

## Anclas verificadas el 29-09-2026

- `P:/scripts/5_Mission/somemission.c:30-38`: una ruta no vacía como `buldozer_mission_default`, sin NO_GUI_INGAME, crea `MissionGameplay`; ruta observada en el log real.
- `P:/scripts/5_Mission/mission/missiongameplay.c:58`: constructor; `:278`: `OnUpdate(float timeslice)`. Conservar `super.OnUpdate(timeslice)`.
- `P:/scripts/3_Game/global/game.c:1162,1174-1187`: APIs de altura, mar y agua utilizadas también por la sonda basal auténtica.
- `P:/scripts/1_core/proto/ensystem.c:397,417,443,481`: FileExist/OpenFile/CloseFile/FPrintln.
- `P:/scripts/config.cpp:3-9`: CfgPatches DZ_Scripts.
- `P:/DayZ_MCP_dev/addon/config.cpp:29-32`: CfgMods/missionScriptModule y files. CfgConvert + contenido PBO + linter son gates offline, no compilación Enforce del consumidor.

## Aceptación y retirada

Se exige marcador de construcción, log completo nuevo, 441 coordenadas únicas y fin de registro. Ejecutar `verify_water_observer.py --native tb/narva_trial/narva_tb_dryland_v1.asc`. PASS solo para la tierra interior muestreada; orillas, conectividad, nado y mapa completo siguen siendo gates separados.

El addon y parámetro `-mod` son temporales. Respaldar los parámetros actuales de TB antes de añadirlo; no tocar perfiles de entrada. Al finalizar, restaurar solo el valor coincidente con el aplicado y retirar por hash la copia temporal del mod. Conservar fuente, paquete y evidencia en el proyecto. La prueba espera la recuperación manual de TB; no elude la ventana de recuperación bloqueada.
