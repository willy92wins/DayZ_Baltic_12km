# Candidato v2 «pulido» sobre Narva — 04-10-2026

Decisiones de Guillermo del 04-10 por la mañana, con sus capturas («queda bastante por pulir… especialmente esa
segunda donde desemboca el río»):
- **Superficie:** fondo de lagos y charcas con el tono del terreno, y anillo de grava solo en ríos y mar.
- **Luga:** unir el río con lake_014 y liberar el corredor del último tramo.
- **Balsas:** suavizar las esquinas.

Base: la cadena del candidato de Narva (manda V29 y los fosos llevan agua). Ejecutor: Claude. GLM-5.3-Flash (GX10)
escribió dos herramientas de análisis y revisó la de pulido (§Delegación). Productos pesados en
`E:/DayZ-Baltic-Build/v30-polish`; la primera construcción, anterior a la revisión, queda en las carpetas `*-r1`.

## Hallazgo en la cabecera del Luga

- **Escalera al final del río.** El río acaba en (10535, 4176) con nivel de diseño 4,20 m. 141 vértices del último
  tramo estaban bajados hasta 2,10 m: el tope del constructor (0,25 m por cada 6 m) los arrastraba hacia 7 vértices
  de charcas pegadas. Una de ellas, una franja estrecha a 1,85 m, está justo donde seguiría el río.
- **Agua colgada.** El río y los lagos de la zona están a ~4,15 m, sobre un terreno a ~3,0 m. Los sujetan diques a
  nivel + 0,35 m (`figures/luga-head-heights-before.png`). El canal nuevo tiene que cruzar ese valle con diques, igual
  que el resto de la zona. El censo de abajo enseña que no es un caso aislado.

## Cadena

| Paso | Herramienta | Salida (bajo `E:/DayZ-Baltic-Build/v30-polish`) | SHA-256 |
|---|---|---|---|
| Pulido | `tools/terrain/polish_luga_head_v30.py` sobre `v30-narva-shore/mouths-moats` (e9cb9d9c) y `sd_v29.npz` (d756a5da) | `polish/terrain_pilot.npz`, `polish/sd_polish.npz` | 931632d6e5b00c92…, 6817bf78b80f89c5… |
| Agua | `tools/water/patch_water_tiles_v30.py --sea-cut-old 0.51 --sea-cut-new 0.51` sobre `v30-narva-shore/water-moats` | `water-polish/pieces.json` | 1e06bc243678167d… |
| Cauces | `tools/water/fit_channel_pieces_v30.py --overlap-all --no-pad --sea-cut 0.51` | `fit-polish/terrain_pilot.npz`, `fit-polish/water/pieces.json` | b7a5e6a1201b10ff…, 0907920a24c745a5… |
| Orillas | `tools/terrain/fit_shore_crossings_v30.py`, argumentos del candidato + `--sd-override polish/sd_polish.npz --narva-core-m 0 --free-corridor-box 10150,3700,10700,4600` | `shore-polish/terrain_shore.npz` | 88ed02684bef02a2… |
| Superficie | `tools/terrain/build_surface_v30.py --workers 12 --bed-tone land --shore-ring flowing` | `surface/` | — |
| Paquete | `tools/terrain/build_v30_package.ps1` del checkout principal, `-WaterSource fit-polish/water` | `package/out/Addons` | mundo f6ca1cb6c689fc8b…, agua 0cca78668025d9c3… |

Desplegado como `@DayZ_Baltic_PolishCandidate` (copias comprobadas por hash), con la misión `BalticShoreSdfCandidateV1.BalticTrial`.

## Qué cambia (`polish/report.json`)

- **Canal Luga–lake_014.** 220 m de eje y 20 m de ancho, con 92 vértices nuevos (78 de tierra y 14 de la charca). Nivel 4,20 → 4,17 m y calado 0,35–2,95 m. Cruza el valle con diques, como el resto de la zona.
- **Río.** 141 niveles vuelven a su banda (hasta +2,10 m). Se sustituyen 17 vértices de la franja y se separan 5 de charcas.
- **Lagos.** Se suavizan 17: 5 con apertura de 8 m (014, 138, 152, 164, 218) y 12 escalonados con Chaikin. Desviación máxima 3,8 m, sin perder lóbulos. Ningún vértice de lago pasa a tierra: el redondeo actúa a través del campo de distancias (1.605 vértices). La apertura sola se descartó porque borraba lóbulos y levantaba diques de 5,9 m sobre el lecho del río (`figures/lake-rounding-discarded-opening.png`).
- **Orillas.** 111 vértices de orilla elevados (máximo 2,95 m). Fuera de la caja (10150, 3700)–(10700, 4600) no cambia ningún vértice (0).
- **Campo de distancias.** Antes de cambiarlo, la regla del constructor reproduce el campo base en la caja: máximo 0,000002 m en 4.510 vértices. Si no lo reprodujera, la herramienta se para.

## Comprobado

| Qué | Cómo | Resultado |
|---|---|---|
| Puertas del terreno | `verify_terrain_v30 --sea-cut 0.51`, frente al candidato de Narva | Idénticas: calado 6 (arroyos), piezas 35 (R2/R3, ya conocidas), orillas/lecho/suelo/pendientes 0/0/0/0. La identidad V29 de Narva cambia por diseño |
| Carreteras | `verify_roads_v30` | PASS: 100 cadenas y 76.513 muestras, como Narva |
| Ajuste de orillas | control interno | 0 mojados someros, 0 subidos donde no toca y 0 bajo el suelo; caras de corredor exactas fuera de la caja |
| Línea de agua en la caja | `luga_box_offsets` (misma medida que el ajuste) | p50/p90/p99 0,070/2,17/4,39 → 0,076/1,92/3,88 m |
| Agua visible en bajamar | `audit_visible_water_v30` + `classify_visible_water_v30` | Igual que Narva salvo el canal: +2.312 m² fuera del diseño `water_v3`, 2.560 de ellos en la ventana del canal. Tierra adentro, 0 |
| Superficie | vista previa (`figures/surface-preview-before-after.png`) | Grava 67,6 → 64,8 M píxeles; lagos y charcas sin fondo negro; ríos y canal lo conservan |
| Paquete | `build_v30_package.ps1` | Alturas exactas; materiales, cabecera y puentes idénticos; 17.573 objetos de agua |
| Sin verificar | — | Vista en motor (la caja la ocupaban otras sesiones: @SimpleGroup y después LFPowerGrid con Guillermo jugando). NM e IA |

## Cauces frente a Chernarus (BALTIC-015)

`tools/water/compare_channel_joints_v30.py` aplica a nuestras piezas la misma regla de juntas con la que se calibró la
biblioteca contra Chernarus, y mide además el área de huella con dos láminas o más.

| Grupo | Piezas | Juntas | Área con dos láminas o más | Desvío de rumbo en junta (p50) | Solape en junta (p50/p90) |
|---|---|---|---|---|---|
| Chernarus, ríos | 660 | 647 | 0,33 % | 0,13° | 0,04/0,11 m |
| Chernarus, arroyos | 389 | 325 | 0,49 % | 0,27° | 0,04/0,10 m |
| R1 | 8 | 0 | 58 % | — | — |
| R2 | 44 | 37 | 73 % | 8,84° | 0,54/1,73 m |
| R3 | 47 | 45 | 75 % | 11,38° | 0,44/2,27 m |

En R1 la regla no encuentra juntas: el solape, de unos 22 m, supera el umbral de 12 m con el que la regla acepta una junta.

Chernarus encadena canto con canto (−4 cm de mediana) y gira dentro de las piezas curvas, con desplazamientos
laterales de hasta ±3,5 m. Nosotros solapamos un par de faldones (`overlap_from=None` en R2/R3 y `--overlap-all`,
`tools/water/fit_channel_pieces_v30.py:263`) y giramos en las juntas. Es la lectura de Guillermo: las costuras de R2
son solapes de colocación (`joints/ours.png` frente a `joints/vanilla.png`).

El consejo del 04-10 (`reviews/2026-10-04-council-rumbo-agua/ARBITRAJE.md`) añadió dos cosas:
- **Solo rectas.** El colocador únicamente usa piezas rectas (`tools/water/fit_channel_pieces_v30.py:211`, filtro
  `turn_deg == 0`), así que el encadenado con curvas nunca se ha probado.
- **Rumbo bien medido.** La primera versión de esta medida comparaba la salida de una pieza con la salida de la
  siguiente, en lugar de con su entrada. Ya corregida, coincide con la calibración de la biblioteca: 647 y 325
  juntas, 0,13° y 0,27°.

## Agua colgada en todo el mapa (BALTIC-017)

`tools/water/census_perched_water_v30.py` agrupa el agua estancada por nivel y compara cada masa con el terreno natural a 12–36 m de su borde. De 631 masas:
- **Colgadas** (más de 0,3 m por encima del terreno natural): 111 lagos, 7,0 km².
- **Con dique** de más de 0,5 m: 190 masas (173 lagos y 17 charcas).
- Los lagos de la cabecera del Luga quedan ~0,8 m sobre el terreno natural, con diques de ~1,4 m. Los dos lagos más grandes también
  salen colgados: el del oeste (nivel 2,64 m, 4,6 km²) por 0,33 m y el del sureste (2,13 m, 2,0 km²) por 0,55 m.

Mapa: `census/map.png` (amarillo de 0,3 a 1 m, rojo por encima de 1 m). Un arreglo posible es derivar los niveles de lago del terreno
natural, pero es una decisión de diseño pendiente.

## Delegación (GX10, GLM-5.3-Flash, 3 carriles)

- **D, `compare_channel_joints_v30.py`.** 8 min. Aceptada con dos cambios del receptor: nunca asignaba los bordes de
  las piezas (`KeyError` al buscar juntas) y la transformación modelo→mundo estaba traspuesta. La autoprueba añade una
  cuña girada que caza la traspuesta. Un tercer fallo se me escapó en la revisión y lo encontró el consejo (astra): el
  rumbo en la junta comparaba salida con salida. Está corregido, con una prueba de dos curvas encadenadas.
- **E, revisión ciega de `polish_luga_head_v30.py`.** 17 min. Cuatro hallazgos reales, todos latentes en esta
  construcción: conversión de lagos fuera de la caja, orillas sin recalcular junto al agua retirada, reproducción del
  campo de distancias sin corte y auditoría de niveles fuera de la caja. Corregidos. La corrección de las orillas sube
  un vértice, (10458, 4050), de 2,82 a 2,98 m, y la cadena se rehízo con la herramienta corregida.
- **F, `census_perched_water_v30.py`.** 5 min. Aceptada con dos cambios: el recuento de clases sin `minlength` daba
  `IndexError` en el primer lago, y los colores del mapa tenían una forma errónea (la autoprueba ahora también dibuja).

## Siguiente

- Ver el candidato en motor con Guillermo (`camera-poses.json`): cabecera del Luga (aérea, oblicua y dos bajas), rectángulos, lake_038,
  fosos de Narva, las manchas de R1_aerial y EDGE1 con la superficie nueva, y SHORE4 para comparar.
- Decidir: cauces vanilla solo en ríos anchos, con encadenado canto con canto y curvas como Chernarus (R2/R3 volverían a planos), y qué
  hacer con el agua colgada (BALTIC-017).

## Vista en motor (04-10, noche)

Run d227200e, las 11 vistas de `camera-poses.json`: hoja en `runtime/view-d227200e/contact-sheet.jpg` y capturas con
hash en `runtime/view-d227200e/shots-manifest.json`. Sondas de superficie en el mismo manifiesto: las placas de los
rectángulos son agua a 4,15 m y las de los fosos a 4,60 y 2,75 m, sobre terreno a unos 3 m.

Veredicto de Guillermo:

- la cabecera del Luga pasa con retoques;
- las placas son agua colgada (BALTIC-016 se resuelve por BALTIC-017);
- en la vista 9 hay que estrechar la franja somera del Narva y suavizar los bordes angulosos;
- el canal a lake_014 tiene que ser navegable.

Todo eso se construye en `../v30-v3-candidate-2026-10-04`.
