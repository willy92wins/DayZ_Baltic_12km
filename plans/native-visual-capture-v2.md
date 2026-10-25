# Capturas nativas para minimizar Computer Use

Las tomas pendientesV1 fallaron por foco/timing o bruma. El mundo no cambió.
[DESIGN] Neva/reserva/sur conservan exactamente poses, cámara y tiemposV1.
SondaV2 pide una captura del backbuffer mediante MakeScreenshot a los25s de
cada pose, únicamente si IsAppActive devuelve true, y registra esa condición.
No manipula ventanas ni entradas. Cualquier foco necesario se agrupará en el
bloque de escritorio; primero probar si el lanzamiento normal ya da foco.

[EXACT] `P:/scripts/1_core/proto/proto.c:136-142`: MakeScreenshot(string name)
guarda DDS bajo `$profile:ScreenShotes` al no empezar el nombre con `$`.
`P:/scripts/3_game/global/game.c:223-227`: IsAppActive indica foco de aplicación.
Mantener registros de posición, dirección, nearplane, clima y restauración.

Aceptar imagen requiere bytes DDS originales, identidad del cliente/PBO,
marca temporal dentro del run/pose, cámara válida y revisión de píxeles. Una
petición de captura, foco true o contador de FPS no bastan. Convertir DDS a PNG
solo decodifica píxeles; no retocar contenido. Conservar intentos fallidos.

Presupuesto: un lanzamiento por grupo y control de foco si es necesario; no
repetir una pose que ya tenga imagen aceptada. Conjunto a4.3km sigue pendiente
porque la bruma oculta terreno; no hacer otra toma idéntica esperando otro resultado.
No presentar esta sonda temporal como arreglo del crash en saltos distantes.
