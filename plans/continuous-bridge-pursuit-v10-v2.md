# V2 — observar el tablero completo sin borrar el criterio de carril

Revision antes del motor: 2026-10-01 10:10 UTC. V1 permanece FAIL: el jugador
alcanzo 4.005626 m laterales, con Y=11 y SurfaceRoadY=11; el infectado seguia a
3.746769 m maximos y con salud100. No prueba caida ni puente atravesable completo.

La pregunta adicional es transito sobre el tablero real. Fuente independiente:
`evidence/narva/evidence/bridge-roadway.json`, Roadway principal del modelo
`bridge_metal_25.p3d`: x=-6.0000004768..6.0000004768, z=-12.5000009537..12.5000009537.
No usar AABB, barandillas ni superficies inferiores para justificar piso.

[DESIGN] Clonar exactamente la mision r4 y el estimulo de V1; cambiar solo
identidad de prueba y parada espacial: dentro de las nueve piezas (estacion
-112.5..112.5 m), ancho admisible +-6 m; fuera, conservar +-4 m. Mantener
contacto -0.2..+0.5 m, salud positiva, continuidad, velocidades, radios y tiempos.
La verificacion separa el resultado de tablero y el criterio historico de carril
+-4 m. Nunca promover V1 ni borrar los seis fallos de persecucion anteriores.

No modificar mapa, WRP, NM ni modelo. Un unico ensayo adicional. Presupuesto
1200 s de motor, cerrar antes de10:36 UTC si no termina; un cierre por presupuesto
es INCOMPLETO. PASS solo acredita este consumidor y geometria, no disciplina de
carril, ausencia de errores AI en todo el mapa ni capacidad80-100 jugadores.

Verificacion previa: artefactos congelados y PBO desplegado por bytes, APIs
ya usadas en V1 sin nuevas firmas. Despues: trazas completas, criterio estricto
de carril informado aparte, negativos del verificador, cierre propio ordenado.
