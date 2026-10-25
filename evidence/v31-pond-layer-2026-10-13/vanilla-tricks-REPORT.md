# Trucos de los mapas vanilla para terreno y agua, medidos (13-10-2026)

Para Baltic 12 km. Mapas medidos: Chernarus+, Livonia (enoch) y Sakhal, con sondas de servidor (sin cliente) y lectura offline de los modelos binarizados de `P:\DZ`. Datos en `E:\DayZ-Baltic-Build\vanilla-tricks-20261013\`.

Autor: subagente Opus 5.5 lanzado por la sesión handoff-astra-map-review-6d301c (el arnés le impidió escribir este archivo; lo guardó el orquestador con el texto íntegro que devolvió).

## 1. Método y evidencia

**Sondas** (`mode=server`, `no_file_patching`, sin mods extra; cierre ordenado y lease liberado):

| Run | Misión | Log (SHA-256) |
|---|---|---|
| 00ddff5f | `BalticVanillaTricksV1.chernarusplus` | `runs\chernarus_tricks_v1.log` (f26f3068…) |
| 0703ec2f | `BalticVanillaTricksV1.enoch` | `runs\enoch_tricks_v1.log` (4e200569…) |
| 06d16734 | `BalticVanillaTricksV1.sakhal` | `runs\sakhal_tricks_v1.log` (2caee254…) |
| 9b47cbe0 | `BalticSakhalGridV1.sakhal` (`SurfaceY` cada 0,25 m) | `runs\sakhal_grid_v1.log` (bcac0a75…) |

Las misiones están en `...\DayZServer\mpmissions\`, con copia en `missions\` (`init.c` d556ed5d… y f7a71642…). El linter da 0 errores y 0 avisos en las dos.

Fases de la misión, con las APIs citadas en `P:\scripts\...`:
- **Fase 0.** Nivel del mar (`game.c:1174-1180`): 0,52 en el momento, mínimo 0,5, máximo 1,0 y ola 0,25, igual en los tres mapas.
- **Fase 1.** Mapa de alturas `SurfaceY` (`game.c:1162`) en 2048² vértices; el tamaño sale de `GetWorldSize` (`world.c:85`) / 2048. Tipo de superficie `SurfaceGetType` (`game.c:1166`) a la mitad de resolución.
- **Fase 2.** Censo con `GetObjectsAtPosition` (`game.c:922`), filtrado por `GetShapeName` (`object.c:509`); ejes del modelo con `ModelToWorld` (`object.c:869`). Resultado: 105.628 objetos en Chernarus, 299.122 en Livonia y 206.261 en Sakhal.
- **Fase 3.** Para cada puente y alcantarilla, cortes cada 1 m de −60 a 60 m por sus dos ejes: terreno, roadway `SurfaceRoadY3D UNDER` (`game.c:1164`, `constants.c:40`) y `GetWaterDepth` (`game.c:1183`).

**Offline:**
- `scripts\models_inventory.py`, sobre `odol_reader.py` (marco «stored» = marco del motor).
- La interpolación planar NO-SE del mapa de alturas (`scripts\terrain.py`) frente a 25.780 `SurfaceY` del sondeo de Astra: error p50 0,8 mm, p99 2 cm.
- Baltic: `v31-pond-layer-20261013\terrain-ev106.npz`.

**No verificado:**
- Nada de render (no hubo cliente).
- Sakhal muestreado cada 7,5 m sobre una malla de 3,75 m.
- 94 de 637 cortes de Chernarus no se escribieron.
- En los puentes metálicos la consulta UNDER da en la celosía.
- `SurfaceGetType` incluye el roadway de los objetos.
- Cruces carretera–cauce calculados con segmentos rectos (las curvas como cuerdas).

## 2. Malla y render

| Mapa | Paso | Diagonal | RMS planar por triángulo |
|---|---|---|---|
| Chernarus | 7,5 m | NO-SE | 0,28 mm (NE-SO 7,7 mm) |
| Livonia | 6,25 m | NO-SE | 0,28 mm (NE-SO 3,6 mm) |
| Sakhal | **3,75 m (4096²)** | NO-SE | 0,28–0,32 mm (NE-SO 47–402 mm) |
| Baltic | 6 m | NO-SE | — |

Evidencia: `data\grid_detect.json`, `data\sakhal_grid.json`.

Chernarus (`world\config.cpp:304-306`) y Livonia (`:372-374`) declaran `terrainNormalTexture`, `heightBlendingMode=1` y `bicubicMode=1`. No los declaran ni el mundo Baltic (`packages\baltic-road-v29\...\config.cpp`) ni `CAWorld`. Los mapas de normales globales miden 1024² (Chernarus) y 2048² (Livonia y Sakhal). Efecto en render sin verificar.

## 3. Arroyos

**Dos sistemas en Chernarus, ninguno en Livonia ni en Sakhal:**
- **Cintas `stream_14` / `river_24`** (460/660 piezas, 10/16 km). Son planas, con faldones que bajan 0,14 m en los últimos 3 m. Inclinación p50/p90: 1,5°/5,8° en arroyos y 1,1°/3,6° en ríos.
- **Kit `streambed`** (1.682 piezas, ~33 km) más 572 piedras `stones_*`.
- Densidad: 59 km de cauce en 180,6 km² de tierra.

**Asiento** (terreno menos lámina; fuente `data\stream_sections.json`, `figures\stream_sections.png`):

| Familia | Eje | 3 m | 6 m | 12 m | 20 m | Agua visible p10/p50/p90 |
|---|---|---|---|---|---|---|
| `river_24` | −0,51 | −0,33 | +0,44 | +2,82 | +5,31 | 8/11/15 m (cp_gravel 54 % en el eje) |
| `stream_14` | −0,28 | +0,25 | +1,13 | +2,46 | +3,90 | 4/5/9 m |
| `streambed` larga recta | −0,33 | +0,70 | +1,81 | +3,13 | +4,31 | 2/3/3,5 m (roadway); 3/4/5,5 m (visible, inferido) |

**Kit `streambed`** (`streambed_leaf_long_straight`):
- **Placa base:** 14 × 24 m, a y = +0,21. Usa el shader Multi con `cp_gravel` del terreno, una máscara y `_mc` propios de cada pieza.
- **Lecho 3D:** 18.583 caras de lecho y 3.800 de piedras, en una banda x de −2,4 a +3,0 m. Las variantes `_2` añaden troncos.
- **Geometry:** dos umbrales de granito en los extremos.
- **Roadway:** cara central `water_ext` a +0,21; es lo que lee el motor (98 % de centros mojados, calado p50 0,35 m).
- **Agua visible:** proxy CalmWater con labios de 0,69 m en los extremos. No tiene roadway, así que el motor no la lee como agua. Inferido: lámina a +0,46.
- **Asiento:** la orilla visible cae a ~2 m del eje y las piedras llegan a 2,4–3,0 m, así que tapan el corte agua/terreno.
- **Red aparte:** ningún `streambed` está a menos de 30 m de un `stream_14`/`river_24`; la mediana queda a 3,1 km. Las piedras se colocan a 2–9 m del `streambed`.

## 4. Río de Livonia

Fuente: `data\enoch_river.json`, `figures\enoch_river_profile.png`.
- 804 modelos únicos, uno por losa de 50 m, de 3 a 40 vértices.
- Todos a la cota 170,000 m (p1–p99: 169,96–170,04). Superficie 0,97 km²; ancho de malla ~57 m.
- **Borde de malla enterrado:** terreno a +1,47 m (p10 +0,48); solo el 0,6 % de las aristas queda bajo la lámina.
- **La línea de agua cae 6,6 m dentro del borde** (p10 12 m, p90 2,2 m).
- Taludes: 0,27 m/m bajo el agua hasta −4 m; 0,2 m/m en seco.
- Puentes: tramos de hormigón de 62–121 m, con el tablero 4,3–5,8 m sobre la lámina.

## 5. Charcas y lagos

Fuente: `data\ponds_*.json`, `data\perched.json`.

| Familia | Terreno en el borde (p50) | Borde enterrado | Línea de agua (dentro del borde) | Fondo |
|---|---|---|---|---|
| Chernarus, losas de 52 m | +2,57 | 98 % | ~24 m | — |
| Chernarus, `pond_big` | +0,11 (p10 −0,07) | 78 % | 2–4 m | plataforma −0,3 m y centro −2 m |
| Chernarus, `pond_small` | +0,37 | 84 % | ~4 m | — |
| Livonia, lagos por teselas | +1,03 | 96 % | ~8 m | ~0,1 m/m |
| Livonia, `pond_50x50_moss` | — | — | el 76–84 % de la losa queda seco | — |

La última fila es el truco «pantano»: una lámina plana justo bajo un terreno con montículos, de modo que el agua solo asoma en las hondonadas. Sakhal hace algo parecido con sus losas de hielo y añade una malla de lecho de 64.000 vértices.

Talud alrededor del agua (mediana de terreno menos lámina):

| | 0–13 m | 13–30 m | 30–60 m | Tierra >0,25 m bajo la lámina a 0–13 m |
|---|---|---|---|---|
| Chernarus | +0,98 | +2,50 | +3,96 | 1,1 % |
| Livonia | +1,15 | +3,15 | +4,27 | 0,4 % |
| Sakhal | +0,43 | +1,13 | +1,96 | 0,2 % |
| **EV106** | +0,91 | +1,35 | +1,43 | 2,3 % |

EV106 no está técnicamente colgado: es llano. Sus bordes p31 están enterrados como los de Chernarus (14,6 % a menos de 0,30 m).

Textura en la orilla: Livonia pinta `en_soil` en el 25 % de los vértices secos de la orilla (2,3 % en el resto de la tierra). Las charcas de Chernarus llevan hierba o tierra.

## 6. Costa y desembocaduras

Fuente: `data\coast_*.json`, `data\mouths.json`.

| | Chernarus | Sakhal (7,5 m) | EV106 |
|---|---|---|---|
| Primer vértice seco / mojado | +0,58 / −0,60 | +0,39 / −0,45 | +0,68 / −0,59 |
| Distancia hasta +2 m (p50) | 16 m | 26 m | 24 m |
| Fondo a 20 / 50 m mar adentro | −2,5 / −5,9 | −2,5 / −5,0 | −2,1 / −3,0 |
| Clases: playa <5° / 5–15° / 15–30° / >30° / sin +2 m en 120 m | 29/40/15/1/15 % | 51/36/3/1/9 % | 30/22/2/0/46 % |
| Textura en la costa | cp_gravel 74 % | sakhal_beach 87 % | — |
| Rocas a <40 m / media en tierra | 7× | 2,2× | — |

**Desembocaduras de Chernarus:** el río se mantiene a ≥1,8 m y en los últimos 20–30 m baja en un tramo inclinado hasta el mar. Las dos piezas finales: `river_24_12` a 0,94 m de cota, 4,9° de inclinación y 7,5 m del mar; `river_24_6` a 1,33 m, 7,1° y 10,6 m.

**Charcas junto al mar:** en Chernarus ninguna a menos de 16,8 m de la costa (cota mínima 1,49 m); en Sakhal ninguna a menos de 33 m. En EV106 hay 5 masas interiores a menos de 18 m, a 0,50 m de cota.

## 7. Carreteras sobre el agua

Fuente: `data\bridges_*.json`, `data\road_crossings_chernarus.json`, `data\culverts.json`, `figures\bridges_chernarus.png`.

**Puentes de Chernarus:**

| Tipo | n | Tablero | Despeje | Con agua debajo | Tablero sobre la lámina | Terreno a 5 m del final del tablero | Garganta |
|---|---|---|---|---|---|---|---|
| `bridge_wood_25` | 27 | 22 m | 3,45 m | 70 % | 2,56 m | −0,23 m | 1,4 m |
| `bridge_stone_25` | 10 | 20,5 m | 5,97 m | 50 % | 5,1 m | −0,01 m | 1,7 m |

- El puente de madera lleva las rampas dentro del modelo (roadway de 0,23 a 2,45 m a lo largo de 33 m).
- Pendiente de acceso entre −11 % y +10 %.

**Cruces carretera–cauce:**
- 36 cruces: 30 con puente, 1 con alcantarilla y 5 a nivel (4 de ellos senderos).
- 65 finales de cauce a menos de 8 m de una carretera: 24 en un puente, 15 con alcantarilla y 26 sin nada.

**Alcantarillas de Chernarus:**
- 182 tubos `misc_concretepipe` a ≤15 m de una carretera; 89 de ellos también a ≤30 m de agua.
- Van perpendiculares a la carretera (p50 77°), en pares (6 m de largo).
- El centro queda 0,67 m bajo el terreno y la carretera 0,7 m sobre la clave del tubo.
- El 51 % lleva rejilla en un extremo.

## 8. Cómo esconden los artefactos

- **Rocas según la pendiente:** en Chernarus pasan de 123 por km² (a 0–5°) a 1.291 (a 40–50°) y 2.168 (por encima de 50°). La textura `cp_rock` cubre el 29 % del terreno a 40–50° y el 53 % por encima de 50°.
- **Carrizos como objetos, no como clutter:** a ≤30 m del agua está el 41 % en Chernarus (16× su proporción en tierra), el 55 % en Livonia (30×) y el 87,5 % en Sakhal.
- **Textura de la orilla:** grava en ríos y costa, `en_soil` en las orillas de Livonia.
- **Capas del `streambed`:** las piedras tapan el corte agua/terreno, el agua tapa el corte placa/terreno y la placa lleva la textura del terreno.
- **Juntas de piezas:** las cintas y el agua del `streambed` acaban en faldones que quedan bajo la pieza vecina.

## 9. Recomendaciones (por impacto)

| # | Recomendación | Problema | Impacto | Esfuerzo | Riesgos |
|---|---|---|---|---|---|
| 1 | Reducir la orilla interior (3,3 km/km² frente a 0,4–1,1): quitar o fundir charcas y arroyos menores; zonas húmedas con el truco «pantano» | escalera, contactos con el mar, lagos colgados | Alto | Medio | El agua es requisito de producto: decidir con Guillermo qué se queda |
| 2 | Arroyos en V: terreno ≥1,1–1,8 m a 6 m del eje, agua de 3–5 m, y piezas vanilla `\DZ\water\streambed\*.p3d` o piedras y carrizos a 2–9 m del eje | escalera en arroyos estrechos (015) | Alto | Medio | En llano hay que excavar; verificar en cliente la altura del proxy de agua |
| 3 | Charcas a ≥17–20 m del mar y con cota ≥1,5 m, o fundidas con el mar; desembocaduras con río ≥1,8 m y último tramo inclinado 5–7°; revisar las 5 masas a 0,50 m | cortes rectos charca/mar | Alto (local) | Bajo | Las lagunas de 020 pueden ser intencionadas |
| 4 | Meter el agua en cuencos: terreno +2,5 m a 13–30 m y +4 m a 30–60 m | lagos que parecen colgados (017) | Medio-alto | Medio | Geografía real llana |
| 5 | Estribos a ras (±0,3 m), acceso con pendiente ≤10 %, garganta de 3–6 m; alcantarillas de 2 tubos con rejilla; ningún cruce a nivel salvo senderos | carreteras que acaban en barranco sobre el agua (015) | Alto | Bajo-medio | Navmesh e IA en los estribos |
| 6 | Costa: textura de grava o playa, rocas en los primeros ~40 m, carrizos; plataforma submarina hasta −5…−6 m a 50 m donde la costa sea alta | suavizado de costa | Medio | Bajo | Lancha; agua de dos colores (EV96) |
| 7 | Prueba A/B de render con `heightBlendingMode=1`, `bicubicMode=1` y `terrainNormalTexture` | facetas a distancia | Desconocido | Muy bajo | Puede no cambiar nada |
| 8 | Carrizos como objetos, rocas en pendientes >35°, banda de barro o grava en la línea de agua | todos | Medio | Bajo-medio | Rendimiento sin medir |
| 9 | Estratégico: malla de 3 m (4096²), como la de 3,75 m de Sakhal | escalera en todo | Muy alto | Muy alto | Memoria, Terrain Builder y teselas p31 a 3 m |

Ya conforme con vanilla, no tocar: los bordes p31 enterrados y la rasante de vértices en la orilla.
