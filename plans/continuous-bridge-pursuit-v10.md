# Persecución continua desde tierra — discriminador del puenteV10

Pregunta distinta de los ensayos de ruido y actores creados sobre el tablero:
¿un infectado vanilla puede entrar desde tierra y seguir físicamente a un
jugador que camina por el puente entero, en ambos sentidos? BALTIC-002 permanece
abierto. No cambiar WRP/NM/modelos, ni promover esta prueba antes del motor.

Fuente de movimiento humano ya probada:
`tests/walk-probe/baltic_walk_probe/scripts/5_Mission/BalticWalkProbe.c`.
Las firmas vivas se verifican antes de escribir la variante. El infectado no
recibe velocidad, rumbo, animación ni posición después de su colocación inicial.
El jugador usa entrada nativa de caminar y un objetivo al otro extremo; nada
de teleport por frame. Una posición inicial por caso, seguida de20s de reposo.
Daño del jugador deshabilitado durante el ensayo, igual que en las pruebas
anteriores, sin curar al infectado.

[DESIGN] Un control de terreno abierto y dos recorridos del eje de Narva,
desde estación−160m a+148m y desde+160m a−148m. El objetivo humano comienza12m
delante del infectado. El actor se crea en tierra antes del acceso y su llegada
exige alcanzar el objetivo más allá del extremo opuesto. Registrar posiciones
de ambos, salud de ambos en servidor, mente, rumbo/dirección, SurfaceY y
SurfaceRoadY, sincronización de fase y entradas solicitadas al jugador.

Congelar referencia float32 y alturas antes del motor. Mantener contacto
−0.2..+0.5m, corredor±4m, hueco de muestra≤1s, error de terreno≤2mm, salud del
infectado positiva y radio de llegada4.002m. El objetivo se mueve ahora por diseño;
su gate es movimiento continuo, contacto y corredor, no la antigua deriva2m
para objetivos estacionarios. Exigir una fase de persecución real y distancia
recorrida completa sin writes de pose. Timeout500s por cruce;1200s globales,
incluyendo control y reposos. Control local fallido invalida el estímulo, sin
concluir falloNM. Revisado antes de implementación:10min no cubrían dos timeouts
de500s, por lo que se reserva este presupuesto coherente y acotado.

Una ejecución inicial después de carga, cauces largos y vistas regionales,
si quedan al menos25min antes del cierre10:42:43UTC. No declarar causa raíz por
una comparación no aleatoria. Si pasa acredita este consumidor continuo; V1/V2/V3
siguen conservadas con sus propios resultados. Si falla, archivar la trayectoria
y dejar BALTIC-002 abierto con la localización real; no estrechar el área probada
ni relajar sus criterios para producir PASS.

## Preflight 09:04 UTC
Antes del primer arranque se cambia el identificador `event` por `marker`; `event` es modificador del lenguaje en `P:/scripts/1_core/workbenchapi.c:111`. La referencia inicial y su init se conservan en `continuous-pursuit-v1/preflight-identifier-fix`; el arranque usara `reference-r2.json`. PBO, geometria, entradas y criterios sin cambios. El verificador serializa discontinuidades de velocidad como null y FAIL, nunca Infinity en JSON.

## Preflight: autoridad de movimiento
La prueba anterior de marcha demostro correcciones de red cuando solo el cliente usaba overrides. Se incorpora el mismo control humano en servidor, fuente `missions/BalticWalk.BalticTrial/init.c:178-183`, preservando r2 e init en preflight-authoritative-input. Arrancar con `reference-r3.json`; las referencias anteriores quedan historicas. El infectado no recibe overrides. Criterios y PBO iguales, init revisado antes de ejecutar.

Referencia de arranque definitiva antes del motor: `reference-r4.json`. La revision r4 evita redeclarar `MissionServer.m_Players`, definido en la fuente vanilla :7; usa una coleccion propia con nombre especifico. r3 e init anterior conservados. La auditoria de campos heredados se hizo antes de gastar otro arranque.
