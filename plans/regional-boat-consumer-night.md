# Lancha: consumidor regional nocturno

Continuación de P9, sin mapeado. Fijar antes de ejecutar cuatro recorridos
simples de los ejes regionales: Narva (bajo el vano oeste), Luga, Neva y delta.
Cada recorrido se ensaya en ambos sentidos con lancha vanilla vacía; son dos
spawns independientes, no una prueba de giro ni de tripulación. El modelo de
agua y todos los vértices de los cauces V9 permanecen exactos en V10; aun así,
repetir Narva después de cambiar los puentes, porque sus colisiones cambian.

Manifestar geometría, alturas, CSV, fuente de misión, addon de OnInput y PBO
desplegado por SHA antes del motor. El servidor crea una sola Boat_01_Orange,
la orienta durante el spawn, pone bujía y combustible, espera15s y arranca.
OnInput transmite acelerador/timón/marcha; sin SetPosition, SetVelocity ni
impulsos durante la prueba. Solo actores propios y un mundo BalticTrial.

Puertas independientes del texto final de la misión: registro completo de los
ocho casos, reloj monótono y muestras<=0.8s, pasos<=3m, sin pérdida de salud>1,
corredor<=7m, llegada<=6m, cobertura de cada punto intermedio<=7m, callbacks
de input crecientes y un tramo sostenido de movimiento con motor/marcha/RPM/
hélice. Comparar elevación del fondo en la posición realmente recorrida con
el ASC desplegado. Un marcador de llegada o una trayectoria solicitada no basta.

El controlador para ante daño, desvío, apagado o timeout450s por caso; apaga y
elimina su propia lancha antes de pasar al siguiente. Al terminar retira su
timer. La navegación antigua de la primera prueba solo arranca la misión:
no prueba IA. Cuatro sectores no acreditan todos los kilómetros de río.

Fuentes instaladas reancladas: scripts/3_game/vehicles/boat.c:49–158;
scripts/3_game/global/game.c:702–704,1162–1187;
scripts/3_game/entities/object.c:293–317,869,990;
scripts/1_core/proto/enphysics.c:104. Controlador existente medido:
packages/boat-input-v2b/compiled/baltic_boat_input/scripts/4_World/BalticBoatInput.c.

## Revision de telemetria, 01-10 05:01 UTC

V1 completo: Luga ida/vuelta PASS; Narva timeout sin dano cerca del puente;
Neva/delta llegan con todos los checks de movimiento PASS, pero la comparacion
SurfaceY falla hasta12.465mm. Se conserva FAIL. Discriminador mismo tick:
ARRIVED contiene vector a6decimales y B concatena escalares redondeados (z a0.1m).
En los ticks caso4/6, usar el vector del mismo instante reduce error3.50/6.58mm
a0.004/0.097mm. Evidencia runtime-complete/position-rounding-discriminator.json.
No recuperar coordenadas inexistentes ni convertir todo V1 a PASS por ese dato.
[DESIGN] V2 conserva ocho rutas/criterios y control; agrega a cada B el vector
posicion completo (campo23). El consumidor V2 lo exige y comprueba compatibilidad
con los escalares antiguos, formato finito y esquema exacto. Nuevas referencias
fijan WRP/PBO/ASC V10 antes de ejecutar. Probar controles positivos y negativos
(mal vector, falta de vector, vector incompatible, terreno realmente distinto).
Fuente real: P:/scripts/1_Core/proto/enconvert.c:115,145; vector.ToString() verificado.
