# Sonda temporal para la revisión visual

Solo se carga mediante `@BalticVisualUIProbe` en pruebas del proyecto. No forma
parte del mapa. Cierra una vez el menú de pausa con la función vanilla Continue;
no mueve jugador/cámara ni modifica archivos, mundo, red o clima.

Estado/menu/temporizador: cliente, sin dato servidor ni puente RPC. Solo
MissionGameplay, jugador presente, mundo BalticTrial, menú activo MENU_INGAME.
Espera 5 s; observa hasta 45 s y permite una solicitud. Verifica menú ausente o
declara FAIL tras 10 s. Otros menús no reciben acciones. Retirar el addon de la
lista de mods al terminar las pruebas; no cambiar DayZ_MCP.

API local verificada antes del código:

- P:/scripts/5_mission/gui/ingamemenu.c:213: OnClick_Continue encola Mission.Continue.
- P:/scripts/5_mission/mission/missiongameplay.c:1297: Continue elimina las
  restricciones de pausa y cierra MENU_INGAME, con sus propias guardas.
- P:/scripts/5_mission/mission/missiongameplay.c:278: OnUpdate(float timeslice).
- P:/scripts/3_game/tools/uimanager.c:59: GetMenu; 117: CloseMenu.
- P:/scripts/3_game/constants.c:178: MENU_INGAME=9.
- P:/scripts/3_game/global/game.c:931: GetWorldName(out string).

PASS exige compilación real, marcador VERIFIED_MENU_CLOSED y captura de DayZ
sin menú. Empaquetar/configurar no acredita ejecución. Si no se obtiene,
conservar el fallo; no ampliar reintentos ni cerrar otros menús.
