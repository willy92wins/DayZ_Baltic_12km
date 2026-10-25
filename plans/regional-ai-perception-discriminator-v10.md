# Separar percepción de locomoción — base V10

V1 conserva un TIMEOUT en reserva, sentido inverso, caso8: todos los estados
observados tras el spawn siguieron en0. Salud/continuidad/contacto/terreno y
posición del objetivo pasan. La ida del mismo sector sí llegó. No basta para
atribuir el fallo a navmesh. La prueba19 sigue hasta completar sus otros casos.

Una ronda posterior acotada conservará el control local y los casos cuyo fallo
sea únicamente llegada/reacción/tiempo. Cambiará solo la forma de emitir el
estímulo: `AddNoiseTarget(goal,5,noise,4)` sustituye a
`AddNoisePos(prey,goal,noise,4)`, cada3s, mismos puntos/criterios y timeout90s.
El objetivo persistente es una API nativa declarada en
`P:/scripts/3_game/noise.c:9-10`; consumidor vanilla:
`P:/scripts/4_world/static/miscgameplayfunctions.c:1750-1760` y
`P:/scripts/3_game/dayzgame.c:3656-3663`. Rifle_Base/NoiseShoot sigue siendo
strength100/type shot (`P:/DZ/data/config.cpp:4182-4185`). No cambiar terreno,
NM, velocidad, posición ni salud del infectado durante su desplazamiento.

Congelar referencia nueva, conservar IDs originales mediante un campo de origen,
registrar el cambio de estímulo y validar el header nuevo. Si llega, demuestra
locomoción con ese estímulo diagnóstico; no demuestra alcance normal de audición
ni identifica por sí solo el mecanismo interno de V1. Si no reacciona tampoco,
no repetir multiplicadores sin un discriminador nuevo. Un fallo de contacto o
spawn se diagnostica aparte y no se mezcla con esta ronda.

Límite: una variante posterior y una ejecución. Priorizar carga/visual y dejar
el ensayo fluvial largo arrancado antes09:00UTC. La evidencia original nunca se
reemplaza por el resultado de una misión con otro estímulo.

El caso13 añadió una observación distinta: en estado2 salió lateralmente del
tablero y buscó por la orilla. Los anchors muestreados sí dieron alturas del
tablero, pero el consumidor regional anterior solo comprobaba15 rutas terrestres,
no conectividad completa del puente. Antes de variar el terreno se ejecutará
`BalticBridgePathV10`: seis rutas de los casos del puente, dos recorridos completos
y un filtroNONE negativo. Registra todos los vértices de FindPath, terreno y
SurfaceRoadY; se contrastan corredor4m, cota del tablero y altura de la fuente.
Un grafo correcto no acredita el actor; un FAIL localizará el siguiente diagnóstico.

Los spawns posteriores sobre el tablero se observaron aY11.0014, correctamente;
por ello el aislamiento del estímulo puede incluir los casos de puente que
salieron del corredor después del spawn. Su criterio4m/contacto sigue intacto.
La selección permite esos fallos como resultados por discriminar, no como PASS.
Un spawn incorrecto, pérdida de salud, discontinuidad o identidad errónea sigue
excluido. Si el grafo falla, no atribuir su corrección a cambiar el estímulo.

El resultado completoV1 contiene10PASS y9FAIL: tres rutas terrestres agotaron
tiempo y los seis casos del puente no cumplieron el corredor/contacto, aun
cuando tres llegaron. La variante incluye también esas llegadas con trayectoria
inválida; mantiene sus límites. La huella real de Roadway se analizará aparte:
el corredor4m es más estrecho que todo el modelo y no convierte automáticamente
una salida del corredor en caída. V1 permaneceFAIL, sin ampliar su tolerancia.
