# V25: cerrar huecos de cobertura en las bandas viales

Continuación autorizada de la base de terreno. Conserva el producto, las
geometrías fuente, las tolerancias y el plan V24; corrige el productor.

## Evidencia antes de editar

V24 satisface su matriz completa en434.657s pero el consumidor independiente
rechaza67 de239126 secciones,4 intervalos de rasante y1 cuerda. Los56 ejemplos
guardados caen en segmentos enteros omitidos por el productor al comprobar
solo sus extremos. `refine_road_network_v16.py:76-89` omite también el empalme
cuando alguno de los vecinos queda fuera. Un segmento puede cruzar una celda
elegible aunque ambos extremos estén fuera. No es un límite insuficiente del solver.

`verify_road_hydrology.py` rechaza18 celdas nativas tocadas por agua, mientras
la máscara de vértices mojados pasa. La máscara de protección no cubre todas
las superficies vectoriales que intersectan celdas. Se conservan ambos FAIL.
Recibos: tests/regional_road_network_v24/{independent-consumer,hydrology,
coverage-diagnostic}.json.

## Corrección acotada

[DESIGN] Dividir cada segmento fuente en cruces exactos con la cuadrícula de
clasificación por vértice más próximo (x/z=6k+3) y el círculo protegido de Narva.
Clasificar los interiores de esos intervalos y restringir su banda completa.
Incluir los discos de empalme con ambas tangentes cuando alguno de los lados
del vértice pertenece a un intervalo elegible. No cambiar el consumidor.

Proteger las cuatro esquinas de todas las celdas tocadas por los polígonos de
agua congelados; dilatar esa máscara30m y sumarla a las exclusiones originales.
Esto impide modificar una cara acuática aunque no contenga vértices mojados.

La cuerda de6m es afín por tramos sobre cada polilínea y triángulo nativo.
Restringir sus extremos en las uniones de los cruces de x/z/x+z=6k, los vértices
de la polilínea y los cambios de elegibilidad, desplazados−3/0/+3m. Mantener
el límite2.2cm; el consumidor permanece a0.37m y exige3cm.

Transición48m, envolvente60.5m, delta<=6m respecto a V33 y V10, banda8m,
gradiente transversal0.0032, longitudinal6%, taludes35grados, reserva/islas,
fairways y Narva480m permanecen. No añadir carreteras ni objetos.

Una construcción y una resolución,600s de solver/650s de worker. Usar un
checkpoint anterior solo si las filas correspondientes son byteidénticas;
en caso contrario empezar por las restricciones inicialmente violadas.
FAIL o timeout se conservan; no ampliar límites para conseguir PASS.

Implementación: conservar matriz/variables V24 como prefijo exacto y añadir
bandas omitidas, empalmes y extremos de cuerda. Mantener el soporte48m original;
los nuevos vértices protegidos se fijan mediante cotas delta=0. Comprobar el
prefijo disperso byteidéntico permite reutilizar sus filas activas sin trasladar
índices a otra matriz. Los empalmes incluyen intervalos elegibles a<=0.5m de
la esquina, cubriendo la tangente interpolada del consumidor a0.37m.

Antes de importar: mismo consumidor vial e hidrológico, controles negativos,
geometría continua de costa,81212 puntos congelados, reserva y accesos. Después,
persistencia nativa, empaquetado exacto, navmesh nueva y pruebas de consumidor.

## Corrección de representación de la exclusión30m — V26

V25 resultó inviable con certificado de2filas: congeló el vértice(7656,9750),
a37.1949m reales del mar. Dilatar30m las esquinas de celdas ya tocadas por agua
sumaba hasta una diagonal de celda extra. Es una sobreextensión de la máscara,
no motivo para relajar anchura, rasante o agua. Evidencia: certificado y
certificate-local-trace.json deV25. Las filas son nuevas bandas, no filas
preexistentes de V24; la contradicción las combina con esa cota delta=0.

V26 mantiene todas las filas exactamente. Fija vértices dentro del buffer
geométrico real30m (centros de raster situados en vértices nativos), más todas
las esquinas de celdas acuáticas. Conserva también la exclusión original.
Control de regresión: el vértice a37.1949m queda libre y todas las caras acuáticas
siguen congeladas. Una resolución adicional600/650s, mismos criterios y gates.

## V27: reconstruir el soporte a partir de las bandas completas

V26 aisló una fila de banda nueva sin ninguna variable libre, rhs−0.454285:
todos sus vértices quedaron fuera del soporte V24. El prefijo conservaba filas
correctamente, pero reutilizar su dominio no podía cubrir las bandas omitidas.
Se conserva el certificado de1fila. No es una necesidad de cambiar tolerancias.

Reconstruir por completo bandas continuas, soporte48m y matriz, con la exclusión
geométrica V26. Rehacer restricciones de todos los triángulos afectados y extremos
de cuerda. No reutilizar índices de filas ni variables anteriores. Una construcción
y resolución600/650s. Misma aceptación independiente y límites de terreno.

## V28: conservar las caras de orilla aceptadas, sin congelar tierra adicional

V27 reconstruyó el soporte completo, pero su certificado de2filas aisló otra
contradicción en el triángulo432/1469/1. Dos vértices secos a27.3166 y28.7566m
de river_contour_0029 se fijaban por el nuevo buffer geométrico30m; estaban
a46.8615 y43.2666m de la máscara original y podían ajustarse en el contrato
previo. La combinación elimina la única variable libre y deja margen0.267504:
subir el delta o el presupuesto no puede resolverla. Evidencia:
tests/regional_road_network_v27/geometric-certificate-trace.json y certificate.npz.

Se sustituye esa protección adicional de tierra seca por la protección exacta
de las cuatro esquinas de toda celda nativa tocada por agua, y por la transición
lacustre6m de V33. Se mantienen la exclusión original30m, fairways y Narva480m.
El consumidor independiente exige igualdad exacta de esas caras contra V33;
además repite suelo seco, pendientes, límites, islas, reserva y81212puntos.
Las carreteras conservan su clasificación original y todas sus tolerancias.

Reconstruir variables y filas desde cero, sin reutilizar índices. Una construcción
y resolución600/650s. V24-V27 siguen rechazadas, sin importar ni desplegar.
Tras resolver, mismos gates independientes, negativos, persistencia y navmesh.

## V29: discriminar el ajuste conjunto de carretera y orilla

V28 conserva FAIL:346 filas individualmente imposibles (299 banda,47 cuerda).
El certificado de una fila corresponde al triángulo382/1434/0, cadena100:
dos vértices secos están a2.98/3.20m de river_contour_0019, pero la máscara
histórica sitúa agua a42.43/48.37m. Congelar esas caras completas impide alisar
la carretera adyacente. Aumentar el delta no resuelve las filas sin variables.
No se cambia ni se reclasifica ninguna muestra vial para obtener aceptación.

[DESIGN] Sustituir exclusivamente la nueva congelación de caras por restricciones
conjuntas sobre sus planos: mismo contorno vectorial, margen seco1.4m/global y
nivel local+0.35m fuera de la transición lacustre6m; núcleos de lago con15cm,
canales/fairways exactos y81212puntos congelados con sus clases/profundidades.
Conservar además todos los vértices nativos dentro del agua vectorial, la
exclusión histórica30m, Narva480m, cotas/dominios/islas y tolerancias viales.
Esto permite modificar vértices secos que sostienen parte de una cara de orilla.
Es una revisión explícita de la prohibición de tocar el collar de orilla; el
producto conserva sus condiciones físicas, pero no hereda igualdad de caras.

Las intersecciones secas y los núcleos se restringen solo en caras afectadas,
con todas sus esquinas de intersección. Holgura numérica1e-6m, menor que1e-5m
del consumidor previo; no modificar los márgenes físicos. Una construcción y
una resolución600/650s; certificados/timeout conservados.

Aceptación V29 requiere repetir el consumidor continuo V33 completo, sin
heredar su PASS. Sus metadatos de diseño se fijan por hash, el ASC es el nuevo.
La igualdad de caras se conserva como diagnóstico histórico; no es el criterio
de esta prueba conjunta. El consumidor hidrológico debe seguir exigiendo agua
en vértices/fairways exacta, islas/reserva y fuentes intactas; la prueba continua
sustituye únicamente la igualdad adicional de caras. Mantener los antiguos
FAIL sin reetiquetarlos. Negativos reales, importación/persistencia, navmesh y
pruebas físicas siguen siendo puertas posteriores. Ningún paquete se modifica
durante este discriminador.

Discriminadores independientes posteriores, previos al resultadoV29:
V24 conserva25 extremos secos deficientes en la orilla local (máximo1.28494m),
aunque pasan las otras12puertas continuas y los81212puntos. Por tanto no basta
con ignorar la comparación de caras: hay que volver a imponer sus condiciones.
La proyección del agua intersecta36muestras viales elegibles de cadena100,
pero river_contour_0019 está a0.475m y el suelo local a6.8–8.2m: esa huella
no implica una carretera físicamente sumergida. Se mantiene su clasificación.
Fuentes: full-outline-discriminator.json, eligibility-vector-water-diagnostic.json,
geometric-certificate-trace.json y road-shore-conflicts.png en la evidencia.
