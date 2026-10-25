# Revisión del relevo de Astra y arreglos EV96/EV97 — 11-10-2026 (Claude)

Base 1.0 sigue **sin aceptar**. Este bloque revisa lo que dejó Astra (Codex, 07-10 a 10-10), encuentra
la causa del agua de dos colores y del cielo morado, y construye dos previews nuevas. La aceptación visual
de EV96/EV97 la hace Guillermo en el motor; aquí solo hay comprobaciones offline y lecturas del servidor.

## 1. Estado en que Astra dejó el mapa

- 52 commits en `claude/codex-handoff-review-74f290` (4382029..65df91f), 85 identificadores EV9–EV95,
  38 previews completas desplegadas y ninguna aceptada. Desde el 08-10 nadie miró el mapa en el juego:
  lo del 09 y 10-10 son puertas offline y lecturas de alturas del servidor.
- Los 20 IDs de `bugs.md` seguían abiertos. Guillermo había señalado directamente 007, 016 y 020; el resto
  son fallos de sondas, IA o navegación encontrados por los agentes.
- Su siguiente paso (consumidor global V2 del candidato 1bd6b67d) se repitió hoy con 40 GiB libres:
  `E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/global-operator-prototype/global-dry-rollback/postsolve-consumer/instrumented-v2/runs/attempt-03/report.json`
  termina `ERROR_INDEPENDENT_CONSUMER` por el tope de 600 s, y antes ya había dado `pass_gate=false` en
  `native_faces_and_sectors`. El candidato global queda descartado.
- La comparación underlay B/A′ no se completó: exige `camera_set`, vetado por BALTIC-001 y denegado por el
  arnés. El run B 8933fce2 se lanzó, escribió `END;1225` y se cerró al caducar el lease.
- Otros hallazgos que hay que corregir (ver auditoría en la sesión):
  - Astra usó `camera_set` pese al veto y el cliente murió (`evidence/v30-base-surface-runtime-2026-10-09/README.md:9`);
    el relevo del 07-10 se contradecía (`HANDOFF.md:66` lo pedía, `:213` lo vetaba).
  - 48,5 GB de mods Baltic en `!Workshop` de C: (153 carpetas). Movidos hoy a E: (sección 5).
  - Repo: +456 MB de evidencia y 13 `tmp_obj` huérfanos (53 MB).
  - Scripts `evidence/v30-global-bank-extension-2026-10-10/*/checkpoint_*.py` y `update_*.py` reescriben por regex
    el LIVE-STATE de HANDOFF.md y la nota de Obsidian (p. ej. `underlay-preflight-checkpoint/checkpoint_underlay_preflight.py:56-69`).
    **No reejecutarlos**: pisan el estado vivo.
  - HANDOFF/bugs contradictorios (lectura nativa EV95 «pendiente» en `bugs.md:1` y PASS en `HANDOFF.md:11`) y
    poco legibles (celdas de 10 KB, palabras pegadas). Reorganizados hoy.

## 2. Cielo morado y texturas que no cargan (BALTIC-019, parte)

Síntoma: cielo morado, terreno blanco con «esquirlas» y puente sin textura. Se descartó la GPU (VRAM 3,7/24 GB)
y el paquete:

| Run | Mundo | Menú de pausa al cargar | Render |
|---|---|---|---|
| 409c4621, 460e1d1d, ff153755 | EV95 f1a148ca | sí | morado |
| e59f7712 | Chernarus vanilla | no | normal |
| dc494595 | B b11c825b | no | normal |
| 4fb00a87 | D1 = B + WRP de EV95 (8f7c6fb4) | sí | morado |
| 55bad625 | D2 = B + 996 PAA de EV95 (62bd6b2c) | sí | morado |
| 9fa1257f | D0 = B reempaquetado sin cambios (c67d030f) | no | normal |
| ff153755 tras clic + «Continuar» de Guillermo | EV95 | — | **normal** |

Causa demostrada: si la ventana de DayZ pierde el foco durante la carga, se abre el menú de pausa y el render
queda roto hasta que recibe **foco real del sistema**; `ui_click continuebtn` no lo arregla. EV95 no estaba
rota. Las 996 PAA de EV95 son estructuralmente iguales a las de B (`scripts/paa_compare.py`: tipo, mips,
dimensiones y SFFO). Consecuencia operativa: toda revisión visual necesita a Guillermo delante para dar el foco.

## 3. Agua de dos colores (BALTIC-016/018) → EV96

Medido en B en el punto que marcó Guillermo, (1912,7; 6495,2): misma lámina 2,45 m, fondo a 1,00 m en unas
celdas (agua clara) y a −4,5/−5,5 m en otras (oscura, con oleaje). Donde el fondo cae bajo el mar del motor
(0,75 ± 0,25 m), el mar se pinta bajo la charca y se transparenta. Eran las «excepciones de bajos/Narva».

Arreglo (`tools/terrain/fix_two_colour_water_v30.py`, decisiones de Guillermo de hoy):
- A: celdas de charca con lámina ≥ 1,95 m y fondo < 1,0 m → fondo 1,0 m. 4.718 editadas (88 de reserva sin tocar), calado mínimo 0,95 m.
- B: tramos bajos de cauce (cls 3/5/6/7, lámina < 1,95 m) con fondo submarino → mar del motor. 14.975 celdas
  en 63 tramos; 12.924 fondos a −0,5 m; 2.326 piezas de charca retiradas; 81 piezas a medias conservadas
  (revisar en motor). Lagos (cls 2) nunca se convierten. 370 celdas de reserva vial quedan con fondo sobre el
  mar: son los cruces secos de BALTIC-015.
- 0 celdas secas cambiadas. Recibo: `ev96-stage-report.json` (original completo SHA `52673475…`), `ev96-deploy.json`.
- `@DayZ_Baltic_EV96_WaterFixV1`: mundo `b12fe58cbb639ba46d3482ab3171a288c8bea970a7fd81194fb2e375e87dc7a6`, agua `3946db8b…` idéntica.
- Lectura del servidor (run 5c9163cb): agua dulce a 2,45 m en los tres puntos medidos. Vista pendiente de foco.

## 4. Relieve en planos angulados (BALTIC-007/011) → EV97

`tools/terrain/smooth_dry_land_ev97.py` (no confundir con `smooth_dry_relief_v30.py`, de Astra), σ = 12 m sobre EV96: convolución normalizada solo con vértices secos,
rampa de 4 celdas desde reserva/plataformas/Narva (fijas), suelos `min(H, lámina vecina + 0,30)` y `min(H, 1,60)`.
- 3.011.785 vértices cambiados; mediana 0,04 m, p99 1,04 m, máx 5,19 m; pico 123,1 → 117,9 m.
- Tierra seca interior: quiebros > 10° 13.889 → 8.198; > 20° 571 → 354; pendiente p99 23,2° → 22,3°;
  mínimos falsos 5.726 → 2.986. 0 vértices inundados, 0 nuevos en la banda de orilla (no hace falta regenerar
  la superficie: `build_surface_v30.py:147-213` solo usa la altura para agua, orilla y tono del fondo).
- σ 9 y 18 m probados: 9 m redondea poco los planos grandes; 18 m crea pliegues en las transiciones.
- `@DayZ_Baltic_EV97_ReliefV1`: mundo `546bdcfd5f2b7f38c78b7d1fe2ce3d791ee81126b7722b5926e7697a6fd39ede`, agua idéntica.
- Lectura del servidor (run 7e79fe3f): 5/5 alturas igual a EV97 al milímetro. Vista pendiente de foco.

## 5. Limpieza

- Mods: `scripts/archive_mods.py` mueve a `E:/DayZ-Baltic-Build/archived-mods-20261011/` las previews de más de
  100 MB salvo V30, B, EV95, EV96, EV97 y ShoreWaveV30_Nav, verificando SHA-256 por archivo antes de borrar
  el origen. Recibo: `archive-receipt.json` en ese destino.
- Todos los runs de hoy se cerraron con `dayz_test_close` ordenado y lease liberado, salvo 8933fce2 y 4054f29d,
  que el daemon retiró al caducar el lease (cierre ordenado en el RPT del cliente).

## Límites

- EV96/EV97 no tienen navmesh regenerada (heredan la de EV95, ya caducada) ni prueba de lancha/IA.
- No se ha visto en el juego que el agua salga de un color ni que las orillas se vean redondeadas.
- Escalón de lámina donde un tramo convertido en mar se une al río más alto (hasta ~1,2 m).

## 6. Tarde del 11-10: decisiones, cuadrados grises (EV98) y orillas

Decisiones de Guillermo: puentes vanilla según ancho (015), rebajar el reborde de los dos lagos grandes sin cambiar su nivel (017),
lagunas pequeñas al final de los ríos (020). Prioridades: orillas en diente de sierra/poligonales y cuadrados grises sobre el agua.
Elegido: **rehacer la capa de charcas** con piezas que entren bajo la orilla (diseño en curso; ver HANDOFF).

**Investigación (dos workflows, 9 agentes y 2 jueces; salidas en C:/Users/guill/AppData/Local/Temp/claude/baltic-understand y baltic-gray):**
- Navmesh: se regenera sin Terrain Builder ni escritorio, con `tools/navigation/generate_navmesh_console.py` y `tools/playtest/attach_navmesh.py`
  (como el 03-10). Hacerlo una vez, sobre el WRP final. EV97/EV98 llevan todavía la NM V29 eb0f131e.
- Cuadrados grises: la malla gruesa del terreno queda **descartada como causa principal** (bordes medidos sobre bordes de piezas, fondo 3,8–6,6 m bajo
  el agua). Causa probable: charca y mar superpuestos que EV96 dejó.
- Orillas: 1.298 esquinas >45° en 355 km; los suavizados anteriores limitaban el movimiento a 4 m y no cambiaban clases. Las piezas cubren celdas
  enteras: la orilla no puede salir de esa escalera de 6 m.

**EV98** (`tools/terrain/separate_pond_sea_v30.py`, sobre EV97): ninguna pieza de charca sobre un vértice mojado con fondo < 1,0 m.
609 piezas con lámina dentro de la banda del mar retiradas (325 globalvis, 221 seamfix…), 196 fondos subidos a 1,0 m (88 bajo el puente de Narva:
reserva mojada sin calzada, excepción explícita), 0 tierra seca. Comprobación independiente (`scripts/verify_ev98.py`): 0 vértices submarinos
bajo pieza; pieza más baja 1,075 m. Coste: 16 vértices navegables más bajo 0,95 m de calado (2.456 → 2.472, mínimo 0,425 m).
`@DayZ_Baltic_EV98_PondSeaV1`: mundo `4330c9a226f81d4572bba09a0d8596a8cd11a85ea825264b6688c91383f650ac`, agua 3946db8b idéntica.
Vista en San Petersburgo (run 6df865b8) sin valoración de Guillermo todavía; la franja de grava vista en (8725, 10037) es una plataforma seca de diseño.

**Orillas: arnés fijo** `tools/terrain/eval_shore_v30.py` (sha 343f5716…), con autoprueba y control negativo (3/3 violaciones detectadas) antes de
construir candidatos. Base EV98: mapa 4,03 dientes/km y 6,29 esquinas/km; San Petersburgo 6,07 y 7,21. Tres enfoques y juez adversarial
(`shore-candidates/judge-*.json`): sdf gana por eliminación (SPB 5,01/6,64, limpio pero modesto); fair suaviza más (SPB 3,78/5,74) pero fragmenta
arroyos finos y cambia >5 % el área de muchos cuerpos; morph descalificado (mueve la orilla >6 m y sus comprobaciones eran sobre datos
intermedios). Ninguno quita la escalera junto a las piezas: de ahí la decisión de rehacer la capa de charcas.

## 7. 12-10: costa de mar suavizada y rebordes de lagos (EV99)

**Arnés v2** (`tools/terrain/eval_shore_v2.py`, sha 422bf818…, congelado con autoprueba 52/52 y controles negativos): métrica sobre los
**triángulos del motor** (el v1 de cuadriláteros infravaloraba el dentado a la mitad), separada mar/charca, más puertas de área exacta por cuerpo,
topología, inundación y navegación. Ninguno de los candidatos de la ronda 1 lo pasaba.

**Ronda 2** (2 constructores y juez): gana **sea-sdf** — resolvedor exacto sobre las aristas NW-SE para que el terreno corte 0,75 m sobre una curva
suave a lo largo de cada línea de costa. SPB mar 11,32 → 3,47 dientes/km; mapa mar 15,20 → 2,33; charca SPB 17,87 → 13,97 (deltas sdf it8).
Juez: escalera de la costa de mar visiblemente eliminada en tramos anchos del Neva, desembocadura y golfo; quedan canales de un vértice y orillas
de charca. Riesgos dentro de las puertas: 110 triángulos más empinados en SPB (orilla del Neva, 23–31°), 3.041 vértices navegables con calado
0,95–1,0 m, un cuerpo al +4,97 % de área (límite 5 %).

**Rebordes de lagos (017)** `tools/terrain/lower_lake_rims_v31.py`: vértices secos a ≤24 m del lago, sin tocar el primer anillo alrededor de
ninguna agua (la primera versión fundía motas sueltas del lago SE: fusión y 8 m² inundados; corregido), suelo = máx. láminas cercanas (incluidas
las de pieza) + 0,30. SO 2.143 vértices (p90 de la franja 0–12 m sobre la lámina 0,78 → 0,68 m), SE 1.380 (0,91 → 0,40 m).

**EV99** = sea-sdf cand3 + rebordes: terreno `8e35c3ab…`, **18/18 puertas v2** (`ev99-harness-v2.json`). `@DayZ_Baltic_EV99_ShoreV1`, mundo
`fb8893a4effc4108e1e92d641b70af71ed02545c214eab956344cc2d5b3f35fe`, agua 3946db8b (piezas de EV98). Sin vista todavía: la lectura de alturas
del servidor exige cliente (`surface_query` responde `client_not_polling` en un run solo servidor); se hará en la sesión con Guillermo.

## 8. 12-10: orillas de charca (EV100)

**Arnés v3** (`tools/terrain/eval_shore_v3.py`, sha a3ea2779…, base EV99, autoprueba 48/48): las 18 puertas de v2 más islotes (perdidos o
<80 % de área), navegables que se secan, banda de calado 0,95–1,0 m (+1 % máx.) y triángulos empinados >20° (≤50 nuevos, ninguno >35°).

**Ronda 3** (2 constructores, juez): **sin ganador limpio**. pond-edge (resolvedor exacto de sea-sdf sobre láminas de charca) sacaba su
ventaja ahogando 54 islotes de un vértice (uno de 60 m² que la puerta K=3 no ve); pond-edge-thin borraba o partía cuerpos pequeños sin
declararlo (hasta −87 %). El juez restauró los 54 vértices de pond-edge (`round3/make_diag_isle0.py`): pasa las 24 puertas.

**EV100** = esa versión restaurada: terreno `d5565f63…`, **24/24 puertas v3** en ejecución propia (`ev100-harness-v3.json`). Triángulos del motor,
EV99 → EV100: SPB charca 13,97 → 6,35 dientes/km (esquinas 12,14 → 11,23); SPB mar 3,47 → 3,40; SPB total 5,91 → 4,05 (desde EV98: 12,80 → 4,05);
mapa total 8,75 → 5,86. Juez: escalera suavizada en charcas anchas, todavía visible en arroyos estrechos que van hacia el NE ((9185,9280),
(8235,9125)); eso exige piezas nuevas (capa v31). Probado y descartado: separar a ±3 cm de la lámina los vértices cercanos para evitar parpadeo
(rompía la topología: desplaza varios metros la línea donde la orilla es casi plana). Vigilar en el juego: 2.103 vértices a <3 cm de la lámina.
`@DayZ_Baltic_EV100_PondBanksV1`: mundo `21e7f71d28300279670e6b2cd3c0b9a25811f0b6247d29157266fc08baf9e953`, agua 3946db8b.

## 9. 12-10: vista de EV100 y fondo del mar suavizado (EV101)

**Vista de Guillermo en EV100** (run 7ce895e1; la del run 517c0dd6 se cortó porque el juego se congeló por la GPU: Guillermo
reinstaló el driver, 617.42). Lectura del servidor: 4/4 alturas exactas. Veredicto: **cuadrados grises «mucho mejor»** (019); el suavizado
«aún bastante mal»; **en la confluencia de un río con el mar se ven dos colores y un encuentro poligonal** (`ev100-confluence-two-colours.jpg`,
cámara libre).

**Causa (medida en los datos; la lectura del color es inferencia).** El sitio que encaja es la confluencia del brazo del delta con el Neva,
~200 m al N del personaje (8650–8750, 10225–10250), donde muere la carretera. No hay piezas de charca allí (capa `cover-level-ev98.npy`): los
dos colores son el mismo mar del motor. El fondo está en mesetas: el delta (cls 4) plano a −2,55 m en el 40 % de sus vértices, la plataforma
junto a la orilla a −0,4/−0,1 m y el golfo plano a −12 m; los saltos van de una meseta a otra en 1–2 celdas. Si el mar se tiñe por profundidad,
cada meseta tiene su color y la frontera sigue la malla de 6 m. Mapa entero: 11.814 pares de vértices de mar vecinos con >1 m de salto. Aparte, 63
puntos donde una pieza de charca toca el mar del motor (323 celdas; `scripts/pond_sea_junctions.py`): ese encuentro (otro sombreador, escalón
≥0,2 m y escalera de celdas) es inevitable mientras la pieza no baje de 0,95 m.

**EV101** = EV100 + `tools/terrain/smooth_sea_bed_ev101.py` (σ 1,5 celdas × 10 pasadas, normalizado sobre el mar). Fijos: toda la tierra, la
primera fila de mar junto a ella (ninguna línea de agua se mueve), Narva y la reserva/plataforma en seco; la reserva de puente **sumergida** sí se
suaviza (si no, su meseta quedaba justo en la confluencia). Topes: navegables (cls 3/4) a ≤ −0,251 m (calado ≥ 1,0 m), resto del mar a ≤ 0,45 m.
Elegido con `scripts/sweep_sea_bed_ev101.py` entre cinco combinaciones. Saltos >0,5 m en el interior del agua (sin contar la fila de orilla,
extremo menos profundo por encima de −4 m) 10.395 → 1.169 (−89 %); >1 m 3.385 → 534 (−84 %). Junto a la fila de orilla: >0,5 m 12.266 → 11.372,
>1 m 5.567 → 4.537. Tierra: 0 de 3.536.025 vértices cambiados. Contrapartida: el centro del Neva sube de −4/−5 a ~−2,5 m (agua algo más clara).
`ev101-depth-confluence.png`.

Arnés v3 (`ev101-harness-v3.json`): 0 en orilla, área, topología, inundación, islotes, `nav_dry`, `nav_band`, `nav_shallow` y pendientes. Saltan
tres, por diseño: `band` (239.110; v1 solo permitía cambios a ≤24 m de la orilla), `nav_channel_raised` (10.532; prohíbe subir el fondo de los
cauces) y `frozen` (702 vértices de reserva sumergida). Las tres existen para que el suavizado de **costa** no tocara el fondo; aquí el
objetivo es el fondo.

`@DayZ_Baltic_EV101_SeaBedV1`: terreno `2d21ccdc…`, WRP de stage `e8d4bcd3…`, mundo
`470ccecede9260da50e760924353718af8174b9d71b1b8f38b2ddbd1e6b1c2c7`, agua 3946db8b. Run 53f5c49f: el servidor da exactamente las alturas de EV101
en 2/2 vértices cambiados ((8580,10224) −1,689; (8676,10236) −1,837; EV100 −2,55). Vista de Guillermo pendiente.

## 10. 12-10: el sitio real de los dos colores, umbrales y conos (EV102)

**Corrección de §9.** Guillermo vio EV101 y la confluencia «sigue igual»; dejó al personaje en el sitio: **(10748,5; 10252,0)**, no la
confluencia del delta. A ras de suelo se ve además el agua a dos alturas (`ev101-lake-river-step-ground.jpg`). Medido: a la derecha, un lago de
**319 ha** (pieza a 1,42 m, fondo plano a 1,0 tras EV98, 0,42 m de calado; (10416–12222, 9936–12228)); a la izquierda, su río de salida, que EV96
convirtió en mar del motor (2.946 vértices desde (9534,9132); láminas originales 0,92–1,1 m). Encuentro: 0,75 frente a 1,42 m, dos sombreadores y
el borde recto de las piezas; es uno de los 63 contactos pieza/mar (323 celdas) listados en §9. La hipótesis de las mesetas del fondo no era la
causa de este sitio; EV101 se mantiene porque quita escalones reales del fondo, sin vista que lo confirme.

**Decisiones de Guillermo (12-10):** en los contactos lago/charca–mar, **umbral de tierra** (el lago conserva su nivel, regla del 11-10); en los
finales de carretera a pico sobre el agua (vio uno en (8696,10198), `ev101-road-end-cliff.jpg`), **terraplén en cono redondeado**.

**EV102** = EV101 + `tools/terrain/sills_and_cones_ev102.py` (solo sube terreno; piezas, carretera en seco y Narva intactas):
- Umbral: fuentes = vértices de pieza vecinos de mar (340 en 63 grupos); cresta = lámina + 0,30 + 0,60·(1 − (r/R)²) (más alta en el centro del
  contacto para que las orillas salgan en curva); flanco 1:8 hacia el mar con hombro redondeado, 1:3 bajo las piezas (solo entierra el borde).
- Cono: fuentes = carretera en seco a ≤2 celdas de un vértice >2 m sobre el agua vecina; envolvente 1:2 con hombro redondeado, ≤24 m.
- Guardas: un cuerpo de piezas no pierde más del 25 % de sus celdas ni un cuerpo de mar el 25 % de sus vértices (salvo bolsas de mar <200 vértices
  junto a un umbral) → 22 cuerpos se dejan como estaban, casi todos **arroyos que corren pegados a una carretera** (los longitudinales de 015);
  ningún triángulo tocado queda por encima de máx(35°, su pendiente anterior).
- Resultado (`ev102-sills-cones-report.json`): contactos pieza/mar 323 → 12 celdas; bordes de pieza expuestos 119 → 45 (0 nuevos); vértices de
  carretera >3,5 m sobre el agua vecina 558 → 206 (los que quedan son esos arroyos); 835 vértices de mar y 380 de charca pasan a tierra; 139
  navegables (cls 3) se secan en umbrales y conos.
- Arnés v3 (`ev102-harness-v3.json`): 0 en `pond_bed`, `piece_edge`, `new_sea`, `slope`, `flood`, islotes, `nav_band`, `steep_over35` y fusiones.
  Saltan por diseño `frozen` (930: reserva de puente sumergida bajo los conos), `band` y `nav_channel_raised` (EV101), áreas y topología (el
  umbral separa la pieza del mar y rellena bolsas de mar; `ev102-water-body-cuts.json`: 23 cortes, todos entre pieza y mar, ninguno de un cono que
  cierre un canal; el mayor es el de este lago), `nav_shallow` 190, `nav_dry` 165 y `steep_count` 58 (conos de 27° sobre fondo plano).

`@DayZ_Baltic_EV102_SillsConesV1`: terreno `5a750877…`, WRP de stage `218d9250…`, mundo
`4d572a76946481c1d19a82fe6ddf6e5cd180bfdb183a1640b61580ad5fa1ca52`, agua 3946db8b. Run 2dcf7b88: el servidor da exactamente la altura de EV102 en
(10746,10248), 2,122 m (EV101 −0,5). Vista de Guillermo en curso.

**EV103 (12-10).** Vista de EV102 en el lago: «hay una zona que aún tiene agua y no debería». Era un trozo suelto del lago de 3 celdas de pieza
(10752–10758, 10200–10218) con dos vértices a 1,1 m bajo su lámina de 1,42: la guarda de pérdida lo protegió porque el umbral lo enterraba más
del 25 %. Corrección en el mismo script (`POND_POCKET_MAX` = 20): los cuerpos de pieza de menos de 20 celdas que tocan una fuente del umbral se
entierran como las bolsas de mar; los otros 21 cuerpos protegidos no cambian. Cuerpos protegidos 22 → 21; bordes de pieza expuestos 45 → 43 (0
nuevos); el resto de cifras y puertas igual que EV102 salvo `nav_dry` 165 → 167 (`ev103-sills-cones-report.json`, `ev103-harness-v3.json`).
`@DayZ_Baltic_EV103_SillsConesV2`: terreno `a1f458ef…`, WRP de stage `a7d8a91b…`, mundo
`441dfda9a30ca11ce5b6ab6ea7f3723cf7aef99bf74dd49355fa606679001eba`, agua 3946db8b. Run d0ab6bfb: el servidor da 2,108 m en (10752,10212), igual
que EV103 y por encima de la lámina.
