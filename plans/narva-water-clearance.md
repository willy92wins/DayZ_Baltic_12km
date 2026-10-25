# Corrección local del terreno inundado

29-09-2026. Encargo vivo: arreglar los problemas del mapa y continuar la versión básica. P2/P4/P8; no decide la Z regional final ni reemplaza lagos por mar.

## Hecho y mecanismo acotado

La sonda auténtica `BALTIC_WATER_OBSERVER_V1` mide mar mínimo 0,50 m, máximo 1,00 m y actual 0,544082 m. En 44 de 297 puntos de tierra interior de referencia, a más de 12 m del agua OSM y excluyendo agua WorldCover, el motor devuelve mar y profundidad positiva. Las alturas coinciden con el ASC guardado dentro de 5,01 mm. El generador limita tierra seca a 0,25 m (`tools/prepare_prototype.py:94-95`): no protege frente al mar observado. Esto demuestra inundación en esos puntos, no un área regional inundada exacta.

## Prueba reversible [DESIGN]

1. Conservar el proyecto Narva actual y su WRP/ASC por hash antes de importar otra altura. No sobrescribir la base regional ni originales GIS.
2. Preparar un candidato derivado del terreno V2. Elevar solo tierra clasificada fuera del agua OSM/WorldCover en un sector de Narva. Margen objetivo de tierra interior: 1,25 m = máximo observado + 0,25 m. La cota del borde se aproxima a 0,75 m, punto medio del rango observado, con rampa de 12 m; el contorno de referencia permanece idéntico. Transición exterior de 120 m hasta cambio cero. No excavar agua ni cambiar los accesos de 2 m.
3. Mantener la escala de 6 m y el registro nativo medido. Mostrar los deltas y comprobar que no se modifican vértices de agua, puentes o alturas fuera del sector. Los canales subcelda necesitan análisis independiente: conservar polígonos no garantiza una orilla idéntica en triángulos de 6 m.
4. Importar solo si pasan esas invariantes. Verificar exportación auténtica y pose del puente después de rebuild. Reaplicar la corrección de canales de materiales tras Generate Layers.
5. Repetir sonda y vista Buldozer. PASS local: ningún punto seco interior de la rejilla dentro del núcleo conserva profundidad positiva y todos están por encima del máximo informado; puente y accesos mantienen 2 m; no se reduce el agua de referencia por editarla. Revisar también el borde, pues elevar tierra cambia la interpolación de la costa.

Presupuesto: un candidato local y una comparación nativa; un fallo cambia la estrategia, no se varían cotas a ciegas. Si las referencias OSM/WorldCover o canales estrechos contradicen el diseño, registrar el conflicto antes de extenderlo. Esta prueba no cierra agua elevada, nado, vehículo, navmesh ni Gate C.
