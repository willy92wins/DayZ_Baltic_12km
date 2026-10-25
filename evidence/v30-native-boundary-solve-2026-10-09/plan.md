# EV52 — resolver la orilla que realmente representa la malla

EV51 conserva topologia y reduce la peor esquina49.345 a45.597 grados, pero no reduce la energia angular1m:3.2823 a3.3635. Se rechaza. El campo de distancia de un objetivo continuo no controla suficientemente su representacion en una malla6m.

Un unico solve restringido en la orilla nativa de Nazia0207. Las intersecciones sobre aristas se calculan directamente desde alturas y nivel, con topologia fija e identidades de arista; no rasterizar un nuevo contorno. Incognitas: solo vertices permitidos que participan en esas intersecciones. Se minimiza la energia de giro de la polilinea a1m, con area igual a fuente, signos mojado/seco conservados, soporte terminal original fijo, limites de altura/fondo/ingenieria y pendientes. El resto del suavizadoEV51 es un punto inicial de autoria, nunca una base promovida.

Presupuesto: una ejecucion SLSQP de100iteraciones, sin segunda semilla ni cambiar pesos/umbrales por los resultados. Consumidor independiente reconstruye triangulos recortados mediante GEOS y mide forma/area/pendientes; mismos gatesEV47/51. Si no converge o no pasa, no empaquetar. Autoria no prueba compilacion ni motor.
