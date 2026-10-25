# EV53 - orilla y talud como restricciones simultaneas

EV52 redujo demasiado una unica magnitud: la energia del contorno. Su mejora del 64% en la orilla empeora el RMS de pliegues nativos de8.581 a9.246 grados. Se conserva rechazado. EV51 ya mejora los taludes pero su orilla no alcanza la mejora minima existente.

Cambio de mecanismo: buscar el menor cambio respecto al perfilEV51 que satisfaga a la vez energia angular <=90% de fuente, peor esquina no mayor, RMS de pliegues no mayor, area exacta, pendiente y limites de altura anteriores. No se busca reducir indefinidamente el contorno ni variar radios. Fuente aceptada sigueEV25, semillaEV51 nunca promovida.

Presupuesto: un SLSQP de100iteraciones y una semilla, sin segunda ejecucion modificando parametros. Antes de resolver, el subconjunto local de pliegues debe reproducir el RMS y numero de pliegues incidentes del consumidor global. Despues, reconstruccion GEOS independiente y todos los gatesEV52, sobre float32 guardado. Exigir convergencia y gates; no empaquetar un fallo. Sin cambios fuera de la banda autorizada, fondo>=1m, punta mojada conservada. No representa cierre de toda la superficie.

Correccion de instrumentacion antes de ejecutar el optimizador: la primera igualdad de numero de pliegues fallo porque el borde izquierdo tenia un solo vertice de margen y un pliegue une dos triangulos. Ampliar exclusivamente el parche de normales con dos filas/columnas fijas; no cambiar dominio, semilla, restricciones ni presupuesto. Mantener las dos igualdades contra el consumidor global.
