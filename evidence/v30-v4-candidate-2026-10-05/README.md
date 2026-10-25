# Candidato v4: perfil de costa y oleaje de ±0,10 m — 05-10-2026, madrugada

Sale de la validación del mar (`../v30-tide-swell-2026-10-04`) y de la prueba offline del perfil de costa
(`../v30-coast-profile-try-2026-10-04`). Productos en `E:/DayZ-Baltic-Build/v30-v4`. Desplegado como
`@DayZ_Baltic_V4Candidate` (mundo `a4f33e02…`, agua `c687a7be…`, la misma del v3; copias comprobadas por hash en
`reports/deploy-receipt.json`) y visto en el run 786a1a2d con la misión `BalticTideProbeV2`.

## Resultado en una frase

El oleaje de ±0,10 m funciona en el motor y la costa sale sin dientes. El oscurecimiento no desaparece porque no
depende de que el suelo sea plano: el motor sombrea en manchas la tierra de 1,40 a 1,50 m, y el microrrelieve la
dejó justo ahí.

## Qué cambia frente al v3b

- **Costa del mar y del delta:** `tools/terrain/profile_coast_v30.py`, con los parámetros por defecto, sobre el
  terreno de orillas del v3b (`fac76aea`). Resultado `3f889c85…`, el mismo hash que la prueba offline y con la
  herramienta del commit 4f57cda.
- **Oleaje:** el paquete se construye con el `build_v30_package.ps1` del worktree. Su `derive_world_v30.py` escribe
  `MaxTide=1.5;` y `MaxWave=0.1;`, comprobado también en los floats del `config.bin` binarizado.
- **Lo demás no cambia:** el parche de agua, las piezas y el ajuste de orillas del v3b, porque sus entradas y
  argumentos no cambian (`-Pieces` reutiliza el agua del v3b).
- **Fuera:** el calado relajado de 0,03 m. Rompe la puerta de 0,10 m y el plan lo deja fuera de 1.0.

`chain-v4.sh` lleva los comandos exactos. Se ejecutó en serie y con prioridad baja, porque la caja tenía otra prueba
de DayZ y unos 2 GB de memoria libres.

## Puertas (offline)

- **`verify_terrain_v30.py`, corte 0,51:** los mismos fallos que el v3b: 6 calados en arroyos, 31 celdas de piezas y
  Narva distinto por diseño.
  - Playa: de 2.679 a 3.525 vértices, 0 por debajo de 0,80 m.
  - Taludes de orilla de más de 35°: de 3.122 a 3.101.
- **Carreteras:** PASS, con los mismos máximos del v3b.
- **Cauces (`verify_channel_reaches_v30.py`):** idénticos al v3b.
- **Lagos colgados:** de 624 masas siguen 11 colgadas; las de dique pasan de 168 a 162.
- **Agua visible** (`reports/audit-visible-water-summary.json`): la auditoría compara con la máscara del mar v33, no
  con el contorno que sigue el perfil.
  - No mide lo serrado: el desfase de la línea de agua (p90 de 12 m, en celdas de 2 m) es igual en los dos.
  - «Inundado por el mar» sube de 33.314 a 41.519 píxeles de 4 m² a 0,85 m, y de 28.839 a 34.141 a 0,65 m. Es la
    playa en pendiente, que el oleaje sube.

## Vistas en motor (run 786a1a2d)

13 poses de `../v30-tide-swell-2026-10-04/tide-poses.json`, en ráfagas de 10–11 frames que cubren un periodo, y 5
vistas de costa de cerca (`coast-closeup-poses.json`). Cerrado en orden, con línea de terminación en cliente y
servidor.

- **Oleaje verificado en el motor:** fila `CFG;0.65;0.85;0.1`. El ajuste sobre 2.348 filas da periodo 12,51 s,
  amplitud 0,0986 m y media 0,7499 m (`runtime/view-786a1a2d/swell-levels.json`).
- **Costa:** en las cinco vistas de cerca la orilla es una curva continua con su línea de espuma, sin dientes
  (`figures/coast-closeups-v4.jpg`). No hay vista del v3 con las mismas poses para comparar.
- **Oscurecimiento:** el criterio de variación ≤ 0,02 por ráfaga no se cumple; lo pasan 5 de 13 poses
  (`flat-darkening-*.json`).
  - Restringido a los antiguos llanos que siguen siendo tierra ≥ 1,40 m fuera de la franja de costa
    (`flat-darkening-kept-*`), FLAT2 de cerca baja de 0,25 a 0,008. Lo de antes era agua y franja reperfilada dentro
    de la máscara.
  - De lejos sigue: EDGE1 0,08 (en el v3, 0,170 con el oleaje por defecto y 0,138 con ±0,05), FLAT2 0,06, FLAT3
    0,04, FLAT4 0,03 y FLAT4 de cerca 0,06.
  - FLAT1 de lejos baja de 0,074–0,076 a 0,022–0,027, y FLAT1 de cerca queda en 0,011–0,016 (0,138 en el v3 con
    el oleaje por defecto).
- **Qué parpadea** (`tools/playtest/flicker_by_height_v30.py`, `runtime/view-786a1a2d/flicker-by-height.txt`): el
  cambio de brillo de cada píxel, agrupado por la altura del terreno que ve.
  - **Tierra de 1,40 a 1,50 m, en frames sueltos y sin seguir al nivel del mar.** En FLAT4 de cerca: +5,7 a
    1,40–1,42 m, +3,7 a 1,42–1,45 m, +2,2 a 1,45–1,50 m y 0 por encima de 1,50 m. En EDGE1: −5,8 y −5,3 a 1,40–1,45 m.
    La vegetación no cambia; solo el suelo, en manchas de borde suave (`figures/flicker-diff-*.jpg`).
  - **La playa nueva (0,8–1,2 m) sigue al oleaje,** con ±10 a ±35 de brillo según la fase. Es el lavado de la ola.
  - **Las capturas del 04-10 cuadran** (`runtime/flicker-by-height-04-10-*`). Con el oleaje por defecto, FLAT1 de
    cerca se oscurece de −19 a −28 a 1,35–1,50 m (los llanos de 1,40 m caen en el bin 1,35–1,40) con el mar a
    0,98–0,99, y −6,6 a 1,50–1,55 m. Con `MaxWave=0.05`, FLAT1 de cerca no cambia, pero EDGE1 parpadea a 1,35–1,45 m.
- **Por qué el microrrelieve no bastó:** lleva los llanos a 1,40–1,52 m, dentro de la franja. En el v4 hay 146.283
  vértices de tierra (527 ha) entre 1,40 y 1,50 m; solo 7.847 están fijos (5.513 en la zona de Narva).

## Condiciones de la captura, distintas del 04-10

- **Ventana de 1273×701 px** en un monitor secundario (x = −1408), aunque se pidió 1920×1080.
  - El FOV vertical, recalibrado con EDGE1 (`scripts/fov_calibrate_v4.py`), sale de 66–67°, con un error mediano de
    0,35–0,54 m. Conservar el FOV horizontal daría 67,4°.
  - Las medidas se dan con 67,4° y 68,5°. Las conclusiones no cambian.
- **Menú de pausa** de DayZ encima de todas las capturas. Es estático, así que no cambia la variación dentro de una
  ráfaga.
- **Texturas que no cargan:** cielo morado y vegetación de suelo blanca «en bloques». La máquina tenía unos 2 GB de
  memoria libres. Estas vistas no sirven para juzgar el aspecto; sí para medir.

## Sin verificar

- El mecanismo de la franja de 1,40–1,50 m: el motor no lo documenta y la medida no lo nombra. Sí se ve que el techo
  sube con el oleaje: 1,50 m con ±0,10 y unos 1,55 m con ±0,25.
- El aspecto de la costa con texturas completas y ventana de 1920×1080.
- Ríos, lagos e islotes interiores: siguen con el ajuste del v3b.

## Siguiente (pendiente de Guillermo)

Subir el suelo de la tierra de 1,40 a 1,60 m fuera de playas y taludes de costa: la tierra libre por debajo de
1,60 m, unos 184.000 vértices, sube como mucho 0,20 m, y el microrrelieve se aplica sobre 1,60 m. Los vértices fijos
de la franja quedan como están: carreteras, Narva, bordes de estanque, reservas y corredores. Después, las mismas
ráfagas, con la caja descargada y la ventana a 1920×1080.
