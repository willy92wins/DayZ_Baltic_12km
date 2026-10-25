# Candidato v11: finales de río redondeados y más profundidad — 07-10-2026

Sobre la v10b, aceptada el 06-10 como base de las orillas junto con su lista de niveles
(`../v30-v10-candidate-2026-10-06/decisions/aceptacion-v10b.json`). Productos en `E:/DayZ-Baltic-Build/v30-v11`;
desplegado como `@DayZ_Baltic_V11Candidate` (mundo c690879f + agua 07c5295f; copias comprobadas por hash, `reports/deploy-receipt.json`), misión `BalticTideProbeV2.BalticTrial`.
**Vista en motor el 07-10 (run 9b486b9a, sección «En motor») y sin aceptar.** El intento de las 3:40 no llegó a capturar: la pantalla estaba apagada (`desktop_all_black`).

## Decisiones (Guillermo, 06-10)

- «acepto la v10b y los niveles, redondea el final de los ríos».
- «hay que meterle algo más de profundidad a ríos y lagos eso sí, se ve todo muy plano». Tras medir: ríos ~1 m en el
  centro, arroyos ~0,4 m y lagos de 1 m a 6 m de la orilla donde el nivel lo permite (el fondo sigue a 1,0 m por el mar
  del motor); sin encajar los cauces; orilla más inclinada a ambos lados para no mover el contorno de la v10b. Las
  variantes medidas (abajo) mostraron que esos calados no se alcanzan con una subida moderada de la tierra; Guillermo
  eligió la variante C.

## Qué cambia frente a la v10b

| commit | herramienta | qué hace |
|---|---|---|
| 698157c, 78f6fa8 | `build_v30_water.py --round-river-ends 30` | redondea el final recto que el corte de 60 m deja en un río: apertura morfológica local en cada corte, radio min(30, 0,45 × corte, 0,9 × medio ancho del río), reducido a la mitad hasta que solo se van las esquinas; en esa zona el surco central ya no sostiene vértices fuera del contorno redondeado |
| f474e6a | `profile_inland_v30.py --slope-by-class --slope-ref` | pendiente del perfil de orilla por clase, a los dos lados del contorno, así que el cruce sigue en el contorno: el agua se ahonda y la primera fila de tierra sube en proporción. Una pendiente más fuerte se limita a (nivel − 1,0) / 4 m y nunca baja de 0,15, para que el fondo de 1,0 m no recorte el cruce |
| — | cadena (`scripts/chain_v11.sh`) | la de la v10 con la pasada de orillas sobre el `sd` del paso 20 (como la v10b), la lista de niveles aceptada, `--round-river-ends 30`, `--slope-by-class 2:0.25,5:0.4,6:0.35,7:0.25` y los arroyos también sobre el contorno del diseño |

## Lanes delegadas (GX10, GLM-5.3-Flash) y revisión

- El reinicio del PC del 07-10 cortó las dos lanes a medias; se relanzaron (las salidas cortadas quedan en el
  scratchpad, `lanes/*-interrupted-reboot`).
- **E1, finales de río** (`glm-lanes/E1_*`, 43 min): entregó la función y su autoprueba. En la revisión: líneas de corte
  vacías (rompían la autoprueba), radio también por el medio ancho real (el Volkhov cruza el borde a unos 22°: corte de
  34 m para un río de 13 m), la condición de aceptación (la cota en r² rechazaba las esquinas agudas) y un caso
  oblicuo en la autoprueba. Después, visto en planta, el surco central sostenía la columna del corte del Гриб: el
  recorte del surco en la zona redondeada (78f6fa8) es mío.
- **P4, pendiente por clase** (`glm-lanes/P4_*`): gastó sus 120.000 tokens razonando sin escribir el fichero
  (`finish_reason: length`, 64 min). Lo escribí aquí. Las lanes se lanzaron sin `GX10_EFFORT=medium`, que es lo que pide
  el estado vivo para GLM: error mío.

## Profundidad: variantes medidas antes de construir

Sobre las entradas de la v10b (`scripts/depth_variants.sh`, `E:/DayZ-Baltic-Build/v30-v11-verify`). En todas, la línea
de agua visible, las puertas y las carreteras salen como en la v10b. Calado en el eje de ríos y arroyos (vértices del
surco central), en m:

| variante | pendientes (lago, río, arroyo, estanque) | eje de ríos p50/p90 | eje de arroyos p50/p90 | lagos 0–6 m | tierra 0–6 m sobre el agua p50/p90 |
|---|---|---|---|---|---|
| v10b | 0,15 todas | 0,32/0,58 | 0,14/0,19 | 0,40 | 0,51/0,77 |
| primeras | 0,167, 0,25, 0,20, 0,167 | 0,44/0,92 | 0,18/0,24 | 0,43 | 0,67/1,00 |
| A | 0,25, 0,4, 0,35, 0,25 | 0,55/1,38 | 0,29/0,41 | 0,51 | 0,87/1,72 |
| B | las primeras, arroyos por el diseño con 0,25 | 0,44/0,92 | 0,20/0,34 | 0,43 | 0,68/1,43 |
| **C (elegida)** | las de A, arroyos por el diseño | 0,55/1,38 | 0,27/0,44 | 0,51 | 0,86/1,96 |

Con la orilla del diseño fija, el calado en el eje crece en proporción a lo que sube la primera fila de tierra: la
estimación inicial (ríos de 1 m con 0,2–0,5 m de tierra) era errónea. La C no crea un dique nuevo: la tierra a 6–12 m
del agua ya estaba a 1,14 m en la v10b, y la C rellena el escalón entre el agua y ese borde. Con los arroyos sobre el
contorno del diseño mejora además su orilla (desfase p50 1,12 → 0,88 m).

## Resultados de la v11 (sin motor)

Cadena completa en 54 min (`reports/chain.log`), terreno 6e452bd3. Paso 4: 3 ríos recortados, sus 3 finales
redondeados y 5 vértices de surco recortados, todos en los finales (`reports/04-water.log`). La lista de niveles
aceptada se reproduce entera: 90 de 90 iguales, `levels/bodies-rule.json` 0eafbd5d.

- **Puertas** (`reports/verify-v11.json`, `roads-v11.json`, `channel-reaches.json`), como la v10b: calado 1 (un
  arroyo); orillas 0; piezas 21, en los mismos 18 vértices que la v10b (`scripts/piece_fails.py`); fondos 0; suelo de
  tierra 0 (6.314 orillas de agua baja elegibles, todas sobre su suelo); taludes 0; Narva distinto por diseño
  (3,25 m); carreteras PASS; tramos iguales.
- **Línea de agua visible** (`reports/waterline-metric-v11.json`), frente a la v10b:

| clase | giros > 45° | desfase p50/p90 | sin agua visible |
|---|---|---|---|
| lagos | 11,3 → 11,3 % | 0,12/1,38 → 0,12/1,38 m | 7,8 → 7,8 % |
| estanques | 18,3 → 18,1 % | 0,38/1,88 → 0,12/1,88 m | 4,7 → 4,8 % |
| ríos | 5,6 → 5,7 % | 0,12/1,38 → 0,12/1,38 m | 2,5 → 2,5 % |
| arroyos | 10,5 → 9,1 % | 1,12/2,62 → 0,88/2,38 m | 1,3 → 1,2 % |

- **Profundidad** (`reports/depth-v11.json` frente a `depth-v10b.json`; eje = vértices del surco central):

| | v10b | v11 |
|---|---|---|
| ríos, mediana / p90 | 0,30 / 0,60 m | 0,48 / 1,33 m |
| ríos con 1 m o más | 3 % | 24 % |
| eje de los ríos, mediana / p90 | 0,32 / 0,58 m | 0,55 / 1,38 m |
| arroyos (y su eje), mediana / p90 | 0,14 / 0,19 m | 0,27 / 0,44 m |
| estanques, mediana / p90 | 0,30 / 1,02 m | 0,45 / 1,20 m |
| lagos en los primeros 6 m | 0,40 m | 0,51 m |
| lagos por dentro | 1,13 m (el máximo con el fondo a 1,0 m) | igual |
| tierra a 0–6 m del agua, sobre ella (p50/p90) | 0,51 / 0,77 m | 0,86 / 1,96 m |
| tierra a 6–12 m del agua (p50/p90) | 1,14 / 1,49 m | 1,22 / 2,46 m |

- **Agua baja** (`figures/sections-v10b-v11.png`): el río, el lago y el estanque del RIVER_80 están a 1,0–1,4 m y
  salen idénticos a la v10b, porque su pendiente se limita por el fondo de 1,0 m: era lo previsto para esa zona. El
  arroyo de (4932, 5772), a 2,05 m, baja 8 cm en el eje y su orilla se empina.
- **Finales de río** (`figures/river-ends-r30.png`, `figures/river-ends-v10b-v11.png`): el Мста acaba redondeado; el
  Volkhov pierde la punta aguda; en el Гриб (el marco oscuro del RIVER_80) la columna del corte pasa a tierra y el
  final retrocede un vértice, pero con 8,8 m de ancho (vértice y medio de malla) sigue casi cuadrado en planta: cómo se
  ve en motor está por comprobar.
- **Primera construcción**, sin el recorte del surco: `E:/DayZ-Baltic-Build/v30-v11-pretrim` y
  `@DayZ_Baltic_V11PreTrim`. No se vio en motor; se conserva.

## En motor (07-10, run 9b486b9a)

Nueve poses, con capturas cada 25–60 s desde el teletransporte (`E:/DayZ-Baltic-Build/v30-v11/views-timeseries`).

**La textura de la tierra tarda en cargar:** entre 25 s y más de 6 min tras cada teletransporte. En Chernarus vanilla
pasa lo mismo, así que no es del mapa (BALTIC-019, `../baltic-019-teselas-oscuras-2026-10-07`). Una vista vale si
`tools/playtest/dark_tiles_v30.py` da menos de 0,2.

- **Vistas válidas:** NAVFREE_85, LAKE10_150, PONDS_120, RIVER_80, RIVER_8 y END_GRIB_40. Dos de ellas tienen una
  franja de teselas oscuras junto al borde este:
  - END_GRIB_40, en la mitad derecha;
  - RIVER_80, en el borde derecho.

  Sin textura quedaron L202_330, BORDER_E330 y END_VOLKHOV_60: en ellas se ve el agua, pero no la tierra.
- **Frente a la v10b** (`figures/engine-v10b-v11.jpg`). La v10b solo tiene vistas válidas de PONDS_120, RIVER_80 y
  RIVER_8; sus NAVFREE_85 y LAKE10_150 no tenían textura.
  - El contorno del agua sale igual en las tres.
  - Desde 8 y 120 m no se distingue el calado añadido ni la tierra más alta junto al agua.
  - Desde 80 m, el arroyo del RIVER_80 sale algo más oscuro en la v11. Es compatible con su eje más hondo (0,14 → 0,27
    m), pero no está comprobado: la luz de las dos sesiones no es la misma.
- **Finales de río** (`figures/river-ends-engine.png`): el del Volkhov sale como un corte recto de una celda de ancho,
  y el del Гриб, casi cuadrado. El radio llega como mucho a 0,9 veces el medio ancho (unos 6 m en el Volkhov y 4 m en
  el Гриб), así que el redondeo no pasa de un vértice de la malla de 6 m. El final del Мста no se miró.

## Qué no se ha comprobado

- La tierra junto a los finales del Volkhov y del Гриб, y las poses L202_330 y BORDER_E330, con la textura cargada.
  También falta el final del Мста (12212, 1785).
- Si el arroyo más oscuro del RIVER_80 es por el calado: haría falta una sonda en el sitio con la misma luz.
- Rendimiento.

## Siguiente

1. Que Guillermo decida sobre la v11. Desde el aire se ve como la v10b. Los finales siguen cuadrados en motor: para
   que se vean redondos, el río tendría que estrecharse a lo largo de varias celdas antes de acabar, y eso es un
   cambio de diseño.
2. Si el agua baja (el RIVER_80 y su entorno, a 1,0–1,4 m) sigue viéndose plana, la única palanca es subir el nivel
   del agua y el terreno de esa zona. Es un cambio grande: el mar del motor fija el fondo en 1,0 m.
