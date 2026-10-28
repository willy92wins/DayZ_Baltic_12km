# Carreteras B1: fuentes localizadas, consumidor pendiente

INCONCLUSIVE_CONSUMER. Descubrimiento acotado completado en0.125s; proceso
medido0.359s/34,701,312bytes.201entradas y2,072,325bytes de texto leídos.
R0 anterior alcanzó10000entradas en2.641s y no produjo informe; se conserva
RESOURCE_FAIL. R1 redujo rutas y excluyó capas raster/cache/navmesh sin aumentar
el presupuesto120s/2GiB,10000entradas ni20MiB de texto.

Las carpetas Shapes sí existen e incluyen roads.tv4s (26,412,747bytes) en Narva
y variantes del proyecto regional. Se inventariaron; NO se decodificaron. Los
proyectos tv4p son ALB1, no XML UTF8; sus bytes se fijaron y la lectura textual
rechazada queda en excluded. No se infiere ausencia de red a partir del buscador.
Los helpers correct_*_layer_offsets sólo tratan registros locales de tv4l para
objetos y requieren exportación nativa: no son un lector general de tv4s/tv4p.

La biblioteca Narva_Vanilla contiene puente metálico; la tabla del WRP compilado
ya sellada conserva28instancias de puente y cero roads/parts. No equivale a28
cruces ni demuestra una red RoadNetwork. El paquete actual usa objetos para los
puentes observados; la vía vial del pavimento sigue sin certificar.

Se reutilizan tres archivos B0 por hash, sin extraer geometría de nuevo:
- asf1_25 y asf2_25: centro local(0,0,12.5)m.
- asf1_10 100: centro(0.714035511,0,9.203353882)m.
Permiten diseñar poses que distingan hipótesis de recentrado. No certifican
la convención de pivote ni el ancho útil. Las caras vanilla permanecen privadas.

Siguiente: elegir y revisar un piloto WRP_OBJECT aislado con piezas recta/girada/
curva, oráculo de pose independiente y comparación fuente->compilado->motor;
o descubrir el esquema ALB1/RoadNetwork antes de usar esa vía. No hace falta
decodificar toda la red para ensayar objetos, pero el piloto no prueba RoadNet.
Conservar toda la huella y accesos, P9/P10/P11 y los cuatro pilotos autorizados.
No se colocó pavimento, no se creó puente y no se probó conducción en esta unidad.
