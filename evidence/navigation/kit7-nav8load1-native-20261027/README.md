# Nav8Load1: configuración nativa y navegación verificadas

**PASS local: configuración esperada y las 607 consultas de navegación. RAM pendiente.**
El servidor cargó el paquete f0e0e6b9… en una única ejecución
f6f09de4-8fe7-4947-a695-c284dc042919. El flag OnLoad presenta tipo entero0,
texto1 e int/float1; GenParams permanece texto true con conversión0.
El resto de los nueve controles pasa. No se conoce la implementación interna
del cargador y estos getters no demuestran por sí solos el efecto en memoria.

607 consultas PASS, sin fallos de altura ni continuidad. Se mantienen 0,801m,
0,011m y 2,1m. El despliegue conserva las 6826 entradas distintas de config.bin,
el NM y el WRP. No se regenera navegación. Identidad de proceso, cuatro paquetes,
118 paquetes vanilla, observador de salida, cierre oficial y liberación verificados.

La revisión detectó un capturador PowerShell inválido antes de lanzar; quedó
corregido y probado con siete controles reales. Se conservan el rechazo y la
corrección. Tras capturar, la invocación aislada de Python no encontró un módulo
hermano del lector de configuración. La recuperación revisada añadió la ruta de
importación explícita, ejecutó el mismo lector sin modificarlo y reprocesó el mismo
registro. Tres controles de CLI aislada validan positivo, flag antiguo y UUID
incorrecto. El error original permanece; no hubo otra partida ni otro muestreo.
El lector publicado debe invocarse con el bootstrap documentado en el script de
recuperación mientras se conserva esta cadena congelada.

Esto permite preparar un único bloque nuevo ABBAAB frente a Chernarus, con seis
mediciones y los límites originales. No hay todavía resultado RAM del candidato,
ni aceptación global, cliente/FPS, actores, barcos o revisión visual. Nav8 original
conserva su FAIL RAM. La ampliación del council sigue detrás del trabajo vigente.
