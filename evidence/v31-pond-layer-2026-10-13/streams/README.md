# Arroyos finos frente a Chernarus (13-10-2026)

Guillermo: «Chernarus tiene arroyos más delgados y no son así». Medido en Chernarus vanilla, servidor sin cliente:

- **Cintas `stream_14`** (`chernarus_ribbons.py` sobre el registro de Astra del 03-10, 384 piezas): el suelo está 0,22 m bajo la lámina en
  el eje (mediana) y ya +1,22 m por encima a 6 unidades de modelo, dentro de la cinta (96 %). El contorno lo dibuja el terreno, no el
  borde de la cinta: el agua es una franja estrecha en el fondo de una V.
- **Diagonal del terreno** (`missions/BalticChernarusStreamGridV1.chernarusplus`, cuadrícula de 1 m en 41×41 m alrededor de 12 piezas,
  `chernarus_triangulation_vote.py`): 202/202 celdas de 7,5 m partidas por la diagonal NO-SE, como en Baltic.
- **Agua** (`GetWaterDepth` a ras de suelo; hay que cargar los objetos con `GetObjectsAtPosition` en el mismo fotograma, si no el servidor
  sin jugadores no ve las piezas): `chernarus-stream-water-12-sites.png`. Los arroyos que van hacia el **NE escalonan** como los nuestros;
  los que van hacia el NO salen lisos (siguen la diagonal) y los N-S/E-O rectos. La franja de agua mide ~2–4 m.
- **Nuestro (9185,9280)** en EV106: banda de 6–12 m con 2–18 cm de agua sobre un fondo de valle plano (orillas +0,02–0,33 m a 6 m). En
  el piloto `tools/water/v_streams_v31.py` (adelgazar a un vértice de cauce sin cortar el agua, orillas en V sin superar el terreno de
  detrás) queda como la franja escalonada fina de Chernarus (`baltic-thin-v-pilot-ab.png`). Sin construir ni ver en el juego.

Conclusión: la escalera NE es de la malla también en vanilla; lo que la hace visible aquí es el ancho y la poca profundidad.
(Corregido abajo: las 1.682 piezas `streambed` no son decoración de orilla sino otra red de arroyos con agua propia.)

## Revisión de los mapas vanilla (subagente Opus, 13-10; `../vanilla-tricks-REPORT.md`, datos en `E:/DayZ-Baltic-Build/vanilla-tricks-20261013/`)

- **`streambed` es un sistema de arroyo completo**: placa de 14 × 24 m (o 14 × 12) con lecho 3D y piedras a ±2,5 m del eje, roadway
  `water_ext` a +0,21 m del centro del modelo (lo que lee `GetWaterDepth`) y lámina visible CalmWater 0,25 m más arriba. 1.682 piezas,
  ~33 km, ninguna a <30 m de una cinta `stream_14`/`river_24`. Agua visible p10/p50/p90: `stream_14` 4/5/9 m, `streambed` 3/4/5,5 m.
- Piedras `stones_*` sueltas: 17 por km y solo junto a `streambed`, a 2,3 m del eje (p50), verticales, 0,08 m enterradas; carrizos
  `p_phragmites` 9–25 por km a 5–7 m (`kit/chernarus-bank-dressing.json`, `kit/scripts/bank_dressing.py`). No tapan la escalera.
- Falso positivo del informe, comprobado con las piezas v31 reales: no hay charcas a 0,50 m junto al mar; las 36 masas de vértices de
  charca a <18 m del mar del motor están a 1,95–2,12 m (el informe leyó la capa `level` antigua, anterior a EV96).

## V fina v4 (evaluada, no construida)

`tools/water/v_streams_v31.py` v4: regla de estrechez local (7 × 7 vértices), solo tramos con ancho visible > 5 m, V para ~4 m de agua.
Ancho medido con el eje medial de la línea de agua TRI (`tools/water/width_compare.py`): 6,0/6,7/9,5 → 3,0/4,2/4,2 m. A/B en
`thin-v-v4-ab-irregular-and-ne.png` y `thin-v-v4-ab-smooth-reaches.png`: los tramos que ya eran lisos de 5–6 m ((3441,2516),
(9228,6026), (1684,398)) pasan a escalera, y en (8235,9125) el agua llega a cortarse. Un tramo hacia el NE solo sale continuo y liso con
dos filas de vértices (~6 m). La anchura no separa los tramos irregulares de los lisos; la profundidad sí (cauce a 1,17 m bajo la lámina
frente a 0,17–0,29 m). Guillermo eligió el 13-10 el piloto del kit `streambed`.

## EV108 = EV107 + piloto del kit `streambed` (`@DayZ_Baltic_EV108_StreambedKitPilotV7`)

`tools/water/streambed_kit_v31.py` v7 (todas las reglas en su cabecera), sobre el terreno, la huella, la cobertura y la envolvente de EV107:
- **Sitios** (`../kit/sites.json`, `../kit/kit-report.json`): kit-118 = el arroyo irregular de (8235,9125), 290 m, 20 piezas (14 cortas;
  las 2 de los extremos quitadas: la carretera aguas arriba y celdas de la envolvente de otro nivel en la salida); kit-7 = arroyo de valle
  aislado de (8350,12100) a (9140,11270), 1,65 km, 119 piezas (81 cortas). Familia `leaf`, 25 % de rectas largas con tronco (`_2`), 44
  grupos de piedras (giros >= 12 grados y cada ~60 m a lo largo del cauce; hueco máximo 68-92 m). Giro máximo entre piezas 8,5 / 29,8 grados.
- **Medido en Chernarus y aplicado** (`../kit/scripts/`): +Z de la pieza aguas arriba; paso entre piezas alineadas 21,5 / 14,9 / 8,8 m
  (solape de ~2,5 m); la cara `water_ext` cubre |z| <= 9 m (larga) / 3 m (corta) y los extremos bajan en rampa a -0,48 m. **El agua
  visible es una lámina plana de 14 x 24 m** (`proxy/streambed_*_water.p3d`, x +-7 m) y la cara `water_ext` también mide 14 m: es la V
  del terreno la que las recorta a 3-5 m.
- **Terreno** (1.273 vértices): asiento de Chernarus hasta 3 m del eje (-0,33 / -0,15 / +0,70); de 3 a 14 m solo se sube, hasta ese
  asiento sin superar el terreno de detrás salvo lo justo para enterrar la lámina; más allá de los extremos del kit, como mucho suelo +
  0,5 m (remate sin tapón). Bajo cada 0,5 m del eje el terreno queda >= 0,03 m bajo el suelo del kit bajando solo vértices de peso >= 0,15
  por el exceso (81 muestras sin resolver; 5 puntos del eje como mucho 6 cm sobre el suelo). El cauce viejo sin agua se rellena hasta su
  desagüe (26 vértices, hasta 2,06 m) y ninguna hondonada queda más honda que antes. Pendientes <= máx(35 grados, antes), fondo mínimo
  1,27 m, 0 vértices de reserva, plataforma o Narva.
- **Charcas**: 394 + 2.201 celdas de cobertura y envolvente retiradas; huella 381.046 -> 380.058 celdas; 43 bordes expuestos (= EV107).
  Verificación exacta (`../kit/ev108-verify-exact.json`): 13.508 piezas, 760.116 medias celdas, pasa.
- **Asiento offline** en la cara de agua (terreno - suelo del kit): eje 5/973 puntos por encima (máx. +0,06); lámina visible en el 59 %
  de los puntos a 2,5 m, 40 % a 3 m, 16,5 % a 4 m, 5,7 % a 5 m; borde final de la lámina como mucho 0,57 m sobre el terreno.
- **Servidor** (`missions/BalticKitProbeV1.BalticTrial`, 1.023 puntos, `../kit/probe-ev108-summary.json`, log `../kit/probe-ev108.log.gz`):
  charcas 100/100 y lagunas 28/28 con nivel exacto, enterrados y exteriores 0/150; **eje del kit 349/417 con agua** (calado p50 0,08 m;
  Chernarus 0,35); 0/278 puntos a 6 m del eje y 0/50 del cauce viejo con agua. El motor solo da el agua del kit con >= 0,10 m bajo el
  suelo (179/180 con ese margen; 68/107 por debajo de 0,05 m): más margen = lámina más ancha.
- **Revisión independiente** (dos rondas, tope fijado antes de la primera): ronda 1 sobre v5, 9 defectos confirmados de 9
  (`../kit/review-round1-v5.json`): extremos recortados que dejaban seco el final y un tapón de 1,3 m sobre la carretera, salida quitada
  por celdas secas, hoyos cerrados de hasta 2 m en el cauce viejo, eje que ensanchaba la lámina, piedras espaciadas en línea recta y
  cuatro latentes. Ronda 2 sobre v6, 9 hallazgos confirmados de 10, 7 defectos distintos (uno lo vieron tres revisores; `../kit/review-round2-v6.json`): el agua conservada en los extremos protegía un
  vértice de la zanja (hoyo de 2,5 m y luego un labio seco), el eje aún hundía vértices lejanos, la salida terminaba bajo terreno
  protegido, relleno incompleto y tres latentes. v7 corrige todos; comprobado con las medidas de arriba y la sonda, sin tercera ronda.
- **Historia de la vista con Guillermo (13-10)**: V3 en el cliente: losas de agua rectangulares con huecos y escalones en las juntas,
  «muy poligonal» (la zanja de V3 dejaba la lámina de 14 m a la vista). V1-V6 construidas y sondeadas; todas borradas de `P:/Mods` salvo
  V7 (fuentes en `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev108-kit/v*-run`).
- Mundo `389e27a6edb02128c8ef872210ed68763cba077207d9143d3cebe499dcd56c87`, agua `a48f2fc10e4e110005c420b2a2c56228d6b4c864c463720c0b004cbd4711c080`.
- **No verificado**: la vista de V5-V7 en el cliente, el aspecto de los remates y del enlace con la carretera del kit-118 (pendiente de la
  015: alcantarilla o puente), las juntas en los giros de hasta 29,8 grados de kit-7, piedras y rendimiento.

## Candidatos para extender el kit (14-10, `tools/water/kit_candidates_v31.py` sobre EV107)

`../kit/kit-candidates.json` / `.csv` / `.png`: los 102 tramos estrechos de río o arroyo del mapa, medidos. El ancho no separa los
irregulares de los lisos (los lisos de 5-9 m tienen el percentil 90 de ancho igual que los irregulares); el calado del cauce sí:
- **Irregulares** (calado p50 > 0,5 m): 16 tramos, 3,84 km; **13 candidatos** (>= 60 m), 3,74 km, incluido kit-118. Seis tienen
  carretera a <= 6 m (la herramienta corta los extremos en la carretera; si la carretera cruza por el medio hace falta un cruce de la 015).
- **Lisos**: 86 tramos, 81,6 km (calado 0,10-0,39 m), como (3441,2516): el kit no es necesario ahí.
- **Antes de extender**: 10 de los 13 tocan agua ancha. `streambed_kit_v31.py` toma como cuerpo todo el agua conectada a la semilla, así
  que necesita un modo que limite el cuerpo al tramo estrecho (la regla de `v_streams_v31.py` v4) y acabe el kit en el agua ancha.
