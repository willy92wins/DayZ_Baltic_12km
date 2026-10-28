# Contactos geométricos de carretera con agua

Censo independiente del inventario de puentes: recorre las124cadenas y36467
aristas de la referencia de carreteras,107.181km, por74357particiones de caras
nativas. No excluye agua, Narva ni extremos. Descubre770aristas con contacto en
29cadenas y1929.125m de eje nominal mojado. No significa770cruces ni770puentes
ausentes: falta contrastar cada contacto con los puentes reales y las capas3D.

92raíces coinciden con el censo nativo independiente, residuo máximo2.57244e-12m.
1313partes mojadas no tienen raíz interior (no desaparecen por ese motivo).
65saltos de agua entre celdas dentro de aristas;0en nodos;0ambigüedades de agua
o numéricas en este conjunto. Todas esas clases tienen fixtures, incluidos
saltos justo en nodos, tangencias, agua menor de1cm entre muestras, carretera
entera sumergida, islas, inversión, división de tramos y borde de mapa.

El caso de posible puente ausente tiene un contacto próximo en cadena49,
arista301, a11.601m del personaje4789.51465/5516.52197. Es contexto sin asociación
exacta de cámara. El extremo de kit118 sigue NO EVALUADO: su agua3D no pertenece
a este dominio y el contacto nativo más cercano a la parada está a1086.304m.

Fable5.1 revisó plan y código;20pruebas pasan con consumidor de polígonos
recortados independiente del recorrido de caras. Se corrigió un hueco propio:
un salto deW situado justo en un nodo se perdía al dividir la carretera. Ahora
se comparan todas las observaciones por nodo, incluso entre cadenas distintas.
Slivers numéricos se conservan y etiquetan inciertos, no se borran ni se declaran
saltos confirmados. No se rebajó ninguna tolerancia.

Única ejecución4.594s, intérprete125272/launcher116600, pico306495488Bresidente
y801845248Bcommit;120s/2GiB cumplidos. Hashes iniciales/finales exactos, exit0.
Los GeoJSON usan XZ local en metros, NO longitud/latitud WGS84. contacts.json
retiene las caras y ambos lados cuando corresponde. partitions.npz externo
está identificado por hash y cubre también las partes secas.

Siguiente: vincular al mundo visitado la geometría real de Roadway de todos los
puentes y las láminas3D, revisar plan y cruzarla con este censo, sin tomar
crossings-ev106 como universo esperado. Así se podrá distinguir omisión,
desalineación, ancho insuficiente o tramo ya resuelto. Ningún mapa reparado,
puente aceptado, conducción ni rendimiento se desprende de este diagnóstico.
Nav8 histórico607PASS; RAM/global y c1 SIN REVISAR permanecen abiertos.
