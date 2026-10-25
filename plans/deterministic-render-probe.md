# Comparación visual automática

Petición viva: Guillermo se ausenta y pide continuar hasta arreglar el mapa.
El render global fue rechazado; baseline3c3a restaurado por hash. Se crea un
instrumento temporal de prueba para comparar siempre las mismas cuatro cámaras,
con clima seco y sin depender de teclas ni clics.

La misión de servidor es una copia nueva BalticRender.BalticTrial, con economía
vacía y fuente de alturas existente. Ajusta clima solo dentro de esta misión.
El addon temporal DIAG_DEVELOPER modifica cámara solo en cliente/BalticTrial.
No añade RPC ni consola, no acepta órdenes externas ni modifica el MCP.

APIs leídas de la instalación: Camera.SetActive/LookAt/SetFOV y
FreeDebugCamera.GetInstance/SetFreezed en scripts/3_game/entities/camera.c;
Object.SetPosition/SetOrientation en entities/object.c:300,317;
MissionGameplay.OnMissionStart/OnUpdate/OnMissionFinish en
scripts/5_mission/mission/missiongameplay.c:186,278,257.
WeatherPhenomenon.Set/SetLimits en weather.c:49,74; Weather.MissionWeather:383.

Presupuesto: cuatro vistas, 235 segundos desde que existe jugador; salida normal
restaura cámara y congelación anteriores. El log prueba las poses y el clima,
las capturas nativas prueban el resultado visible. Si no se ejecuta o no concuerda
la cámara, INCONCLUSO. No confundir compilación offline con ejecución.

Lifecycle por tools MCP, lease durante la prueba y renovación mientras está
activa. Al terminar, retirar el addon temporal por hash, conservar evidencias y
dejar solo el paquete de mapa aceptado. No introducir dependencia de este addon
en la entrega jugable.
