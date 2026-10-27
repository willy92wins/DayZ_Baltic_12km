# Kit7: experimento de navegación de8m preparado

Los cuatro fallos nativos de altura siguen abiertos. Este commit valida las
herramientas y el paquete de entrada del nuevo ensayo; no declara corregidas
las rutas ni contiene una nueva navmesh aceptada.

El único cambio del mundo es GenParams.tileWidth12.5→8. Compilación y nueva
decodificación conservan la semántica de toda la configuración restante;
6826entradas permanecen byte a byte. WRP, modelos, agua y tránsito no cambian.
El NM12.5m conservado en la entrada no es el resultado8m propuesto.

Pruebas finales:14del generador/inspector,3de configuración y7del observador
Windows, incluidas salidas reales de procesos de prueba. El coordinador pasa
19casos y rechaza5mutantes. Un paquete base con hash falso se rechaza antes de
crear salida. Esto no sustituye evidencia del motor DayZ.

Fable5.1 revisó plan y código como SOUND-with-fixes. El presupuesto quedó en
18000s, con observador18300s, sin cambiar los defaults. El límite del bucle se
corrigió para usar tiempo transcurrido:1901respuestas rápidas ya no cancelan
una generación sana y el vencimiento real sí cancela la generación propia.
Fuentes revisadas y resultados previos se conservaron. TIMEOUT es INCONCLUSO.

Siguiente: generación nativa por FIFO MCP, inspecciónTESMv9/VAND12 de8m,
empaquetado sin otros cambios y las mismas607consultas/562corredores, con
0,801m de altura intactos. Después se repetirá RAM frente a Chernarus. Ninguna
predicción offline, éxito de empaquetado o prueba simulada cierra los4fallos.
No aceptación visual, de actores, barcos, FPS ni globalEV112.
