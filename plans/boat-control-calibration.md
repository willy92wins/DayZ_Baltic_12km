# Calibración del control de lancha — 30-09-2026

Continúa P9 y terrain-first sin cambiar terreno, puente, config de la lancha
ni navegación. La prueba anterior no aislaba control/transmisión: acelerador0.22,
motor encendido,3.248m netos y sin lectura RPM/embrague/hélice.

## Discriminador y presupuesto

Una misión nueva BalticBoatCalibration.BalticTrial, con el mismo PBOee93a4c4.
Zona abierta de mar (2000,11200), cuadrado±120m verificado en ASC: cota-12m
en toda la malla6m. Confirmar en runtime mar y profundidad en rejilla24m antes
de crear la lancha. Jugador de ensayo cerca, sin daño, para no confundir ausencia
de streaming con falta de empuje. La lancha conserva daño y física originales.

Una lancha vacía, rumbo norte y sin giro; estabilización10s, arranque/marcha,
tramos de15s a0.22 sin override de embrague,0.22 con embrague0,0.50 con0 y0.75
con0; después acelerador0 y motor parado. Registrar cada0.5s RPM, embrague,
marcha actual/futura/neutra, hélice, autoridad/proxy, actividad física, velocidad
horizontal, posición, salud y profundidad de hélice. Sin moverla por script
después del spawn. Parar a85s, por daño>1, distancia>90m o fondo somero.

PASS de calibración: log nuevo completo, motor compilado y movimiento horizontal
real>10m sin daño/teletransporte, con control y transmisión medidos. No es PASS
de ruta Narva ni tripulante/gálibo. Si no hay empuje, conservar INCONCLUSO y usar
las nuevas lecturas para escoger el siguiente ensayo, sin repetir ciegamente.
Un cambio entre fases secuenciales es indicio, no causalidad aislada A/B/A/B.

## APIs releídas y lados

Todo el controlador y el log ejecutan en MissionServer con IsDedicatedServer;
cliente solo recibe jugador/mundo por réplica nativa. No nuevas RPC ni SyncVars.

- [EXACT] P:/scripts/3_game/vehicles/boat.c:49–61 throttle/steering/clutch;
  :79 RPM, :91–106 marcha/neutra/ShiftTo, :112–115 hélice.
- [EXACT] P:/scripts/3_game/entities/pawn.c:194–203 autoridad/proxy;
  P:/scripts/1_core/proto/enphysics.c:68 dBodyIsActive(IEntity).
- [EXACT] P:/scripts/3_game/entities/object.c:1192 SetAllowDamage(bool),
  aplicado únicamente al jugador de esta misión de diagnóstico.
- [EXACT] P:/dz/vehicles/water/config.cpp:123–146 torque,fricción200,
  rpmClutch1250 y defaultThrust0.75. Que0.22 quede bajo acople es HIPÓTESIS.
- MissionServer/CreateCharacter,CreateObjectEx,CallLater,SurfaceIsSea/SurfaceY,
  GetWaterDepth y cierre de FileHandle: ya compilados en BalticBoat init37f67389.

UI nativa: en la reobservación el proveedor devolvió capturas de Codex con
identificador Terrain Builder. No enviar clics sobre esa captura ni editar
archivos nativos para aparentar una importación. No falta autorización.

## Resultado y segundo discriminador

Run759f03c7, log3bd67650:170 muestras/85s, salud600 constante,0.30m netos.
RPM700, marcha1=neutral1 y hélice0 en todas las fases de aceleración. Lectura
GetClutch=-1832932600 no interpretable; no usarla como evidencia del embrague.
La subida de acelerador no resolvió la transmisión. INCONCLUSO para navegación.

[EXACT] transport.c:251–262 recomienda guardar entradas y aplicar Setters en
OnInput porque otros sistemas pueden sobrescribirlas. BoatScript:342–345 llama
super y no aporta entradas. [HIPÓTESIS] CallLater pierde sus solicitudes frente
a la simulación. Segundo ensayo, una ejecución: mismo mar, barco, física, fases,
límites y mapa; addon de diagnóstico aplica inputs en OnInput y solicita marcha
adelante mientras la marcha futura no coincida. Guarda contador de callbacks.
Opt-in por instancia desde esta misión, dedicado/BalticTrial/autoridad, watchdog
1s de entradas obsoletas con motor parado. Sin RPC ni cambios de pose/velocidad.
No declarar causalidad separada del cambio de frecuencia de ShiftTo; aisla el
conjunto del mecanismo de control. Si falla, conservar evidencia y cambiar de
estrategia tras leer nuevas métricas; no alterar el cauce para compensarlo.

Antes del segundo run, reforzar la aceptación contra deriva: además de10m,
exigir10 muestras consecutivas a0.5s con motor encendido, RPM>800 (ralentí medido700),
marcha distinta de neutra, hélice girando y velocidad horizontal>0.5m/s.
No basta desplazarse por oleaje. El control negativo modifica únicamente posición
y velocidad del log sin propulsión; debe seguir INCONCLUSO. No es evidencia real.

## Resultado OnInput y retorno al cauce

Run31271ac6: PASS_CALIBRATION_MOVEMENT_ONLY,116 muestras hasta la parada por
distancia,89.278m entre primera/última muestra y85 muestras consecutivas de
propulsión, salud600 intacta. Fase0.22 avanzó10.5m antes del override de embrague;
fase0.22 con override avanzó18.1m. No separar causalidad del callback/ShiftTo ni
deducir acelerador interno del GetThrottle leído después: informó0 mientras
RPM/hélice/movimiento sí respondían. Fuente9b29af8f, análisis y log preservados.

Siguiente ensayo único: misma ruta piloto original de120m bajo puente, barco
vacío y mismo terrenoee93a4c4; sustituir las entradas CallLater por el mecanismo
validado OnInput, throttle0.22 y clutch0. Mantener180s y daño>1; añadir guardia
de distancia al eje6m. Steering positivo por error de rumbo sigue HIPÓTESIS,
el desvío acotado la discrimina. No mover posición/velocidad por script.
La aceptación local requiere muestras continuas a ambos lados del puente,
avance propulsado, ruta alcanzada y salud constante. No cubre tripulante,
regreso, barco mediano, navmesh ni red regional. No iterar si falla sin medir causa.

## Resultado del cruce y discriminador de continuidad

Run ca8a8d0f llegó con salud600, pero el verificador estricto rechazó un hueco
de2.387s entre t0.994 y3.381 (motor apagado, deriva0.022m). Evidencia completa
conservada en route-input-complete-v1; no se cambió el criterio para aceptarlo.
Repetición acotada, una ejecución solo servidor con misión/control/mapa idénticos:
run c9dc7555,226 muestras sin huecos,196 consecutivas de propulsión, llegada,
paso bajo vano central, salud600. PASS_EMPTY_BOAT_LOCAL_OUTWARD sin cambios del
verificador. La ausencia del hueco no demuestra su causa interna; no hay prueba
visual cliente ni tripulación. Evidencia route-input-server-v1, log8ad568ff.
Seis negativos sobre ese registro medido rechazados por el gate correspondiente.
Ambos runs cerrados por MCP, forced_kill/exit_metrics_valid=false, sin lease vivo.
