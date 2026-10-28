# B3G1: delta offline validado, aún sin nueva prueba nativa

47testsPASS,3.0s y62,386,176bytes de memoria muestreada; lint1archivo,1.313s.
Fable5.1 revisó plan67.328s y código56.625s; hallazgos adjudicados con negativos.
La primera suite47falló sólo por diagnóstico naive_time frente a clock_not_utc;
se conserva. El helper antiguo YA rechazaba timezone naive; esa parte del
hallazgo fue refutada. Se unifica diagnóstico y exige además offsetUTCcero.

La misión nueva divide una expresión en tres, conserva los20campos W y el resto
de la fuente. El test prueba orden/delta, NO compilación Enforce. Otras fórmulas
largas todavía pueden fallar en el motor. La misión anterior no se sobrescribe.

El wrapper normaliza exclusivamente JSON600/600.0 en copia, rechaza tipos/valores
inválidos y deja el recibo crudo intacto. Conserva identity anterior y exige
UTC, run/PID, ready<=start<=end<=ready+180s y momento de lectura del script log.
El pin declarado de script_log no prueba lectura por sí solo: el coordinador
y consumidor futuros deben fijar sus bytes, frescura, identidad y errores.

Pendiente antes de nuevo DayZ: preparador con nuevos destinos; coordinador con
heartbeat concurrente tras adopción, reloj persistido, vigilancia de error de
misión y finally oficial; negativos/revisión; preflight y pareja nueva única.
No existe ese coordinador todavía. No relanzar B3G R0 ni sus scripts consumidos.
No aceptación física/visual global, ni alteración de los47FAIL/21inciertos.
