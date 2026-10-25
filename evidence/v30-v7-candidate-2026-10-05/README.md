# Candidato v7: orillas e islas de los lagos, y el fondo de los lagos a 1,0 m — 05-10-2026

Sobre el v6 (`../v30-v6-candidate-2026-10-05`), con dos cambios:

- El fondo de lagos y estanques, que Guillermo decidió el 05-10 tras la prueba de BALTIC-018
  (`../v30-bed-probe-2026-10-05`).
- El siguiente frente del orden acordado: las orillas e islas de los lagos.

Productos en `E:/DayZ-Baltic-Build/v30-v7`. Desplegado como `@DayZ_Baltic_V7Candidate`, con el mundo `44edfd45` y el
agua `c687a7be` del v3b, sin cambios; las copias están comprobadas por hash en `reports/deploy-receipt.json`. Visto en
motor en el run `06e14fcf`, cerrado en orden.

## Qué cambia frente al v6

- **`tools/terrain/profile_lakes_v30.py`** (nuevo) da el terreno `8ee1139f` a partir del v6 (`e07ee373`). Aplica a
  cada lago o estanque el método de `profile_coast_v30.py`, en una ventana alrededor del cuerpo y con su propio nivel.
  - **Contorno:** la distancia con signo al cuerpo, islas incluidas, se suaviza (sigma 12 m) y se limita a 4 m de
    desplazamiento.
  - **Perfil:** los vértices de las aristas que cruzan ese contorno toman `nivel + 0,15 × distancia`. Así la línea de
    agua del motor (triángulos nativos con diagonal NO-SE) pasa por el contorno suavizado.
  - **Lo que respeta:** agua al menos 0,10 m bajo el nivel; tierra al menos 0,05 m por encima del nivel y por encima
    del suelo de 1,40 m; topes de movimiento; nada entre las dos puertas.
  - **Lo que deja fijo:** el mar, el delta, los navegables, ríos y arroyos y sus alrededores; las carreteras, la
    reserva natural, Narva, el borde del mapa y los contactos entre dos cuerpos.
  - **Ninguna clase cambia de lado:** el desplazamiento de 4 m es menor que la rejilla de 6 m. Clases y niveles quedan
    idénticos al v6, y las teselas de agua del v3b siguen valiendo; las celdas de plano distintas son 0.
  - **Fondo de 1,0 m** (`--bed-floor 1.0 --bed-min-depth 0.30`): sube el fondo de todos los cuerpos perfilados, salvo
    en los corredores navegables y en Narva.
- **Superficie:** `build_surface_v30.py --bed-tone depth` (nuevo). Bajo el agua estancada mezcla el color de la tierra
  (hasta 0,3 m de agua) con el fondo oscuro (desde 1,2 m). Con el fondo subido, el modo `land` del v6 habría pintado
  lagos enteros del color de la tierra. El modo `land` sigue igual byte a byte (4 de 4 ficheros comparados).
- **El resto de la cadena** es la del v6 (`chain-v7.sh`). Las teselas de agua no se parchean porque no hay celdas que
  cambien. Tampoco podrían: `patch_water_tiles_v30.py` no conoce las 99 piezas de cauce del piloto, que no tienen
  `origin`.

## Resultado offline (`reports/`)

- **Lagos** (`lakes-report.json`):
  - 623 de 624 cuerpos perfilados; el que falta está por debajo del corte de 0,80 m, donde el agua la pone el mar.
  - 40.899 vértices de orilla ajustados y 287.564 fondos subidos (hasta 7,57 m, en el lago 106).
  - 54 vértices quedaron en el tope de movimiento; la recuperación de caras deshizo 98.
  - Fondos de agua estancada bajo 0,85 m: de 287.813 a 1.155. Quedan los corredores navegables, Narva y estanques
    con el agua a menos de 1,15 m.
- **Ajuste al contorno suavizado** (distancia entre el cruce del terreno y el del contorno, en 54.957 aristas):
  - p50 / p90 / p99 de 0,80 / 2,57 / 4,63 m a 0,00 / 1,22 / 3,99 m;
  - el 0,00 sale así por construcción donde los dos extremos de la arista toman el objetivo; el resto mide dónde
    interfieren vértices fijos, topes y el fondo mínimo.
- **El giro de la línea de agua por cada 12 m no sirve para esto:** sube de p50 14,7° a 18,4°, porque redondear un
  escalón reparte el giro. Lo que se ve está en `figures/shore-259-plot.png`: en el v6 (rojo) las islas tienen picos
  y en el v7 (azul) siguen el contorno suavizado (verde). En `figures/shore-202-plot.png`, la orilla de ese lago ya
  era suave en el v6.
- **Comprobador independiente** (`scripts/check_profile_lakes.py`, `check-profile-lakes.json`):
  - 0 cambios de clase y ningún vértice cambiado a más de 22 m del agua estancada;
  - los cambios en el borde del mapa (2.049) y en la reserva de carretera (5) son subidas de fondo bajo el agua;
  - quedan 2 vértices bajo el suelo de fondo.
- **Puertas:**
  - `verify_terrain_v30.py`: los mismos fallos conocidos que el v6 (6 calados en arroyos, 31 celdas de piezas, Narva
    por diseño); taludes de orilla de más de 35°: 3.049, frente a 3.051;
  - carreteras PASS, idénticas; cauces idénticos;
  - censo: 10 lagos colgados, como el v6; lagos con dique, de 156 a 124.
- **Agua visible frente al diseño a 0,85 m:**
  - inundado fuera del diseño: 210.468 m², frente a 211.788;
  - huecos secos dentro del diseño: 36.400 m², frente a 32.540. Son unos 3.860 m², sobre todo en estanques, donde la
    orilla suavizada se aparta del polígono SIG.
- **Contraste con otra implementación:** GLM-5.3-Flash escribió por su cuenta la misma herramienta (lane B3, razonamiento
  medio, 36 min; su fichero, informe y encargo en `glm-lanes/`).
  - Coincide con esta en 326.628 de 328.054 vértices cambiados, con las mismas clases y niveles.
  - Difiere en 1.426, por reglas distintas de qué queda fijo.
  - La suya añade 7 celdas de piezas y 1 orilla por debajo del nivel a las puertas; esta no añade ninguna.
  - Las lanes B1 y B2, con razonamiento máximo y el mismo encargo, generaron lo mismo byte a byte, porque el GX10 es
    determinista. B1 agotó los 120.000 tokens razonando y se cortó al empezar el fichero, a los 73 minutos
    (`glm-lanes/B1_EXIT.json`). B2 se canceló.

## En motor (`runtime/shots-manifest.json`, `figures/v7-lagos.jpg`, `figures/v7-islas.jpg`)

Captura tras 30–90 s en cada pose, para que cargue la textura (BALTIC-019).

- **Peipus y lago 202 desde 330 m:** agua uniforme, sin las bandas del v6 ni las del lago 202 sin tocar en el run de la
  prueba. Orillas redondeadas.
- **Islas del lago 259 desde 60 y desde 10 m:** orillas redondeadas, sin puntas.
- **Lago 106, con 0,43 m de agua:** desde 330 y 40 m se ve como agua, con oleaje. El fondo en tono tierra apenas
  asoma, en motas sueltas.
- **LHIGH desde 80 m:** tierra verde y con textura a los 90 s, sin la «frontera».

## Revisión de otra familia

GLM-5.3-Flash en el GX10 revisó `profile_lakes_v30.py` (`review-glm-lakes/`; razonamiento medio, 32 min). Veredicto:
aceptar con arreglos. Hay dos hallazgos menores con citas exactas, y comprobó sin hallazgos las ventanas, los signos,
las aristas, el conteo de reclamaciones y la máscara del fondo.

- **F1** (el ajuste de la zona muerta escribía el valor exacto de la puerta, que tras float32 podía quedar del lado
  malo, y podía saltarse el tope de movimiento): solo ocurre si la entrada ya rompe una puerta. Ahora ajusta con un
  margen de 0,1 mm y vuelve a aplicar el tope.
- **F2** (el margen de 22 m no rodea carreteras, reserva natural ni borde del mapa): es lo que se buscaba. El docstring
  lo dice ahora con precisión.

Con los dos arreglos, el autotest pasa y el terreno sale idéntico (`8ee1139f`).

## El recuadro del borde del mapa y la v7d (05-10, 22–23 h, `border-fix/`)

Guillermo señaló un recuadro claro junto al borde este en la vista del lago 202 (`border-fix/l202-v7-rectangle.jpg`).

- **No es agua nuestra:** las piezas de la última columna (`edge_13320`) terminan en x = 12282, el último vértice
  (`border-fix/pieces_near.py`).
- **Causa:** el fondo subido en el borde.
  - Proyectado con el modelo de cámara, el recuadro cae en x = 12240–12340, z = 742–836.
  - Ese tramo del borde este (z = 252–990) es donde el fondo del lago 202 pasó de estar bajo el mar a estar a 1,0 m.
  - En el mapa hay unos 1.000 vértices de borde así: lagos 202, 106 y Peipus.
  - Fuera del mapa, el motor continúa el terreno desde el borde. Con el borde bajo el mar, el mar lo tapaba, como en
    el v6; con el borde a 1,0 m queda por encima y se dibuja liso, sin textura.
- **Arreglo:** el suelo de fondo deja fuera la franja de dos vértices del borde (`profile_lakes_v30.py`).
  - Terreno `ee048e5a`: ningún vértice de borde queda ya por encima de 0,85 m.
  - Difiere del v7 en 2.049 vértices.
  - Puertas como el v7, 0 cambios de clase.
- **`OutsideTerrain` de Chernarus, probado y descartado:**
  - **Con `enableTerrainSynth=1`** (v7b, run 828a1837): el recuadro desaparece, pero salen líneas horizontales y
    cuadros sobre el lago 106 que en el v7 no estaban (`border-fix/l106-v7-vs-v7b-synth.jpg`).
  - **Con la síntesis apagada** (v7c, run 1ac013d7): el lago 106 sale limpio (`border-fix/l106-v7c-no-lines.jpg`).
    En el lago 202, en cambio, salen líneas sobre el agua y sobre la tierra, y una orilla recta extraña a distancia
    (`border-fix/l202-v7-vs-v7c-outside.jpg`).
  - `derive_world_v30.py` sigue sin `OutsideTerrain`.
- **v7d** = solo el arreglo del borde, sin `OutsideTerrain`.
  - Mundo `4897a2e1` + agua `c687a7be`, desplegado como `@DayZ_Baltic_V7dCandidate` (`border-fix/build-receipt-v7d.json`).
  - **Vista en motor el 06-10** (run f5082893, `border-fix/shots-manifest-v7d.json`):
    - en el lago 202 ya no está el recuadro; fuera del borde sigue el mar del motor (`border-fix/l202-v7-vs-v7d.jpg`);
    - en el lago 106 tampoco está la franja clara (`border-fix/l106-v7-vs-v7d.jpg`);
    - a 0,8–1 km sobre el lago 106 salieron rayas oscuras, y manchas en su orilla, que dos minutos después ya no
      estaban, con algo más de bruma (`border-fix/l106-v7d-streaks-gone-after-3min.jpg`). Encaja con la carga de
      texturas (BALTIC-019) y deja en duda que las líneas del v7b vinieran de la síntesis de `OutsideTerrain`: allí
      no se repitió la captura.
  - La v7d sustituye al v7.

## Navegables desde el aire (v7d, run f5082893)

El Luga desde 330 m (`border-fix/luga-v7d-navigable-bands.jpg`):

- orillas serradas, el siguiente frente (v8);
- una mancha gris lisa de bordes rectos sobre el cauce, en x ≈ 6620–6640, z ≈ 4750–4800, con el fondo entre −1,9 y
  −3,2 m: el mar del motor bajo un fondo hondo, como las bandas de BALTIC-018 en los lagos. Con el calado de 3,05 m
  ningún fondo navegable puede quedar por encima de 0,85 m; lo decide el contrato de navegación.

## Sin verificar

- Las orillas a la altura del jugador fuera del lago 259.
- Fuera de los bordes de tierra (este, z = 1500–9750), el exterior se dibuja sin textura desde el v4. Nadie lo ha
  señalado, y la solución vanilla (`OutsideTerrain`) empeora este mapa.
