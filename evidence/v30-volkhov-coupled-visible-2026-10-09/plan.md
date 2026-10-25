# EV56 - remate Volkhov con P/F distintos y contorno cerrado

FuenteEV55(Msta) sobreEV54. Descubrimiento: P tiene6niveles, F produce una orilla abierta250.38m y un islote cerrado47.63m. La metrica heredada omitia el giro de cierre y su energia1m dependia del punto inicial del anillo (grafo7.002 frente aGEOS5.424 para la misma geometria). No aceptar esa discrepancia como cambio de terreno.

Usar la energia1m existente para la linea abierta, con direccion canonica por extremos. En anillos usar suma de cuadrados de TODOS los giros reales, incluido el cierre: invariante a rotacion/reversion. Controles: anillo irregular con todos los inicios y sentidos; cuadrado frente a circulo. El consumidor GEOS calcula todos los giros mediante vectores independientes. No modificar retrospectivamente los fallos anteriores.

Una solucion minima en apoyos secos:47deorilla y2deislote antes de aplicar perimetro. Todos los apoyos mojados(P/F/mar), ingenieria y niveles exactos. Conservar areaP yareaF por separado, signos ytopologia; energia de ambas lineas>=10%mejor, peor esquina no mayor, RMSnativo no mayor, pendiente sin regresion. Variacion<=1.5m, cruce<=4.1m, suelo seco no baja de min(fuente,1.8m). Fuente de suelo1.8: objetivo vigente contra artefactos; excepciones bajas se conservan sin rebajarlas. Ningun nuevo nivel ni malla3m.

Presupuesto: un SLSQP100iteraciones/120s, semilla fuente. Sin barrido. Candidato FAIL no se empaqueta. Antes de optimizar, grafo y consumidor deben coincidir en las dos metricas; despues, consumidor float32 GEOS y dominio global. Las esquinas del plano fisico escalonado se inventarian aparte; no se presentan como la curva dibujada porF. Mantener sus conexiones/area y comparar forma fisica en el consumidor.
