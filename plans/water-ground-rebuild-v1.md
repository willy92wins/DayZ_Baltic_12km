# Rehacer agua y suelo sobre V29

Petición de Guillermo, 02-10-2026: las zonas de agua se ven cuadradas o poligonales,
puede faltar agua donde debería haberla y lo mismo pasa con los colores del suelo.
Diagnóstico medido en `evidence/v29-water-color-audit-2026-10-02/` (scripts en
`tools/audit/`). Decisiones de Guillermo del 02-10: ríos navegables con forma natural
y ancho variable; añadir ríos con nombre y arroyos largos; restaurar brazos e islas
del delta del Neva; añadir las lagunas desde ~300 m². Relieve: conservar las zonas
altas, dejar zonas de llanos y ajustar el resto a algo más natural, en lugar del ×5
general.

Aprobado por Guillermo el 02-10. La fase 1 es diseño offline y no toca terreno,
paquete ni despliegue; su puerta es el OK de Guillermo a los mapas de relieve y de
agua antes de la fase 2.

## Diagnóstico de partida (V29)

- Agua: el 97 % del área de referencia está construida, pero faltan ríos enteros
  (Vóljov, Shelón, Msta, Oredezh, Grib, canal de Sívers), el delta del Neva está
  entre el 10 y el 39 % según el brazo y faltan unas 400 lagunas de más de 300 m².
  De los 427 km de ríos y arroyos OSM dibujados como línea, el 86 % no tiene agua.
- Forma: el Narva–Luga–Neva es un canal de ~60 m de ancho uniforme. El agua interior
  son 10.152 piezas: losetas de 48 m solapadas 2 cm y 6.186 bordes recortados, y el río
  va en 168 escalones de 25 mm (`tools/navigation/prepare_regional_water_assets.py`,
  función `generate`).
- Satélite: coloración plana de WorldCover a 6 m/px y 8 colores, sin regenerar desde
  el 29-09 (`tools/prepare_prototype.py`, bloque «four-material prototype»). 1,10 km²
  pintados de azul sobre tierra seca y 1,29 km² de agua sin pintar.
- Suelo: cuatro materiales (grava, hierba, coníferas, hierba alta) en 4.775 materiales
  de tile; 4.560 tiles llevan los cuatro (`tools/audit/pbo_materials.py`).
- Relieve: el rectángulo de San Petersburgo y la elipse de la reserva quedan llanos con
  una transición de 330 m, y fuera el relieve es ×5 de base y hasta ×20–24 en dos zonas
  (`tools/navigation/prepare_regional_outline.py`, máscaras `spb`/`reserve_mask` y
  objetivo `target`). Se ven bordes rectos y una elipse.

## Fase 1a — Diseño del relieve (offline)

Decisión de Guillermo del 02-10: mantener las zonas altas, dejar zonas de llanos y
ajustar el resto a algo más natural. [DESIGN] `tools/terrain/design_relief_v30.py`
sustituye el factor ×5 uniforme por un campo de exageración que varía suavemente:
las dos zonas altas (A al oeste de Gatchina y B al sur) conservan sus cotas; los
llanos (costa y delta, valles y llanuras de inundación de los ríos grandes, la reserva
y las zonas que en el modelo físico son bajas y planas) quedan cerca de ×1; el resto,
en torno a ×2–3 sobre el relieve físico. Las transiciones son anchas (kilómetros) y de
contorno irregular, sin rectángulos ni elipses. Se conservan XY, costa, islas, agua y
el acceso de Narva.

Salida: sombreado y pendiente actual frente a propuesto, perfiles y distribución de
pendientes. Las carreteras se vuelven a nivelar sobre el relieve nuevo en la fase 2.

Resultado, 02-10: Guillermo eligió la mezcla entre tres opciones. Las zonas altas
conservan las colinas de V29 sin el rectángulo ni la elipse: el pipeline de relieve de
Codex, reproducido con diferencia máxima 0,0 m, se volvió a ejecutar sin esas
protecciones. El resto toma el relieve regenerado desde la topografía real (llanos y
valles suaves), y el contorno de las zonas altas sigue la curva de nivel real. Llano
(<2°) en el 55,5 % del terreno frente al 47 % de V29; pendiente >10° en el 11,8 % frente
al 19,4 %; ninguna celda >35°; agua, orillas y Narva idénticos a V29. Scripts en
`tools/terrain/`, rásteres en `tests/relief_v30/` (no versionados) y evidencia en
`evidence/v30-relief-design-2026-10-02/`. Pendiente de valorar: los hoyuelos redondos
que V29 tiene alrededor de lagunas OSM diminutas siguen en las zonas altas.

## Fase 1b — Diseño del agua (offline)

[DESIGN] Un único script de diseño, `tools/water/design_water_v3.py`, con parámetros en
`design/water-v3.json`. Produce cuerpos de agua con tipo, polígono, nivel y perfil de
lecho, más mapas de previsualización. Reglas:

- Navegables (Narva, Luga, tronco del Neva): eje OSM suavizado; ancho entre 30 y 60 m
  según el ancho real comprimido, con variación lenta y orillas irregulares (±2 m). El
  canal libre de 24 m de los fairways actuales (`fairways-main-game.json`) queda dentro.
- Delta del Neva: Gran y Pequeño Neva navegables (≥30 m); Nevkas y Canal Marítimo de 12
  a 20 m. Las islas resultantes se conservan como tierra seca.
- Ríos con nombre que tienen polígono OSM: Vóljov, Shelón, Msta, Oredezh, Izhora,
  Tosna… de 8 a 20 m, poco profundos, no navegables.
- Arroyos largos: cursos con nombre por encima de un umbral de longitud que se fija
  con un mapa de selección. Hay 44 cursos de más de 2 km (191 km) y 92 de más de 1 km
  (259 km): demasiado para jugar. Cauce de 3 a 6 m.
- Lagunas: polígonos OSM no fluviales de al menos 300 m² que hoy faltan (~400).
- Niveles: en ríos y arroyos, perfil monótono hacia la desembocadura, sacado del fondo
  del valle; en lagunas, nivel por debajo del punto más bajo de su orilla.

Puerta de la fase 1: mapas de relieve y de agua, con los kilómetros de cada clase de
agua. Guillermo aprueba ambos (sobre todo el umbral de arroyos) antes de tocar el
terreno.

Resultado, 02-10 (aprobado por Guillermo, que pasa a la fase 2): navegables de 30–60 m
sobre los fairways (Luga con mediana de 43 m, frente al canal uniforme de 60 m); delta
con el Gran Neva navegable hasta el golfo, el Pequeño Neva, las Nevkas, el Canal
Marítimo y las dársenas, al nivel del mar, sin los 25 fragmentos del fairway «Delta
Neva»; 13 ríos con nombre de 8–20 m (49 km); **arroyos desde 2,5 km** (25 cursos, 95 km;
elección de Guillermo); 387 lagunas nuevas de 300 m² o más. Cruces únicos con
carreteras principales y secundarias: navegables 29+52, delta 6+5, ríos 17+26,
arroyos 32+33. Guillermo también pidió rellenar en las zonas altas los hoyuelos que no
son laguna. Scripts en `tools/water/`, salida en `tests/water_v3/` (no versionada),
evidencia en `evidence/water-v3-design-2026-10-02/`.

Para la fase 2 quedan anotados el relleno del agua de V29 que el diseño no usa (bucle
viejo del delta y márgenes del canal de 60 m), el rebaje de crestas donde un cauce
exigiría un corte de más de 5 m (3,4 km de ríos y 2,8 km de arroyos de 4 km o más) y la
renivelación de las carreteras, que sobre el relieve nuevo quedan como diques.

## Prototipo de arroyo, antes de producir en masa

Un arroyo con pendiente puede necesitar cientos de escalones de nivel si se hace con
planos horizontales. Se comparan en el juego tres variantes sobre un mismo tramo:
planos escalonados propios, piezas vanilla `DZ\water\streams` (`stream_14_*`,
`river_24_*`) y lecho seco con decoración vanilla (`Land_streambed_*`). Se elige por
aspecto y número de objetos.

## Fase 2 — Terreno V30 (ráster determinista, no LP)

[DESIGN] `tools/terrain/build_v30.py` parte del ASC V29 y aplica capas separadas: el
relieve de la fase 1a (que ya elimina el rectángulo y la elipse), la nivelación de las
carreteras sobre ese relieve, la excavación de cauces y lagunas (sección con fondo y
taludes) y las orillas por encima del nivel con resguardo. Se conservan las
protecciones actuales: puente de Narva y su gálibo, fairways, islas y costa. Donde un
cauce nuevo cruce una carretera queda una reserva de puente o vado, excluida de las
puertas viales hasta el mapeado.

Puertas offline, reutilizando los verificadores de Codex cuando apliquen y con
referencias nuevas: profundidad y resguardo de cada cuerpo; ninguna celda por debajo
del mar fuera de las zonas marinas previstas; carreteras lisas fuera de las reservas
(6,5 %, 3 cm transversal); taludes ≤35°; anchura y calado del canal navegable a lo
largo de los fairways; gálibo de Narva sin cambios. Un fallo se arregla en su sitio y
se documenta; no se abre una versión nueva por cada fila.

## Estado de la fase 2 — 02-10, 03:40

- `tools/terrain/build_v30_water.py`: clases y niveles del agua V30 en la malla de vértices
  (navegable 31.858 vértices, delta 1.088, ríos 20.524, arroyos 24.611 con `all_touched`,
  lagunas 5.472). Agua V29 sobrante: 7.397 vértices. Ojo: `bank_support` de Codex es
  tierra (6,8 km², mediana 2,89 m), no agua.
- `tools/terrain/verify_roads_v30.py`: puerta vial con la definición de Codex
  (`audit_dense_road_sections.py`) y su propio muestreo. Control positivo: V29 PASS en 99
  cadenas y 88.452 estaciones, 0 fallos. Control negativo: el relieve sin renivelar falla.
- `tools/terrain/build_v30.py`: pasos 1–7 escritos. Carreteras todavía en FAIL. Primera
  pasada (perfiles por cadena con cruces fijos): 5.869 fallos transversales, 515 de pendiente
  y 552 de cuerda sobre 75.864 estaciones. Segunda (sistema único + proyección de
  pendiente): 8.894 de pendiente, proyección sin converger. Causa localizada: cadenas que se
  cruzan sin nodo común (84 y 81 en (8781, 9673)) reciben perfiles distintos. Añadido el
  acoplamiento de estaciones a menos de 6 m; la tercera pasada se detuvo porque la
  proyección con `np.add.at` en 20.000 iteraciones es demasiado lenta.
- Siguiente: proyección rápida (barridos por cadena o `np.bincount`), carreteras PASS,
  puertas de agua (calado, orillas), pendientes ≤35°, Narva idéntico y exportar el ASC.

## Resultado de la ejecución autónoma — 02-10, 04:00–06:00

- Fase 2: cerrada. Carreteras como un único QP (ADMM y pulido) con la pendiente reducida en
  curvas, cadenas acopladas y reparación local. Orillas y costa siguen la distancia firmada al
  contorno suave. Un plano por celda, con la misma regla para piezas, terreno y satélite.
  Todas las puertas PASS, incluida la nueva de coherencia con las piezas.
- Fase 3: hecha, 17.715 planos pond. El prototipo de arroyo en el juego quedó sin hacer, porque
  no había pantalla: se usan planos propios y surcos de vértices.
- Fase 4: hecha con los cuatro materiales de V29; los 215 materiales incompletos se rehicieron
  completos. Más superficies, pendiente de decidir.
- Fase 5: paquete `@DayZ_Baltic_V30` derivado del de V29 sin Terrain Builder y probado en el
  juego por funciones. Faltan la navmesh (NavMeshGenerator con Computer Use) y la revisión visual.
- Detalle, pasos y decisiones abiertas: HANDOFF, sección «Resultado de la ejecución autónoma».
  Evidencia en `evidence/terrain-v30-2026-10-02`, `evidence/surface-v30-2026-10-02` y
  `evidence/v30-preview-ingame-2026-10-02`.

## Fase 3 — Piezas de agua V3

Revisión de cobertura del 02-10 por la tarde: el cierre anterior de fase 2
acreditaba puertas genéricas, pero no todo el canal útil entre vértices.
BALTIC-012 (Luga) y BALTIC-013 (delta) reabren esa aceptación geométrica,
sin cambiar las decisiones de producto. Correcciones locales y comprobación
de la misma cobertura vial en `plans/v30-delta-fairways.md`; candidato a84dfff0
con paquete aislado 8b2d404a. Falta su consumidor real y navegación nueva.

Regenerar las piezas desde el diseño de la fase 1, reutilizando el generador actual y
revisando el solape de 2 cm entre losetas. Los arroyos siguen la variante elegida en
el prototipo.

## Fase 4 — Satélite y máscara V2

[DESIGN] `tools/surface/build_surface_v2.py`: satélite a 1 m/px (12.288²) con detalle
procedural y transiciones suaves entre clases, sin bloques de 6 m. El agua se pinta
exactamente donde está el agua de la fase 2, con lecho según la profundidad y franjas
de orilla. La máscara usa más superficies vanilla (`DZ\surfaces\data\terrain`: bosque
caducifolio, coníferas, musgo, tierra, hierba, hierba alta, grava y roca en pendientes
fuertes), con un máximo de materiales por tile compatible con lo que ya funciona (hoy,
cuatro). Antes de producir hay que entender qué provocó las «manchas negras» que Codex
resolvió (canales TerrainX), para no reintroducirlas.

## Fase 5 — Construcción, navmesh y revisión

Importación en Terrain Builder (bloque de Computer Use anunciado y agrupado, o pasos
manuales de Guillermo con lista), exportación y persistencia, paquete con el wrapper
existente, navmesh nueva y prueba de humo: un tramo de lancha, un recorrido en coche y
las consultas de IA. Revisión visual con capturas desde la vista del jugador; la cámara
programada queda fuera mientras BALTIC-001 siga abierto. Guillermo juzga las capturas.

## Reparto y límites

- Diseño, puertas e integración: Claude. Los generadores mecánicos (satélite, piezas)
  pueden delegarse con brief y revisión de otra familia.
- No se modifican V10, V33 ni V29: todo es una versión nueva en carpetas nuevas.
- El relieve cambia según la fase 1a: zonas altas conservadas, llanos y el resto más
  natural. Obliga a volver a nivelar las carreteras y a repetir sus puertas.
