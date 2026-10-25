# EV76 — lectura nativa para localizar los rectángulos

Run `3b4a4a81-09ea-452f-aaaa-a31917f42f89`, mapa EV72 original: mundoa08b96a1,agua3946db8b. Sonda de sólo lectura `@BalticWaterProjectionV2` SHA57971ccf, derivada de la sonda comprobada EV43 y con16puntos alrededor del puente. Se verifica el script incluido dentro del PBO real y el lint de2archivos sin errores.

Pose exacta de EV73: cámara[2417,65,6745],dirección[0,-0.3022438586,0.9532306194],FOV solicitado1.1. La sonda lee `Camera.GetCurrentFOV=1.1` y1920×1080. `camera_get.fov=0` no era el FOV nativo leído. Perfil persistido33ccbabd idéntico al de EV74 y al cierre. No cambia terreno, agua, materiales, opciones ni clima por la sonda.

La espera por substring `2417 65 6745` agota30s porque el log serializa vectores como `<2417.000000, 65.000000, 6745.000000>`. El log sí contiene muestras completas; no se repite la espera ni se confunde su patrón incorrecto con fallo de proyección.

La captura nueva tiene cielo magenta y terreno sin textura: INVÁLIDA para aceptación visual. La proyección devuelve datos independientes de carga de texturas. Se compara con el frame EV73 `capture_20261009_233431_541.jpg`, de igualpose/FOVsolicitado/perfil/viewport. Esa transferencia debe declararse; no fingir que se ha identificado el material del parche.

Cliente y servidor cerrados orderly, ambos terminan y logout confirmado. Lease liberado, `session_status` sin ocupación. No se pidió foreground ni se lanzó el candidato rechazado EV75. Análisis de calibración y de fronteras de objetos en curso por dos Luna; no emitir veredicto visual antes de revisar los datos.
