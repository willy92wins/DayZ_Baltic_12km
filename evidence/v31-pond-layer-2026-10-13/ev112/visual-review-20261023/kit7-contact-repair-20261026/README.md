# Kit7 — reparación localizada de colisión

Resultado nativo: **PASS: 6.801 puntos, cero fallos**. Calibración fresca:0,039991446m,
5aciertos vanilla y289controles vacíos. Se mantienen las mismas6801muestras,
productores y tolerancias de la sonda anterior que falló19contactos.

Solo cambia Geometry de19modelos. Las otras182piezas yconfig son byteexact;
las139poses son idénticas. Componentes8623→8623;caras263552→265384(+0,695%);
vértices149022→149938. Máximo por componente72vértices/140caras.
Solape horizontal local de1/512m, conservando las seis cotas de bbox exactas.
El overlay completo de fuente y compilado pasa con los umbrales originales.

Los LOD fuente ajenos aGeometry son byteexact. Para el compilado se comparan
todos los campos decodificados: Roadway conserva caras orientadas, multiplicidad,
vértices y etiquetas de superficie; solo se canoniza el orden de caras/secciones.
Los campos desconocidos que el reader descarta no quedan cubiertos.
El comparador rechaza seis mutaciones locales, LOD ausente, resolución cambiada
yNaN con payload distinto. La revisión Fable y su corrección de tests se conservan.

Dos candidatos anteriores quedan rechazados: anclas que excedían el coste y
anclas con exceso horizontal0,019326562m². La variante final elimina esas anclas
innecesarias; no usa la partición experimental archivada. No se relajó ningún gate.

La coincidencia original de los19fallos con vértices compartidos es evidencia
de localización. El mecanismo interno de precisión del motor sigue siendo hipótesis.
No se deriva aceptación visual, navegación, actor, rendimiento ni calidad global.
El censo de terreno conserva268picos,1144depresiones y4transiciones pendientes.

Ambos runs propios quedaron cerrados oficialmente, sin cliente, sin comandos
pendientes ni limpieza degradada. Paquete piloto3d9550bf; mundo10e09e3f sin cambios.
