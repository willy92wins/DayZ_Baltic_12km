# Prueba de foco y carga de teselas

Se reprodujo la carga incompleta en la reserva y se observó su recuperación al devolver el foco a DayZ. **Es una mitigación comprobada en este caso, no una corrección del motor ni el cierre global de BALTIC-019.** No se cambiaron PBO, materiales, perfil gráfico, hora ni clima durante el ensayo.

Run `71f340c9-14e3-4df4-b267-b4c5d4ac25a4`, Floor095Preview. Inicio con foco: suelo y cielo cargados. Las vistas media y lejana muestran texturas, con el alcance de esas poses. Tras volver a segundo plano, la escena cercana conserva las texturas durante 68,546 s y la matriz de cámara permanece exacta.

Al teletransportar al jugador a la reserva y situar la cámara en (7920,155,4940), el suelo aparece gris. A los 68 s carga una parte por la derecha, pero a las 12:51:20.552 continúa incompleto. La siguiente muestra, a las 12:51:21.574, registra foco y muestra las texturas pendientes. Ambas imágenes se conservan sin editar en `transition/`; la matriz de cámara anterior y posterior coincide exactamente.

El foco posterior fue intermitente: las primeras siete muestras fueron positivas, seguidas de varios cambios. No se acredita una permanencia continua de 20 s. Tampoco se mide residencia de recursos interna: las imágenes prueban el cambio visible y su coincidencia temporal con el cambio manual de foco. Parte del mapa cargó sin foco, así que «sin foco no carga» sería incorrecto.

La vista baja posterior de la reserva conserva el terreno texturizado. No basta para aceptar visualmente toda la reserva o San Petersburgo. Las alertas `render_frozen_signal` del capturador también aparecen en escenas estáticas válidas y no son por sí solas un fallo de texturas.

Uso para las siguientes revisiones: no aceptar una vista gris como defecto del material; comparar la misma cámara después de una carga visible completa. Si reaparece en segundo plano, usar un breve cambio manual de foco y registrar el resultado. No robar el foco por script ni declarar PASS por el umbral de `dark_tiles_v30.py`.

`record.json` conserva cámaras, capturas y ciclo de vida; `result.json` conserva intervalos de foco, hashes y limitaciones; los CSV originales incluyen el hueco entre las dos sondas. El primer arranque agotó el presupuesto de servidor de 1 s y se limpió; el segundo, con 20 s, inició este run. Los dos primeros intentos de cámara omitieron `cam_mode=matrix` y fueron rechazados; sus capturas son de gameplay y no se usan como comparación de cámara fija.

Cliente y servidor cerrados con `orderly_close`, líneas de terminación de ambos y run retirado. Lease liberado; owner=null, occupied=false, runs=[], pending_commands=0.
