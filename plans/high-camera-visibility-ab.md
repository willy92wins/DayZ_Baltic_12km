# Discriminador de cámara alta y distancia visible

Condición inicial: el arco blanco aparece con cámara a1300m; el perfil real
`P:/DayZ_MCP_dev/_client/profiles/Users/Dev/guill_settings.DayZProfile:26`
contiene viewDistance=1600. Esto es una hipótesis, no un diagnóstico confirmado.
Preparar esta prueba solo si el ensayo de síntesis exterior tampoco lo resuelve.

Contrato: addon DIAG temporal, solo MissionGameplay/BalticTrial; sin RPC ni
actores. Cámara y visibilidad pertenecen al cliente, sin datos replicados.
Cuatro fases en la misma pose SPB:1600→6000→1600→6000m. Mantener PBO del mapa,
fecha y clima. Registrar pose asentada y distancia solicitada; la API no expone
getter de distancia efectiva. No afirmar que el motor aplicó6000 solo por log.

API [EXACT] leída: scripts/3_game/global/game.c:930 GetWorld();
scripts/3_game/global/world.c:71 SetViewDistance(float). No usar el setter
persistente SetPreferredViewDistance. Restaurar1600 al finalizar y conservar
hash del perfil antes/después. API cámara/registro es la del fixture regional
ya ejecutado; conservar su restauración de estado.

PASS causal acotado: blanco con1600, ausente con6000, reaparece al volver1600 y
desaparece otra vez6000, con las cuatro capturas y registros concordantes.
FAIL: blanco persiste en ambas distancias. INCONCLUSO: cambia pose/clima, falta
captura o el motor no ejecuta la sonda. No convertir un resultado en obligación
de imponer6000m a80–100 jugadores ni modificar opciones del usuario globalmente.
