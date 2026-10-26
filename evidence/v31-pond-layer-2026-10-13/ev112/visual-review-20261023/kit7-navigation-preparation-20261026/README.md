# Kit7 — navegación preparada, sin generación

La puerta física ya pasa6801puntos con cero fallos. Este checkpoint prepara
la generación propia del kit7; **no contiene una navmesh nueva ni un PASS de IA**.
El banco compartido mantenía la reserva de otra prueba H2R al guardar el estado.

El coordinador conserva la generación observada de C y fija exactamente el
nuevo mundo,piloto,agua,bridge y motor. Fable5.1 encontró cinco defectos; todos
se corrigieron y la segunda revisión dioSOUND. El cambio posteriorv3 proyecta
solo tres campos del manifiesto al runtime JS para evitar truncar la salida;
la verificación completa de hashes sigue ejecutándose sobre el archivo.
El único fallo de preparación ocurrió antes de cualquier llamada de lanzamiento.
Cero intentos de generación consumidos.

Pruebas:17escenarios de flujo y3mutaciones,2casos de lease,8casos del wrapper,
7ejecuciones reales del PowerShell de identidad(incluidos6rechazos), métodos
JS comprobados en Functions y lectura real del manifiesto de714caracteres.
Los controles simulados no sustituyen un servidor ni una generación nativa.

Siguiente: consultar session_status y solo con banco libre ejecutar
orchestrate_nav_kit7_v3.js mediante Functions; mantiene heartbeat,captura del
generador y cierre oficial propio. Presupuesto7200s,observador7500s,un intento.
Después inspeccionar TESMv9, empaquetar exclusivamenteNM y probar45regresiones
más rutas específicas del kit7 que demuestren atravesar la superficie nueva.
La vista humana y locomoción real siguen separadas.
