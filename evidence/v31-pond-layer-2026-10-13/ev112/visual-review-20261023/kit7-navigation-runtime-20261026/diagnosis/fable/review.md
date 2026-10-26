**Identidad:** Claude Fable 5.1 (`claude-fable-5-1`), CLI nativo, solo Read/Glob/Grep. Sin escrituras ni procesos.

**Hechos extraídos de la evidencia**

- Las ocho muestras de 124/133, también las cuatro de orilla izquierda que pasan, están por debajo de Roadway. Rango: 0,33 a 1,17 m. El PASS izquierdo es solo cuestión de umbral, no de mecanismo distinto.
- En todo el kit7 la Y de navmesh queda entre terreno y Roadway. Ejemplos: piece_010 error 0,08 a 0,44; piece_050 0,03 a 0,35; piece_090 0,25 a 0,56. En los puentes vanilla de regresión la navmesh coincide con Roadway salvo en las rampas, donde también queda intermedia (bridge_out índice 3: nav 1,72, road 1,98, terreno 1,57).
- piece_138 índice 1 da navmesh por encima de Roadway en 0,35 m y por encima del terreno. Una capa inferior o geometría ignorada nunca produce un valor superior a la superficie.
- Entre puntos vecinos de la misma orilla la navmesh tiene pendiente propia donde la calzada es plana: 1,524 frente a 1,708 a 0,8 m de distancia. Eso es un plano inclinado, no un desplazamiento constante.
- SampleNavmeshPosition devuelve el mismo XZ solicitado con Y 2,0 m de radio pidiendo Roadway+0,2. Si existiera un polígono a nivel de calzada en ese XZ lo habría elegido por cercanía vertical. Luego en ese XZ solo hay un polígono y su altura es la errónea.

**Hipótesis ordenadas**

1. **Simplificación vertical del polígono** (más probable). Las piezas kit7 tienen corona estrecha con taludes continuos de pendiente menor que 60° y sin escalón mayor que 0,45 m, así que la región caminable baja hasta la orilla. Los vértices del polígono quedan en el borde de la región, es decir, al pie del talud, y el interior se interpola. Explica valores intermedios, valores por encima en concavidades y pendiente propia del plano. Explica también que los puentes vanilla, con escalón o borde a nivel de tablero, coincidan.
2. **Capa subyacente o geometría parcial.** Refutada parcialmente por el punto anterior y por la Y superior en piece_138. No descartada del todo hasta el discriminador 2.
3. **Caché o test.** El productor lee la misma Q que FindPath consume y las regresiones vanilla coinciden, así que el verificador no está desplazado globalmente. Solo quedaría una NM vieja en el PBO. Discriminador: hash de la NM dentro del PBO frente al archivo generado, ya debería constar en la identidad del paquete.

**Discriminadores baratos, en orden**

1. **Offline, sin motor.** Con odol_reader y las poses del WRP, cortar el LOD Geometry perpendicular a la calzada en los ocho XZ de 124/133 y en piece_010. Medir pendiente máxima y escalón máximo desde la corona hasta el agua. Predicción de la hipótesis 1: los cuatro FAIL tienen talud continuo bajo 60° y sin escalón de 0,45; piece_010 tiene borde abrupto. Si los FAIL muestran escalón vertical en el borde de calzada, la hipótesis 1 cae.
2. **Misión aislada, mismo paquete, solo lectura del motor.** En las dos piezas, transecto perpendicular cada 0,1 m desde orilla a orilla y transecto longitudinal por el eje, registrando nav, SurfaceY y SurfaceRoadY. Predicciones: hipótesis 1 da Y continua, lineal a trozos, con quiebros en los límites de región y cruces por encima y por debajo de Roadway; capa inferior da Y igual a terreno o desplazamiento constante con discontinuidad en el borde del modelo; geometría ignorada da Y igual a terreno en toda la pieza. Añadir en cada XZ una segunda consulta con Y pedida terreno+0,2 y radio 0,5: si devuelve el mismo punto, hay una sola capa.
3. **Verificador.** Confirmar que la puerta compara con Roadway y no con max(terreno, Roadway). Es solo lectura del código y no cambia tolerancia.

**Corrección mínima posible, condicionada**

Si el discriminador 1 y 2 confirman la hipótesis 1, el fallo es propiedad del generador sobre taludes suaves, no del WRP ni del lector. Las salidas honestas son dos. Una regeneración controlada en copia aislada cambiando una sola variable de GenParams y midiendo los mismos ocho puntos, sin asumir qué significa cada cellSize antes de medir. O un cambio de geometría en el LOD Geometry que cree un borde de región en la corona, que es cambio de producto porque impide bajar al talud y requiere decisión del usuario. No recomiendo la segunda sin ese mandato.

**Física frente a contrato**

Los 6801 puntos físicos prueban contacto actor-Geometry. La Y del actor la fija la física, no el polígono de navmesh. Un actor cruza bien con navmesh baja, como en el antecedente de V30. Por eso ese PASS no toca el contrato 0,801, y el FAIL se conserva hasta que el generador dé alturas dentro del umbral.

**Límites.** No he leído el LOD Geometry completo ni calculado distancias al borde de la región seca. El diagnóstico se basa en ocho puntos y en el patrón de valores de otras piezas, no en el algoritmo interno del generador.
