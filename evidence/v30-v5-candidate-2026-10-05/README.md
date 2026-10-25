# Candidato v5: suelo de la tierra a 1,60 m — 05-10-2026

Decisión de Guillermo (05-10) tras el v4 (`../v30-v4-candidate-2026-10-05`). El motor sombrea a ratos la tierra de
1,40 a 1,50 m, y hasta 1,55 m con el oleaje por defecto, así que la tierra sube a 1,60 m fuera de playas y taludes
de costa. Productos en `E:/DayZ-Baltic-Build/v30-v5`. Desplegado como `@DayZ_Baltic_V5Candidate` (mundo `8c523be2…`,
agua `c687a7be…`, la del v3b; copias comprobadas por hash en `reports/deploy-receipt.json`). Visto en motor en el run
`6d727dd7` (misión BalticTideProbeV2), cerrado en orden.

## Qué cambia frente al v4

- **`tools/terrain/profile_coast_v30.py --floor 1.60 --raise-land`**, sobre el mismo terreno de orillas v3b
  (`fac76aea`). El resultado es el terreno `62b162cb…`.
  - `--raise-land`: la tierra libre por debajo de `--floor`, fuera de la franja de costa, sube hasta él antes de la
    comprobación de taludes. El microrrelieve (hasta 0,12 m) va encima.
  - La máscara de playa y la comprobación de suelo usan ahora el suelo del verificador, 1,40 m
    (`verify_terrain_v30.py:30`), no `--floor`.
  - Con los parámetros por defecto la herramienta da exactamente el terreno del v4, `3f889c85`.
- **El resto de la cadena** es la del v4 (`chain-v5.sh`): puertas, superficie, paquete del worktree con `MaxWave=0.1`
  y las piezas de agua del v3b.

## Resultado offline (`reports/`)

- **Subida:** 172.853 vértices suben a 1,60 m, con 173.520 en microrrelieve. El cambio es de 0,23 m de mediana y
  0,27 m en p90; la comprobación de taludes revierte 88.
- **Tierra que queda entre 1,40 y 1,60 m:**
  - 12.089 vértices fijos: carreteras, Narva, bordes de estanque, reservas y corredores;
  - 974 en la franja de costa (el talud);
  - 68 libres, devueltos por la comprobación de taludes.
  - En el v4 había 146.283 solo entre 1,40 y 1,50 m.
- **Línea de agua:** igual que en el v4. Desfase frente al contorno, p50 0,00 m y p90 1,58 m; giro cada 12 m, p50 6,2°.
- **Puertas:**
  - `verify_terrain_v30.py`: igual que el v4 (6 calados en arroyos, 31 celdas de piezas, Narva por diseño). Taludes de
    orilla de más de 35°: de 3.101 a 3.092.
  - Carreteras: PASS, con los mismos máximos.
  - Cauces: idénticos.
- **Agua visible a 0,85 m:** como el v4, con 41.498 píxeles inundados por el mar frente a 41.519.
- **Lagos colgados:** de 11 a 10. Los de dique pasan de 162 a 156, porque al subir el entorno los diques sobresalen
  menos.

## En motor (`runtime/view-6d727dd7/`)

Cliente a 1920×1080, sin menú de pausa y con texturas completas. Las 13 poses de
`../v30-tide-swell-2026-10-04/tide-poses.json` van en ráfagas de 10 capturas (130, todas a 1920×1080, FOV vertical
68,5°). El nivel del mar de cada captura sale del registro de la sonda (`swell-levels.json`): oleaje de 0,65 a 0,85 m,
periodo de 12,49 s, amplitud de 0,0994 m y residuo del reloj p95 de 1,4 ms.

- **Llanos levantados a 1,60 m** (`flat-darkening-160.json`). Cada frame da el cociente entre la tierra a 1,60 m y la
  de 1,62–1,80 m; se mide la variación dentro de cada ráfaga.
  - 10 de 13 ráfagas quedan en ≤ 0,02, todas ellas por debajo de 0,011. FLAT4 de cerca baja de 0,064 en el v4 a
    0,001; EDGE1 de 0,079 a 0,0008.
  - FLAT1 de lejos da 0,0225, como en el v4 (0,0218).
  - EDGE1 doble da 0,039 por un solo frame en el valle del oleaje (0,651 m).
  - CONTROL de cerca da 0,074 por un frame con el mar a 0,841 m. Esa pose mira al tramo sur del dique de Kronstadt,
    con agua a los dos lados.
- **Tierra de 1,60 a 2,2 m frente a la de 2,2 m o más** (`flicker-by-height.json`, columna `ref`).
  - En 8 de las 10 poses con referencia ningún frame se aparta más de 1.
  - EDGE1 de cerca se aparta 1,1 y 1,3; en esa ráfaga cambia todo el encuadre (la referencia va de +3,5 a −1,1).
  - CONTROL de cerca se aparta 3,9: es el dique.
  - FLAT2, FLAT3 y FLAT4 de cerca no tienen tierra de 2,2 m en el encuadre; para ellas vale la medida anterior.
- **Lo que sigue oscureciéndose** es el talud de costa entre la playa y el suelo, de 1,35 a 1,55 m. Con el mar alto
  baja frente a la tierra de 1,60–1,80 m:
  - FLAT2 de cerca, mar a 0,83 m: −20,8 a 1,35–1,40 m, −17,4 a 1,40–1,42 m, −12,9 a 1,42–1,45 m y −2,4 a 1,50–1,55 m;
  - FLAT3 de cerca, mar a 0,82 m: −10,4, −6,2 y −3,2 en los mismos tres primeros tramos.
  - Es una franja estrecha pegada a la playa. La playa de 0,8 a 1,2 m sigue al oleaje: es el lavado de la ola.
- **Costa de cerca** (`figures/v5-costa-de-cerca.jpg`, las cinco poses de
  `../v30-v4-candidate-2026-10-05/coast-closeup-poses.json`): orilla continua con playa y espuma, sin dientes.
  - Se capturaron con la ventana a 1273×701, porque Guillermo la había movido; son solo visuales.

## Bordes puntiagudos (señalados por Guillermo el 05-10)

Números en `reports/edges-v5.json`, de `scripts/edges_v5_numbers.py`.

- **Fotos 2 y 3: el dique de Kronstadt, tramo este** (de Kotlin a la orilla norte). Mismo contorno escalonado en el
  v5, a 30 y 80 m (`figures/v5-bordes.jpg`).
  - Sus 225 celdas de tierra son plataforma, y 215 además reserva. `profile_coast_v30.py:128` deja fijas las dos cosas,
    así que el contorno es el de la máscara a 6 m: 2 a 4 celdas de ancho (12 a 24 m), en escalones.
  - La cresta está a 1,45–1,53 m (p5–p95), dentro de la franja que el motor oscurece.
  - Tierra de plataforma o reserva en contacto con agua: 13,3 km medidos en escalones.
- **Foto 1: la isla no se ha localizado en el terreno v5.** Revisadas sus islas y los bajos de los lagos, no he
  encontrado una con esa forma.
  - Las islas del mar quedaron suaves: la del golfo, en (1365, 10554), sale redonda vista desde 330 m.
  - El perfil solo edita el mar y el delta: 37 de unos 600 km de orilla medidos en escalones.
  - Lagos, ríos, arroyos y sus islas conservan el ajuste v3b, con escalones de 6 m y puntas: es el «ríos e islotes,
    pendientes» de BALTIC-007.
- **Nuevo (BALTIC-018): agua del lago 269 partida en bandas vista desde el aire.**
  - Desde 330 y 40 m aparecen zonas de agua plana y parda con bordes rectos o en dientes, junto a agua oscura con
    oleaje.
  - A 3,4 m sobre el agua el lago se ve uniforme.
  - En (310, 740) el servidor da agua a 2,65 m, y el rayo llega al fondo a 0,71 m.
  - 324.155 de las 382.745 celdas de agua interior tienen el fondo por debajo de 0,85 m: el mar del motor pasa por
    debajo de los lagos.
  - Causa sin identificar.

## Sin verificar

- La causa de las bandas del agua de los lagos y si siguen las teselas de agua de 48 m (`pieces.json`, `tile_m` 48).
- Dónde se sacó la foto 1.
- Los 12.089 vértices fijos que siguen en 1,40–1,60 m, aparte del dique: carreteras y Narva sin poses propias.
