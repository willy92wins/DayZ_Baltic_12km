# EV86 — piloto de perfil estricto, verificado offline

EV86 pasa el consumidor independiente sobre dos parches de orilla:33 alturas,
220 signos estrictos de vecinos conservados, cero extremos axiales nuevos.
Los focos bajan0,858/0,780m y su energía angular baja43,31%/35,82%.
Pasan cotas, pendientes, sectores, p99/conteos, P/F, cruces, componentes y
cobertura física/visible ODOL. El candidato NPZ es85b09e55954811edfa3933d979db1513898ea9ea328421f68c87007ac79f6076.

La fuente/preview sigue EV82-B f9fb23de; EV86 no se empaquetó por separado.
La cobertura usa transforms0WZD fuente ligados por hash al OPRW/PBO desplegado;
no es readback del motor, prueba gráfica ni aceptación de base1.0.

## Por qué cambió el método

EV85 SLSQP dio estado8 y12 inversiones micrométricas. Su única corrección
numérica explícita EV85-R corrigió orden y cruces, pero dejó9 extremos débiles
por mesetas; ambos se mantienen RECHAZADOS. El diseño permitía igualar vecinos
pero su criterio de forma prohibía esos extremos: repetir tolerancias no lo resolvía.

EV86 fija el punto medio B/R y demuestra que conserva al menos la mitad de cada
pendiente original antes de redondear. Verifica signos estrictos después de
cuantizar, sin reparar ULP ni buscar factores. El consumidor conserva el gate
de extremos débiles, que ahora pasa. Corrigió además un flag informativo que el
harness anterior había situado por error entre los gates: los metadatos reales
se comprueban con terrain_metadata_exact; no cambia el rechazo geométrico deR.

## Cobertura del mapa y siguiente unidad

El inventario lee toda la malla2048²:18768 vértices secos editables incidentes a
quiebros>30°,15173 junto al agua,2358 en taludes secos de río y1237 interiores.
Son medidas geométricas, no ese número de defectos visuales confirmados.
Se prepara EV87, una pasada de parches disjuntos en todas las crestas editables,
con máscaras protegidas intactas y verificador global. Plan vivo externo:
E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010/plan.md.

Los rectángulos de render, agua visual sobre tierra, grandes lagos, finales,
TerrainBuilder y navmesh continúan abiertos. No hubo DayZ ni lease en esta unidad.
