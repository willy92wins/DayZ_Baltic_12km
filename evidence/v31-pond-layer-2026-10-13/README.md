# Capa de charcas v31 — piloto en San Petersburgo (13-10-2026, Claude)

Petición de Guillermo (13-10): «avanza lo máximo posible en lo demás»; él verá luego EV103 y decidirá los arroyos pegados a
carretera. La capa v31 sigue el plan del juez del 11-10 (pasos S0–S14, puertas G1–G14; texto completo en la transcripción de
esa sesión), adaptado a EV103. Ventana piloto alineada a teselas de 48 m: **x 7776–10224, z 8976–11040**. Fuera de ella, el
mundo y el agua de EV103 no cambian. Todo lo grande vive en `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/`.

## Herramientas (`tools/water/`)

| Paso | Archivo | Qué hace |
|---|---|---|
| S2+S4 | `pond_footprint_v31.py` | Envolvente (cobertura base + 2 anillos geodésicos con esquinas ≥ P + 0,30, sin reserva/plataforma/Narva), huella = celdas visibles + cierre de hasta 2 anillos, campo F = `make_field` copiado de Astra (`derive_connected_visual_field.py:12-44`) |
| S5 | `pond_author_v31.py` | Una pieza MLOD por (tesela 48 m, banda 25 mm), 2 triángulos nativos por celda, LODs de `water_mesh.py:38-63`, visual a F − L, roadway plano, nombre `p31_<sha16>` |
| S6 | `pack_water_v30.ps1` (de Astra, sin cambios) | AddonBuilder |
| S7+S8 | `stage_pond_pilot_v31.py` | Funde el PBO de agua actual (3946db8b) con los p31; en el WRP quita los registros de agua cuyo centroide de roadway compilado cae en la ventana y añade los nuevos en origen + centro del ODOL |
| S11 | `verify_pond_pilot_v31.py` | Cobertura compilada contra la huella (2 puntos por celda), solapes, nivel físico = banda, visual = F |
| S12 | `missions/BalticPondLayerProbeV1.BalticTrial` | Sondeo de servidor: `SurfaceIsPond`, `GetWaterSurfaceHeightNoFakeWave`, `GetWaterDepth` |
| — | `render_ab_v31.py` | Orillas A/B (modelo TRI) para revisar en planta |

## P0 = EV104 (`@DayZ_Baltic_EV104_PondLayerPilotV1`)

Terreno EV103 sin tocar + piezas nuevas en la ventana (`p0-*`):
- Huella del mapa (`p0-footprint-report.json`): envolvente +125.771 celdas; huella 376.402 (989 celdas base secas se caen, 21 nuevas);
  44 vértices de borde expuestos (<5 cm; 14 en Narva, el resto en la cascada del borde sur y contactos con mar; **1 en la ventana**,
  (9168,10476)); 12 contactos nuevos del campo F en divisorias secas, **todos fuera de la ventana** (cascada sur). En la ventana: 224
  piezas (222 modelos, 123 con rampa) por 272 viejas de Astra (53 edge, 124 flatfix, 51 globalvis, 41 patch, 2 seamfix, 1 nativeseam;
  el juez había previsto 272).
- Compilado (`p0-verify-compiled.json`): cobertura nueva = huella exacta, 0 dobles, 0 solapes con piezas viejas, nivel físico = banda
  (error 2e-7 m), visual = F (6e-7 m). WRP: registros que no son de agua idénticos byte a byte y en orden. Los 204 huecos de muestra
  del marco ya existían en EV103 (ninguna pieza retirada cubría celdas de fuera; `scripts/frame_holes.py`).
- Servidor sin cliente, EV103 frente a EV104, 190 puntos (`probe-compare.json`): 60/60 dentro del agua con charca, profundidad > 0
  y nivel exacto (1e-7) en los dos; 40 de orilla enterrada y 90 a 6/9/12 m fuera, 0 con charca en los dos. Única diferencia: un punto
  de fuera tenía una pieza vieja enterrada (lámina 1,95) que la huella nueva ya no tiene.
- Mundo `66e7e6a52a24f06c90b3199237bab2dba8785fb8f530966e26541109ab451818`, agua `c1e7090a…`.

## P1 = EV105 (`@DayZ_Baltic_EV105_PondLayerPilotP1V1`)

Terreno: el constructor de orillas de charca de la ronda 3 (`round3/pond-edge`, el que dio EV100) con base EV103, la **envolvente como
cobertura** y todo congelado fuera de la ventana y en Narva; mismos parámetros que EV100. Cambios frente al original: solo rutas y lo de
`p1-builder/*.diff`; `pe_build/pe_run/pe_curve/pe_topo_local` idénticos salvo rutas. Evaluación con la semántica del arnés v3 y esa base
y cobertura (`p1-builder/eval_p1_v31.py`; autoprueba EV103 contra sí mismo 24/24 en 0, `eval-self-ev103.json`).
- P1a tocó 1.126+2 vértices; un vértice de borde nuevo expuesto en (9126,10362) (contacto charca/mar) → P1b devuelve a EV103 un radio de
  12 m ahí. **P1b: 24/24 puertas en 0** (`p1b-eval.json`), sin bordes expuestos nuevos frente a P0.
- Ventana SPB, orilla de charca (triángulos del motor): dientes de sierra 6,62 → 5,35 /km; esquinas 11,0 → 11,2 /km; longitud 4,08 →
  3,92 km. Costa de mar sin cambios (3,66).
- **Límite medido:** los arroyos estrechos del NE ((9185,9280), (8235,9125); `p1a-narrow-streams-ab.png`) siguen en escalera. Un cauce de
  un vértice de ancho que corre en diagonal NE-SO es una unión de rombos de vértice sobre la diagonal nativa NO-SE: la envolvente no lo
  arregla (el plan del juez ya lo daba como límite de la rejilla, punto (g)). Hace falta ≥2 vértices (~12 m) de ancho, contra la decisión
  del 02-10 (arroyos de 3–6 m): decisión de Guillermo.
- Compilado igual que P0 (`p1b-verify-compiled.json`). Mundo `4f1766a4b9c3b83e2c49abacdff81b4fc76157da5afdb7aadc30806f7f03a86f`, agua
  `a989d148…`. Sin sondeo de servidor propio (misma cadena que P0).

## EV106 = mapa entero + lagunas (`@DayZ_Baltic_EV106_PondLayerMapV1`)

Construido antes de la vista del piloto, a petición de «avanzar lo máximo posible», como candidato aparte (EV103 sigue intacto).
1. **Suavizado de orillas de charca con la envolvente en todo el mapa** (`p1map-builder`: el piloto con la ventana = mapa entero):
   77.445 vértices; 24/24 puertas (`eval-map1-summary.json`). Mapa, orilla de charca: dientes 6,87 → 6,28 /km, esquinas 7,45 → 7,27.
2. **Lagunas de 020** (`tools/water/lagoons_v31.py`, `ev106-lagoons-report.json`): 48 finales en tierra del estudio del 11-10; **28
   construidas** (radio 12 m arroyo / 15 m río, fondo ≥1,0 m, línea de agua en el círculo, reborde que no sube junto a agua existente,
   embudo 1:2 hacia fuera que no corta bordes de pieza, guarda de 35°) y **20 descartadas**: 14 «colgadas» (el valle sigue por debajo de
   la lámina a ≤R+24 m: harían falta diques, lo que Guillermo rechazó en 017) y 9 con agua a otro nivel cerca (alguna cumple ambas).
   Las lagunas entran como sellos en la envolvente (`envelope-lag.npy`). Render: `ev106-lagoons-ab.png`.
3. **Bordes de pieza expuestos nuevos** (`tools/water/bury_edges_v31.py`): 6, todos del suavizado junto a cruces de carretera; se
   entierran subiendo esos 6 vértices → 43 expuestos (EV103: 44), 0 nuevos.
4. Puertas con la envolvente + sellos (`eval-ev106-lag-summary.json`): 0 salvo, por diseño de las lagunas, `area_large` 11 (cauces que
   ganan su laguna), `flood` 1.072 (agua nueva del disco) y `topo_tri_merge` 2 (laguna que se une a agua del mismo nivel a 9 y 50 m).
5. Piezas: 13.779 instancias, 8.368 modelos (4.578 con rampa), 381.046 celdas; PBO de agua **23,9 MB** (antes 49,4 MB). Las 15.089
   piezas viejas (edge, full, globalvis, flatfix, patch, seamfix, halo, globalseam, nativeseam) se retiran todas.
6. Verificación exacta (`verify_pond_exact_v31.py`, `ev106-verify-exact.json`): 762.092 medias celdas cubiertas una sola vez en física y
   visual, 0 triángulos fuera de la malla, nivel < 1e-6 m. Controles negativos sobre el piloto: mover una pieza 1 cm (28 triángulos fuera)
   y quitar una (6 medias celdas sin cubrir) fallan como deben.
7. Servidor sin cliente, EV103 frente a EV106, 278 puntos de todo el mapa (`probe-map-compare.json`): 100/100 dentro del agua con charca,
   profundidad > 0 y nivel exacto en los dos; 60 enterrados y 90 a 6/9/12 m, 0 con charca; **centros de laguna: 13/28 en EV103 → 28/28 en
   EV106** con el nivel del cauce. 0 fallos.
8. Mundo `3b3695630ec9362c906ac1c9fadf93ddaf9817cb64deccbe60ea795d8780fe08`, agua `ec47c2946cfab03fb2a0ccc20c68afb9bc72b3c73de6b81f217ac82bcfc6072e`.

## EV107 = EV106 + primer puente vanilla (piloto de 015, `@DayZ_Baltic_EV107_BridgePilotV1`)

`tools/terrain/bridges_v31.py` coloca un puente vanilla en un cruce de «centro seco»: eje del modelo a lo largo del rumbo de la carretera,
inclinado para que los dos extremos del roadway (leídos del ODOL) caigan sobre la calzada (convención comprobada con los 9 vanos de Narva:
mundo = posición + R·vértice ODOL, matriz = ejes locales X, Y, Z en columnas + posición); abre el cauce bajo el tramo plano del tablero
(talud 1:2; puede rebajar reserva/plataforma solo bajo el tablero); si el agua del cauce es **mar del motor** el fondo baja a 0,0 m y no se
sella nada (el mar lo llena); si es charca, sella el cauce en la envolvente al nivel del arroyo. `stage_bridges_v31.py` añade los registros.
- Piloto: cruce #15 (Okhta, (9091,10305)), `bridge_wood_25`, inclinación 0,60°, extremos de calzada 2,488 / 2,836 m. La tabla de cruces
  del 11-10 (sobre EV97) decía charca a 1,083 m: en EV106 ese tramo es mar (EV96). Primer intento con sellos → piezas de charca sobre el mar
  (lo que EV96/98 eliminó); corregido con el modo mar. Huella de charca idéntica a EV106 → mismas piezas y PBO de agua.
- Servidor (`missions/BalticBridgeProbeV1.BalticTrial`, `bridges/probe-ev107.json`): superficie de rodadura continua por el eje
  (calzada 2,49 → rampa → tablero 4,80–4,96 → calzada 2,85; paso máximo 0,31 m por metro = la rampa vanilla de ~17°); cauce bajo el tablero
  con mar en 21/21 puntos y 0,4–0,8 m de agua; gálibo ~4,1 m.
- Mundo `033702db18ab7d9b97dfad2d6384961987b262e67ba3305cb35f528485184274`, agua = EV106.
- **Inventario rehecho sobre EV106** (`tools/terrain/crossings_resurvey_v31.py`, `bridges/crossings-ev106.csv`): primer agua a lo largo
  del cauce a 4–36 m de la carretera (los conos de EV102 rellenaron los primeros metros). De 31 cruces transversales: **13 listos** (9
  `bridge_wood_25`, 4 `bridge_metal_25` ×2, contando el piloto #15); **2 por decidir**: #5 (calzada 1,88 m sobre el agua: el metálico no
  cabe por debajo) y #45 (cauce navegable con la calzada a 0,77 m sobre el mar: ninguna lancha pasa); **16 en espera**: 10 con agua distinta
  a cada lado, 3 con dos niveles de charca, 3 sin agua a ≤36 m.
- Antes del despliegue: que Guillermo vea el aspecto del piloto (puente de madera con joroba y rampas de ~17°; los metálicos son planos).

## EV108 = EV107 + piloto del kit `streambed` (`@DayZ_Baltic_EV108_StreambedKitPilotV7`)

Arroyos finos con las piezas vanilla de Chernarus (lecho 3D, piedras y agua propia) en dos cauces: kit-118 (8235,9125) y kit-7, de
(8350,12100) a (9140,11270). Detalle, medidas vanilla, iteraciones y sondeo en `streams/README.md`; ficheros en `kit/`. Revisión de los
mapas vanilla del subagente: `vanilla-tricks-REPORT.md`. Mundo `389e27a6…`, agua `a48f2fc1…`.

## EV109 = EV108 V7 + 10 puentes vanilla más de la 015 (`@DayZ_Baltic_EV109_BridgeRolloutV1`)

Despliegue de los cruces «listos» del inventario de 15 cruces rehecho sobre EV106 (`bridges/crossings-ev106.csv`), con
`tools/terrain/bridges_v31.py` v3. Ficheros en `bridges/ev109/`.
- **Sitios** (`bridges/ev109/sites-rollout.json`): metálicos dobles 015-8, 015-11 y 015-13; de madera de 25 m 015-18, 015-19, 015-25 y
  015-37; de madera de 50 m 015-16, 015-40 y 015-42. La reserva de carretera dentro del cauce llega a 13,9-16 m a lo largo de la
  calzada y no cabe bajo el tramo plano del de 25 m (10,1 m), pero sí bajo el de 50 m (19,3 m). **Fuera, para Guillermo**: 015-4
  (Plyussa: reserva hasta 35 m a lo largo del puente, más allá de dos metálicos), 015-34 (carretera pegada al agua 59 m: arroyo
  longitudinal) y 015-5 (gálibo, ya pendiente). El piloto 015-15 sigue de EV107.
- **Cambios en la herramienta** (cabecera de `bridges_v31.py`): dos tramos metálicos alineados sobre una sola rasante (`spans`); cauce
  abierto por toda la franja de reserva bajo el largo del tablero; corte, a cada lado, hasta la reserva + 6 m o el primer agua + 4 m
  (25-60 m); enlace recto con el cauce real cuando el rumbo del inventario no lo toca (7 sitios); taludes tendidos en pasos de 0,1 m
  fuera del fondo y de la carretera; capa `v31_bridge_cut` acumulada; informe con la cota real de rodadura y el cauce dentro de la
  huella del tablero.
- **Revisión independiente** (`bridges/ev109/review-bridges-v31.json`, una ronda): 8 hallazgos confirmados de 12 sobre la versión del
  piloto (dos tramos imposibles de expresar, corte fijo de 25 m que dejaba umbrales secos en 5-9 sitios, métricas del informe, capa del
  piloto perdida) y 4 rechazados; todos los confirmados están cubiertos por los cambios de arriba.
- **Offline**: las 10 láminas bajo el tablero unen las dos orillas (`bridges/ev109/continuity.json`; en EV108 ninguna); 0 bordes de
  pieza expuestos nuevos (43 = EV108); verificación exacta del agua, 13.511 piezas, pasa. 86 caras de más de 35 grados quedan donde la
  explanada fija se encuentra con el cauce (67 bajo los puentes, 19 en arcenes de la misma reserva): son los estribos.
- **Servidor** (`missions/BalticBridgeProbeV2.BalticTrial`, carga los objetos antes de consultar; 1.859 puntos;
  `bridges/ev109/probe-ev109-summary.json`): calzada continua en los 10 (escalón máximo 0,31 m/m en madera, la rampa vanilla de ~17
  grados; <= 0,08 en metal); agua bajo el tablero a la cota del arroyo y sin mar (9 de 10 con todos los puntos mojados; 015-18 6/9: los
  otros tres caen sobre la orilla de un cauce de 4,3 m); charcas 100/100, lagunas 28/28, kit 349/417 como EV108.
- Mundo `7ad4d6cf87ca231354b6e2d6f2c3ab2765c60e3a1f3bcf0273623c337b6b7b12`, agua `b003e7f6e5fc37d3eb9a604ec5337c6bcdd05e1bb900597d3172e27fd73ad4b5`.
- **No verificado**: el aspecto en el cliente (puentes de 50 m y metálicos dobles, estribos), la navegación de IA y vehículos sobre
  los puentes, y que los cruces sin puente sigan como estaban.

## EV109R = EV109 + claves de render de Chernarus (`@DayZ_Baltic_EV109R_RenderKeysV1`, para comparar con EV109)

Recomendación 7 de la revisión vanilla: Chernarus (`world/config.cpp:304-306`) y Livonia (`:372-374`) declaran
`terrainNormalTexture`, `heightBlendingMode=1` y `bicubicMode=1`; el mundo Baltic, ninguna (`render-keys/config.diff`).
- **Mapa de normales global**: `tools/terrain/global_normal_map.py` (convención medida decodificando `global_nohq.paa` de Chernarus
  contra su relieve: R = este, G = norte, B = 0,385 (1 - arriba), A = 1, fila 0 al sur; cabecera del script) sobre el relieve de EV109,
  2048 x 2048 (un píxel por vértice) -> `ImageToPAA` -> `data/baltic_global_nohq.paa` (2,56 MB). Ida y vuelta por PAA: correlación
  0,998 / 0,993 con las normales, error máximo de compresión 0,12.
- Mismo WRP fuente y misma agua que EV109; cambian el WRP binarizado (3 bytes), `config.bin` y el PAA nuevo. El servidor carga el
  mundo sin errores nuevos (los avisos del RPT son los habituales del banco).
- **No verificado**: el efecto en el render del cliente; puede no notarse. Para compararlo, abrir EV109 y EV109R en el mismo sitio con
  la misma hora.

## EV110 = EV109 + kit en malla + orillas rectas + puentes v5 + suelo bajo puentes (`@DayZ_Baltic_EV110_LatticeShoresV1`)

Vista de Guillermo del 15-10 en EV109 y lo que corrige:
- **kit-118**: «poligonal», «muy falsa, poco uniforme el ancho», «3 hexágonos casi solapados en las puntas».
  - Medido (`ev110/reviews/kit_outline.py`): el agua del kit medía 3,2/5,8/7,9 m (p10/50/90), con el 69 % de la orilla fuera de las piedras. Chernarus da 2,5/3,6/4,9 m y un 17 %.
  - Chernarus pone 1.653 de sus 1.682 piezas en las tres direcciones con arista de la malla (N-S, E-O y NO-SE), centradas en una fila de vértices.
  - `tools/water/streambed_kit_v31.py` v8 tiende el kit así: rectas, curvas de 45°, codos con `slanted` y una V lineal por anillos de vértices.
  - Resultado: kit-118 3,01/3,53/4,12 m (fuera de banda 6,2 %) y kit-7 3,13/3,49/3,74 m (4,3 %). Una sola lámina continua.
- **015-8**: «una de las esquinas clipea». `bridges_v31.py` v4 y v5 suben cada extremo lo justo (2–6,5 cm). La franja del tablero queda ≥ 1,4 cm sobre el terreno.
- **Islote de la bahía norte** (6900, 10500): «zigzags» en las orillas de las calzadas.
  - `tools/water/shore_ramp_v31.py` (nueva) tiende una rampa uniforme a cada lado de una orilla suavizada (σ 12 m), en modo estricto. Guillermo autorizó mover el margen del terraplén (reserve sin platform), nunca la calzada.
  - 154 de 329 tramos tratados (27,1 km), 17.870 vértices, 1.233 de reserva sin plataforma. Islote: 6 de 7 tramos; el 313 se rechaza (0,102 > 0,080).
- **015-13**: «hendidura poligonal … asomar la esquina del puente». v5 añade un encaje de extremos resuelto como programa lineal sobre las caras ODOL reales: la cara interior del estribo pasa de 1,17 m a 0,01 m descubierta.
- **015-16**: «soportes del puente en el aire. Apilar un puente debajo … borrar el tramo extra de los caminos».
  - Los 7 de madera tenían entre 4 y 12 patas en el aire, hasta 4,8 m. v5 apila una copia 5,04 m más abajo en 015-16, 18, 19, 37 y 40: 0 patas en el aire. En 015-42 cambia a `bridge_wood_50_1` (0 patas en el aire). 015-25 queda sin cambio.
  - La pintura de camino viene de las capas de EV95. `build_surface_v30.py --road-off-lowered`, `patch_surface_v31.py` y `package_surface_patch_v31.py` repintan 147 celdas en 20 teselas donde el terreno bajó > 0,5 m.
- Cadena y hashes: `ev110/BUILD-EV110.md` y `ev110/deploy.json`.
  - Mundo `narva_trial.pbo` 226932e3d9346e322b86f5e04958492fe1f417b958e44a3038d7516f051fbb8d; agua 46e63c70e60a2775781bb5c7b75fa000c2c2897f0712954c06b14b2149c358db.
  - Terreno `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev110/terrain-ev110.npz` d25e9428…; WRP 79274097….
  - Frente a EV95 cambian 41 entradas: el WRP y 40 PAA de capas.
- **Sonda de servidor** (`missions/BalticBridgeProbeV2.BalticTrial`, 2.881 puntos, `ev110/probe/`):
  - Puentes: calzada continua (≤ 0,327 m/m) y agua bajo el tablero al nivel exacto, sin mar. Iguales que en EV109, salvo 015-8: 0,136 frente a 0,076 m/m, por la subida. 015-18 sigue con 6/9 bajo el tablero, como en EV109 (el cauce va por el enlace lateral).
  - Orillas: 50/50 puntos mojados y 50/50 secos; islote 10/10.
  - Kit: eje 492/492 con agua y 689/689 controles secos.
  - **Labios y juntas de hormigón: 0/390 con agua del motor.** La lámina visible es continua; el agua jugable se corta 3–4 m en cada junta. Geometría vanilla; sin comprobar si Chernarus hace lo mismo.
- **Revisiones**: diseño, implementación (dos rondas de Codex por herramienta, tope fijado antes) y verificación del build (Codex: «ship_with_fixes»; el único punto, `split_log.py`, está corregido con controles negativos). Todo en `ev110/reviews/`.
  - Debilidades abiertas: `shore_ramp_v31.validate` compara recuentos de cadenas cerradas; el gate G2 ya compara identidad espacial. Bridges G7 tiene escapes con informes manipulados.
- **Abierto, decide Guillermo**:
  - aire bajo las rampas de madera (0,86–2,31 m; G2 de v5 en FAIL; alternativa medida offline: «tablero enrasado», ~2,2 m más bajo);
  - 015-25 (el apilado dejaría el tablero inferior a 1 m del agua);
  - excepción de corredor de v4 (29 vértices congelados fuera de las huellas; G5 en FAIL; quitarla deja presas);
  - 23,4 km de cauces finos en zigzag (diseño en `ev110/reviews/design-shores-thin-kit.json`, pista thin_streams), a decidir tras ver el kit en malla;
  - agua del motor en las juntas del kit.

## Pendiente

- **EV112: seguir `plans/ev112-plan-astra.md`** (relevo a Astra, 18-10). La vista de Guillermo de EV111 V2 (17-10), con el diagnóstico de
  cada comentario, está en `ev110/review-ingame-2026-10-17.md`. Las pistas nuevas tienen su evidencia en `dam/`, `despike/`, `ev112/` y
  `bridges/ev112/`.
- Lo que solo decide Guillermo (no bloquea): rampas de madera («tablero enrasado»), 015-25, FPS del kit y del bosque, y el agua del motor
  en las juntas del kit.
- Después de EV112: Terrain Builder, navmesh, IA y lancha.
