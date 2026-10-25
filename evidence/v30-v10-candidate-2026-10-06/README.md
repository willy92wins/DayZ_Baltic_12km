# Candidatos v10 y v10b: lagos, estanques y ríos suavizados — 06-10-2026

Plan `plans/v30-cadena-desde-diseno.md`, a continuación de la v9 (`../v30-v9-candidate-2026-10-06`). Productos de la v10
en `E:/DayZ-Baltic-Build/v30-v10`; desplegada como `@DayZ_Baltic_V10Candidate` (mundo 7ccce78b, agua c00e5687; copias
comprobadas por hash, `reports/deploy-receipt.json`), misión `BalticTideProbeV2.BalticTrial`, vista en el run c06ea85c.
La v10b (abajo) es la v10 con un solo cambio en la pasada de orillas. **Ninguna está aceptada**: falta Guillermo.

## Decisiones aplicadas (Guillermo, 06-10)

- Lista de niveles: connected_136 a 1,35 m (regla) y review_181 añadida a 1,44 m.
- Borde: lake_047 y lake_107 se conservan enteros; los otros 6 cuerpos que entran en la franja sin tocar el borde, fuera.
- Contornos de lagos, estanques y cuerpos de río suavizados «suave»: σ 12 m, cada punto ≤ 4 m, área conservada.
- Orilla de agua muy baja: el vértice de tierra que fuerza puede bajar de 1,40 m hasta su nivel + 0,05 m (mínimo
  1,0 m), con la comprobación de parpadeo en RIVER_8.
- Límites de bosque y prado suavizados en la textura del suelo.
- Canal de Sivers recto; solo se redondean sus cruces.

## Qué cambia frente a la v9

| commit | herramienta | qué hace |
|---|---|---|
| bc9bd8f | `build_v30_water.py --contour --border-keep-m 45` | lee los lagos de contorno de una ruta (los suavizados) y deja entero un lago o estanque cuyo polígono queda a ≥ 45 m del borde |
| 54ef854 | `build_surface_v30.py --landcover smooth --landcover-sigma 1` | la cubierta (bosque, hierba, hierba alta, grava) sale de los campos de clase desenfocados y de su máximo bilineal, no del vértice más cercano |
| e0cd2fb | `tools/water/smooth_water_outlines_v30.py` | suaviza los anillos de lagos, estanques y cuerpos de río del diseño (σ 12 m, ≤ 4 m, área conservada; contactos con otras aguas y Narva fijos) |
| b1b8b70 | `tools/water/audit_waterline_v30.py` | métrica independiente: desfase y giro de la línea de agua visible a lo largo de las normales del diseño |
| e763fee | `profile_inland_v30.py --outline-sd --low-water-bank`, `verify_terrain_v30.py --low-water-bank-min` | la pasada de orillas sigue un contorno vectorial en lagos, estanques y ríos (los arroyos conservan el ráster) y deja que el agua muy baja llegue a su orilla |
| 6c3bf78 | `derive_signed_levels_v30.py` | una masa con nivel firmado lo conserva aunque la clasificación ya no la baje |
| 9f2264a | `profile_inland_v30.py` | la orilla relajada sube al nivel más alto del agua adyacente, el mismo que mira la puerta |

## Cadena (`scripts/`)

`chain_v10.sh` paró dos veces y se reanudó con el arreglo:

1. Lista de niveles: 5 masas firmadas salían `not_lowered` (con el contorno suavizado, la clasificación ya no las
   bajaba). 6c3bf78 y `chain_v10_from21.sh`.
2. Puerta de orillas de agua muy baja: 16 fallos, porque la pasada relajaba al nivel más cercano y la puerta mide el más
   alto adyacente. 9f2264a y `chain_v10_from_inland.sh`.

## Lanes delegadas (GX10, GLM-5.3-Flash) y revisión

Todas entregaron con `stop` y RC 0 (`glm-lanes/`); la revisión de otra familia (Claude) encontró y corrigió:

| lane | tarea | s | corregido en la revisión |
|---|---|---|---|
| S1 | cubierta suavizada | 170 | una línea de cierre de bloque suelta y los campos de clase en bruto |
| M1 | métrica de la línea de agua | 548 | origen de filas en 12.288 m en vez de (N−1)·6; argumentos obligatorios que rompían `--selftest` |
| W1 | suavizado de contornos | 1.070 | la unión de todos los demás cuerpos por cada elemento, la rampa de contacto cuadrática y las bandas de río tomadas como contacto |
| P3 | contorno vectorial y orilla de agua baja | 1.324 | el recuento de la puerta, limitado al suelo de tierra |
| D4 | contorno por ruta y regla del borde | — | la paré yo: lancé 4 lanes con una ya ocupada y el GX10 admite 4 en total; la hice aquí |

## Resultados offline de la v10

- **Línea de agua visible** (`reports/waterline-metric-v9.json` y `-v10.json`; criterio fijado antes: cada clase mejora
  frente a la v9, arroyos no peor de +0,5 puntos, p90 del desfase no peor). **Pasa.**

| clase | giros > 45°, v9 → v10 | desfase p50/p90, v9 → v10 | sin agua visible, v9 → v10 |
|---|---|---|---|
| lagos | 21,4 → 15,8 % | 1,38/3,62 → 0,88/2,88 m | 12,9 → 8,6 % |
| estanques | 32,7 → 30,1 % | 2,12/4,62 → 1,62/4,12 m | 13,0 → 6,1 % |
| ríos | 16,7 → 8,0 % | 1,62/4,12 → 0,62/2,12 m | 3,9 → 2,7 % |
| arroyos | 10,5 → 10,5 % | 1,12/2,62 → igual | 1,3 → 1,3 % |

- **Diseño** (`reports/design-smoothing-report.json`): giros > 45° por elemento, lagos 18,3 → 7,6 %, estanques
  25,9 → 18,5 %, ríos 9,0 → 6,9 % (incluidas las esquinas de los cruces); ningún anillo volvió atrás.
- **Puertas** (`reports/verify-v10.json`, `roads-v10.json`, `channel-reaches.json`): calado 1 fallo (un arroyo, como la
  v9); orillas 0; fondos 0; suelo de tierra 0 (727 orillas relajadas de 6.321 elegibles, todas sobre su suelo); taludes
  0; carreteras PASS; tramos 0; Narva distinto por diseño (3,25 m). **Piezas: 21 (v9: 20).** Las 15 esquinas de agua
  son los mismos 13 vértices de un arroyo empinado (x 7236–7386, z 5658–5850). Las de tierra siguen en el mismo tramo de
  cauce (x 8220–8280, z 8982–9222) pero en otros vértices: 5 esquinas en la v9 y 6 en la v10, con déficits de 0,5 a
  6,7 cm (v9: hasta 8,6 cm) (`scripts/piece_fails.py`). Es un fallo más en una zona que ya fallaba, no «sin fallos
  nuevos», como se dijo antes de esta comprobación.
- **Aristas de orilla fijadas** (`scripts/pinned_edges.py`): 1,1 → 0,6 % en el mapa; 33 → 13,7 % en la ventana RIVER_80.
- **Lista de niveles** (`levels/report.json`): 84 iguales a la v9; 5 cambian por la regla, porque el anillo medido se
  movió con el contorno suavizado (231 de 1,68 a 1,76 m; 417 de 2,51 a 2,58; 432 de 1,76 a 1,93; 468 de 3,13 a 3,20; 514
  de 2,19 a 2,33); la 216 desaparece (era un fragmento); el lake_047, ahora dentro, es la masa 165 a 1,37 m (la v3b le
  daba 1,36).
- **Borde** (`reports/04-water.log`): 3 lagos recortados (288, 106, 202), lake_047 entero, 7 lagos y 9 estanques
  quitados (v9: 9 y 9); el lake_107 ya no entra en la franja después del suavizado; 3 ríos y 7 arroyos acaban antes
  del borde.

## En motor (run c06ea85c; 3 min de carga por pose; `views/`)

| pose | frente a la v9 |
|---|---|
| RIVER_80 | la red de cauces de la derecha pasa de tramos rectos y giros en ángulo a curvas; el río principal tiene menos dientes. Siguen en escalera el lago alargado de la izquierda (≈ 12018, 1805) y el estanque junto al río (12093, 1690). El marco oscuro rectangular de la derecha, igual en la v9, es el corte recto del río a 60 m del borde (≈ 12225, 1561): situado proyectando la cámara, con la focal (≈ 700 px) calibrada con el estanque (`views/review/river80-*-crop.jpg`) |
| RIVER_8 | sin parpadeo en la orilla cercana: entre dos capturas a 6 s cambian la vegetación y una línea del horizonte lejano, no la orilla (`views/review/river8-frame-difference.jpg`). Delta máximo entre cuadros 0,00079 con 4 cuadros (v9: 0,00055) |
| PONDS_120 (nueva) | estanques redondeados; ver BALTIC-019 abajo |
| LAKE10_150 (nueva) | el lago 10 con la orilla suavizada; a la derecha, teselas sin cargar |
| NAVFREE_85, NAV_330 | manchas de hierba con el borde redondeado (cubierta suavizada); el canal navegable del Luga, igual, con los dientes de su orilla (corredor protegido) |
| L202_330, BORDER_E330 | teselas oscuras de bordes rectos donde la v9 tenía textura |
| L288_330, L288_60, L106_330 | prácticamente iguales |

**Teselas oscuras (BALTIC-019).** En PONDS_120, las capturas de las 15:20, 15:22 y 15:24 tienen teselas planas y
oscuras; la de las 15:51 sale texturizada (0,7 % → 0 % de píxeles bajo 60; `views/review/ponds120-four-captures.jpg`).
No es la superficie: la de la v10 pesa algo menos que la de la v9 (satélite −1 % y máscaras −3 % de mediana por tesela),
con 4 superficies como máximo por tesela (`views/review/surface-tiles-v9-v10.json`), y los RPT del cliente de los dos
runs no tienen errores de texturas ni materiales del mapa. L202_330, BORDER_E330 y LAKE10_150 no se repitieron.

## Por qué la v10 aún deja lagos y estanques en escalera

En planta (`figures/visible-water-v9-v10.png`), el estanque del RIVER_80 es un bloque en escalera más pequeño que su
contorno, y el lago en media luna de al lado también. Sondeado el terreno (`scripts/probe_bodies_v10.py`):

- La pasada de orillas nunca cambia clases: la línea de agua solo puede cruzar las aristas entre un vértice de agua y uno
  de tierra, y lo que se ajusta es dónde, dentro de cada arista. Toma el contorno externo solo donde su signo coincide
  con la clase (`tools/terrain/profile_inland_v30.py:196-204`).
- La v10 le daba el `sd_shape` del paso 22 (`tools/terrain/smooth_shore_outline_v30.py`), que vuelve a suavizar la línea
  (σ 12 m, ≤ 4 m) sin conservar el área: un estanque pequeño encoge hasta 4 m. Además pone el signo por la clase de la
  malla de 6 m (`smooth_shore_outline_v30.py:181`, `np.where(wet_out[sup], -dist, dist)`). En el paso 22 de la v10 la
  línea se movió 1,27 m de mediana; al menos el 5 % de los puntos topó con el máximo de 4 m, y 9.034 vértices cambiaron de
  signo respecto a la entrada.
- Así, el cruce se pega al vértice de agua y la orilla calca la escalera. La propia métrica lo muestra: la pasada no
  mejora lo que recibe (lagos 15,5 → 15,8 %, estanques 29,5 → 30,1 % de giros > 45°), mientras que en los arroyos, que
  usan el contorno ráster con su propio signo, baja de 18,8 a 10,5 %.
- El `sd` del paso 20 sí es el del diseño: distancia a los anillos suavizados del diseño con el signo por «punto dentro
  del polígono» (`tools/terrain/build_v30_water.py:195-202`; los pasos 18 y 20 solo lo cambian en Narva y en la cabecera
  del Luga).

## Candidato v10b

La v10 con un único cambio: la pasada de orillas lee `--outline-sd` del paso 20
(`E:/DayZ-Baltic-Build/v30-v10/20/sd_polish.npz`) en vez del 22. Los pasos previos son los de la v10, sin tocar; productos en
`E:/DayZ-Baltic-Build/v30-v10b` (`scripts/chain_v10b.sh`). Antes se probó como experimento
(`E:/DayZ-Baltic-Build/v30-v10-exp-sd20`, `scripts/exp_sd20.sh`); la cadena da el mismo terreno, aa1c093c, byte a byte.
Es la segunda y última ronda de arreglo fijada antes de empezar.

- **Línea de agua visible** (`v10b/waterline-metric-v10b.json`), frente a la v10:

| clase | giros > 45° v10 → v10b (diseño) | desfase p50/p90 v10 → v10b | sin agua visible v10 → v10b |
|---|---|---|---|
| lagos | 15,8 → 11,3 % (11,4 %) | 0,88/2,88 → 0,12/1,38 m | 8,6 → 7,8 % |
| estanques | 30,1 → 18,3 % (19,0 %) | 1,62/4,12 → 0,38/1,88 m | 6,1 → 4,7 % |
| ríos | 8,0 → 5,6 % (4,6 %) | 0,62/2,12 → 0,12/1,38 m | 2,7 → 2,5 % |
| arroyos | sin cambio (usan el contorno ráster) | igual | igual |

  En lagos y estanques los giros de la orilla visible quedan al nivel de los del propio diseño. En planta
  (`figures/visible-water-v10-vs-v10b.png`), el estanque y el lago en media luna del RIVER_80 llenan su contorno, y los
  estanques de PONDS_120 salen redondeados.
- **Puertas**: idénticas a la v10 (calado 1, orillas 0, fondos 0, suelo de tierra 0 con 1.026 orillas relajadas, taludes
  0, piezas 21 en los mismos vértices, carreteras PASS, tramos iguales, Narva por diseño).
- **Empaquetado:** el agua es la de la v10 (`-Pieces`: la pasada no cambia clases ni niveles, así que los planos y las
  piezas son los mismos; PBO de agua c00e5687). El primer intento usó `-WaterSource` y se paró antes de escribir nada:
  el script crea las uniones DZ/bin/core dentro de la carpeta de agua y la v10 ya las había dejado allí; `New-Item` se
  negó sin borrar nada (`P:\DZ` sin carpetas modificadas hoy). Reanudación en `scripts/chain_v10b_package.sh`.
- **Paquete y despliegue:** mundo f20dea67 + agua c00e5687, desplegado como `@DayZ_Baltic_V10bCandidate` (copias
  comprobadas por hash, `v10b/deploy-receipt-v10b.json`), misión `BalticTideProbeV2.BalticTrial`.
- El censo de esquinas vivas por km (`v10b/shore_failure_census_v10b.json`) sale igual que en la v10: mide la planta de
  la malla de clases (el cero del `sd` ráster suavizado), que la v10b no cambia. Lo visible lo mide la métrica de la
  línea de agua.
- Aristas de orilla fijadas por el suelo de tierra (`scripts/pinned_edges.py`): 0,7 % en el mapa y 14,6 % en la
  ventana RIVER_80 (v10: 0,6 % y 13,7 %); en la ventana, 31 de 34 son del río a 1,0 m.

### En motor (run 75536ac9; 3 min de carga por pose; `v10b/views/`)

| pose | frente a la v10 |
|---|---|
| RIVER_80 | el lago en media luna (≈ 12018, 1805) pasa de escalones a una curva limpia y el estanque junto al río (12093, 1690) pierde la sierra; el río principal tiene las dos orillas suaves y el estanque grande del primer plano es un óvalo (`v10b/views/river80-*-crop-v10-v10b.jpg`). Los cauces de la red de la derecha llevan un borde oscuro, como el río principal, sin causa comprobada (talud o luz de otra hora). Sigue el marco oscuro del final del río a 60 m del borde |
| RIVER_8 | delta máximo entre cuadros 0,0016 y 0,0019 (v10: 0,00079). Por píxel, entre dos capturas a 6 s, el cambio está en el agua (media 2,38 frente a 0,86) y en el cielo (0,35 frente a 0,18), no en la franja de la orilla cercana (píxeles con cambio > 20: 0,29 % frente a 0,32 %): oleaje y luz de otro momento, no parpadeo de la orilla |
| PONDS_120 | estanques algo más ovalados; con textura a los 3 min |
| LAKE10_150 | el lago 10 con la orilla del diseño; la tierra, sin textura en las dos visitas (BALTIC-019) |
| NAVFREE_85 | la tierra, sin textura a los 6 min (BALTIC-019); el Luga navegable no cambia (corredor fijo) |

En este run la máquina estaba justa de memoria: 5,9 GB disponibles y 102 GB comprometidos (85 GB privados entre todos
los procesos, 17 GB de ellos en WSL; otras aplicaciones y sesiones). La 3090 tenía 18,7 GB libres y el lease de GPU
estaba LIBRE. La tierra de NAVFREE_85 y LAKE10_150 no cargó textura en 6–8 min, y la de PONDS_120 y RIVER_80 sí.
Incidencias de la sesión, sin efecto en las vistas buenas:

- El cliente abrió solo el menú de pausa en la primera pose; se cerró con `ui_click continuebtn`.
- El lease caducó una vez en cada run (v10 y v10b), en pausas de más de 120 s. Las capturas de esos momentos repetían
  la pose anterior y están, con la del menú, en `views-invalid` de `E:/DayZ-Baltic-Build/v30-v10` y `v30-v10b`.

## Qué no se ha comprobado

- Vistas a nivel del suelo o desde una lancha: solo aéreas y una a 8 m.
- La v10b solo se ha visto en las cinco poses de lagos, estanques y ríos: su cambio no toca el borde, el Peipus ni los
  navegables.
- Que las teselas oscuras de L202_330, BORDER_E330 y LAKE10_150 de la v10 se carguen con el tiempo: no se repitieron.
- Los 7 puntos de oleaje que el suavizado movió en la v9, en sus sitios nuevos.
- Rendimiento.

## Decisiones para Guillermo

1. Aceptar la v10b como base de las orillas de lagos, estanques y ríos.
2. Lista de niveles: los 5 cambios por la regla (231, 417, 432, 468, 514; de 7 a 17 cm), la 216 que desaparece y la
   masa 165 del lake_047 a 1,37 m.
3. El final recto de los ríos a 60 m del borde (el marco oscuro del RIVER_80): redondearlo (recomendado) o dejarlo.
4. Lo que queda: el canal navegable del Luga con dientes (corredor protegido, contrato de navegación) y BALTIC-019
   (probar la carga de texturas con el cliente en primer plano).
