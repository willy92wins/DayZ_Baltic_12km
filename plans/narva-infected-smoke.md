# IA real en Narva: estímulo vanilla y trayectoria de servidor

P4 y pendiente de navegación: FindPath encuentra cruce, pero SampleNavmeshPosition
difiere0.833077m del acceso oriental. El actor real es un consumidor independiente;
no cambiar ese umbral ni modificar navmesh a ciegas por una aproximación del grafo.

API y consumidor [EXACT]: scripts/3_game/global/game.c:702,704 CreateObjectEx y
ObjectDelete; entities/dayzinfected.c:106 GetInputController; inputcontroller.c:9
GetMindState; noise.c:10,22 AddNoiseTarget/LoadFromPath. Consumidor vanilla:
dayzgame.c:3488 y trapspawnbase.c:649. Config real DZ/data/config.cpp:4033,4182:
CfgWeapons Rifle_Base NoiseShoot, strength100/type shot. DZ/characters/zombies/
config.cpp:3115 ZmbF_JournalistNormal_Blue. ce/centraleconomy.c:16,17,37 flags.

[DESIGN] Misión aislada, mapa ebc60f4f, observador humano fuera de vista del puente.
Crear un infectado vivo cada vez; solo estímulo de ruido en el destino, sin
override de velocidad/heading, waypoints inventados ni SetPosition tras nacer.
Tres etapas: control local en ribera oeste, oeste→este, este→oeste. Ruido de5s
repetido cada3s; dejar6s entre etapas para caducar estímulos previos.90s máximo
por etapa; detener si falla inicialización/control. Al final borrar solo actores
creados por esta misión. No disparar arma ni aplicar daño para el estímulo.

Registro servidor cada0.2s: tiempo/etapa/posición/salud/estado mental/objetivo.
PASS físico del cruce: alcanzar d>=25 desde d<=-28 (y viceversa), muestras
continuas por vano abs(d)<=12.5, altura pies>=1.7, corredor lateral<=2.5m,
salud>0, sin grandes saltos entre muestras. Control local debe mostrar alerta
y avance>=12m al destino. Estímulo sin respuesta = INCONCLUSO, no fallo de puente.
Una ejecución y hasta dos reparaciones de compilación/control; no ajustar geometría
ni ampliar criterios para lograr PASS. Separar navgraph, respuesta de IA y físico.

## Ejecución y reparación 1

El run aa6ffd15 terminó por access violation a los86s de misión. Stack nativo:
ObjectGetType -> init.c:74 Record -> OnUpdate. Se llamó GetType sobre el retorno
de GetTargetEntity después de comprobarlo como verdadero. La fuente declara
EntityAI, pero eso no acredita una referencia desreferenciable en este caso.
No atribuir el crash al terreno o a la navmesh. Se conserva script/log/crash
en evidence/infected/noise-v1-*. La reparación retira únicamente esa lectura;
registra target_entity=not_read y mantiene estímulo, recorrido y umbrales.

Datos de esta misión: actor, posición, salud, mente y estímulos solo servidor;
cliente observador recibe replicación vanilla. Sin RPC, overrides ni estado
nuevo sincronizado. La misión de entrega BalticTest no incluye este experimento.

Verificador offline: recomputar eje y lateral desdeXYZ, no aceptar columnas
d/cross como oráculo. Antes de completar cruce se fijan gaps<=0.6s, pasos3D<=2.5m
(sprint vanilla máximo9m/s, muestreo0.2s),10 muestras mínimo de vano por sentido,
pies1.7..2.4m y lateral2.5m sobre vano. No limitar el camino libre en la ribera
al corredor del puente. Exigir marcasREACHED y finalCOMPLETE_ALL_STAGES.

## Reparación de control2: objetivo humano real

Noise-v2 no volvió a producir crash y completó control local; etapa1 terminó
TIMEOUT a133.34s en d22.26/lateral8.84. Recorrido salió del corredor2.5m,
por tanto no pasa aceptación. No borrar este resultado ni ampliar tolerancias.

Misión separadaBalticChase: único jugador de ensayo colocado antes de nacer
cada actor en destino (control-60, cruce+30, retorno-30), invulnerable durante
el ensayo. Solo se mueve el humano entre etapas; IA conserva movimiento nativo.
Ruido asociado al humano por AddNoisePos, no al punto sintético. Mantener90s,
mismas anclas de inicio, umbrales y verificador; no leerGetTargetEntity.
APIs[EXACT]: object.c:300 SetPosition,1192 SetAllowDamage; noise.c:7 AddNoisePos;
consumidor servidor actionopendoors.c:81 lo usa con action_data.m_Player.
Invulnerabilidad se restaura al cierre de la misión propia. Esto prueba un
estímulo humano más apropiado; no demuestra qué target interno elige el motor.
