# EV62–66: consultas bajo puentes y propuesta del Volkhov

La prueba de omisión EV64 atribuye cinco lecturas de ausencia de agua a la presencia de los objetos de puente. El terreno de trabajo sigue siendo EV61; ninguna propuesta del Volkhov pasó todos los criterios y ninguna fue empaquetada.

## Cinco lecturas bajo puentes: discriminación completada

Se comparó el censo completo de servidor EV61 con un paquete que omite únicamente los objetos 16787374, 16787375 y 16787376 (`bridge_metal_25`). Todas las alturas, agua y restantes objetos permanecen exactos; 6826 entradas del PBO también. Los cinco puntos que antes no detectaban agua pasan a detectarla. Sus calados nominales son 0,101–1,130 m, por encima del margen declarado de 0,10 m. Los otros trece desacuerdos de clase fluvial permanecen idénticos y corresponden a orillas geométricamente secas.

El contador total pasa de 23 a 21 porque el mar tiene cinco observaciones en A y ocho en B por su fase; esa diferencia no se utiliza como medida del efecto. El contraste relevante es 18→13 en la clase fluvial y la identidad de los cinco puntos. `comparison.json` conserva controles positivos y negativos. El mecanismo interno exacto del objeto sigue opaco: el experimento identifica la dependencia de la consulta respecto al puente, sin probar qué subcomponente del modelo la produce.

El servidor leyó 4194304 vértices y 1205 planos calibrados; error máximo de suelo 0,0000152588 m. Siete corrupciones del registro son rechazadas. Run `4620146a-09ae-4ed7-9526-391dbdeabe43`, cierre ordenado, lease liberado y banco libre. Sin cliente, foco ni Computer Use. Mundo diagnóstico `7d63d853a9bbe8dc5e9fea69217e54c84cea79fa92058000d9c0f0aef6e3b5db`, agua `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`. La base mantiene sus nueve puentes; el diagnóstico jamás se promociona.

## Volkhov: propuestas rechazadas y mecanismo descubierto

EV62 enumera los soportes de los grupos fluviales bajos. Msta comparte la gran masa 693; Nazia se une al grupo costero protegido. No se modifican. El grupo 349 del Volkhov permitiría elevar su fondo mínimo 0,425 m, de 0,58542 a 1,01042 m, conservando el calado. Su cierre incluye también las charcas 647/651, cuyos fondos ya cumplían: esa excepción de política permanece pendiente, no autorizada por la mera preparación de una propuesta.

EV63 conserva geometría y política local, pero falla la transición: incremento máximo 5,466° y exceso de pliegue nuevo 3,653°. El dominio rígido de 2448 vértices incluía 1131 vértices secos de cajas de modelos sin función de apoyo de agua. Allí están los mayores fallos. EV65 usa los 1317 vértices que sostienen triángulos realmente mojados; las caras secas cumplen desigualdades que evitan inundarlas. Su transición variacional converge en 251 iteraciones: incremento máximo 0,843°, pero empeora pliegues ya existentes hasta 0,562° y falla el límite declarado.

EV66 incorpora explícitamente las restricciones de normales en seis grupos independientes (1019 variables). Solo converge uno; el conjunto continúa fallando. El cálculo analítico de normales concuerda con el consumidor de productos vectoriales a 1,42e-14° y sus derivadas centrales a 7,55e-10. No es prueba de imposibilidad matemática: demuestra que esta corrección acotada no proporcionó una solución aceptable. Los campos heredados `displacement_bending_energy`, `controls` y `gradient_direction_error` de su `authoring.json` describen EV65; los controles nuevos se identifican como `analytic_*`. No se usan aquellos como mediciones de EV66.

Los tres candidatos conservan fondo, huellas, profundidad, componentes y conexiones; eso no sustituye los gates de pliegue. No se empaquetan, no se relajan sus límites y no se repite un barrido de cotas. Candidatos completos en E; scripts, dominios, informes y hashes en los cinco directorios de evidencia y `evidence-manifest.json`.

## Continuación

EV67 actualiza las 1024 teselas de superficie sobre EV61, con el mismo generador y parámetros de EV28. Continúan pendientes los contornos residuales, los grupos bajos compartidos/protegidos, los 2197 objetivos secos rechazados por EV60, los 45 cruces, los dos lagos grandes reservados al usuario, el streaming, Terrain Builder y navmesh/IA. La base 1.0 no está terminada.
