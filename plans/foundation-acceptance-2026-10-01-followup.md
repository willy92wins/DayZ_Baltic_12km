# Continuación de la base V10: pruebas sin bloquear el escritorio

Petición viva: continuar la base del mapa y agrupar/minimizar Computer Use.
Sesión única executor/integrador. Deriva de foundation-acceptance-next.md,
P9/P10/P11/P13. No cambia encuadre, terreno, WRP, navmesh ni paquete entregado.
El archivo nocturno permanece inmutable. Evidencia nueva en
`evidence/foundation-followup-2026-10-01/`.

## 1. Cauces: BALTIC-003 y BALTIC-004

[EXACT] `missions/BalticFullRiverV2.BalticTrial/init.c:58,95-107,122-138`
controla cada100ms, registra cada500ms y corta motor dentro de4m del destino.
La parada terminal espera10s sin medir velocidad nula. El controlador desplegado
`packages/boat-input-v2b/compiled/baltic_boat_input/scripts/4_World/BalticBoatInput.c:12-52`
admite throttle0..1 y engrana avance; forward=false selecciona neutral, no reversa.
`tools/navigation/verify_regional_boat_consumer.py:62-77` congela los límites
físicos, incluidos radio final6m, corredor7m y máximo salto de índice2.

[DESIGN] Misión nueva V3, mismos puntos/agua/mapa y addon de entrada. Primera
prueba: control11 y casos fallidos6/8/10. Registrar cada transición de objetivo
con índice anterior/nuevo, tiempo, posición y distancia; emitir también muestra
física en ese tick. Mantener además el muestreo500ms. Reducir velocidad solicitada
en los últimos20m a0.8m/s y en los últimos8m a0.5m/s, mediante corte de throttle;
declarar llegada solo dentro de1.5m y a<=0.8m/s, después observar10s con motor
apagado. No escribir pose/velocidad después del spawn. El texto heredado
ARRIVED_AND_STOPPED significa llegada y motor apagado, nunca inmovilidad.

Datos: mando, posición, salud, agua y log son exclusivamente servidor. No cliente,
RPC, teclado, ventana ni cámara necesarios. Posición precisa mediante el formato
vectorial ya validado. No se requiere modificar ni empaquetar el addon.

VERDE: mismos gates físicos originales, secuencia completa de transiciones
contiguas1..N-1 contrastada con las muestras y geometría, salud conservada,
distancia terminal<=6m y motor apagado durante observación. FAIL previo permanece.
Contrapruebas cerradas: terminal ausente, caso ausente, posición no finita, salto
físico, salud reducida, tierra incorrecta, transición omitida/duplicada/índice
saltado/tiempo desordenado, marcador de llegada sin movimiento y motor final activo.
Prueba contra un positivo real; no declarar PASS por texto de código.

Presupuesto: una implementación de la sonda y hasta dos ejecuciones físicas
guiadas por fallos concretos. Si no converge, registrar el discriminador que falta
y cambiar a otro gate; no ampliar tolerancias. Por caso<=4200s y cierre del run
exacto al terminar. Antes del arranque: hashes de mapa/addon/misión y lint.

## 2. Puente: BALTIC-002

Mientras el servidor fluvial trabaja, inspeccionar sin mutarlo los controles de
humano en cliente/servidor y los logs V1/V2/sin-infectado. Verificar API antes de
instrumentar estados de comando, combate y movimiento. Elegir un discriminador
acotado por mecanismo observado; fijar referencia antes de lanzar. Ningún cambio
del terreno/navmesh por una sonda que desvía al personaje. Nunca desreferenciar
GetTargetEntity().GetType() en esta investigación.

## 3. Escritorio y cierre

Computer Use solo cuando la observación visual o una herramienta nativa lo exija.
Preparar todos los archivos antes; anunciar el bloque, observar, operar y liberar.
No reservar el escritorio durante cálculos, logs, pruebas de servidor o esperas.
Lifecycle solo DayZ MCP con identidad de run; lease para trabajo exclusivo activo
y liberar antes del cierre high-level. No tocar procesos ajenos ni reactivar la
automatización nocturna ya terminada. Actualizar HANDOFF y conocimientos verificados.
