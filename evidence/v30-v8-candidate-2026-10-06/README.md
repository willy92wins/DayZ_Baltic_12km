# Candidato v8: orillas de navegables, ríos y arroyos, y fondo de ríos y arroyos a 1,0 m — 06-10-2026

Sobre la v7d (`../v30-v7-candidate-2026-10-05`, vista en motor en el run f5082893). Es el siguiente frente del orden
acordado: ríos, arroyos y navegables.

Productos en `E:/DayZ-Baltic-Build/v30-v8` (`scripts/chain-v8.sh`). Desplegado como `@DayZ_Baltic_V8Candidate`: mundo
`f6137a05` y agua `c687a7be`, la del v3b sin cambios. Las copias están comprobadas por hash en `reports/deploy-receipt.json`.
Sin ver en motor.

## Qué cambia frente a la v7d

`tools/terrain/profile_rivers_v30.py` (nuevo) da el terreno `54af9940` a partir de la v7d (`ee048e5a`). Lo escribió
GLM-5.3-Flash en el GX10 a partir del encargo `glm-lanes/brief_profile_rivers.py`, y lo revisé antes de usarlo (más
abajo). Es el método de los lagos, con estas diferencias:

- **Nivel por vértice.** El agua que fluye baja en escalones de 0,025 m. El objetivo de un vértice es el nivel del
  vértice más cercano del cauce más 0,15 × la distancia con signo al contorno suavizado. Las puertas van por vértice:
  - agua, por debajo de su nivel − 0,10 y del plano − 0,02;
  - tierra, por encima del nivel del agua más cercana + 0,05, del plano y del suelo de 1,40 m.
- **Ninguna clase ni nivel cambia:** el lado de un vértice es su clase de entrada. Planos, piezas y teselas de agua
  siguen valiendo, y el agua del paquete es la misma.
- **Navegables con los bordes libres.** Solo queda fijo el corredor exacto de 24 m (las caras que tocan su polígono),
  no su margen de un vértice. El agua de un borde puede subir hasta 6 m para llegar a su objetivo; la tierra, 2 m;
  bajar, 1,5 m.
- **Fijo además:** plataformas, reserva y envolvente natural, Narva, el borde del mapa, el mar y el delta, lagos y
  estanques, los tramos por debajo del corte de 0,80 m, los tramos de piezas vanilla R1–R3, todo lo que está a 22 m
  de ellos y los contactos entre dos cauces.
- **Fondo de ríos y arroyos a 1,0 m**, con 0,30 m de agua al menos (`--bed-floor 1.0`): la decisión de los lagos
  aplicada al agua que fluye y no navega. Los navegables conservan el calado.

## Resultado offline (`reports/`)

- **Cauces:** 105 de 158 componentes perfiladas (53 tienen menos de 4 vértices). 70.613 vértices cambiados, 299 en el
  tope de movimiento, 2.287 devueltos por la recuperación de caras y 796 fondos subidos.
- **Desfase del cruce frente al contorno suavizado** (`rivers-report.json`; el comprobador independiente da lo mismo):

  | clase | p50 (m) | p90 (m) | p99 (m) |
  |---|---|---|---|
  | ríos | 1,45 → 0,00 | 3,51 → 1,02 | 5,29 → 3,67 |
  | arroyos | 0,67 → 0,00 | 1,98 → 0,30 | 3,16 → 1,96 |
  | navegables | 1,55 → 0,83 | 3,79 → 3,64 | 5,64 → 5,31 |

- **Fondos por debajo de 0,85 m:** ríos, de 1.487 a 699; arroyos, de 739 a 28; navegables, de 29.921 a 29.007 (el
  calado se conserva).
- **Comprobador independiente** (`scripts/check_profile_rivers.py`, `check-profile-rivers.json`):
  - 0 cambios de clase y de nivel;
  - nada cambiado en plataformas, reserva, Narva, el borde, el corredor exacto ni en agua de mar o estancada;
  - ningún cambio a más de 22 m del agua que fluye; una subida de fondo a menos de 22 m de un tramo vanilla;
  - 3.161 vértices del margen del corredor movidos: los bordes libres.
- **Puertas:**
  - las mismas que la v7d: 6 calados en arroyos, 31 celdas de piezas y Narva por diseño;
  - taludes de orilla de más de 35°: de 3.049 a 2.534;
  - carreteras PASS, idénticas; tramos vanilla idénticos; censo igual (10 lagos colgados y 124 con dique).
- **Agua visible frente al diseño a 0,85 m** (`audit-v8-085.json`):
  - inundado fuera del diseño: de 210.468 a 193.764 m²;
  - huecos secos dentro del diseño: de 36.400 a 46.944 m², casi todos en ríos (+10.200 m²). La orilla deja el escalón,
    que se salía del polígono SIG, y se mete hasta la línea media suavizada.

## Figuras (`figures/`, v7d en rojo y v8 en azul)

- `shore-river-11922-1464.png`: el río sigue el contorno suavizado donde antes hacía escalones.
- `shore-stream-5034-138.png`: los arroyos de un vértice de ancho en diagonal conservan el zigzag. El contorno
  suavizado no puede moverse más de 4 m y el cauce es más estrecho que la rejilla. Es el paso 6 del plan: los arroyos
  estrechos, en una sesión aparte.
- `shore-navigable-930-4650.png`: mejora donde el navegable tiene agua fuera del corredor.
- `shore-luga-6750-4350.png`: en el Luga el corredor exacto ocupa todo el ancho y la orilla casi no cambia. Arreglarla
  pide el contrato de navegación (paso 2): calado y anchura útil.

## Revisión de otra familia

GLM-5.3-Flash escribió la herramienta en el GX10 (lane R1, razonamiento medio, 55 min, 44.139 tokens; `glm-lanes/`, con
su fichero original). La revisé yo (Claude) antes de ejecutarla:

- **F1:** tomaba el corredor con su margen (el segundo valor de `protect_corridors`) en lugar del exacto, y así dejaba
  fijos los bordes que el encargo quería libres. Corregido.
- **F2:** `gate_counts` concatenaba los ángulos 2-D sin aplanarlos, y el autotest se rompía. Corregido.
- **F3:** el docstring y los límites decían que había que reconstruir teselas de agua; esta herramienta no cambia
  clases ni niveles. Corregido.

El resto se ajusta al encargo. Con los arreglos, el autotest pasa y no es vacuo: 3.039 vértices cambiados y el p90 del
río sintético de 1,49 a 0,03 m.

## En motor y lo que marcó Guillermo (06-10, runs ae5e7e32 y 1777a889; `border-trial/shots-manifest.json`)

- **Mejor, pero no bien.** Guillermo vio la vista RIVER_80 en directo: «se ve mejor, pero aún algunos cauces muy
  rectos/poligonales» y «una zona cuadrada parche» fuera del mapa.
- **Dónde cae cada marca** (`general-review/locate_marks.py`, `marks-located.json`):
  - el canal largo de la izquierda es un lago (clase 2) pegado a un río, y el estanque del centro (clase 7) también;
    cada herramienta congela 22 m alrededor del agua del otro tipo, así que nadie los tocó;
  - los cauces quebrados son ríos perfilados (clase 5): lo que se ve es su planta;
  - el parche es el exterior sin textura del borde de tierra este (BALTIC-020).

## Revisión general (`general-review/`)

**Generación:**

- **La planta del diseño, lo principal.** `tools/water/design_water_v3.py:173-178` y `:207-213` hacen la cinta sobre
  la línea OSM remuestreada cada 6 m, sin suavizar. Esas líneas tienen 43 giros de más de 20° por km y 17,6 de más
  de 45° (`centreline-sigma.json`); el perfil de orillas solo mueve la orilla 4 m y hereda la planta: unas 14
  esquinas vivas por km en ríos, arroyos y lagos (`shore-failure-map-v8.png`).
- **El 16 % de la orilla interior no se movió** (25.125 de 157.298 aristas; `shore-failure-census-v8.json`):
  - 9 % por protecciones (envolvente natural 7.000, Narva 2.800, corredores 1.600, borde 1.400, reserva 1.400);
  - 2,5 % por contacto entre agua estancada y que fluye;
  - 4,5 % por otras reglas (cuerpos diminutos, dos cuerpos a menos de 44 m, recuperación de caras).
- **La superficie lo subraya:** fondo oscuro bajo el agua que fluye y franja de grava (`tools/terrain/
  build_surface_v30.py:50,115-117`). Con `--bed-tone depth-all` los cauces someros toman el tono de la tierra
  (`bed-tone-depth-vs-depth-all.png`); los hondos siguen oscuros.

**Revisión (por qué no lo vi):**

- la métrica principal medía el objetivo de la propia herramienta (desfase frente a su contorno suavizado): da
  0,00 por construcción y no ve ni la planta ni lo congelado;
- las ventanas de las figuras se eligieron donde más cambió la herramienta, no donde más defecto queda;
- en motor miré puntos sueltos; en RIVER_80 vi el canal de borde oscuro y no lo investigué;
- el comprobador independiente comprueba invariantes, no calidad, y la revisión del código de GLM era de
  conformidad con un encargo que ya tenía el tope de 4 m y los contactos congelados.

Desde ahora, cada candidato lleva el censo de defectos con mapa, vistas aéreas amplias con 3 min de carga
comparadas con el anterior, y figuras en las peores ventanas.

## Borde exterior (`border-trial/`)

- **Sin síntesis (v8b, mundo 065a9fdd):** fuera del borde de tierra este sigue la franja lisa a los 3 min.
- **Con síntesis, como Chernarus (v8c, mundo e2fc5cc7):** fuera del borde se ve tierra con textura, estable a los
  3 min (`border-v8b-vs-v8c.jpg`); queda una mancha oscura rectangular sobre la línea del borde.
  - El primer intento salió roto (cielo magenta, terreno sin textura) después de que el cliente abriera el menú de
    pausa (`v8c-first-attempt-broken.jpg`); el segundo, sin tocar el cliente, salió bien.
  - El lago 106 (líneas en el v7b) no se pudo ver: un DayZ retail abierto en el equipo bloqueó el MCP.
- `tools/terrain/derive_world_v30.py --outside-terrain [--outside-synth]` y `build_v30_package.ps1
  -OutsideTerrain/-OutsideSynth` dejan la prueba como opción, sin cambiar el paquete por defecto.

## Decisiones de Guillermo (06-10)

- **Planta:** rehacer la cadena entera desde el diseño con las líneas de ríos y arroyos suavizadas (sigma 18 m,
  extremos fijos: de 17,6 a 1,3 giros de más de 45° por km, desplazamiento p95 6,5 m).
- **Borde:** OutsideTerrain; tras el segundo intento, con síntesis.
- **Reserva natural:** sus orillas también se perfilan (±4 m, sin cambiar clases ni niveles).
- `tools/terrain/profile_inland_v30.py` (GLM, lane I1, revisado: un vértice de tierra que una masa deja igual ya no
  anula la bajada que pide otra) hace lagos, estanques, ríos y arroyos en una pasada, sin congelar contactos ni la
  reserva; autotest PASS. Se usará al final de la cadena rehecha.

## Sin verificar

- La v8 entera a la altura del jugador; el lago 106 con OutsideTerrain y síntesis.
- El contrato de navegación (`reports/navigable-draft-table.json`).
- El calado de la `Boat_01_Orange` (`DZ/vehicles/water/config.cpp:162-166`).
