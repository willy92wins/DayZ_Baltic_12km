**Veredicto: SOUND-with-fixes.** La hipótesis de recuperación es plausible y acotada; la orquestación y la equivalencia JSON son correctas en concepto, pero faltan tres precisiones ejecutables antes de la pareja nativa.

**Hipótesis de compilación (plan:23-24, init.c:219-220).** El error apunta a la línea 220, que concatena `row` más nueve valores con conversiones implícitas bool/float a string: 19 operandos. Las líneas que sí compilaron llegan a 15-16 operandos (init.c:217, init.c:219). Dividir en tres asignaciones de tres valores deja unos 7 operandos por sentencia, muy por debajo del umbral observado. El segundo error "Incompatible parameter ';'" (excerpt:2) es cascada del primero y no exige acción aparte. Riesgo señalado: Enforce reporta un error por sentencia y abortó la compilación, así que init.c:219 con 16 operandos no está demostrada como válida, solo no fue alcanzada por un error. El plan ya admite "fallo reproducido" como salida (plan:58); si ocurre en 219, no es sorpresa ni motivo de reintento interno. Mantener el nombre del log `baltic_contact_b3g.log` sin cambio es obligatorio, porque binding:69 lo fija; la misión nueva solo cambia carpeta y hash del productor, y binding:60 lo recoge vía deployment nuevo. Conteo de campos W verificado: 20, coherente con plan:24.

**Equivalencia JSON número 600 (plan:17-19, 26-28; binding:41-42).** Confirmado: `type(request[k]) is type(v)` con `v=600.0` rechaza un `600` entero aunque `600==600.0` sea verdadero. La normalización en copia previa a `identity()` es correcta y no toca funciones puras. Fix requerido: especificar el normalizador como "aceptar sólo si `isinstance(x,(int,float))`, no bool, `math.isfinite(x)`, `x==600`, y sólo para la clave `wait_for_box_s`"; convertir con `float()` sin esa guarda aceptaría `True` como 1.0 y oscurecería el negativo bool. El recibo crudo `launch.json` sigue hasheándose intacto en binding:83, así que no hay reescritura.

**Orquestación (plan:32-37).** Contradicción ejecutable: "heartbeat oficial cada <=20s" dentro de "un único exec asíncrono" sólo se cumple si la llamada de lanzamiento con `wait_for_box_s=600` es realmente awaitable o devuelve run_id de inmediato. Si la herramienta bloquea hasta 600s, el heartbeat caduca igual que en R0. El plan debe nombrar el mecanismo concreto: tarea concurrente de heartbeat o sondeo no bloqueante; no inventaré la API, Codex debe verificarla antes del code review. Segundo fix: definir `readyUTC` sin ambigüedad. Propongo el instante en que el peer servidor está BOUND con versión ok y poll fresco (binding:48), y exigir que la vigilancia del script log por PID/creation_time detecte el error de misión exacta antes de arrancar la captura. Persistir deadline en cuanto se calcula, no al cierre, cubre el hueco de R0 (plan:14).

**Puertas, presupuestos, negativos (plan:42-54).** Los negativos listados cubren los dos fallos reales y la falsa equivalencia de tipos. Añadir uno: `wait_for_box_s` como string `"600.0"` o como `600.0000001`, para fijar que la normalización es exacta. Presupuestos sin cambios respecto a R0, correcto. Nota no bloqueante: 180s de captura para 270 filas con dos frames y 100ms por punto dan margen de unos 60-80s, pero no autoriza relajar umbral.

**Pareja y aislamiento.** `pair_bound` exige productor y csv iguales entre brazos (binding:89-90); ambos brazos deben usar la misión B3G1, nunca mezclar con R0. Gate `unit_consumed` (binding:35) obliga directorios nuevos, coherente con plan:38.

**Fixes exigidos antes de la pareja nativa:**
- Mecanismo explícito de heartbeat concurrente frente al FIFO de 600s.
- Definición de `readyUTC` y orden detección-error antes de captura.
- Normalizador con guardas int/float, no bool, finito, igualdad exacta, clave única.
- Log filename y `CreateCustomMission` inalterados en la misión nueva.

Nada de lo anterior toca geometría, puntos, agua ni tolerancias. B3G R0 permanece cerrado y sin reintento.

FIN_REVISION