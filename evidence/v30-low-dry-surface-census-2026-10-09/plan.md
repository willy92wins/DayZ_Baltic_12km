# EV45 — índice no visual de tierra baja seca en todo el mapa

Consumidor de los 8.380.418 triángulos nativos de EV25/28. Hallar el área exacta con terreno sobre el máximo del mar medido (0,85 m), sobre el plano físico P y el visible F, y bajo el objetivo de tierra seca de 1,80 m. Se usa 1,79999 m para no clasificar la meseta float32 de 1,80 m por ruido de redondeo. P y F congelados, nunca reconstruidos desde clases/niveles.

La geometría de cada cara se recorta por tres desigualdades lineales. Solo unir partes con contacto de longitud positiva; esquinas que apenas se tocan no son una conexión. Inventariar áreas, coordenadas, relación con agua y presencia de ingeniería/Narva. Vincular el punto residual y las alertas condicionales A2 de EV43.

La banda no diagnostica el shader ni certifica que no haya reflejos por encima de ella: es un índice global de candidatos basado en el objetivo existente y la observación local. No subir todo lo detectado ni tocar carreteras/agua por tener una alerta. Una ejecución y controles analíticos de área, exclusión de agua prevista y conectividad. No mapas nuevos ni runtime.
