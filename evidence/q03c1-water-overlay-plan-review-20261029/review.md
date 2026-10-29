## Veredicto: **SOUND-with-fixes** — **CONVERGE**

El núcleo es viable: racionales exactos, clipping por el semiplano afín `W-B>=0`, unión sin duplicación y un consumidor basado en un arreglo de líneas son métodos compatibles e independientes. La distinción entre relación con agua seleccionada y exposición real está correctamente preservada, así como el contacto `W==B` como convención de esta medición.

Las correcciones siguientes deben congelarse en el contrato antes del código. No requieren bajar guardas ni cambiar la intención.

### Fallos y especificaciones ausentes

1. **[Falta de especificación] Miembros canónicos e identidad de cara.**  
El índice muestra alias con idéntico digest, por ejemplo `bed.npy`/`road_bed.npy`. Decir sólo “copias de water/bed” deja abierta una doble lectura. Deben fijarse los nombres canónicos exactos, excluir alias `road_*` salvo justificación, y definir la identidad testificable como `(model_index, ordinal_en_el_miembro, source_ids_completo)`. No debe suponerse todavía qué columna de `source_ids` es `face_index`. Impacto si no se fija: duplicación de lecho o testigos no comparables entre productor y consumidor.

2. **[Falta de especificación] Ejes, padding y área con signo.**  
El contrato debe escribir literalmente proyección `(coordenada0, coordenada2)`, altura `coordenada1`, área proyectada absoluta y normalización de winding. Para `n==3`, el cuarto vértice debe tener un criterio literal: el productor histórico lo crea con ceros según `pilot_visible_surface_ev112.py:218-221`; hay que declarar si se exige exactamente `(0,0,0)` o si sólo lo cubre el digest del miembro. “Intacto y observado” no es comprobable sin ese literal.

3. **[Falta de especificación] Degenerados y correspondencia de estados.**  
“Water degenerado que podría cruzar” no define si cruce significa intersección con el interior, con el borde, de un segmento XZ o sólo solape AABB. Productor y consumidor podrían emitir estados distintos ante el mismo caso. Debe definirse por separado: bed con proyección cero, water como punto, water como segmento que toca borde/interior y water que atraviesa el interior. También falta la tabla final: `MEASURED_SELECTED_WATER_OVERLAY_ONLY` sólo debería ser posible si las 1520 caras tienen triple numérico verificado; cualquier `RESOURCE_INCONCLUSIVE`, `INCONCLUSIVE_GEOMETRY` o degenerado no medido debe conducir a parcial o rechazo, nunca quedar absorbido por “terminales definidos”.

4. **[Diseño incompleto] Invariantes de la unión del productor.**  
La resta secuencial es correcta en principio, pero el contrato debe exigir que los fragmentos vivos sean polígonos simples, de interiores disjuntos y cuya unión sea exactamente el resto pendiente; la orientación del polígono de recorte no puede depender del winding de entrada. Faltan oráculos para un water estrictamente interior que genera un resto con hueco representable por piezas, un resto no convexo tras varias restas, vértice sobre arista, contacto puntual/segmento y `W-B=0` coincidente con una arista. Sin ellos, el error probable no es una pequeña desviación: es área duplicada, negativa o perdida.

5. **[Falta de especificación] Definición de “par” comparable y clasificación del consumidor.**  
El productor puede enumerar pares por intersección; el consumidor, por celdas del arreglo. Debe fijarse si un par exige intersección XZ de área positiva y cómo se tratan toques puntuales o lineales y los extremos `W-B` en intersecciones degeneradas. En el consumidor, incluir las tres rectas de cada water candidato y su recta `W-B=0` sí hace constantes cobertura y signo dentro de cada celda abierta, siempre que se incluyan también líneas coincidentes/duplicadas sin crear celdas fantasma y se defina el punto interior racional. Los invariantes por permutación o subdivisión de water deben comparar áreas y estados, no la lista literal de pares, porque ésta cambia legítimamente al subdividir.

6. **[Falta de especificación] Terminal íntegro y prefijo.**  
`fsync` por sí solo no define cómo detectar un registro truncado. Cada terminal necesita secuencia contigua, longitud y digest propio, escritura atómica o mecanismo equivalente, y criterio de prefijo válido sin huecos. El consumidor debe poder verificar ese prefijo y mantener el resultado global como parcial. Esto es especialmente importante porque timeout y `RESOURCE_INCONCLUSIVE` son salidas previstas, no excepcionales.

7. **[Viabilidad no demostrada, no error de corrección] Complejidad del arreglo frente a los caps.**  
Para `K` water candidatos por bed, el consumidor puede generar orden `(4K)^2` celdas; con `K` moderado puede agotar 1024 fragmentos antes que el productor. Además, los vértices creados por clipping sucesivo aumentan el tamaño racional. El plan acierta al fallar cerrado, pero todavía no demuestra que `FULL` sea alcanzable. Antes de codificar debe fijarse la contabilidad separada de celdas/fragmentos de cada caminante, deduplicación de rectas coincidentes, una cota previa por operación y un oráculo sintético con múltiples capas solapadas que ejercite esa contabilidad. Si los datos reales agotan el cap, el resultado honesto es parcial; no debe prometerse cobertura completa.

También debe congelarse la codificación JSON canónica de racionales, por ejemplo numerador y denominador enteros reducidos con denominador positivo, rechazando floats y booleanos. Sin eso, el consumidor podría perder exactitud al parsear la salida.

**Conclusión:** no aparece un defecto que invalide el algoritmo dual ni la semántica limitada del resultado. Es **SOUND-with-fixes**. Habrá **CONVERGE** si esos literales, invariantes y oráculos quedan cerrados en la única revisión contractual previa; si la semántica de miembros/IDs o la tabla de estados no puede fijarse desde el material pinado, el resultado pasaría a **LOOP** por especificación insuficiente, no por inviabilidad geométrica.
