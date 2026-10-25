# Candidato v9: cadena rehecha desde el diseño suavizado — 06-10-2026

Plan `plans/v30-cadena-desde-diseno.md`, pasos 1–4, sobre el replay del paso 0 (`../v30-chain-replay-2026-10-06`).
Productos en `E:/DayZ-Baltic-Build/v30-redesign`. Desplegado como `@DayZ_Baltic_V9Candidate` (mundo b4f68bf1, agua
a1abc83f; copias comprobadas por hash, `reports/deploy-receipt.json`), misión `BalticTideProbeV2.BalticTrial`.
**No aceptado**: falta Guillermo, y tres decisiones suyas (abajo) pueden cambiar los pasos 21 en adelante.

## Qué cambia frente a la v8

- **Diseño:** ríos y arroyos suavizados a lo largo del cauce (sigma 18 m, extremos fijos) y semillas por cauce
  (`design_water_v3.py --course-sigma-m 18 --seed-per-course`). Giros de más de 45° por km: de 17,64 a 1,2; cauce
  total de 175 a 143 km. Lagos de contorno y estanques OSM no se tocan.
- **Borde del mapa:** el agua interior acaba a 60 m del borde (`build_v30_water.py --border-margin 60
  --drop-border-water-km2 0.05`); el mar y el delta llegan al borde; OutsideTerrain con síntesis.
- **Orillas:** una sola pasada (`profile_inland_v30.py`) para lagos, estanques, ríos y arroyos, sin congelar contactos
  ni la reserva natural; fondos a 1,0 m con 0,30 m de agua como mínimo.
- **Superficie:** `--bed-tone depth-all` (los cauces someros toman el tono de la tierra).

## Cadena (`scripts/`)

| tramo | script | notas |
|---|---|---|
| 4 | `redesign_04.sh` | agua V30 con la regla del borde: 98067e22 |
| 5–20 | `redesign_05_20.sh`, `redesign_13_20.sh` | la primera pasada paró en el paso 13 (abajo); el segundo script la reanuda |
| lista de niveles | `tools/water/derive_signed_levels_v30.py` | clasificación del terreno del paso 20 y lista por regla (abajo) |
| 21–final | `redesign_21_final.sh` | paso 25 a6be703a, costa 9760f2b9, dique 13adf74e, orillas e27f0f3e; puertas, superficie, paquete, auditorías |

- Mismas herramientas y parámetros que el replay byte a byte de la v8; solo cambian las entradas (diseño nuevo, agua
  nueva) y las opciones nuevas, que con sus valores por defecto dan el producto de siempre (commits 10c2541, 265f20f y
  f7691ba; cada uno con su comprobación por sha256 en el replay).
- Paso 10: el agua nueva se empaqueta de verdad (`tools/water/pack_water_v30.ps1`, AddonBuilder): 12.898 modelos,
  8.306 únicos y 16.810 instancias (v8: 13.434, 8.775 y 17.637).
- Pasos 6 y 7: los pasillos navegables y los ejes del delta salen idénticos a los archivados (28866a8c, 038470e9), así
  que las demás herramientas pueden seguir leyendo esos ficheros por defecto. Igual el `sd_sea` del agua nueva, que la
  costa lee de su ruta fija: idéntico al viejo.
- Paso 13 (márgenes de oleaje): 7 de los 13 puntos medidos en motor (524, 548, 642, 765, 1176, 1224, 1312) están junto
  a arroyos que el suavizado movió; su cota ya no es la de referencia. `--skip-moved-points` los deja fuera y los
  anota (`reports/wave-margins-build.json`); en los 6 restantes ahonda 42 vértices, 0,22 m como máximo. El calado
  mínimo de 0,30 m del perfilado final cubre el agua en general, no esos puntos concretos.
- La auditoría del agua visible se corrió primero contra el diseño viejo (faltaban `--water-v3` y `--streams`); se
  repitió con el diseño nuevo, que es la que se da aquí, y el script ya lleva las dos opciones.

## Borde del mapa (`reports/border-bodies.json`)

- Recortados con la franja de 60 m: los lagos 288 (Peipus), 106 y 202 (lake_000/001/002 del contorno), que conservan el
  94,9 %, 93,6 % y 94,5 %; 3 ríos (river_057, river_074, Volkhov) y 7 arroyos terminan antes del borde.
- Quitados: 18 cuerpos de menos de 0,05 km² que entran en la franja, 9 lagos de contorno y 9 estanques OSM, sin solaparse.
  **10 tocan el borde** (los «diez» del plan). Los otros **8 no lo tocan**, pero entran en la franja: lake_018 (1,45 ha,
  a 18 m del borde), lake_188 (a 10 m), 4 estanques a 28–37 m, y lake_047 y lake_107, que la rozan a 52 y 58 m.
- Agua interior a menos de 60 m del borde: de 16.098 vértices en la v8 a 0 (`reports/compare-v8-v9.json`).
- La franja queda como tierra a la cota de orilla: en el Peipus, llana a 2,99 m (0,35 m sobre el lago) con la orilla
  recta en x ≈ 61 m; allí el fondo de la v8 caía a −5,36 m bajo una orilla a 2,70 m y ahora es 1,0 m (talud sumergido
  de unos 19°).

## Lista de niveles (`levels/`)

La lista firmada no tiene comando registrado. Se reconstruyó su regla sobre la clasificación del v2 de la que salió
(`scripts/signed_list_rule.py`): las 84 masas aisladas o colgadas (69 + 15) son `max(nivel propuesto por
classify_perched_water_v30.py, 1,35 m)`; las conectadas llevan la cota de su río, puesta a mano; los fosos, 2,45 m; los
lagos de la cabecera del Luga bajan con el río. `derive_signed_levels_v30.py` aplica esa regla al terreno del paso 20
y mantiene el nivel firmado mientras la regla quede a 5 cm o menos (el anillo medido en otro terreno de la cadena mueve
la regla unos centímetros). En el replay reproduce la lista entera: 92 iguales y 1 masa nueva.

Sobre el diseño nuevo (90 entradas):

| | masas |
|---|---|
| iguales a la firmada | 88 (en 18 la regla daría 1–5 cm de diferencia) |
| desaparecen con el borde | lower_to_ring_159 (lake_088), _175 (lake_047), _515 (lake_129) |
| **cambia** | **connected_136** (lagos 222 y 233): firmada a 1,43 m, la cota del arroyo 0094. El arroyo suavizado ya no pasa a menos de 3 m, el clasificador la ve aislada y la regla da **1,35 m**. Ni antes ni ahora toca el arroyo en la malla. |
| **nueva** | **review_181** (lake_203, 25 vértices, en 11664, 1902): colgada 0,33 m, de 2,19 a **1,44 m**. También sale en el replay: no la causa el rediseño, sino que en el terreno del v2 no cumplía. |

## Resultados offline

- **Puertas** (`reports/verify-v9.json`, `roads-v9.json`, `channel-reaches.json`), v9 frente a v8:
  - calado: 1 fallo (6), en arroyos;
  - celdas con plano: 20 (31);
  - orillas, suelo de tierra, suelo de playa, taludes y fondos: 0 (0);
  - identidad de Narva: falla por diseño, igual que antes (3,25 m);
  - carreteras PASS; tramos vanilla: 0 fallos fuera de las celdas retiradas (3).
- **Pasillos navegables** (`compare-v8-v9.json`): 17 de 19 idénticos. En el Luga cambia 1 vértice en 8 mm; en el Neva,
  el nivel de 381 vértices en 2–3 mm, sin cambiar alturas ni clases (lo dibuja el mar del motor). **Las pruebas de lancha
  (BALTIC-012/013) siguen valiendo.**
- **Orillas** (`reports/inland-report.json`): desfase de la orilla de los lagos frente al contorno suavizado, p50/p90
  de 0,90/2,96 m a 0,00/0,37 m; fondos de lago por debajo de 0,85 m (BALTIC-018), de 270.705 vértices a 514.
- **Censo de defectos** (`reports/shore_failure_census_v9.json`, `figures/shore-failure-map-v9.png`):

| clase | aristas de orilla movidas v8 → v9 | esquinas vivas por km v8 → v9 |
|---|---|---|
| lagos | 81,5 % → 94,7 % | 15,1 → 14,4 |
| navegables | 64,0 % → 66,3 % | 3,2 → 2,9 |
| ríos | 87,1 % → 95,9 % | 13,8 → 4,9 |
| arroyos | 92,7 % → 97,8 % | 14,5 → 2,9 |
| estanques | 74,3 % → 94,1 % | 37,4 → 37,3 |

- **Agua visible** (`reports/audit-v9-085.json`, mar a 0,85 m), fuera de una franja de 66 m y de los cuerpos quitados
  (que el contorno de referencia aún incluye): huecos de 39.336 a 47.796 m², tierra inundada de 142.568 a 131.152 m².
- `figures/waterline-v8-v9.png`: la línea de agua real en las marcas de Guillermo, en la zona RIVER_80 y en arroyos
  del centro.

## En motor (run 6d421b36, `views/`, 3 min de carga por pose)

| pose | frente a | qué se ve |
|---|---|---|
| RIVER_80 | v8 | el parche liso de fuera del borde que marcó Guillermo es tierra sintetizada con textura; los trozos de cauce que llegaban al borde desaparecen; el río principal tiene menos quiebros, aunque su tramo alto aún se ve anguloso; **el canal recto de la marca A sigue igual**: es un lago de contorno (clase 2) y los lagos no se suavizaron |
| RIVER_8 | v8 | al fondo, tierra donde la v8 mostraba agua plana más allá del borde |
| L106_330 | v8c | sin las bandas rectangulares sobre el agua; orilla recta junto al borde y tierra al otro lado |
| L202_330 | v7d | donde la v7d mostraba un exterior como mar, orilla recta y tierra con textura |
| BORDER_E330 | v8c | igual, con tierra sintetizada; la mancha oscura sobre la línea del borde sigue, más pequeña |
| NAVFREE_85, NAV_330 | v8, v7d | prácticamente iguales (navegables y Luga sin cambios) |
| L288_330, L288_60 | — | Peipus: orilla recta del recorte, franja de tierra y exterior sintetizado, sin bandas |

## Qué no se ha comprobado

- Vistas a nivel del suelo o desde una lancha; solo aéreas y una a 8 m.
- Los 7 puntos de oleaje movidos en sus nuevos sitios.
- Rendimiento.

## Decisiones para Guillermo

1. Lista de niveles: connected_136 a 1,35 m (regla) o a 1,43 m (firmada); añadir review_181 a 1,44 m o dejarla.
2. Borde: quitar también los 8 cuerpos que entran en la franja sin tocar el borde, o recortarlos/dejarlos (lake_047 y
   lake_107 apenas la rozan).
3. Siguiente frente de planta: lagos de contorno y estanques (14 y 37 esquinas vivas por km), incluido el canal recto de
   la marca A, y la mancha oscura del borde este.
