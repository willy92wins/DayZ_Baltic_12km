# Cruce a pie autónomo: ensayo acotado

Producto P4: cruce jugable entre ambas riberas; las consultas de altura no prueban
locomoción. El paquete5030cb74 corrige los rectángulos en cuatro cámaras; este
ensayo no edita WRP, alturas, materiales ni navegación.

[EXACT] P:/scripts/3_game/human.c:6-11 enum de override; :234,237 velocidad/ángulo;
:25 GetMovement, :28 GetHeadingAngle (radianes), :1424 GetInputController,
:1486 GetCommand_Swim. P:/scripts/1_core/proto/enmath.c:16,399 RAD2DEG/Atan2.
P:/scripts/3_game/entities/object.c:990 GetHealth.
P:/scripts/5_mission/mission/missionserver.c:102 OnUpdate y :243 GetPlayers.

[DESIGN] Addon temporal DIAG/cliente/BalticTrial, misión independiente sin CE.
Spawn inicial en acceso oeste ya medido. A los10s, usar movimiento normal con
velocidad1 hacia el acceso este; pausar3s y regresar. No SetPosition ni
teletransportes durante el recorrido. Desactivar overrides al acabar/abortar.
Registro cliente de inputs/posición cada0.25s y servidor independiente de la
posición/vida/nado. Timeout150s; abortar si se separa más de3m del eje. La salud se valida en el registro servidor. Un ensayo inicial; si el control no mueve como se espera, INCONCLUSO,
no atribuirlo al puente. Correcciones de compilación hasta2; no bucle ilimitado.

[HIPÓTESIS A VERIFICAR] OverrideMovementAngle usa grados relativos al heading;
la firma no declara unidad. La trayectoria/GetMovement deben demostrar la
dirección real antes de aceptar el recorrido. No usar la orden como evidencia.

PASS: servidor observa oeste→este→oeste (d<-28, d>28, d<-28), pasos intermedios
continuos por el tablero, error lateral<2.5m, Y>=1.7m sobre su vano, salud>0,
sin comando de nado, con cliente terminado y paquete comprobado por SHA.
FAIL: atasco o caída con control correcto. INCONCLUSO: control/carga/log ausente.
Vehículo, IA, CE y80–100 quedan fuera de este gate.

Preparación del consumidor: primer arranque rechazó concatenar un float como
primer operando del CSV; corregido a cadena inicial. Segundo arranque compiló,
pero el guard cliente leyó salud0 mientras el servidor leía100 y abortó antes
de aplicar movimiento. Se retira ese guard cliente; salud sigue siendo criterio
obligatorio del servidor. No representa caída ni fallo de locomoción.

La unidad del ángulo ya está observada:98.753grados produce dirección local
(0.988353,0,-0.152176). El primer control aplicado solo en cliente mostró
predicción oscilante de menos0.3m y servidor inmóvil, por lo que es INCONCLUSO
para locomoción. Se permite un discriminador adicional: aplicar el mismo
control en servidor, conservando registros separados y sin SetPosition.
Máximo120s desdeinicio del driver servidor; si tampoco hay avance, cerrar y
marcar pendiente la interacción real, sin modificar la geometría.
