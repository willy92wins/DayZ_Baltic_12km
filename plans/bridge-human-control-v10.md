# Control humano sin infectado — antes del motor

2026-10-01 10:16 UTC. V2 de persecucion termina FAIL: jugador6.003488m lateral,
pico horizontal9.236822m/s y retroceso, aunque ambas entidades conservan salud100
y Y11 en la ultima muestra. Actor contactoPASS, maximo5.508567m lateral. La
prueba del puente completo sigue incompleta; no identifica falloNM ni colision.

[DESIGN] Mismo controlador humano V2 en cliente/servidor, sin crear infectado ni
ruido. Dos casos: control local y recorrido este de296m desde el mismo origen
del humano. Misma referencia geometrica/tablero6m-acceso4m, asentamiento20s,
salud, continuidad1s, velocidad4m/s y radio2.002m. Una colocacion inicial por caso,
ninguna escritura de posicion despues. Congelar referencia y PBO antes del run.

PASS requiere trayectoria fisica completa del humano sin actor, contacto
-0.2..+0.5m y altura de terreno corroborada con ASC2mm. FAIL local invalida el
controlador; FAIL puente sinAI demuestra que no hace falta infectado para ese
sintoma, no su causa raiz. PASS sinAI tampoco prueba causalidad unica del actor:
es una observacion no aleatoria. No acredita locomocion AI ni cierra BALTIC-002.

Presupuesto: una ejecucion,90s local y500s puente,700s globales y cierre duro de
la prueba propia antes10:33UTC para dejar margen de entrega. No cambiar WRP/NM.
APIs ya usadas: P:/scripts/3_game/human.c:25,28,234,237. Verificar paridad de mod y
mision; conservar logs, emitir negativos contra un control positivo real y cerrar.
