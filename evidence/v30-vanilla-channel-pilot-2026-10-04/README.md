# Piloto de cauces con piezas vanilla inclinadas — 04-10-2026 (BALTIC-015)

Plan: `plans/v30-vanilla-channel-water-pilot.md`, aprobado por Guillermo el 03-10 por la noche.
Ejecutor: Claude. Herramientas: `tools/water/vanilla_channel_pieces.py`, `tools/water/fit_channel_pieces_v30.py`,
`tools/playtest/prepare_vanilla_channel_readback.py`, `tools/playtest/verify_vanilla_channel_readback.py` y
`tools/navigation/prepare_vanilla_channel_boat.py`. Productos pesados en `E:/DayZ-Baltic-Build/v30-vanilla-channel-pilot`.

## Identidades

| Artefacto | Ruta | SHA-256 |
|---|---|---|
| Terreno piloto | `E:/.../v30-vanilla-channel-pilot/fit/terrain_pilot.npz` | 1807d824e74e04d6… |
| Agua del piloto | `E:/.../fit/water/pieces.json` | 024d385062cae93f… |
| Mundo | `E:/.../package/out/Addons/narva_trial.pbo` | 3e7987bed29ae39d031dc54627f7b8db718c6d3758e741ff5300d22898a937f1 |
| PBO de agua | `E:/.../package/out/Addons/baltic_water_v30.pbo` | e56aa9f1ae1c9d3d1f2f385a0b6ac53e47bad95c2f1a3435a01203d173d49a51 |

El mod `@DayZ_Baltic_CauceVanillaPilot` lleva los dos PBO, comprobados por hash tras copiarlos. Las misiones
`BalticVanillaChannelPilotV1.BalticTrial` y `BalticVanillaChannelBoatV1.BalticTrial` están desplegadas idénticas a
las del repo. Base: terreno d5dadae8 y agua deduplicada 339fa17f.

## Resultados

| Paso | Fichero | Resultado |
|---|---|---|
| Biblioteca | `library.json` | 14 piezas. El gate previsto falla: solo el 13,8 % de las juntas de río y el 12,6 % de las de arroyo encajan a ≤0,5 m y ≤2°. La causa es que vanilla desplaza las piezas de lado en las juntas (p10/p90 de ±3,4 a 4,1 m). Los marcos son coherentes: −4,4 cm de mediana a lo largo del cauce y 0,13°/0,27° de rumbo |
| Ajuste | `fit-report.json` | FAIL por defectos locales. R1: 29 celdas sin cubrir, que siguen con planos horizontales, 15 vértices mojados sin cubrir y 1 al aire (−0,17 m). R2: 1 vértice al aire (−0,02 m) y una junta de 0,22 m, mayor que el faldón. R3: juntas de 0,16 y 0,10 m. Terreno: 495 vértices bajan (máximo 0,21 m), ninguno sube, todos de cauce. Agua: 309 piezas horizontales afectadas, 13 recortadas, 296 retiradas y 5 astillas |
| Paquete | `package-diff-*.json` | En el mundo solo cambian el WRP, `texHeaders.bin` y 16 texturas de capa. En el agua, las 8.776 entradas originales son idénticas y se añaden 13 modelos recortados |
| Lancha R1 | `boat/verification.json` | PASS en los dos sentidos (run e5ccbe6a). Pasillo máximo 3,24 y 2,89 m, error de suelo 0,1 mm, propulsión continua 134,5 y 137,1 s |
| Lectura | `readback/verification.json` | Piezas 100/100: posición ≤0,65 mm, dirección y vector arriba ≤4,4e-5°, escala ≤5e-6 (run 8392533a). Agua FAIL: residual mediano de 0,3 mm en R1, 1,5 cm en R2 y 10 cm en R3. Hay saltos de hasta 12 m donde el motor devuelve el nivel del mar (0,54 m, es decir, sin agua) dentro de la huella. Muestras de orilla que deberían estar mojadas y salen sin calado: 35 en R1, 55 en R2 y 7 en R3 |
| Banco | `readback/verification.json` | Pieza plana, escala 1: la lámina coincide en la parte plana. Piezas inclinadas: la pendiente coincide, pero la lámina queda por encima de la malla, +6 cm (2°, escala 1) y +1,5 cm (1°, escala 2). El motor no hunde el faldón del extremo +z. A escala 0,5, parte de la huella sale sin agua |
| Control negativo | `control/verification.json` | Paquete actual (run bfb265e3): 0/100 piezas, como se esperaba. Residual frente a la lámina prevista: 2,1 cm en R1, 3,2 cm en R2 y 8,2 cm en R3 |
| Capturas | `readback-v2/shots-manifest.json` | 04-10: piloto 19/19 (run 63008090) y control 13/19 (run 337562e3, cortado por un reinicio del PC). Revisión visual pendiente. El 03-10 no se hicieron porque se cerró el cliente |

## Lectura

- El motor respeta la matriz del WRP `[derecha, arriba, adelante, posición]` y la escala uniforme.
- La lancha navega sobre `river_24` inclinado y a escala 3,3–4 (agua roadway).
- **Diagnosticado (sección siguiente):** el desfase, los huecos y el faldón +z «sin hundir» salen de cómo el motor
  resuelve el agua roadway y de la sonda V1, que consultaba desde suelo + 50 m. A alturas de juego no hay huecos
  previstos.

## Diagnóstico del agua del motor — 04-10, 01:00

`tools/water/engine_water_model.py` reproduce 1.940 de las 1.941 filas del run 8392533a a ≤2 mm
(`diagnosis/engine-rule-vs-run-8392533a.json`). La regla para las caras de agua del roadway:

1. Son candidatas las caras cuya caja xz en el mundo contiene el punto de consulta.
2. El punto pasa al espacio del modelo con su altura, a través de la transformación completa del objeto.
3. La cara cuenta si ese punto cae dentro de ella en xz del modelo.
4. El nivel es la `y` del primer vértice de la cara, horizontal en el modelo, devuelto como la `y` en el mundo de
   (lx, y₀, lz). Entre varios objetos gana el más alto.

Consecuencias:

- En una pieza inclinada, una consulta hecha a Δy de la lámina lee el nivel desplazado Δy·sen θ a lo largo de la
  pieza. Desde 50 m: +6,0 cm a 2° y +1,5 cm a 1°; el error es ≈ Δy·θ² y no depende de la escala. Cerca de los
  bordes de cara se pierde el agua: esos son los huecos del banco y de los tramos.
- Faldones de las rectas: el −z lee su fondo (primer vértice a −0,07 m) y el +z el nivel plano (primer vértice a
  +0,07 m). Chernarus usa las mismas piezas, así que tiene el mismo comportamiento (no medido aparte).
- A alturas de juego (casco a lámina + 0,05 m, cuerpo a lámina − 1 m) el modelo prevé cero huecos en los tres
  tramos. La parte plana queda a ≤1 cm en el 96,5 % de las muestras de R1, el 87,8 % de R2 y el 83,9 % de R3; el
  resto, hasta 13 cm, son juntas donde el nivel de la pieza vecina queda por encima. En los faldones la diferencia
  es de ±0,07·escala.
- Segunda altura de control (calado a suelo + 0,01 m, no usada para deducir la regla): residual medio entre
  −0,0002 y −0,0097 m, con desviación de 0,055 m por las olas.

Hipótesis descartadas:

| Hipótesis | Prueba |
|---|---|
| El roadway difiere del LOD visual | idénticos vértice a vértice en `river_24_24` y `stream_14_24` |
| Selección por el polígono exacto proyectado | falla en 137 casos de R2/R3 con piezas solapadas y guiñada distinta de 0 |
| Selección solo en espacio del modelo | falla en PAD1 dz −10 (21 filas) |
| Cercanía a una frontera de cara | aceptados y rechazados van de 0 a 3 m |
| Gana la más cercana en unidades del modelo | 241 desacuerdos; el máximo acierta en todos menos uno |

Sin explicar: R1 s=228,02 m, offset 30,5 m. El motor da el nivel inferior de dos piezas solapadas; las filas
vecinas siguen el máximo.

Defecto real del ajuste: en la mitad de R1 colocada a tope, con rectas sin solape y giros de hasta 46,8°, quedan
huecos en las curvas. En s≈122–128 m el motor solo ve el mar a 0,525 m sobre un lecho a −5 m, y eso es lo que
dejó pasar a la lancha. Con solo rectas hace falta solape.

Preparado y sin ejecutar: lectura V2 a alturas de juego, con la predicción congelada antes del run. Misión
`BalticVanillaChannelPilotV2.BalticTrial` (`init.c` b2b90ae0dda4f58a…, linter PASS, desplegada) y referencia
`E:/.../readback-reference-v2.json` (615.757 bytes). Irá en el mismo run que las capturas; a las 01:10 el DayZ
MCP estaba ocupado por la sesión de H2R.

## Lectura V2 a alturas de juego y capturas — 04-10, 02:15–02:45

Misión `BalticVanillaChannelPilotV2.BalticTrial` (`init.c` b2b90ae0…), con la predicción del modelo congelada en
`readback-v2/reference.json` antes de ejecutar. Consultas a casco (lámina + 0,05 m) y a cuerpo (lámina − 1 m).

| Run | Paquete | Piezas | Concordancia con el modelo | Huecos a casco | Capturas |
|---|---|---|---|---|---|
| b295208e | piloto | 100/100 | R2 614/614, R3 387/387, R1 99,65 %, banco 100 % | 0 en tramos; 3 en el banco, previstos | 3 (cliente cerrado a las 02:21) |
| 63008090 | piloto | 100/100 | idéntica | idéntica | 19/19 y una repetida |
| 337562e3 | actual (control) | 0/100, como se esperaba | baja: no hay piezas vanilla | 7 en R2: los planos escalonados dejan agujeros | 13/19 (reinicio del PC) |

- El gate formal `no_hull_holes` sale FAIL por los 3 puntos del banco, que el modelo había previsto antes del run.
  No se relajó: en los tres tramos hay 0 huecos.
- Residual a casco frente a la malla visual: igual que el previsto. Parte plana ≤1 cm en el 96,5 % (R1), 87,8 % (R2)
  y 83,9 % (R3); faldones ±0,07·escala.
- El cliente del primer run se cerró a las 02:21:17 sin volcado de fallo y con entrada humana 40 s antes. El
  reenganche `mode=client` pidió `takeover`, así que se relanzó el run completo (63008090) tras guardar el log.
- Las capturas arrancan con el menú de pausa abierto; se cerró con `ui_click continuebtn` desde el bridge.
- Faltan las vistas 14–19 del control (aéreas y desembocaduras) y revisar todas las capturas.

## Orillas y zonas inundadas — petición de Guillermo, 04-10, 01:15

Guillermo ve bordes del agua sin suavizar y zonas inundadas que no deberían. Medido sobre el terreno d5dadae8
(`diagnosis/shore-profile-d5dadae8.json` y `diagnosis/flood-edge-pilot.json`):

- **Orillas en escalera (BALTIC-007).** La altura de cada vértice de 6 m se asigna por clase: la tierra que toca el
  agua queda 0,45 m por encima del nivel (mediana; p10 0,15, p90 0,80) y el primer vértice mojado 0,28 m por debajo
  (p90 1,25). La línea de agua cae entre dos vértices y calca la malla, en dientes de 6 m. En los navegables el
  primer vértice ya está a 3,49 m (mediana): es un escalón.
- **Desembocaduras (variante de BALTIC-015).** Los planos de río acaban a 0,80 m (el corte del mar) junto al mar a
  0,54 m: escalón de unos 26 cm en (2544, 7628), (2091, 7371), (2052, 7308) y (9187, 9618). Hay 33 grupos de bordes
  de plano al aire en el interior del mapa.
- **Zonas inundadas (BALTIC-016).** No hay tierra por debajo del mar (0 vértices bajo 0,54 m). Los planos pisan
  tierra en 200 vértices (≈7.200 m²) en manchas pequeñas cerca de Narva. Lo que ve Guillermo no está localizado.

## Desviaciones del plan

1. R1 pasó de la cabecera del Luga a Narva_28. La cabecera del Luga es una incoherencia de nivel entre lago y
   río, no una pendiente; Narva_28 es el único tramo navegable que baja de forma monótona (1,62 → 0,95 m en 300 m).
2. Las curvas vanilla encadenadas borde a borde se sustituyeron por rectas independientes sobre un eje suavizado
   (σ de 15 m en arroyos y 40 m en R1), con un faldón de solape. El motivo: los ejes de diseño giran 7–14° cada
   10 m. Las curvas quedan en la biblioteca sin usar.
3. Los planos horizontales se recortan en lugar de retirarse enteros, para no dejar huecos en cruces y bifurcaciones.
4. El lecho baja en cada vértice lo mismo que baja la lámina, de modo que conserva su calado actual.
5. Gates offline: el calado se mide en los vértices que hoy están mojados; el salto de las juntas se compara con
   la profundidad del faldón (en vanilla el p90 es de 9–15 cm); la escala máxima en R1 es 4.

## Límites

Sin capturas, NM nueva, IA física ni serie V3. Las lecturas son de APIs nativas desde el servidor.

## Ficheros

| Fichero | Bytes | SHA-256 |
|---|---|---|
| `library.json` | 30650 | 5343b6c032b5f3c5… |
| `fit-report.json` | 7502 | 474da1db4693c061… |
| `fit-axes.json` | 93085 | 7d774678fac1133c… |
| `package-diff-world.json` | 1030 | f3bb0de7538646a7… |
| `package-diff-water.json` | 1223 | ffa4db1dd78c1889… |
| `package-build-receipt.json` | 350 | ec9da976b0c32820… |
| `camera-poses.json` | 2292 | 697b3a1feb8ef11b… |
| `boat/reference.json` | 9900 | 25b54cfd999e5b91… |
| `boat/run.log` | 112534 | 3da8548f01977e71… |
| `boat/verification.json` | 3016 | e94b460c2d0876db… |
| `readback/reference.json` | 331860 | 219535df43c16ccf… |
| `readback/run.log` | 129065 | d9b244ff438d0de4… |
| `readback/verification.json` | 7443 | 30e78f9410dbe659… |
| `control/run.log` | 111284 | cf182800561e8e36… |
| `control/verification.json` | 5960 | c856cc1eb4435826… |
| `diagnosis/engine-rule-vs-run-8392533a.json` | 789 | 8a7791b646937110… |
| `readback-v2/reference.json` | 615757 | 38773adc1a49bb21… |
| `readback-v2/pilot-b295208e.log` | 162493 | a144b0192af55a40… |
| `readback-v2/pilot-b295208e-verification.json` | 5436 | 6887c4a1d807fa49… |
| `readback-v2/pilot-63008090-verification.json` | 5436 | 4ce45c06cd4b45d1… |
| `readback-v2/control-337562e3.log` | 141260 | b784e2eae9629b30… |
| `readback-v2/control-337562e3-verification.json` | 12800 | 0bc55623ef6b3fbb… |
| `diagnosis/shore-profile-d5dadae8.json` | 2935 | fc9862051cceae6a… |
| `diagnosis/flood-edge-pilot.json` | 4948 | 6a673a7da45b1b59… |
