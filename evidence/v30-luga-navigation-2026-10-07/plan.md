# Continuación autorizada: Luga y navegación V12

Guillermo: «sigue con el plan». Partida: commit9e53b28; preview de relieve ya probada. Sin subagentes.

## Descubrimiento y corrección concreta

`diagnosis.json` conserva los perfiles de las estaciones7771 y7846. Ambas tocan agua clase2, no solo el Luga clase3. El piloto congela los vértices clase2 pero permite cambiar tierra que comparte sus caras nativas. En7771, el vértice1405/1710 baja4,265223→3,518055m y el plano3,15m invade tierra; en7846 se hunde la franja seca que separaba cruces. Esto sale de interpolar triángulos existentes, sin atribuirlo a caché ni al motor.

Corrección: conservar todos los vértices de cada celda nativa que contiene agua de una clase distinta de3. La máscara proviene exclusivamente de V12; no de los fallos del verificador. Aplicarla al candidato18-vector ya construido, mantener su delta en el resto y repetir el descarte de caras secas empeoradas. No cambia sigma, niveles ni clasificaciones; no mueve estaciones ni excluye los dos fallos.

Alcance de esta unidad: un candidato de corrección por mecanismo; evaluación independiente una vez. Si falla, conservar su FAIL y analizar la causa, sin barrido de parámetros. Si pasa, combinar con el relieve seco ya validado solo tras demostrar máscaras disjuntas, preservar agua/carreteras/Narva y verificar el paquete nuevo y el resultado en motor.

Puertas: mismas estaciones y ±8m del piloto anterior, cero nuevos cruces ausentes individualmente, p90 y curvatura por sector no peores; todas las caras con agua ajena idénticas; corredores, metadatos y fuera de máscara idénticos. Añadir estaciones intercaladas a1m como conjunto independiente; conservar cobertura histórica. El verificador general puede mantener los FAIL heredados, pero no empeorarlos. Rechazar el candidato anterior y un control que altera una cara protegida.

## Navegación

Adaptar el consumidor existente `prepare_vanilla_channel_boat.py` y la misión/autopiloto históricos a sectores representativos de V12: aparición oeste, Luga alto y tramo bajo. Congelar rutas/calado/criterios antes de ejecutar. Leer firmas reales de misión y addon, comprobar el PBO desplegado y el terreno de referencia. Una lancha vacía y unos tramos no aceptan todo el río ni navegación con tripulación. Sin modificar el addon de control si basta la misión/rutas.

Solo gestionar runs propios por MCP público, con lease y cierre ordenado. No forzar foco. Para imágenes preferir aparición directa y cámara próxima al jugador; el diagnóstico completo de tiles continúa abierto.
