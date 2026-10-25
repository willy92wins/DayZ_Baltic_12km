# Candidato de orillas sobre el contorno, desembocaduras a la bajamar y R1 con solape — 04-10-2026

Plan: `plans/v30-shore-crossing-candidate.md`, aprobado por Guillermo a las 03:30: candidato aparte con prueba en motor
y sin tocar lo desplegado ni el canónico. Ejecutor: Claude, en la sesión nocturna. GLM-5.3-Flash (GX10) escribió la
herramienta de parche de agua y la auditoría de agua visible, y revisó las dos herramientas nuevas (§Delegación).

Productos pesados en `E:/DayZ-Baltic-Build/v30-shore-sdf`. Base: terreno d5dadae8 y agua deduplicada 339fa17f.

## Identidades

| Artefacto | Ruta (bajo `E:/DayZ-Baltic-Build/v30-shore-sdf`) | SHA-256 |
|---|---|---|
| Terreno con desembocaduras | `mouths3/terrain_mouths.npz` | cb5326053f7ff554cfc2e610367df6c87f0fb6da1b37d828ec774dbcb89088f3 |
| Agua parcheada | `water-mouths/pieces.json` | 7399885fa58befd05d4237a77d7fad9505771f5c01094e2491482cf78231b36f |
| Terreno con cauces | `fit3/terrain_pilot.npz` | ec6aa61a49d7ae1e3c0c45bade9105c67f7f05a60c3f52864133a60490d2cccb |
| Agua con cauces | `fit3/water/pieces.json` | f8f35985b33ec6ba7c80c93024341d3ca4e6db8d3e89d7ef3790d2828ea5bce9 |
| Terreno candidato | `shore4/terrain_shore.npz` | e144ad1a131ba90f6b9ccf55d867d45da3b4996e4eb53387bb0a692dba39e0e6 |
| Mundo | `package/out/Addons/narva_trial.pbo` | 0ab61bab7e400ffe91a11f4b010b649b3c99911b92a9ab698cd9d8085eb84cd2 |
| PBO de agua | `package/out/Addons/baltic_water_v30.pbo` | 6ebc62cbf29c8399cf45f26432dcb41e57132095b7abdde1b99e78e21dda4eb1 |
| Misión de lectura | `mission/BalticShoreSdfCandidateV1.BalticTrial/init.c` (linter PASS) | 0b9eecc09b6d53e8bbe7065fc3ef7d0076390a387c94f7355a851a3f66ed9253 |

El mod nuevo `@DayZ_Baltic_ShoreSdfCandidate` lleva los dos PBO, comprobados por hash al copiarlos, y la misión
`BalticShoreSdfCandidateV1.BalticTrial` está en `mpmissions`. No se tocó ningún mod ni misión existente.

## Cadena

| Paso | Herramienta | Qué hace |
|---|---|---|
| 1 | `tools/water/profile_river_mouths_v30.py` | El agua sin plano (≤ 0,80 m) que toca el mar o el delta pasa a una rampa geodésica, de 0,50 m en el lado del mar a 0,80 m en el primer plano. Corte de mar del candidato: 0,51 m |
| 2 | `tools/water/patch_water_tiles_v30.py` | Regenera solo las teselas de 48 m cuyas celdas cambian (escrita por GLM; ver §Delegación) |
| 3 | `tools/water/fit_channel_pieces_v30.py --overlap-all --no-pad --sea-cut 0.51` | R1 con solape en todo el tramo; R2 y R3 igual que el piloto; sin banco de calibración |
| 4 | `tools/terrain/fit_shore_crossings_v30.py --reg 0.05 --dry-raise-max 0.4 --levee-cap 0.15 --corridor-margin 0` | Mínimos cuadrados acotados para que el terreno cruce el agua visible donde el contorno de diseño corta cada arista nativa |
| 5 | `tools/terrain/build_surface_v30.py` y `build_v30_package.ps1` del checkout principal | Superficie y paquete; la copia del worktree no tiene `packages/baltic-road-v29` |

## Resultados offline

- **Desembocaduras.** Se re-perfilan 3 componentes: Narva (2.397 vértices, 1.435 m), borde del delta del Neva (1.432,
  945 m) y EDGE1/2 (410, 189 m). Hay 4.575 celdas de plano nuevas o cambiadas, la más baja a 0,50 m (bajamar). Bajan 6
  lechos, como máximo 0,156 m, y ninguno está protegido.
- **Agua.** Se regeneran 146 teselas (24 piezas retiradas y 309 nuevas). Las demás piezas quedan idénticas a las
  deduplicadas.
- **R1 con solape.** Lleva 8 piezas. Quedan 0 celdas sin cubrir (antes 29), 1 vértice mojado sin cubrir (antes 15) y
  ninguno al aire. A alturas de juego no se prevé ningún hueco en R1, R2 ni R3.
- **Orillas.** Desvío entre el cruce del terreno con el agua y el contorno de diseño, por arista nativa (p50 / p90, en m):

  | Clase | Antes | Después |
  |---|---|---|
  | Todas (124.142 aristas) | 0,517 / 2,441 | 0,082 / 1,591 |
  | Lagos | 0,351 / 1,275 | 0,033 / 0,666 |
  | Navegables | 2,071 / 4,567 | 0,974 / 3,892 |
  | Ríos | 0,441 / 1,793 | 0,082 / 1,083 |
  | Arroyos | 0,973 / 2,566 | 0,309 / 1,521 |
  | Lagunas | 0,388 / 1,506 | 0,040 / 0,777 |
  | Cauces vanilla | 0,618 / 1,775 | 0,106 / 1,397 |

  - Cambian 91.857 vértices (|Δ| p50 0,20 m, p90 0,40 m).
  - El tope de dique (0,15 m sobre la tierra exterior) deja 7.045 vértices de primera fila sobre su exterior, frente a
    6.162 antes. Sin el tope eran 9.092.
  - Del desvío que queda por encima de 1 m, el 38,5 % son aristas con un extremo protegido y el 47,3 % vértices mojados
    ya en el calado mínimo de 0,10 m.
- **Puertas.**
  - `verify_terrain_v30 --sea-cut 0.51`: solo fallan R2/R3 y Narva.
  - `verify_channel_reaches_v30.py`: 0 fallos fuera de las celdas retiradas. Dentro de R2/R3 quedan 33 vértices mojados a
    menos de 2 cm bajo la pieza, ya presentes en el ajuste de cauces (34 antes de las orillas).
  - Narva: la diferencia heredada de las 4 lagunas restauradas (1,84 m), igual que la base.
  - Taludes de tierra ≤ 35°. Triángulos de orilla de más de 35°: 3.060 (base 3.950).
  - Carreteras: PASS, 100 cadenas y 76.536 estaciones, con los mismos máximos que d5dadae8.
  - Muestras secas congeladas: 463/463.
  - Los 13 puntos someros del margen de oleaje quedan idénticos (radio de 24 m fijo).
  - Las caras de los 23 corredores, exactas.
- **Figura.** `offline/waterline-candidate.png`: rojo antes, azul después y negro el contorno.

## Motor

**Run 8aaa58a7, candidato.** Lectura PASS_VANILLA_CHANNEL_READBACK:
- las 99 piezas en su sitio exacto (≤ 0,65 mm);
- concordancia con la regla del motor del 99,67 % en R1 y del 100 % en R2 y R3;
- 0 huecos a alturas de juego;
- mar a 0,544 m (bajamar).

**Run bedb362b, control (ShoreWaveV30).** Sin piezas vanilla, como se esperaba: 7 huecos en R2 y 281 en el banco.

Las capturas son 31 vistas idénticas en los dos runs (`runtime/shots-manifest.json`, con hash). Hay parejas en `visual/`.

- **Orillas navegables:** el control enseña escalones rectos de 90° y el candidato los cambia por una línea suave.
  - Se ve claramente en SHORE4, SHORE6 y SHORE7.
  - En SHORE2 la orilla queda más natural; en SHORE0 y SHORE3 el cambio es sutil.
- **Lagunas (SHORE5):** dejan de verse rectangulares.
- **R3:**
  - De cerca, el candidato cambia las terrazas por agua continua en pendiente (R3a_oblique, R3a_low).
  - Desde el aire, las piezas rectas forman una banda en zigzag de anchura uniforme, más artificial que el control
    (R3_aerial).
- **R2:** agua continua, pero con costuras y esquinas de pieza visibles (R2b_low, R2_aerial).
- **R1:** igual que el control en las vistas cercanas.
- **Banco de calibración:** ya no aparece.
- **Desembocaduras (MOUTH0/1):** a esta distancia y en bajamar no se aprecia escalón en ninguno de los dos.
- **Manchas oscuras con interior granulado:** salen sobre tierra en uno u otro run y en sitios distintos. El candidato
  las tiene en R1_aerial y el control en EDGE1_aerial y FLOOD1; el piloto las tuvo en EDGE1. Las teselas de superficie
  son iguales en esos sitios y no es agua: la tierra de esas vistas está a 1,40 m o más y el mar del motor no pasa
  de 1,25 m (§Agua visible frente al diseño). Es un efecto de render dinámico. En el run 3ba786ef, con la misma
  cámara en EDGE1_aerial, la mancha sale en 1 de 5 capturas a lo largo de 2,5 min y desaparece en las siguientes
  (`variants/EDGE1_blotch_sequence.jpg`). El servidor mantuvo la nubosidad en 0,10 todo el tiempo; la captura con
  mancha llegó justo después de pedir 0,6, que la misión no aplicó. Candidatas: sombra de nube en el cliente o carga
  de texturas; no se distinguen desde el cliente.

## Agua visible frente al diseño (BALTIC-016)

`tools/water/audit_visible_water_v30.py` (escrita por GLM, §Delegación) compara, en una malla de 2 m sobre todo el
mapa, el agua que enseña el motor (mar, planos pond y láminas de pieza) con el contorno de diseño: water_v3, arroyos de
tier ≥ 2.500 m, lagos de contour-v2 y el mar v33 suavizado, las mismas fuentes que el constructor V30. Cuenta como
inundada el agua visible a más de 3 m fuera del contorno. `tools/water/classify_visible_water_v30.py` asigna cada
mancha a una zona. El mar se evalúa a 0,54 m (bajamar), 1,00 m (pleamar) y 1,25 m (pleamar con la cresta de ola de
0,25 m de `evidence/v30-shore-wave-2026-10-03/temporal-v3-result.json`).

| Zona, en bajamar | Base d5dadae8 | Candidato | Lectura |
|---|---|---|---|
| Borde oeste | 5,02 ha | 5,02 ha | Artefacto: la columna 0 de la máscara de mar v33 no es mar; en el juego es mar junto a mar |
| Costa | 3,77 ha | 3,77 ha | Franja de marea: 7,69 ha en pleamar y 10,34 ha con cresta. La playa (≥ 0,80 m) se moja por diseño |
| Narva (protegido) | 1,22 ha | 1,23 ha | Bandas estrechas en la orilla sureste del río (vistas R1, EDGE1 y FLOOD1) y 2.924 m² de lagos de diseño secos al lado; terreno V29 sin tocar |
| Delta | 1,01 ha | 1,01 ha | Canales del Neva excavados desde la fuente OSM completa (BALTIC-013), más anchos que water_v3; solo 932 m² caen dentro de los corredores de 24 m |
| Orillas | 3,68 ha | 2,67 ha | Astillas a lo largo de ríos y lagos por la malla de 6 m; el candidato quita el 27 % |
| Tierra adentro | 0 | 0 | 28 m² en pleamar |

- Total: base 14,7 / 19,0 / 22,5 ha y candidato 13,7 / 17,9 / 21,2 ha (bajamar / pleamar / cresta).
- Frente a la base, el candidato quita 1,04 ha de agua inundada y añade 316 m² junto a las rampas de EDGE y del Neva.
  Los huecos (agua de diseño que sale seca) bajan 328 m² netos; los nuevos son 213 puntos de 20 m² como mucho.
- El mar no alcanza la tierra: a 1,25 m solo quedan por debajo 19 vértices de tierra, todos de playa, y ninguno en
  Narva ni en el resto del mapa. Por eso las manchas oscuras de las capturas no son agua del motor.
- Ficheros: `audit/zones.json` (zonas y las 12 manchas mayores de cada una, con el hash del terreno y de las dos
  herramientas), `audit/*-audit.json` (las 6 auditorías), `audit/zones-base-low.png` y `audit/zones-cand-low.png`
  (mapa por zonas) y `audit/crops-base.png` (recortes en las vistas con manchas, el delta, el borde y la costa).
- No verificado: dónde vio Guillermo lo inundado. La auditoría compara mapas; no proyecta las capturas.

## Delegación (GX10, GLM-5.3-Flash-EXL3, API directa con streaming)

| Lane | Encargo | Resultado | Recepción |
|---|---|---|---|
| A | Auditoría de agua visible frente al diseño | Sin contenido tras 80 min de razonamiento; corte por tiempo | Relanzada con esfuerzo `medium` |
| A2 | La misma auditoría, con esfuerzo `medium` | `stop`, 25 min, 34k tokens | Aceptada con un cambio: la ruta a `tools/terrain`. Autoprueba PASS; firmas y orientación de la malla comprobadas contra `v30_common.py` y `engine_water_model.py`; usa las mismas fuentes de diseño que el constructor V30. Límites anotados en su cabecera: franja del borde oeste, delta de water_v3 y desvíos cuantizados a 2 m |
| B | `patch_water_tiles_v30.py` | `stop`, 46 min, 50,6k tokens | Aceptada con un cambio: el brief pedía área exacta por banda y eso eliminaba los solapes de 0,01 m entre teselas del constructor original. Se reconstruye desde una ventana una celda más ancha y la comprobación admite ese margen (error máximo 1,92 m²) |
| C | Revisión ciega de las herramientas de desembocaduras y orillas | `stop`, 75 min (`review/glm-review-raw.md`) | 1 crítico refutado: scipy 1.18.1 tiene `return_predecessors=False` por defecto y la herramienta funcionó. 2 riesgos teóricos (taludes y margen de orilla tras subir niveles) con 0 fallos en las puertas ejecutadas. 1 cosmético. Las notas de premisa se recogen en Límites |

## Variantes exploratorias y diagnóstico de cauces (tras el aviso de merge)

Variantes del candidato con un solo cambio cada una, mismas entradas y argumentos (`variants/variants.json`, con
hashes, desvíos por clase, límites del ajuste y puertas). Ninguna se adopta.

| Variante | Arroyos p50/p90 | Ríos p50/p90 | Lagos p90 | Diques | Puertas |
|---|---|---|---|---|---|
| Candidato (surco fijo) | 0,309/1,521 m | 0,082/1,083 m | 0,666 m | 7.045 | Las del candidato |
| Calado 0,03 m a ≤ 2 m del contorno | 0,308/1,520 m | 0,073/1,057 m | 0,417 m | 6.946 | Falla la de 0,10 m en 3.683 vértices, por diseño; el resto igual |
| Sin tope de dique | 0,305/1,509 m | 0,081/1,080 m | 0,647 m | 7.928 | No ejecutadas |
| Surco libre hasta 0,10 m de calado | 0,041/0,607 m | 0,036/0,746 m | 0,667 m | 6.903 | Las mismas que el candidato |
| Surco con calado ≥ 0,25 m | 0,239/1,246 m | 0,063/0,899 m | 0,665 m | 7.045 | No ejecutadas |
| Surco con calado ≥ 0,40 m | 0,289/1,406 m | 0,071/0,967 m | 0,666 m | 7.045 | No ejecutadas |

«Diques» cuenta tierra de primera fila más de 0,2 m por encima de toda su tierra exterior (base d5dadae8: 6.162).

- **Calado 0,03 m.** Cambia 5.212 m² de agua visible en todo el mapa, 56 m² como mucho por tesela de 120 m. Paquete
  construido sin desplegar (mundo `da68a129…`). No se probó en motor: el cambio no se ve a distancia de juego.
- **Tope de dique.** No es lo que frena los ríos estrechos: quitarlo apenas mueve los desvíos y añade 883 diques.
- **Surco.** Los 9.975 vértices mojados fuera del contorno son todos de surco (`diagnosis/narrow-groove-outline.json`):
  dan la continuidad de los cauces estrechos sobre la malla de 6 m, y fijarlos ancla la orilla en escalera. Con el
  surco libre cambian 4,93 ha de agua visible.
  - Se probó en motor como `@DayZ_Baltic_ShoreGrooveCandidate` (mundo `bd0483a3…`, run 16aca2e1), frente al candidato
    en las mismas 8 vistas (run f084ba3d). Poses y manifiestos con hash en `variants/`.
  - En GROOVE2 desaparece la escalera de 90° del arroyo (`variants/GROOVE2_stream.jpg`).
  - En GROOVE0 y GROOVE5 el arroyo pasa de banda o poza ancha a línea estrecha. Con 0,10 m de lámina se ve casi
    transparente y en primer plano parece seco (`variants/GROOVE5_stream.jpg`).
  - Exigir más calado en el surco devuelve la mayor parte de la escalera: con 0,25 m queda el 26 % de la mejora en el
    p50 de los arroyos y el 30 % en el p90.
- **Cauces vanilla.** Las costuras no son escalones de altura: entre piezas el salto es de 1 mm de mediana y 8 mm en
  p90, y solo 0,8 m de 392 m de costura de R2 pasan de 3 cm (`diagnosis/seam-check.json`). En cambio, el 79–81 % del
  agua visible de R2 y R3 tiene dos o más láminas de pieza, con la de abajo a 5 cm o más en 1.936 m² de R2
  (`diagnosis/layer-overlap-check.json`).
  - Comprobado con cámara cenital (run 2e3c51b1, `variants/nadir-2e3c51b1-shots-manifest.json`): las líneas rectas
    que se ven dentro del agua de R2 no coinciden con ningún borde de pieza del modelo, ni de contorno, ni interno, ni
    enterrado, para focales de 850 a 1.760 px (`variants/R2b_nadir_piece_edges_f850.jpg`). La proyección registra
    el eje del tramo y, con 1–2 m de margen, el contorno del agua prevista. La hipótesis de las láminas dobles no
    se sostiene.
  - El LOD visual de las piezas resultó idéntico al roadway (los mismos 8 vértices), así que esa pista cae.
  - Lo que sí encaja son las isolíneas de profundidad del lecho bajo la lámina. Con f = 1.000 px, la de 0,30 m cae
    sobre la línea transversal visible y la de 0,20 m junto a la diagonal de debajo
    (`variants/R2b_nadir_depth_contours_f1000.jpg`).
  - Bajo una lámina inclinada, la profundidad es lineal en cada triángulo de 6 m, y sus isolíneas son polilíneas
    rectas con cualquier ángulo. Lectura: compatible, no demostrada, porque la focal real no se conoce.
  - Si se confirma, las costuras vienen de la forma del lecho (profundidad visible de 0,07 a 0,49 m, p10–p90) y no
    de las piezas. Un lecho de profundidad casi constante dentro del cauce las reduciría, pero R2 y R3 no tienen
    ningún vértice mojado interior: todos tocan tierra, porque los cauces miden 1–2 vértices de ancho. Las isolíneas
    son inherentes a esa anchura sobre la malla de 6 m, y fijar la profundidad movería la orilla.
  - Corrección del 04-10 por la mañana. Guillermo lee esas líneas como solapes y piezas mal colocadas. Las líneas
    donde la lámina de arriba pasa de una pieza a otra, proyectadas a f = 850 px, caen en las mismas zonas de
    solape entre piezas consecutivas, aunque no calcan su forma. La explicación más probable es la suya: costuras
    de solape por colocación. Las isolíneas quedan como alternativa sin confirmar.
  - Los planos pond que sobreviven en el margen de los tramos son poca cosa: 99 m² visibles en R2 y 51 m² en R3
    (`diagnosis/margin-planes-check.json`).

## Límites y decisiones para Guillermo

- **Ríos estrechos con surco sobre llanura.** La línea de agua sigue la malla de 6 m: los vértices del surco no suben,
  para proteger la continuidad del lecho, y la llanura está al margen mínimo. Ejemplo en la ventana x 9730 z 140 de la
  figura. Hay que elegir entre arroyos anchos y escalonados con agua visible (candidato) y arroyos sobre el contorno
  pero someros y casi transparentes (surco libre, probado en motor); los calados intermedios recuperan poco
  (§Variantes exploratorias).
- **Calado mínimo relajado (variante exploratoria, sin paquete).** Con 0,03 m de calado a ≤ 2 m del contorno, los lagos
  bajan su p90 de 0,666 a 0,417 m y las lagunas de 0,777 a 0,615 m (`offline/waterline-shallow-vs-candidate.png`).
  Requiere rebajar la puerta de 0,10 m cerca del contorno. Cambia poco a la vista: 5.212 m² en todo el mapa.
- **Cauces vanilla.** Arreglan el agua escalonada y su borde casi nunca queda al aire: 2 m en R1, 1,5 m en R2 y 0 m en
  R3, de 900–1.170 m de perímetro por tramo (`diagnosis/piece-edge-check.json`). En R3 el borde que se ve es el
  cruce del terreno con la lámina sobre la malla de 6 m: 1.817 m² de agua visible frente a 552 m² de diseño, 440 m²
  a más de 1 m fuera del contorno; de ahí el zigzag de anchura uniforme. En R2 se ven las costuras entre piezas
  solapadas. Estrechar la banda mojada da poco: en R3 solo 20 vértices mojados quedan a más de 1 m fuera del contorno,
  y en R2 y R3 solo 9 pasan a tierra sin cambiar un plano vecino (`diagnosis/reach-band-check.json`). Afinar R3 pide
  orillas más altas junto al arroyo o aceptar esa anchura; no se ha probado.
- **Fuera de alcance esta noche.** La costa de marea y el delta no se reperfilan (allí el agua ≤ 0,45 m y la tierra
  ≥ 1,40 m). Las aristas cuyo extremo contradice el signo del contorno no se ajustan. Con bandas de 25 mm, el plano más
  bajo de una arista queda hasta una banda fuera.
- **No adoptable aún.** No hay navmesh nueva ni IA física.
