# V22: abrir la transición solo en la ladera del conflicto

[EXACT] El certificado V21 tiene 79 filas originales verificadas contra la
matriz V18: 67 de carretera y 12 de talud. Su combinación conserva un único
vértice fijo, (4326,6936), altura42.319954m, a33.453699m del eje fuente y492m
del agua; no pertenece al fairway. `conflict-v21-trace/{trace,fixed-boundary}.json`.
El resto de sus vértices está entre(4326,6924) y(4524,6960). Conservar ese borde
obliga a un cambio local>=6.301367m; no demuestra que todo el mapa lo requiera.

[DESIGN] Mantener las bandas de carretera, pendientes, cuerda y agua originales.
Usar la transición24m de V18 en general, y48m solo dentro del rectángulo
x[4278,4572],z[6876,7008], que añade48m alrededor del certificado. La envolvente
geográfica independiente seguirá siendo36.5m fuera de ese rectángulo y60.5m
dentro. El nuevo dominio continúa limitado por el agua30m, fairways, Narva480m
y los pisos de islas. No cambiar las referencias ni el relieve fuera de él.

Construir una nueva matriz completa desde el productor V16 congelado, con
hash de código comprobado. Primera solución con cota5m, inferior a V21: L1,
generación de restricciones y comprobación de todas las filas. Presupuesto600s
de solver,650s de worker, un hilo, guardia RAM2GiB. No elevar automáticamente.
Si es inviable, conservar certificado y cambiar el discriminador.

Antes de importar: geometría densa independiente, mapa/cuantiles de cambios,
hidrografía/islas/reserva, negativos y límites de dominio. Solo después, un
bloque nativo para importación/persistencia, nueva navmesh y pruebas consumidor.
V10 permanece desplegado mientras exista cualquier gate pendiente.
