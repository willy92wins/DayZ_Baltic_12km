# Candidato v3: niveles firmados, canal navegable y contorno suavizado — 04-10-2026, noche

Sale de ver el v2 en motor con Guillermo (run d227200e) y de sus decisiones de esa noche (plan
`plans/v30-rumbo-agua-1.0.md`, pasos 1 a 3). Productos en `E:/DayZ-Baltic-Build/v30-v3`. Desplegado como
`@DayZ_Baltic_V3Candidate` (copias comprobadas por hash), con la misión `BalticShoreSdfCandidateV1.BalticTrial`.

## Decisiones de Guillermo

- **Vistas del v2** (`../v30-polish-candidate-2026-10-04/runtime/view-d227200e/`):
  - la cabecera del Luga pasa con retoques;
  - las placas grises de los rectángulos y los fosos son agua colgada (BALTIC-016 pasa a BALTIC-017);
  - en la vista 9, estrechar la franja somera del Narva y suavizar el río, «y el resto que tienen esos límites tan
    angulares».
- **Canal Luga–lake_014:** navegable (P9). Se le da el estándar de BALTIC-012/013: 3,05 m de calado.
- **Luga:** los lagos de la cabecera bajan con el río a 3,14 m. El río queda plano 4,4 km, con una bajada máxima de
  1,06 m (`decisions/luga-profile.json`, `figures/luga-profile.png`).
- **Fosos de la fortaleza:** los dos altos, a 4,61–4,62 m, bajan al entorno, a 2,45 m. El tercero se queda a 2,75 m.
- **Lagos grandes 269 y 170:** verlos en motor antes de decidir.
- **Lista de niveles firmada** (`decisions/levels-signed.json`):
  - 69 masas aisladas con dique de más de 1 m bajan a la cota del entorno menos 5 cm (p25 del anillo de 12–36 m);
  - 15 colgadas de 0,3 a 0,5 m, con el mismo criterio;
  - 6 conectadas bajan a la cota del entorno o a la de su río, la más alta;
  - el 132 y el 242 se quedan, porque están a la cota de su río.

Corrección dentro de la sesión: la franja gris de la vista 9 es agua somera del Narva, de 1 a 2 m, y no grava. Lo
primero que dije salió de una sonda que cayó fuera de la franja (`figures/flood1-v2-crop.jpg`,
`figures/flood1-shore4-visible-depth.png`).

## Cadena

| Paso | Herramienta y parámetros | Qué hace | Salida (SHA-256) |
|---|---|---|---|
| 1 | `tools/terrain/polish_luga_head_v30.py --channel-width 30 --bed-depth 3.05`; eje alargado hasta (10620, 4360), dentro de lake_014 | Canal navegable: 140 vértices, todos a 3,05 m | terreno 1c0a52fb…, sd 11564fdb… |
| 2 | `tools/terrain/relevel_bodies_v30.py --river Luga_0:4440:3.14 --with-river-box 10150,3700,10700,4600:3.9 --bodies decisions/levels-signed.json` | Niveles: el lecho baja con el agua, los afluentes se topan, las orillas bajan hacia el relieve natural y se separan aguas | fdfe2ff8… |
| 3 | `tools/terrain/smooth_shore_outline_v30.py` (σ 12 m, 18 m en Narva; desplazamiento ≤ 4 m) | Margen y repisa del Narva; contorno suavizado y su sd | terreno 5f207001…, sd a234bd7e… |
| 4 | `patch_water_tiles_v30.py`, `fit_channel_pieces_v30.py` y `fit_shore_crossings_v30.py`, con los flags del v2 y `--sd-override` del paso 3 | Agua, piezas y orillas | agua 3f3b74f4… (parche) y 481e1dda… (con cauces); terreno fac76aea… |
| 5 | `build_surface_v30.py --bed-tone land --shore-ring flowing` y `build_v30_package.ps1` | Superficie y paquete | mundo 9034a494…, agua c687a7be… |

La primera pasada (Luga, fosos, canal y contornos, sin la lista) está en las carpetas sin sufijo `-b` y dio las
mismas puertas.

## Resultados offline

- **Niveles** (`reports/relevel-report.json`):
  - 15.415 vértices de agua bajan; el máximo, 2,17 m, son los fosos;
  - el Luga baja en 5.272 vértices a 3,14 m, junto con los 16 lagos de la cabecera;
  - las 92 masas de la lista aparecen todas, con la misma cota y los mismos vértices que en el v2;
  - 10.170 vértices de orilla bajan hacia el relieve natural (mediana 0,56 m, máximo 2,82 m);
  - 6 vértices pasan a tierra por separación;
  - el tope actúa en 4 vértices de afluentes (≤ 0,66 m).
- **Narva** (`reports/shape-report.json`):
  - 327 vértices de margen con menos de 0,6 m de calado pasan a tierra;
  - 185 vértices de repisa se profundizan (mediana 0,34 m) hasta un perfil de 0,4 m a 6 m de tierra y 3,0 m a 18 m.
- **Contorno:** el giro por cada 12 m de orilla, en p50/p95, baja de 15,9°/85,9° a 8,8°/68,1° (desplazamiento p50
  1,72 m, tope 4 m).
- **Puertas** (`reports/verify-terrain.json`): las mismas fallas que el v2 y ninguna nueva.
  - Calado: 6 fallos, en arroyos.
  - Celdas con plano: 31 fallos (35 en el v2).
  - Identidad de Narva: falla por diseño, con 3,25 m de diferencia máxima.
  - Orillas, suelo y taludes: 0 fallos.
- **Carreteras** (`reports/roads.json`): PASS, con 76.513 muestras y 0 fallos.
- **Cauces** (`reports/channel-reaches.json`): un vértice mojado sin pieza, como en el v2.
- **Censo** (`census/`):
  - 624 masas;
  - lagos colgados más de 0,3 m: de 111 (7,0 km²) a 11 (6,65 km²). Quedan los lagos 269 y 170 con sus satélites,
    el 242 (a la cota del Narva) y el tercer foso;
  - masas con dique de más de 0,5 m: de 190 a 168, un área dominada por los dos lagos grandes.
- **Clasificación** (`classification/`, sobre el terreno del v2; `tools/water/classify_perched_water_v30.py`, de GLM
  con correcciones):
  - 484 aisladas, 75 conectadas, 66 con contacto accidental, 3 grandes y 3 fosos;
  - acciones: mantener 519, bajar al entorno 73, bajar con su río 17, revisar 16, decidir aparte 3, excepción 3.

## En motor

Run a7769d66, 15 vistas. Comparación en `runtime/view-a7769d66/compare-1.jpg` y `compare-2.jpg`, con el v2 a la
izquierda.

- **Mejor:**
  - el Luga llega azul y continuo hasta lake_014, y el canal navegable se ve (vistas 1, 2 y 4);
  - la franja clara del Narva es más estrecha (vista 9).
- **Igual:**
  - los rectángulos siguen siendo placas rectangulares, ahora a ras de suelo (vista 5);
  - los fosos (vista 8), R1 y EDGE1.
- **Sin resolver:** bordes en escalera en el Luga bajado (vistas 14 y 15) y en el tramo navegable (vista 7).
  - Causa medida en s = 3.000 m: el corredor navegable tiene 3,5 m de calado hasta el último vértice mojado, y la
    tierra de al lado queda 0,5–0,7 m sobre el agua.
  - El ajuste de orillas fija el corredor fuera de la caja de la cabecera, y no reajusta la costa del mar
    (`limits` de su informe), así que la línea de agua sigue la malla de 6 m.
- **Lagos grandes** (vistas 12 y 13): no se ve bien el dique; hay que repetirlas más bajas y más cerca.

Guillermo, al ver la comparación:

- «casi toda la costa y bordes de los ríos son poligonales o "serrados" eso no es nada realista. Lo mismo pasa con
  islotes y otros»;
- «aún hay zonas bajas donde cuando sube un poco la marea sobresale el mar por encima de la tierra», con una captura
  de EDGE1 marcada.

## Sin verificar

- La franja gris a lo largo del Luga bajado (vistas 14 y 15): no sé si es el anillo de grava o el talud.
- Los lagos 269 y 170 en motor.
- La altura máxima real del mar con pleamar y oleaje.
- Navmesh, IA y lancha en el canal nuevo.

## Siguiente

1. **Mar sobre tierra con marea (BALTIC-016).**
   - En motor: lectura del mar con `GetWaterSurfaceHeight` (con oleaje) y `SurfaceGetSeaLevel` en puntos de costa
     y en los bajos de tierra, con el tiempo acelerado para cubrir la marea, en calma y con tormenta.
   - Resultado: la altura máxima visible del mar.
   - Offline: mapa de la tierra por debajo de esa altura más un margen, en todo el mapa, porque el mar del motor es
     un plano global.
   - En motor otra vez: vistas en pleamar y tormenta en los peores sitios.
   - Arreglo: subir esos bajos o convertirlos en agua de diseño, a decidir con Guillermo.
2. **Orillas serradas en costa, ríos e islotes (BALTIC-007).**
   - Perfil de orilla como función de la distancia a un contorno suave, para que la isolínea del agua siga el
     contorno: un vértice deja de ser «mojado a 3,5 m» o «tierra a +0,5 m».
   - En los navegables, liberar del corredor los vértices exteriores y dejar fijos los 24 m útiles a 3,05 m.
   - En la costa, un ajuste propio a la banda de marea.
3. **Lagos 269 y 170:** vistas más bajas, y decisión.
