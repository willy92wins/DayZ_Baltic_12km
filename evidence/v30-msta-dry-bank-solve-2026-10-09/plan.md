# EV55 - Msta, mantener todo apoyo mojado

FuenteEV54. NaziaEV53r1 demostro un mecanismo compatible entre forma y talud. El Msta tieneP=F=1m en el remate; pertenece a las excepciones de fondo bajo. No se puede imponer fondo>=1m bajo esa lamina ni ahondar/subir sus niveles sin otra politica.

Una unica solucion de minima variacion en los apoyos SECOS del contorno nativo, con los mojados exactos. Dominio: caja heredada del remate, interior y proteccionesEV16; la semilla es la fuente. Misma reduccion minima10% de energia1m, peor esquina y RMSdepliegues no mayores, area constante, signos/conexiones y pendiente conservados, desplazamiento<=4.1m y altura<=1.5m. Fondo y agua exactos, sin reinterpretar la excepcion baja. Recorte analitico de1mm reproduce el dominio del consumidor. Margen numerico interno1e-4, sin relajar el consumidor.

Presupuesto: un SLSQP100iteraciones, sin barrido ni segunda semilla. Si es inviable, mantener la fuente y documentar la restriccion incompatible. Verificador GEOS independiente, float32 y dominio global. Compilacion y motor solamente trasPASS. El Volkhov, con varios nivelesP yF distinto, no se introduce silenciosamente en este caso plano.
