# Mar sobre tierra con marea: validación en motor — 04-10-2026, noche

Sale del aviso de Guillermo al ver el v3: «aún hay zonas bajas donde cuando sube un poco la marea sobresale el mar por
encima de la tierra», con la captura de EDGE1 marcada (BALTIC-016). Todo se mide sobre el candidato v3
(`@DayZ_Baltic_V3Candidate`, terreno `fac76aea`, evidencia en `../v30-v3-candidate-2026-10-04`).

## Resultado en una frase

El motor no tiene marea lenta. Lo que vimos es un oleaje global de 12,5 s, y la tierra que se oscurece «como si
entrara el mar» es exactamente la que quedó plana en el suelo de 1,40 m junto a la costa. Bajar el oleaje lo quita de
cerca, pero no de lejos, así que el arreglo de fondo es no dejar llanos a esa cota.

## Qué es el mar de DayZ

- **No hay marea: es oleaje.** `SurfaceGetSeaLevel()` (`scripts/3_game/global/game.c:1176`) vale
  `MaxTide/2 + MaxWave·sen(2πt/12,5 s)`.
  - Ajuste a 664 filas del 01-10: período 12,5 s, media 0,75 m, amplitud 0,25 m, error 0,8 mm.
  - En directo, en el run 8834df0e, con 908 filas cada 250 ms: período 12,51 s y amplitud 0,248 m.
  - Lo que antes llamábamos marea de 0,5–1,0 m es este oleaje: todo el plano del mar sube y baja cada 12,5 s.
- **La «ola» de la API es el mismo oleaje.** `SurfaceGetSeaWaveCurrent()` vale el nivel menos `MaxTide/2`, y
  `SurfaceGetSeaWaveMax()` vale `MaxWave`.
- **No depende de la fecha.** En 8 fechas de un mes lunar el mínimo y el máximo son los mismos
  (`runs/b34a7490-patch-v1/tide-probe-result.json`).
- **La tormenta no lo cambia.** Con nubosidad 1 y viento 20, el nivel y la ola falsa son iguales que en calma
  (`runs/8834df0e-default/`). Encaja con `waves=0` en todas las clases de nubosidad de `DZ\data\config.cpp`.
- **La ola falsa añade poco.** `GetWaterSurfaceHeightWithFakeWave` sube como mucho 0,12 m sobre el nivel en la costa
  norte y 0,09 m en el canal de EDGE1. La superficie más alta que da la API en la orilla es 1,12 m.
- **Se configura por mundo.** `MaxTide=1.5` y `MaxWave=0.25` cuelgan de `class CAWorld` (`DZ\data\config.cpp:258`,
  valores en `:1667-1668`), y nuestro `BalticTrial: CAWorld` los hereda. Se comprobó con dos parches de configuración
  (`P:\Mods\@DayZ_Baltic_TideProbePatch_v1` y `_v2`, sin tocar el mundo):

  | Parche | Mar medido |
  |---|---|
  | `MaxTide=1.2`, `MaxWave=0.05` | 0,55–0,65 m |
  | `MaxTide=1.5`, `MaxWave=0.05` | 0,70–0,80 m (oleaje de 12,58 s y 0,049 m) |

## Qué tierra queda baja

Censo del terreno v3b (`census/lowland-v3b.json`):

- **Tierra por debajo de 1,25 m:** 20 vértices en todo el mapa. Por debajo de 1,00 m, 6.
- **Lechos de agua que pinta el mar** (nivel ≤ 0,80 m, sin plano propio) por encima de 0,50 m: 1.170 vértices
  (4,2 ha), todos por debajo de 0,70 m.
- **Tierra exactamente en el suelo de 1,40 m:** 69.824 vértices (251 ha), en llanos planos que salen de las reglas de
  orilla. 12.005 de esos vértices están a menos de 30 m del agua que pinta el mar.

Con el mar de la API (como mucho 1,12 m en la orilla), ninguna tierra debería quedar cubierta.

## Qué se ve en motor

Tres runs, todos cerrados en orden con línea de terminación:

| Run | Configuración | Capturas |
|---|---|---|
| b34a7490 | Solo servidor, parche v1 | Ninguna: barrido del mar |
| 8834df0e | Configuración por defecto | 53: EDGE1 a tres distancias, cuatro llanos y un control; calma y tormenta |
| c9d46700 | Parche v2 (`MaxWave=0.05`) | 31: EDGE1 y llano 1 |

Cada captura se fecha en la fase del oleaje con las filas `RT` de la misión `missions/BalticTideProbeV2.BalticTrial`.
El reloj del servidor queda alineado con el de la captura con 18 ms de error (p95). El campo de visión de la cámara
(68,5° en vertical) se calibró con la línea de agua de EDGE1, con un error mediano de 0,22 m.

- **La banda de EDGE1 no sigue al mar.** Dos capturas separadas 1,2 s, con el mar a 0,509 y 0,513 m, salen una con
  banda y otra sin ella (`figures/edge1-band-flip.jpg`). Ningún desfase entre cliente y servidor separa los frames
  oscuros de los claros.
- **Las zonas oscuras son los llanos de 1,40 m.** Proyectando el terreno sobre la captura, las regiones escalonadas
  que se oscurecen coinciden con la tierra a 1,40 m exactos (magenta). La tierra de 1,41 a 1,60 m que la rodea
  (naranja) no se oscurece (`figures/flat1-flats-overlay.jpg`; EDGE1 igual).
- **No es agua.** De cerca, las zonas oscuras conservan la hierba y el matorral, sin reflejos ni oleaje, y la espuma
  de la orilla no se mueve. Ninguna celda de llano a 1,40 m tiene plano de agua: 0 de 48.396.
- **Medida de oscurecimiento** (`tools/playtest/tide_views_v30.py flats`): brillo medio de los llanos dividido entre el
  de la tierra de 1,42–1,60 m; 1,00 es sin oscurecimiento.

  | Pose | Por defecto (±0,25 m) | `MaxWave=0.05` (±0,05 m) |
  |---|---|---|
  | Llano 1, de cerca (10 m) | 0,87–1,01; 2 de 5 frames oscuros | 1,00–1,005; 8 de 8 limpios |
  | EDGE1, de lejos (unos 70 m) | 0,89–1,06 | 0,90–1,04 |
  | Llano 1, de lejos | 0,80–0,87 | 0,75–0,83 |

  De cerca, bajar el oleaje lo quita. De lejos no cambia, aunque la cresta queda 0,6 m por debajo de los llanos.

## Qué no está verificado

- El mecanismo de render que oscurece los llanos de lejos (candidatos: LOD del terreno, sombras o hierba sobre suelo
  perfectamente plano). La medida no nombra la causa.
- Que quitar los llanos lo arregle. Es la hipótesis que se valida con el mismo método tras el cambio.
- Sitios distintos de EDGE1 y el llano 1: el llano 3 y el control solo se capturaron una vez, sin medir.
- La espuma y el lavado de playa con `MaxWave=0.05` (el oleaje pasa de ±0,25 a ±0,05 m).

## Siguiente

1. **Quitar los llanos de la costa.** La tierra junto al mar debe subir con una pendiente suave desde la orilla, sin
   mesetas a cota fija: por ejemplo, por encima de 1,40 m más una pendiente con la distancia y algo de microrrelieve.
   Encaja con el arreglo de orillas serradas (BALTIC-007): el mismo perfil de orilla en función de la distancia a un
   contorno suave.
2. **Decidir el oleaje** (Guillermo). `MaxWave` de 0,25 a 0,05–0,10 en nuestro `config.cpp`, con `MaxTide=1.5` para no
   mover la media. Es más propio del Báltico y quita el efecto de cerca, a cambio de menos movimiento en la orilla.
3. **Validar** con las mismas poses y ráfagas de al menos 10 frames (un período), y
   `tools/playtest/tide_views_v30.py flats` con las máscaras del terreno v3b, para medir las mismas zonas de pantalla
   en las capturas nuevas.
   - Criterio: variación del cociente dentro de la ráfaga ≤ 0,02 en todas las poses. Hoy es 0,07–0,17.
   - El nivel absoluto no sirve de criterio: en el llano 1 de lejos los llanos ya son más oscuros por textura.
   - Repetir el censo de tierra a 1,40 m.

## Decisión

Guillermo, 04-10: oleaje de **±0,10 m** (`decision-swell.json`). Aplicado en `tools/terrain/derive_world_v30.py`,
que escribe `MaxTide=1.5;` y `MaxWave=0.1;` en la clase `BalticTrial` del `config.cpp` del mundo. El motor debe dar
un mar de 0,65 a 0,85 m (fila `CFG;0.65;0.85;0.1` de la misión de sonda). Sin verificar hasta el próximo paquete.
