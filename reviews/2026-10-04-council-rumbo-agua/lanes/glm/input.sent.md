# Consejo: rumbo del agua de DayZ Baltic 12km (04-10-2026)

## Tarea (una frase)

Da una segunda opinión independiente y con evidencia sobre el rumbo del sistema de agua y orillas del terreno DayZ
Baltic 12km, y propone una secuencia fija de trabajo hasta la base 1.0.

## Rol y criterio de éxito

Eres un consejero de solo lectura, de una familia de modelos distinta a la del orquestador (Claude). El dueño del
proyecto, Guillermo, quiere fijar un rumbo y dejar de dar vueltas. Tu dictamen sirve si:

1. critica primero el encuadre (Q0);
2. responde Q1–Q5 con una recomendación clara y su porqué;
3. cita cada hecho que use con `ruta:línea` o con el fichero;
4. marca como [SUPUESTO] lo que no pueda verificar;
5. dice dónde discrepa del orquestador.

Discrepar es bienvenido: el objetivo es elegir bien, no ratificar lo propuesto.

## Contexto mínimo

- **Qué es.** Un mapa DayZ de 12,288 × 12,288 km (2048² vértices a 6 m) de la región báltica (Narva, el Luga, San
  Petersburgo), generado desde datos GIS. Terreno «V30» con relieve rediseñado; todavía sin edificios ni vegetación
  colocada, por decisión de producto (`product-spec.md`, fila P10).
- **Cómo dibuja el agua el motor** (medido en este proyecto):
  - Mar: un plano horizontal infinito con marea de 0,50 a 1,00 m.
  - Agua interior: un plano horizontal por celda de 6 m, a la media de los niveles de sus esquinas mojadas,
    redondeada a 25 mm (`tools/terrain/v30_common.py:88`). La orilla visible es la línea donde el terreno, triangulado
    por la diagonal NO-SE, corta ese plano.
  - Piezas vanilla de cauce de Chernarus (`river_24_*`, `stream_14_*`): láminas inclinadas con faldones en los
    extremos. Hoy se usan en tres tramos piloto: R1 (río ancho, Narva), R2 y R3 (arroyos).
- **Puertas offline del terreno** (`tools/terrain/verify_terrain_v30.py:31`):
  - calado ≥ 0,10 m;
  - tierra a ≤ 8,5 m del agua al menos 0,05 m sobre el nivel del agua más cercana;
  - tierra ≥ 1,40 m;
  - pendientes de tierra ≤ 35°;
  - en cada celda con plano, esquinas mojadas por debajo del plano y esquinas de tierra por encima.

## Hechos verificados (con su fuente)

- **H1, orillas (BALTIC-007).** Un candidato ajusta el terreno para que cruce el agua justo en el contorno de diseño.
  El desvío p50/p90 de la línea de agua pasa de 0,517/2,441 a 0,082/1,591 m, medido sobre todas las aristas
  agua-tierra del mapa con signo coherente (`evidence/v30-shore-crossing-candidate-2026-10-04/README.md`). En motor
  desaparecen los escalones de 90° de las orillas navegables.
- **H2, arroyos estrechos.** Los cauces de 1–2 vértices de ancho se ven en escalera. Con «surco libre» (calado
  mínimo 0,10 m) la escalera desaparece, pero en motor el agua se ve casi transparente. Con calado ≥ 0,25 m solo
  queda el 26–30 % de la mejora (`bugs.md`, fila BALTIC-007, línea 19).
- **H3, piezas vanilla (BALTIC-015).** En motor la lectura es PASS, sin huecos, pero se ven costuras en R2. Área
  de cauce con dos láminas o más, medida hoy (`evidence/v30-polish-candidate-2026-10-04/joints/joints.json`, bloque
  `groups`):
  - Chernarus: 0,33 % en ríos (660 piezas) y 0,49 % en arroyos (389 piezas);
  - nuestros tramos: 58 % en R1, 73 % en R2 y 75 % en R3.
  - Chernarus encadena canto con canto (mediana −0,044 m en la junta) y gira dentro de piezas curvas (desvío de
    rumbo en la junta, p50 0,44°).
  - Nosotros solapamos un par de faldones (`tools/water/fit_channel_pieces_v30.py:263`, con `overlap_from=None` en
    R2 y R3, líneas 56 y 58) y giramos en las juntas (p50 8,8° en R2 y 11,4° en R3).
- **H4, agua colgada (BALTIC-017).** De 631 masas de agua estancada, 111 lagos (7,0 km²) tienen el nivel más de
  0,3 m por encima de la mediana del terreno situado a 12–36 m de su borde, y 190 masas tienen diques de más de
  0,5 m (`evidence/v30-polish-candidate-2026-10-04/census/census.json`).
  - Los niveles de lago salen de las superficies V29 `contour-v2` (`tools/terrain/build_v30_water.py:46-51`).
  - El constructor sube toda la tierra a ≤ 8,5 m del agua hasta nivel + 0,35 m (`tools/terrain/build_v30.py:40` y
    `:449-450`).
  - Caso típico, la cabecera del Luga: agua a ~4,15 m sobre un terreno a ~3,0 m, con diques de ~1,4 m.
- **H5, escalera por tope de nivel.** En el agua que fluye, el constructor rebaja el nivel hasta 0,25 m por cada
  6 m hacia cualquier vecino mojado más bajo (`tools/terrain/build_v30_water.py:224`). Una charca pegada a un río
  lo arrastra en escalera: en el Luga, 141 vértices bajaron hasta 2,10 m
  (`evidence/v30-polish-candidate-2026-10-04/reports/polish-report.json`).
- **H6, agua visible (BALTIC-016).** Fuera del contorno de diseño, en bajamar: borde oeste 5,0 ha (artefacto de
  máscara), costa 3,8 ha, Narva protegido 1,2 ha, delta 1,0 ha y astillas de orilla 2,7 ha; tierra adentro, nada.
  Las manchas oscuras que vio Guillermo son probablemente fondos de charca pintados casi negros, visibles cuando la
  lámina no se dibuja. El arreglo está construido en el candidato v2, sin ver en motor (`bugs.md`, línea 28).
- **H7, candidato v2 «pulido».** Desplegado y sin ver en motor
  (`evidence/v30-polish-candidate-2026-10-04/README.md`).
- **H8, producto** (`product-spec.md`):
  - P2: conservar agua y ríos;
  - P9: ríos navegables con lancha vanilla;
  - P10: terreno y navegación antes del mapeado;
  - P12: relieve selectivo, que permite exagerar alturas de zonas concretas;
  - P14: contorno suave y bajos sin agua indeseada;
  - línea 23: «No confundir ese candidato con una decisión de cerrar todos los niveles de agua».
- **H9, estado.** La base 1.0 no está aceptada. Faltan navmesh, pruebas físicas e IA sobre el candidato que se
  acepte, y Terrain Builder cuando se congele la base (`HANDOFF.md`, bloque LIVE-STATE, campo `next`).

## Interpretaciones del orquestador (rebatibles)

- **I1.** El agua colgada nace de usar niveles V29 sobre el relieve V30 rediseñado (P12): los niveles no se
  volvieron a derivar del terreno nuevo. [SUPUESTO: no se ha comparado lago a lago con el terreno V29.]
- **I2. Rumbo que propone el orquestador.**
  - (a) Piezas vanilla solo en ríos anchos, encadenadas como Chernarus: canto con canto, curvas con piezas curvas y
    desplazamiento lateral permitido. Los arroyos estrechos (R2/R3) vuelven a planos.
  - (b) Agua colgada: derivar los niveles de lago del terreno natural (bajar el agua al nivel del entorno) en vez
    de levantar diques, empezando por las zonas visibles.
  - (c) Orden: ver v2 en motor → decidir (a) y (b) → reconstruir → navmesh e IA → congelar → Terrain Builder.
- **I3.** Para arroyos estrechos sobre la malla de 6 m no hay buena solución con planos: o escalera, o agua casi
  transparente.

## Preguntas

- **Q0 (primero, obligatoria).** ¿Qué puede estar mal en el encuadre del problema, en los hechos elegidos o en las
  opciones? Puedes aceptar un hecho y rechazar la inferencia.
- **Q1, agua colgada.** ¿Volver a derivar los niveles, rebajar el terreno, aceptar los diques o una mezcla? ¿Con qué
  criterio por masa de agua y con qué riesgos (ríos conectados, navegabilidad P9, puertas)?
- **Q2, cauces.** ¿Piezas vanilla solo en ríos anchos, encadenadas como Chernarus? ¿Cómo resolver las curvas sin
  solapes ni huecos? ¿Con qué umbral de anchura?
- **Q3, arroyos estrechos.** ¿Hay una tercera vía además de la escalera o el agua transparente (otra resolución,
  texturas, objetos…)?
- **Q4, rumbo fijo.** Secuencia numerada de 5 a 8 pasos hasta la base 1.0. Cada paso con su criterio de salida
  medible y lo que se congela al terminarlo.
- **Q5.** ¿Qué dejarías fuera de 1.0, y por qué?

## Fuentes obligatorias (solo lectura; léelas antes de opinar)

Raíz del repo: `P:\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290`. Es la misma carpeta que
`C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290`.
Rutas relativas a esa raíz:

1. `product-spec.md`
2. `evidence/v30-polish-candidate-2026-10-04/README.md`
3. `evidence/v30-shore-crossing-candidate-2026-10-04/README.md`
4. `bugs.md`: solo las filas de la tabla, líneas 19 (BALTIC-007) y 27–29 (BALTIC-015, -016 y -017)
5. `HANDOFF.md`: el bloque LIVE-STATE, líneas 3–23
6. `tools/water/fit_channel_pieces_v30.py`: líneas 1–60 y 240–300
7. `tools/terrain/build_v30_water.py`: líneas 40–60 y 205–235
8. `evidence/v30-polish-candidate-2026-10-04/census/census.json` y
   `evidence/v30-polish-candidate-2026-10-04/joints/joints.json` (solo el bloque `groups`)

Puedes abrir otros ficheros del repo para comprobar algo concreto; cita lo que uses. Mods hermanos con el mismo
problema: ninguno (censo de `P:\`, 486 entradas: las únicas carpetas de terreno son de este proyecto).

## Fronteras

- Solo lectura: no escribas, no muevas ni borres nada, no ejecutes scripts del repo, no lances DayZ ni uses la red.
- Lee los ficheros con tu herramienta de lectura, no con comandos de shell.
- No leas fuera del repo, salvo este brief.
- Entorno: Windows. Hay rutas con espacios bajo OneDrive; si tu herramienta parte las rutas por espacios, usa la
  forma `P:\`. Los ficheros están en UTF-8.
- Tiempo orientativo: unos 30 minutos. No hace falta leer cada fichero entero si bastan las líneas indicadas.

## Entregable (formato exacto)

Tu respuesta final es el dictamen, en Markdown y en español, con estas secciones en este orden:

```
## 0. Crítica del encuadre
## 1. Agua colgada
## 2. Cauces y piezas
## 3. Arroyos estrechos
## 4. Rumbo fijo
## 5. Fuera de 1.0
## 6. Discrepancias con el orquestador
## LO_NO_VERIFICADO
```

- La última línea es exactamente `FIN-DICTAMEN`.
- Cada hecho que uses lleva su `ruta:línea` o el nombre del fichero. Lo que no tenga cita va a LO_NO_VERIFICADO o se
  marca [SUPUESTO].
- Longitud orientativa: 1.200–2.500 palabras.

## Receptor

Claude, el orquestador, recibe cada dictamen por separado y sin mostrar los de los demás. Re-verifica las citas que
sostienen cada recomendación y se los presenta a Guillermo, con el disenso tal cual.


---

# ANEXO para esta lane (no puede abrir ficheros): contenido literal de las fuentes obligatorias
Cada bloque lleva su ruta relativa a la raíz del repo y el número de línea real del fichero, para que cites `ruta:línea`. Los dos JSON van recortados y se indica qué se recortó.

### `product-spec.md`
```
   1| # Producto y aceptación
   2| 
   3| Fuente de autoridad: peticiones de Guillermo en esta conversación, límites v0 aprobados el 29-09-2026. El handoff heredado se usa como orientación, no como prueba de herramientas o datos.
   4| 
   5| | ID | Requisito | Criterio de aceptación |
   6| |---|---|---|
   7| | P1 | Región condensada, propuesta 12,288 × 12,288 km | 2048² celdas de 6 m; encuadre aprobado completo y orientación norte, confirmado también por Terrain Builder. |
   8| | P2 | Conservar agua, costa, islas, ríos y zona natural | Geometrías de referencia trazables; posteriormente costas recorribles y agua funcional; no sustituir todos los lagos por mar. |
   9| | P3 | Conservar íntegro el acercamiento de San Petersburgo | Misma transformación global, sin escalado local. Huella aproximada 4,81 × 3,83 km. Verificar canales y cruces a escala de juego. |
  10| | P4 | Narva, frontera y territorio occidental | Localidad y ambas riberas presentes; cruce jugable diseñado y probado; futura base/búnker occidental pendiente de ubicación. |
  11| | P5 | Conexiones principales | Referencia topológica coherente y una selección jugable medida; las vías se construyen con piezas y anchuras humanas. |
  12| | P6 | Assets vanilla primero | Inventario y medidas reales antes de colocar edificios/puentes; futuros assets distintivos se priorizan después. |
  13| | P7 | Objetivo 80–100 jugadores, experiencia tipo Chernarus | Ensayo de carga con hardware y escenarios definidos; separar cliente, servidor, IA, loot y persistencia. No demostrado en fase 0. |
  14| | P8 | Fuentes y generación reproducibles | Originales identificados por hash/fecha/licencia; transformaciones, excepciones, deltas y resultados registrados. |
  15| | P9 | Ríos navegables y puentes elevados | Petición30-09: lancha vanilla y margen para barcos medianos. Continuidad de agua, anchura útil, profundidad con agua mínima y gálibo con agua máxima; paso real de embarcación por cauce y puente, además de cruce terrestre. El antiguo ensayo de Narva a tablero2m no satisface este requisito; el candidato posterior debe acreditarlo con su geometria y consumidores identificados en el HANDOFF. |
  16| | P10 | Terreno y navegación antes del mapeado | Petición30-09: terminar primero relieve, hidrografía, cauces, orillas y navegación base. Posponer población, edificios, vegetación colocada, carreteras físicas y decoración. Los objetos de ensayo solo reservan gálibos y cruces; después del mapeado habrá que regenerar y validar de nuevo la navmesh. |
  17| | P11 | Carreteras lisas para conducción DayZ | Petición30-09: perfiles longitudinales progresivos, superficie sin baches ni escalones, y empalmes suaves entre terreno, piezas y puentes. Medir cambios de pendiente y caída transversal, además de pendiente máxima; validar después con vehículos vanilla a distintas velocidades, sin saltos, golpes ni encallamientos atribuibles a la vía. Preparar la reserva del terreno ahora; mapeado físico después según P10. |
  18| | P12 | Relieve selectivo por jugabilidad | Aprobación30-09: exagerar alturas de zonas concretas por encima de ×3 si conviene, sin fidelidad obligatoria a la escala vertical. Conservar XY, agua/islas/closeup, conexiones y P9/P11; medir perfiles, accesos, cobertura y líneas de visión. Cotas y máscaras de diseño en plans/selective-relief.md; aceptación posterior de terreno y navmesh regenerada. |
  19| | P13 | Reserva natural y variedad de biomas | Petición30-09: conservar la reserva como punto clave, con alta densidad de árboles en ciertos sectores. Reservar ahora terreno, humedales y mosaico de bosque denso/claros; contrastar el perímetro antes de editar Z. Colocar vegetación después según P10, comprobar contraste entre biomas desde jugador, accesos, colisiones/navmesh y rendimiento del sector más denso. No equiparar cobertura WorldCover con densidad de instancias. |
  20| | P14 | Contorno suave y bajos sin agua indeseada | Petición01-10: suavizar el outline general y corregir el agua que asoma intermitentemente en zonas bajas. Separar forma del terreno, textura y agua dinámica; comprobar margen y transiciones en las orillas, sin sacrificar canales navegables, islas, humedales ni la reserva. Validación visual con cámaras comparables y muestreo entre vértices, además de alturas nativas. |
  21| | P15 | Red ferroviaria de circunvalación, radiales y estación de San Petersburgo | Petición03-10: diseñar una red principal que dé la vuelta al mapa, con algunas radiales y bifurcaciones adicionales. Al menos el tramo de San Petersburgo debe seguir su posición y recorrido reales, con la misma transformación XY aprobada, para colocar su estación emblemática en el emplazamiento correspondiente. En la fase de diseño se concretarán estación, corredores y cruces, conservando cauces navegables, gálibos y reserva. **Alcance futuro: no ejecutar ahora**; diseño y colocación física pendientes, respetando P10. |
  22| 
  23| El criterio de relieve selectivo está aprobado; las cotas del candidato regional ya estan implementadas y medidas, con aceptacion final segun HANDOFF. No confundir ese candidato con una decision de cerrar todos los niveles de agua. No están decididos densidad urbana, número de puentes jugables, economía militar ni ubicación/diseño del búnker. No se cambian silenciosamente para adaptar los datos al motor.
  24| 
```

### `evidence/v30-polish-candidate-2026-10-04/README.md`
```
   1| # Candidato v2 «pulido» sobre Narva — 04-10-2026
   2| 
   3| Decisiones de Guillermo del 04-10 por la mañana, con sus capturas («queda bastante por pulir… especialmente esa
   4| segunda donde desemboca el río»):
   5| - **Superficie:** fondo de lagos y charcas con el tono del terreno, y anillo de grava solo en ríos y mar.
   6| - **Luga:** unir el río con lake_014 y liberar el corredor del último tramo.
   7| - **Balsas:** suavizar las esquinas.
   8| 
   9| Base: la cadena del candidato de Narva (manda V29 y los fosos llevan agua). Ejecutor: Claude. GLM-5.3-Flash (GX10)
  10| escribió dos herramientas de análisis y revisó la de pulido (§Delegación). Productos pesados en
  11| `E:/DayZ-Baltic-Build/v30-polish`; la primera construcción, anterior a la revisión, queda en las carpetas `*-r1`.
  12| 
  13| ## Hallazgo en la cabecera del Luga
  14| 
  15| - **Escalera al final del río.** El río acaba en (10535, 4176) con nivel de diseño 4,20 m. 141 vértices del último
  16|   tramo estaban bajados hasta 2,10 m: el tope del constructor (0,25 m por cada 6 m) los arrastraba hacia 7 vértices
  17|   de charcas pegadas. Una de ellas, una franja estrecha a 1,85 m, está justo donde seguiría el río.
  18| - **Agua colgada.** El río y los lagos de la zona están a ~4,15 m, sobre un terreno a ~3,0 m. Los sujetan diques a
  19|   nivel + 0,35 m (`figures/luga-head-heights-before.png`). El canal nuevo tiene que cruzar ese valle con diques, igual
  20|   que el resto de la zona. El censo de abajo enseña que no es un caso aislado.
  21| 
  22| ## Cadena
  23| 
  24| | Paso | Herramienta | Salida (bajo `E:/DayZ-Baltic-Build/v30-polish`) | SHA-256 |
  25| |---|---|---|---|
  26| | Pulido | `tools/terrain/polish_luga_head_v30.py` sobre `v30-narva-shore/mouths-moats` (e9cb9d9c) y `sd_v29.npz` (d756a5da) | `polish/terrain_pilot.npz`, `polish/sd_polish.npz` | 931632d6e5b00c92…, 6817bf78b80f89c5… |
  27| | Agua | `tools/water/patch_water_tiles_v30.py --sea-cut-old 0.51 --sea-cut-new 0.51` sobre `v30-narva-shore/water-moats` | `water-polish/pieces.json` | 1e06bc243678167d… |
  28| | Cauces | `tools/water/fit_channel_pieces_v30.py --overlap-all --no-pad --sea-cut 0.51` | `fit-polish/terrain_pilot.npz`, `fit-polish/water/pieces.json` | b7a5e6a1201b10ff…, 0907920a24c745a5… |
  29| | Orillas | `tools/terrain/fit_shore_crossings_v30.py`, argumentos del candidato + `--sd-override polish/sd_polish.npz --narva-core-m 0 --free-corridor-box 10150,3700,10700,4600` | `shore-polish/terrain_shore.npz` | 88ed02684bef02a2… |
  30| | Superficie | `tools/terrain/build_surface_v30.py --workers 12 --bed-tone land --shore-ring flowing` | `surface/` | — |
  31| | Paquete | `tools/terrain/build_v30_package.ps1` del checkout principal, `-WaterSource fit-polish/water` | `package/out/Addons` | mundo f6ca1cb6c689fc8b…, agua 0cca78668025d9c3… |
  32| 
  33| Desplegado como `@DayZ_Baltic_PolishCandidate` (copias comprobadas por hash), con la misión `BalticShoreSdfCandidateV1.BalticTrial`.
  34| 
  35| ## Qué cambia (`polish/report.json`)
  36| 
  37| - **Canal Luga–lake_014.** 220 m de eje y 20 m de ancho, con 92 vértices nuevos (78 de tierra y 14 de la charca). Nivel 4,20 → 4,17 m y calado 0,35–2,95 m. Cruza el valle con diques, como el resto de la zona.
  38| - **Río.** 141 niveles vuelven a su banda (hasta +2,10 m). Se sustituyen 17 vértices de la franja y se separan 5 de charcas.
  39| - **Lagos.** Se suavizan 17: 5 con apertura de 8 m (014, 138, 152, 164, 218) y 12 escalonados con Chaikin. Desviación máxima 3,8 m, sin perder lóbulos. Ningún vértice de lago pasa a tierra: el redondeo actúa a través del campo de distancias (1.605 vértices). La apertura sola se descartó porque borraba lóbulos y levantaba diques de 5,9 m sobre el lecho del río (`figures/lake-rounding-discarded-opening.png`).
  40| - **Orillas.** 111 vértices de orilla elevados (máximo 2,95 m). Fuera de la caja (10150, 3700)–(10700, 4600) no cambia ningún vértice (0).
  41| - **Campo de distancias.** Antes de cambiarlo, la regla del constructor reproduce el campo base en la caja: máximo 0,000002 m en 4.510 vértices. Si no lo reprodujera, la herramienta se para.
  42| 
  43| ## Comprobado
  44| 
  45| | Qué | Cómo | Resultado |
  46| |---|---|---|
  47| | Puertas del terreno | `verify_terrain_v30 --sea-cut 0.51`, frente al candidato de Narva | Idénticas: calado 6 (arroyos), piezas 35 (R2/R3, ya conocidas), orillas/lecho/suelo/pendientes 0/0/0/0. La identidad V29 de Narva cambia por diseño |
  48| | Carreteras | `verify_roads_v30` | PASS: 100 cadenas y 76.513 muestras, como Narva |
  49| | Ajuste de orillas | control interno | 0 mojados someros, 0 subidos donde no toca y 0 bajo el suelo; caras de corredor exactas fuera de la caja |
  50| | Línea de agua en la caja | `luga_box_offsets` (misma medida que el ajuste) | p50/p90/p99 0,070/2,17/4,39 → 0,076/1,92/3,88 m |
  51| | Agua visible en bajamar | `audit_visible_water_v30` + `classify_visible_water_v30` | Igual que Narva salvo el canal: +2.312 m² fuera del diseño `water_v3`, 2.560 de ellos en la ventana del canal. Tierra adentro, 0 |
  52| | Superficie | vista previa (`figures/surface-preview-before-after.png`) | Grava 67,6 → 64,8 M píxeles; lagos y charcas sin fondo negro; ríos y canal lo conservan |
  53| | Paquete | `build_v30_package.ps1` | Alturas exactas; materiales, cabecera y puentes idénticos; 17.573 objetos de agua |
  54| | Sin verificar | — | Vista en motor (la caja la ocupaban otras sesiones: @SimpleGroup y después LFPowerGrid con Guillermo jugando). NM e IA |
  55| 
  56| ## Cauces frente a Chernarus (BALTIC-015)
  57| 
  58| `tools/water/compare_channel_joints_v30.py` aplica a nuestras piezas la misma regla de juntas con la que se calibró la
  59| biblioteca contra Chernarus, y mide además el área de huella con dos láminas o más.
  60| 
  61| | Grupo | Piezas | Juntas | Área con dos láminas o más | Desvío de rumbo en junta (p50) | Solape en junta (p50/p90) |
  62| |---|---|---|---|---|---|
  63| | Chernarus, ríos | 660 | 577 | 0,33 % | 0,44° | 0,04/0,11 m |
  64| | Chernarus, arroyos | 389 | 310 | 0,49 % | 0,69° | 0,04/0,10 m |
  65| | R1 | 8 | 0 | 58 % | — | — |
  66| | R2 | 44 | 37 | 73 % | 8,84° | 0,54/1,73 m |
  67| | R3 | 47 | 45 | 75 % | 11,38° | 0,44/2,27 m |
  68| 
  69| En R1 la regla no encuentra juntas: el solape, de unos 22 m, supera el umbral de 12 m con el que la regla acepta una junta.
  70| 
  71| Chernarus encadena canto con canto (−4 cm de mediana) y gira dentro de las piezas curvas, con desplazamientos
  72| laterales de hasta ±3,5 m. Nosotros solapamos un par de faldones (`overlap_from=None` en R2/R3 y `--overlap-all`,
  73| `tools/water/fit_channel_pieces_v30.py:263`) y giramos en las juntas. Es la lectura de Guillermo: las costuras de R2
  74| son solapes de colocación (`joints/ours.png` frente a `joints/vanilla.png`).
  75| 
  76| ## Agua colgada en todo el mapa (BALTIC-017)
  77| 
  78| `tools/water/census_perched_water_v30.py` agrupa el agua estancada por nivel y compara cada masa con el terreno natural a 12–36 m de su borde. De 631 masas:
  79| - **Colgadas** (más de 0,3 m por encima del terreno natural): 111 lagos, 7,0 km².
  80| - **Con dique** de más de 0,5 m: 190 masas (173 lagos y 17 charcas).
  81| - Los lagos de la cabecera del Luga quedan ~0,8 m sobre el terreno natural, con diques de ~1,4 m. Los dos lagos más grandes también
  82|   salen colgados: el del oeste (nivel 2,64 m, 4,6 km²) por 0,33 m y el del sureste (2,13 m, 2,0 km²) por 0,55 m.
  83| 
  84| Mapa: `census/map.png` (amarillo de 0,3 a 1 m, rojo por encima de 1 m). Un arreglo posible es derivar los niveles de lago del terreno
  85| natural, pero es una decisión de diseño pendiente.
  86| 
  87| ## Delegación (GX10, GLM-5.3-Flash, 3 carriles)
  88| 
  89| - **D, `compare_channel_joints_v30.py`.** 8 min. Aceptada con dos cambios del receptor: nunca asignaba los bordes de
  90|   las piezas (`KeyError` al buscar juntas) y la transformación modelo→mundo estaba traspuesta. La autoprueba añade una
  91|   cuña girada que caza la traspuesta.
  92| - **E, revisión ciega de `polish_luga_head_v30.py`.** 17 min. Cuatro hallazgos reales, todos latentes en esta
  93|   construcción: conversión de lagos fuera de la caja, orillas sin recalcular junto al agua retirada, reproducción del
  94|   campo de distancias sin corte y auditoría de niveles fuera de la caja. Corregidos. La corrección de las orillas sube
  95|   un vértice, (10458, 4050), de 2,82 a 2,98 m, y la cadena se rehízo con la herramienta corregida.
  96| - **F, `census_perched_water_v30.py`.** 5 min. Aceptada con dos cambios: el recuento de clases sin `minlength` daba
  97|   `IndexError` en el primer lago, y los colores del mapa tenían una forma errónea (la autoprueba ahora también dibuja).
  98| 
  99| ## Siguiente
 100| 
 101| - Ver el candidato en motor con Guillermo (`camera-poses.json`): cabecera del Luga (aérea, oblicua y dos bajas), rectángulos, lake_038,
 102|   fosos de Narva, las manchas de R1_aerial y EDGE1 con la superficie nueva, y SHORE4 para comparar.
 103| - Decidir: cauces vanilla solo en ríos anchos, con encadenado canto con canto y curvas como Chernarus (R2/R3 volverían a planos), y qué
 104|   hacer con el agua colgada (BALTIC-017).
 105| 
```

### `evidence/v30-shore-crossing-candidate-2026-10-04/README.md`
```
   1| # Candidato de orillas sobre el contorno, desembocaduras a la bajamar y R1 con solape — 04-10-2026
   2| 
   3| Plan: `plans/v30-shore-crossing-candidate.md`, aprobado por Guillermo a las 03:30: candidato aparte con prueba en motor
   4| y sin tocar lo desplegado ni el canónico. Ejecutor: Claude, en la sesión nocturna. GLM-5.3-Flash (GX10) escribió la
   5| herramienta de parche de agua y la auditoría de agua visible, y revisó las dos herramientas nuevas (§Delegación).
   6| 
   7| Productos pesados en `E:/DayZ-Baltic-Build/v30-shore-sdf`. Base: terreno d5dadae8 y agua deduplicada 339fa17f.
   8| 
   9| ## Identidades
  10| 
  11| | Artefacto | Ruta (bajo `E:/DayZ-Baltic-Build/v30-shore-sdf`) | SHA-256 |
  12| |---|---|---|
  13| | Terreno con desembocaduras | `mouths3/terrain_mouths.npz` | cb5326053f7ff554cfc2e610367df6c87f0fb6da1b37d828ec774dbcb89088f3 |
  14| | Agua parcheada | `water-mouths/pieces.json` | 7399885fa58befd05d4237a77d7fad9505771f5c01094e2491482cf78231b36f |
  15| | Terreno con cauces | `fit3/terrain_pilot.npz` | ec6aa61a49d7ae1e3c0c45bade9105c67f7f05a60c3f52864133a60490d2cccb |
  16| | Agua con cauces | `fit3/water/pieces.json` | f8f35985b33ec6ba7c80c93024341d3ca4e6db8d3e89d7ef3790d2828ea5bce9 |
  17| | Terreno candidato | `shore4/terrain_shore.npz` | e144ad1a131ba90f6b9ccf55d867d45da3b4996e4eb53387bb0a692dba39e0e6 |
  18| | Mundo | `package/out/Addons/narva_trial.pbo` | 0ab61bab7e400ffe91a11f4b010b649b3c99911b92a9ab698cd9d8085eb84cd2 |
  19| | PBO de agua | `package/out/Addons/baltic_water_v30.pbo` | 6ebc62cbf29c8399cf45f26432dcb41e57132095b7abdde1b99e78e21dda4eb1 |
  20| | Misión de lectura | `mission/BalticShoreSdfCandidateV1.BalticTrial/init.c` (linter PASS) | 0b9eecc09b6d53e8bbe7065fc3ef7d0076390a387c94f7355a851a3f66ed9253 |
  21| 
  22| El mod nuevo `@DayZ_Baltic_ShoreSdfCandidate` lleva los dos PBO, comprobados por hash al copiarlos, y la misión
  23| `BalticShoreSdfCandidateV1.BalticTrial` está en `mpmissions`. No se tocó ningún mod ni misión existente.
  24| 
  25| ## Cadena
  26| 
  27| | Paso | Herramienta | Qué hace |
  28| |---|---|---|
  29| | 1 | `tools/water/profile_river_mouths_v30.py` | El agua sin plano (≤ 0,80 m) que toca el mar o el delta pasa a una rampa geodésica, de 0,50 m en el lado del mar a 0,80 m en el primer plano. Corte de mar del candidato: 0,51 m |
  30| | 2 | `tools/water/patch_water_tiles_v30.py` | Regenera solo las teselas de 48 m cuyas celdas cambian (escrita por GLM; ver §Delegación) |
  31| | 3 | `tools/water/fit_channel_pieces_v30.py --overlap-all --no-pad --sea-cut 0.51` | R1 con solape en todo el tramo; R2 y R3 igual que el piloto; sin banco de calibración |
  32| | 4 | `tools/terrain/fit_shore_crossings_v30.py --reg 0.05 --dry-raise-max 0.4 --levee-cap 0.15 --corridor-margin 0` | Mínimos cuadrados acotados para que el terreno cruce el agua visible donde el contorno de diseño corta cada arista nativa |
  33| | 5 | `tools/terrain/build_surface_v30.py` y `build_v30_package.ps1` del checkout principal | Superficie y paquete; la copia del worktree no tiene `packages/baltic-road-v29` |
  34| 
  35| ## Resultados offline
  36| 
  37| - **Desembocaduras.** Se re-perfilan 3 componentes: Narva (2.397 vértices, 1.435 m), borde del delta del Neva (1.432,
  38|   945 m) y EDGE1/2 (410, 189 m). Hay 4.575 celdas de plano nuevas o cambiadas, la más baja a 0,50 m (bajamar). Bajan 6
  39|   lechos, como máximo 0,156 m, y ninguno está protegido.
  40| - **Agua.** Se regeneran 146 teselas (24 piezas retiradas y 309 nuevas). Las demás piezas quedan idénticas a las
  41|   deduplicadas.
  42| - **R1 con solape.** Lleva 8 piezas. Quedan 0 celdas sin cubrir (antes 29), 1 vértice mojado sin cubrir (antes 15) y
  43|   ninguno al aire. A alturas de juego no se prevé ningún hueco en R1, R2 ni R3.
  44| - **Orillas.** Desvío entre el cruce del terreno con el agua y el contorno de diseño, por arista nativa (p50 / p90, en m):
  45| 
  46|   | Clase | Antes | Después |
  47|   |---|---|---|
  48|   | Todas (124.142 aristas) | 0,517 / 2,441 | 0,082 / 1,591 |
  49|   | Lagos | 0,351 / 1,275 | 0,033 / 0,666 |
  50|   | Navegables | 2,071 / 4,567 | 0,974 / 3,892 |
  51|   | Ríos | 0,441 / 1,793 | 0,082 / 1,083 |
  52|   | Arroyos | 0,973 / 2,566 | 0,309 / 1,521 |
  53|   | Lagunas | 0,388 / 1,506 | 0,040 / 0,777 |
  54|   | Cauces vanilla | 0,618 / 1,775 | 0,106 / 1,397 |
  55| 
  56|   - Cambian 91.857 vértices (|Δ| p50 0,20 m, p90 0,40 m).
  57|   - El tope de dique (0,15 m sobre la tierra exterior) deja 7.045 vértices de primera fila sobre su exterior, frente a
  58|     6.162 antes. Sin el tope eran 9.092.
  59|   - Del desvío que queda por encima de 1 m, el 38,5 % son aristas con un extremo protegido y el 47,3 % vértices mojados
  60|     ya en el calado mínimo de 0,10 m.
  61| - **Puertas.**
  62|   - `verify_terrain_v30 --sea-cut 0.51`: solo fallan R2/R3 y Narva.
  63|   - `verify_channel_reaches_v30.py`: 0 fallos fuera de las celdas retiradas. Dentro de R2/R3 quedan 33 vértices mojados a
  64|     menos de 2 cm bajo la pieza, ya presentes en el ajuste de cauces (34 antes de las orillas).
  65|   - Narva: la diferencia heredada de las 4 lagunas restauradas (1,84 m), igual que la base.
  66|   - Taludes de tierra ≤ 35°. Triángulos de orilla de más de 35°: 3.060 (base 3.950).
  67|   - Carreteras: PASS, 100 cadenas y 76.536 estaciones, con los mismos máximos que d5dadae8.
  68|   - Muestras secas congeladas: 463/463.
  69|   - Los 13 puntos someros del margen de oleaje quedan idénticos (radio de 24 m fijo).
  70|   - Las caras de los 23 corredores, exactas.
  71| - **Figura.** `offline/waterline-candidate.png`: rojo antes, azul después y negro el contorno.
  72| 
  73| ## Motor
  74| 
  75| **Run 8aaa58a7, candidato.** Lectura PASS_VANILLA_CHANNEL_READBACK:
  76| - las 99 piezas en su sitio exacto (≤ 0,65 mm);
  77| - concordancia con la regla del motor del 99,67 % en R1 y del 100 % en R2 y R3;
  78| - 0 huecos a alturas de juego;
  79| - mar a 0,544 m (bajamar).
  80| 
  81| **Run bedb362b, control (ShoreWaveV30).** Sin piezas vanilla, como se esperaba: 7 huecos en R2 y 281 en el banco.
  82| 
  83| Las capturas son 31 vistas idénticas en los dos runs (`runtime/shots-manifest.json`, con hash). Hay parejas en `visual/`.
  84| 
  85| - **Orillas navegables:** el control enseña escalones rectos de 90° y el candidato los cambia por una línea suave.
  86|   - Se ve claramente en SHORE4, SHORE6 y SHORE7.
  87|   - En SHORE2 la orilla queda más natural; en SHORE0 y SHORE3 el cambio es sutil.
  88| - **Lagunas (SHORE5):** dejan de verse rectangulares.
  89| - **R3:**
  90|   - De cerca, el candidato cambia las terrazas por agua continua en pendiente (R3a_oblique, R3a_low).
  91|   - Desde el aire, las piezas rectas forman una banda en zigzag de anchura uniforme, más artificial que el control
  92|     (R3_aerial).
  93| - **R2:** agua continua, pero con costuras y esquinas de pieza visibles (R2b_low, R2_aerial).
  94| - **R1:** igual que el control en las vistas cercanas.
  95| - **Banco de calibración:** ya no aparece.
  96| - **Desembocaduras (MOUTH0/1):** a esta distancia y en bajamar no se aprecia escalón en ninguno de los dos.
  97| - **Manchas oscuras con interior granulado:** salen sobre tierra en uno u otro run y en sitios distintos. El candidato
  98|   las tiene en R1_aerial y el control en EDGE1_aerial y FLOOD1; el piloto las tuvo en EDGE1. Las teselas de superficie
  99|   son iguales en esos sitios y no es agua: la tierra de esas vistas está a 1,40 m o más y el mar del motor no pasa
 100|   de 1,25 m (§Agua visible frente al diseño). Es un efecto de render dinámico. En el run 3ba786ef, con la misma
 101|   cámara en EDGE1_aerial, la mancha sale en 1 de 5 capturas a lo largo de 2,5 min y desaparece en las siguientes
 102|   (`variants/EDGE1_blotch_sequence.jpg`). El servidor mantuvo la nubosidad en 0,10 todo el tiempo; la captura con
 103|   mancha llegó justo después de pedir 0,6, que la misión no aplicó. Candidatas: sombra de nube en el cliente o carga
 104|   de texturas; no se distinguen desde el cliente.
 105| 
 106| ## Agua visible frente al diseño (BALTIC-016)
 107| 
 108| `tools/water/audit_visible_water_v30.py` (escrita por GLM, §Delegación) compara, en una malla de 2 m sobre todo el
 109| mapa, el agua que enseña el motor (mar, planos pond y láminas de pieza) con el contorno de diseño: water_v3, arroyos de
 110| tier ≥ 2.500 m, lagos de contour-v2 y el mar v33 suavizado, las mismas fuentes que el constructor V30. Cuenta como
 111| inundada el agua visible a más de 3 m fuera del contorno. `tools/water/classify_visible_water_v30.py` asigna cada
 112| mancha a una zona. El mar se evalúa a 0,54 m (bajamar), 1,00 m (pleamar) y 1,25 m (pleamar con la cresta de ola de
 113| 0,25 m de `evidence/v30-shore-wave-2026-10-03/temporal-v3-result.json`).
 114| 
 115| | Zona, en bajamar | Base d5dadae8 | Candidato | Lectura |
 116| |---|---|---|---|
 117| | Borde oeste | 5,02 ha | 5,02 ha | Artefacto: la columna 0 de la máscara de mar v33 no es mar; en el juego es mar junto a mar |
 118| | Costa | 3,77 ha | 3,77 ha | Franja de marea: 7,69 ha en pleamar y 10,34 ha con cresta. La playa (≥ 0,80 m) se moja por diseño |
 119| | Narva (protegido) | 1,22 ha | 1,23 ha | Bandas estrechas en la orilla sureste del río (vistas R1, EDGE1 y FLOOD1) y 2.924 m² de lagos de diseño secos al lado; terreno V29 sin tocar |
 120| | Delta | 1,01 ha | 1,01 ha | Canales del Neva excavados desde la fuente OSM completa (BALTIC-013), más anchos que water_v3; solo 932 m² caen dentro de los corredores de 24 m |
 121| | Orillas | 3,68 ha | 2,67 ha | Astillas a lo largo de ríos y lagos por la malla de 6 m; el candidato quita el 27 % |
 122| | Tierra adentro | 0 | 0 | 28 m² en pleamar |
 123| 
 124| - Total: base 14,7 / 19,0 / 22,5 ha y candidato 13,7 / 17,9 / 21,2 ha (bajamar / pleamar / cresta).
 125| - Frente a la base, el candidato quita 1,04 ha de agua inundada y añade 316 m² junto a las rampas de EDGE y del Neva.
 126|   Los huecos (agua de diseño que sale seca) bajan 328 m² netos; los nuevos son 213 puntos de 20 m² como mucho.
 127| - El mar no alcanza la tierra: a 1,25 m solo quedan por debajo 19 vértices de tierra, todos de playa, y ninguno en
 128|   Narva ni en el resto del mapa. Por eso las manchas oscuras de las capturas no son agua del motor.
 129| - Ficheros: `audit/zones.json` (zonas y las 12 manchas mayores de cada una, con el hash del terreno y de las dos
 130|   herramientas), `audit/*-audit.json` (las 6 auditorías), `audit/zones-base-low.png` y `audit/zones-cand-low.png`
 131|   (mapa por zonas) y `audit/crops-base.png` (recortes en las vistas con manchas, el delta, el borde y la costa).
 132| - No verificado: dónde vio Guillermo lo inundado. La auditoría compara mapas; no proyecta las capturas.
 133| 
 134| ## Delegación (GX10, GLM-5.3-Flash-EXL3, API directa con streaming)
 135| 
 136| | Lane | Encargo | Resultado | Recepción |
 137| |---|---|---|---|
 138| | A | Auditoría de agua visible frente al diseño | Sin contenido tras 80 min de razonamiento; corte por tiempo | Relanzada con esfuerzo `medium` |
 139| | A2 | La misma auditoría, con esfuerzo `medium` | `stop`, 25 min, 34k tokens | Aceptada con un cambio: la ruta a `tools/terrain`. Autoprueba PASS; firmas y orientación de la malla comprobadas contra `v30_common.py` y `engine_water_model.py`; usa las mismas fuentes de diseño que el constructor V30. Límites anotados en su cabecera: franja del borde oeste, delta de water_v3 y desvíos cuantizados a 2 m |
 140| | B | `patch_water_tiles_v30.py` | `stop`, 46 min, 50,6k tokens | Aceptada con un cambio: el brief pedía área exacta por banda y eso eliminaba los solapes de 0,01 m entre teselas del constructor original. Se reconstruye desde una ventana una celda más ancha y la comprobación admite ese margen (error máximo 1,92 m²) |
 141| | C | Revisión ciega de las herramientas de desembocaduras y orillas | `stop`, 75 min (`review/glm-review-raw.md`) | 1 crítico refutado: scipy 1.18.1 tiene `return_predecessors=False` por defecto y la herramienta funcionó. 2 riesgos teóricos (taludes y margen de orilla tras subir niveles) con 0 fallos en las puertas ejecutadas. 1 cosmético. Las notas de premisa se recogen en Límites |
 142| 
 143| ## Variantes exploratorias y diagnóstico de cauces (tras el aviso de merge)
 144| 
 145| Variantes del candidato con un solo cambio cada una, mismas entradas y argumentos (`variants/variants.json`, con
 146| hashes, desvíos por clase, límites del ajuste y puertas). Ninguna se adopta.
 147| 
 148| | Variante | Arroyos p50/p90 | Ríos p50/p90 | Lagos p90 | Diques | Puertas |
 149| |---|---|---|---|---|---|
 150| | Candidato (surco fijo) | 0,309/1,521 m | 0,082/1,083 m | 0,666 m | 7.045 | Las del candidato |
 151| | Calado 0,03 m a ≤ 2 m del contorno | 0,308/1,520 m | 0,073/1,057 m | 0,417 m | 6.946 | Falla la de 0,10 m en 3.683 vértices, por diseño; el resto igual |
 152| | Sin tope de dique | 0,305/1,509 m | 0,081/1,080 m | 0,647 m | 7.928 | No ejecutadas |
 153| | Surco libre hasta 0,10 m de calado | 0,041/0,607 m | 0,036/0,746 m | 0,667 m | 6.903 | Las mismas que el candidato |
 154| | Surco con calado ≥ 0,25 m | 0,239/1,246 m | 0,063/0,899 m | 0,665 m | 7.045 | No ejecutadas |
 155| | Surco con calado ≥ 0,40 m | 0,289/1,406 m | 0,071/0,967 m | 0,666 m | 7.045 | No ejecutadas |
 156| 
 157| «Diques» cuenta tierra de primera fila más de 0,2 m por encima de toda su tierra exterior (base d5dadae8: 6.162).
 158| 
 159| - **Calado 0,03 m.** Cambia 5.212 m² de agua visible en todo el mapa, 56 m² como mucho por tesela de 120 m. Paquete
 160|   construido sin desplegar (mundo `da68a129…`). No se probó en motor: el cambio no se ve a distancia de juego.
 161| - **Tope de dique.** No es lo que frena los ríos estrechos: quitarlo apenas mueve los desvíos y añade 883 diques.
 162| - **Surco.** Los 9.975 vértices mojados fuera del contorno son todos de surco (`diagnosis/narrow-groove-outline.json`):
 163|   dan la continuidad de los cauces estrechos sobre la malla de 6 m, y fijarlos ancla la orilla en escalera. Con el
 164|   surco libre cambian 4,93 ha de agua visible.
 165|   - Se probó en motor como `@DayZ_Baltic_ShoreGrooveCandidate` (mundo `bd0483a3…`, run 16aca2e1), frente al candidato
 166|     en las mismas 8 vistas (run f084ba3d). Poses y manifiestos con hash en `variants/`.
 167|   - En GROOVE2 desaparece la escalera de 90° del arroyo (`variants/GROOVE2_stream.jpg`).
 168|   - En GROOVE0 y GROOVE5 el arroyo pasa de banda o poza ancha a línea estrecha. Con 0,10 m de lámina se ve casi
 169|     transparente y en primer plano parece seco (`variants/GROOVE5_stream.jpg`).
 170|   - Exigir más calado en el surco devuelve la mayor parte de la escalera: con 0,25 m queda el 26 % de la mejora en el
 171|     p50 de los arroyos y el 30 % en el p90.
 172| - **Cauces vanilla.** Las costuras no son escalones de altura: entre piezas el salto es de 1 mm de mediana y 8 mm en
 173|   p90, y solo 0,8 m de 392 m de costura de R2 pasan de 3 cm (`diagnosis/seam-check.json`). En cambio, el 79–81 % del
 174|   agua visible de R2 y R3 tiene dos o más láminas de pieza, con la de abajo a 5 cm o más en 1.936 m² de R2
 175|   (`diagnosis/layer-overlap-check.json`).
 176|   - Comprobado con cámara cenital (run 2e3c51b1, `variants/nadir-2e3c51b1-shots-manifest.json`): las líneas rectas
 177|     que se ven dentro del agua de R2 no coinciden con ningún borde de pieza del modelo, ni de contorno, ni interno, ni
 178|     enterrado, para focales de 850 a 1.760 px (`variants/R2b_nadir_piece_edges_f850.jpg`). La proyección registra
 179|     el eje del tramo y, con 1–2 m de margen, el contorno del agua prevista. La hipótesis de las láminas dobles no
 180|     se sostiene.
 181|   - El LOD visual de las piezas resultó idéntico al roadway (los mismos 8 vértices), así que esa pista cae.
 182|   - Lo que sí encaja son las isolíneas de profundidad del lecho bajo la lámina. Con f = 1.000 px, la de 0,30 m cae
 183|     sobre la línea transversal visible y la de 0,20 m junto a la diagonal de debajo
 184|     (`variants/R2b_nadir_depth_contours_f1000.jpg`).
 185|   - Bajo una lámina inclinada, la profundidad es lineal en cada triángulo de 6 m, y sus isolíneas son polilíneas
 186|     rectas con cualquier ángulo. Lectura: compatible, no demostrada, porque la focal real no se conoce.
 187|   - Si se confirma, las costuras vienen de la forma del lecho (profundidad visible de 0,07 a 0,49 m, p10–p90) y no
 188|     de las piezas. Un lecho de profundidad casi constante dentro del cauce las reduciría, pero R2 y R3 no tienen
 189|     ningún vértice mojado interior: todos tocan tierra, porque los cauces miden 1–2 vértices de ancho. Las isolíneas
 190|     son inherentes a esa anchura sobre la malla de 6 m, y fijar la profundidad movería la orilla.
 191|   - Corrección del 04-10 por la mañana. Guillermo lee esas líneas como solapes y piezas mal colocadas. Las líneas
 192|     donde la lámina de arriba pasa de una pieza a otra, proyectadas a f = 850 px, caen en las mismas zonas de
 193|     solape entre piezas consecutivas, aunque no calcan su forma. La explicación más probable es la suya: costuras
 194|     de solape por colocación. Las isolíneas quedan como alternativa sin confirmar.
 195|   - Los planos pond que sobreviven en el margen de los tramos son poca cosa: 99 m² visibles en R2 y 51 m² en R3
 196|     (`diagnosis/margin-planes-check.json`).
 197| 
 198| ## Límites y decisiones para Guillermo
 199| 
 200| - **Ríos estrechos con surco sobre llanura.** La línea de agua sigue la malla de 6 m: los vértices del surco no suben,
 201|   para proteger la continuidad del lecho, y la llanura está al margen mínimo. Ejemplo en la ventana x 9730 z 140 de la
 202|   figura. Hay que elegir entre arroyos anchos y escalonados con agua visible (candidato) y arroyos sobre el contorno
 203|   pero someros y casi transparentes (surco libre, probado en motor); los calados intermedios recuperan poco
 204|   (§Variantes exploratorias).
 205| - **Calado mínimo relajado (variante exploratoria, sin paquete).** Con 0,03 m de calado a ≤ 2 m del contorno, los lagos
 206|   bajan su p90 de 0,666 a 0,417 m y las lagunas de 0,777 a 0,615 m (`offline/waterline-shallow-vs-candidate.png`).
 207|   Requiere rebajar la puerta de 0,10 m cerca del contorno. Cambia poco a la vista: 5.212 m² en todo el mapa.
 208| - **Cauces vanilla.** Arreglan el agua escalonada y su borde casi nunca queda al aire: 2 m en R1, 1,5 m en R2 y 0 m en
 209|   R3, de 900–1.170 m de perímetro por tramo (`diagnosis/piece-edge-check.json`). En R3 el borde que se ve es el
 210|   cruce del terreno con la lámina sobre la malla de 6 m: 1.817 m² de agua visible frente a 552 m² de diseño, 440 m²
 211|   a más de 1 m fuera del contorno; de ahí el zigzag de anchura uniforme. En R2 se ven las costuras entre piezas
 212|   solapadas. Estrechar la banda mojada da poco: en R3 solo 20 vértices mojados quedan a más de 1 m fuera del contorno,
 213|   y en R2 y R3 solo 9 pasan a tierra sin cambiar un plano vecino (`diagnosis/reach-band-check.json`). Afinar R3 pide
 214|   orillas más altas junto al arroyo o aceptar esa anchura; no se ha probado.
 215| - **Fuera de alcance esta noche.** La costa de marea y el delta no se reperfilan (allí el agua ≤ 0,45 m y la tierra
 216|   ≥ 1,40 m). Las aristas cuyo extremo contradice el signo del contorno no se ajustan. Con bandas de 25 mm, el plano más
 217|   bajo de una arista queda hasta una banda fuera.
 218| - **No adoptable aún.** No hay navmesh nueva ni IA física.
 219| 
```

### `bugs.md` (líneas 19–19, 27–29)
```
  19| | BALTIC-007 |PARCIAL; ABIERTO|Orillas y relieve facetado|V30: orilla derecha de Narva sur aún escalonada en visual-tour-resume/01-narva-south.jpg, fuera de la protección del puente; cima visible sin cuadros azules. Inventario global03-10: 4.149 caras mixtas >35°, no equivalentes a defectos visuales confirmados; sectores en evidence/v30-shore-inventory-2026-10-03. No aceptación global. 04-10, a petición de Guillermo («falta smoothing en los bordes»): la línea de agua calca la malla de 6 m porque la altura se asigna por clase de vértice; tierra +0,45 m y primer vértice mojado −0,28 m (medianas), navegables −3,49 m en el primer vértice (evidence/v30-vanilla-channel-pilot-2026-10-04/diagnosis/shore-profile-d5dadae8.json). Candidato nocturno (tools/terrain/fit_shore_crossings_v30.py: el terreno cruza el agua donde el contorno corta cada arista, con todas las puertas como cotas): desvío p50/p90 0,517/2,441 → 0,082/1,591 m; lagos 0,033/0,666, navegables 0,974/3,892 (corredores fijos). En motor (run 8aaa58a7 frente a bedb362b) desaparecen los escalones rectos en SHORE4, SHORE6 y SHORE7. Quedan: ríos estrechos con surco sobre llanura (el surco no sube y la llanura está al margen mínimo) y el calado mínimo de 0,10 m, que impide acercar la línea al contorno en lagos y lagunas (variante exploratoria con 0,03 m: lagos p90 0,417). Tras el aviso de merge (variants/variants.json): los 9.975 vértices mojados fuera del contorno son todos de surco; con el surco libre hasta 0,10 m de calado, arroyos p50/p90 0,309/1,521 → 0,041/0,607 m y ríos 0,082/1,083 → 0,036/0,746 m, con las mismas puertas. En motor (run 16aca2e1 frente a f084ba3d) desaparece la escalera de los arroyos, pero con 0,10 m el agua se ve casi transparente. Con calado ≥ 0,25 m en el surco queda el 26 % (p50) y el 30 % (p90) de la mejora de los arroyos. Quitar el tope de dique no ayuda (+883 diques). evidence/v30-shore-crossing-candidate-2026-10-04 Candidato v2 «pulido» (04-10, tarde; evidence/v30-polish-candidate-2026-10-04): corredor del Luga liberado en la cabecera (fit_shore_crossings_v30.py --free-corridor-box 10150,3700,10700,4600) y lagos de la zona suavizados (apertura de 8 m en los de lados rectos, Chaikin en los escalonados; tools/terrain/polish_luga_head_v30.py). En la caja, línea de agua p50/p90/p99 0,070/2,17/4,39 → 0,076/1,92/3,88 m frente al candidato de Narva. Sin ver en motor.|
   …
  27| | BALTIC-015 |PILOTO EN MOTOR; LANCHA PASS; V2 SIN HUECOS EN TRAMOS; REVISIÓN VISUAL PENDIENTE|Agua escalonada discontinua en cauces con pendiente|Causa: planos pond horizontales sobre lecho inclinado. Chernarus usa piezas river_24/stream_14 inclinadas (sonda af204798). Piloto 04-10 con tres tramos, mundo 3e7987be y agua e56aa9f1: lancha PASS en R1 (run e5ccbe6a); el motor coloca las 100 piezas exactas (run 8392533a). El desfase de +1,5 a +6 cm, los huecos y la mediana de 10 cm en R3 eran efecto de la sonda V1 (consulta desde suelo + 50 m) y de la regla del agua roadway (tools/water/engine_water_model.py, 1.940/1.941 filas); a alturas de juego no hay huecos previstos y los faldones difieren ±0,07·escala, como en vanilla. Lectura V2 a alturas de juego (runs b295208e y 63008090): ≥99,65 % de concordancia con la regla y 0 huecos en los tramos; el control con el paquete actual (337562e3) deja 7 huecos en R2. Capturas: piloto 19/19, control 13/19, sin revisar. Variante: escalón río-mar de unos 26 cm en desembocaduras (plano de 0,80 m junto al mar a 0,54 m; 4 puntos). Evidencia evidence/v30-vanilla-channel-pilot-2026-10-04. Noche 04-10: el mar es de marea (0,50–1,00 m) y el escalón es de bajamar; el candidato re-perfila las 3 componentes sin plano (Narva, delta del Neva, EDGE1/2) en rampa 0,50 → 0,80 m con corte 0,51 m (tools/water/profile_river_mouths_v30.py, tools/water/patch_water_tiles_v30.py). R1 con solape total: 0 celdas sin cubrir y lectura PASS_VANILLA_CHANNEL_READBACK (run 8aaa58a7: 99,67 % en R1, 100 % en R2/R3, 0 huecos, sin banco). Visual: R3 sin terrazas de cerca, pero desde el aire se ve un zigzag de anchura uniforme; en R2, costuras y esquinas de pieza. Medido (diagnosis/piece-edge-check.json): el borde de las piezas casi nunca queda al aire (2 m en R1, 1,5 m en R2 y 0 m en R3, de 900–1.170 m de perímetro); el zigzag de R3 es el cruce del terreno con la lámina sobre la malla de 6 m, con 1.817 m² de agua visible frente a 552 m² de diseño. Estrechar la banda mojada da poco: solo 9 vértices pasan a tierra sin cambiar un plano vecino. Costuras de R2: los saltos de altura entre piezas son de milímetros (p90 8 mm), pero el 79–81 % del agua visible de R2/R3 tiene dos o más láminas, con la de abajo a 5 cm o más en 1.936 m² de R2 (diagnosis/layer-overlap-check.json). Prueba cenital (run 2e3c51b1): las líneas rectas visibles dentro del agua de R2 no coinciden con ningún borde de pieza del modelo para focales de 850 a 1.760 px, así que la hipótesis de las láminas dobles no se sostiene. El LOD visual es idéntico al roadway. Las líneas encajan, en cambio, con isolíneas de profundidad del lecho (0,20–0,30 m) bajo la lámina inclinada: compatible, no demostrado (focal desconocida). Si se confirma, se arregla con un lecho de profundidad casi constante, no tocando las piezas; pero en R2/R3 todos los vértices mojados tocan tierra (cauces de 1–2 vértices de ancho), así que eso movería la orilla. Corrección (04-10, mañana): Guillermo las lee como solapes y colocación, y las líneas de cambio de pieza proyectadas caen en las mismas zonas de solape; esa es la lectura más probable, a resolver con la colocación (ver cómo encadena Chernarus). evidence/v30-shore-crossing-candidate-2026-10-04. Chernarus frente a nuestros tramos (04-10, tarde; tools/water/compare_channel_joints_v30.py, evidence/v30-polish-candidate-2026-10-04/joints): área con dos láminas o más 0,33 % en ríos y 0,49 % en arroyos de Chernarus, frente a 58/73/75 % en R1/R2/R3. Chernarus encadena canto con canto (junta a -0,044 m) y gira dentro de las piezas curvas (desvío de rumbo en junta p50 0,44°); nosotros solapamos un par de faldones (overlap_from=None en R2/R3 y --overlap-all, fit_channel_pieces_v30.py:263) y giramos en las juntas (8,8° en R2, 11,4° en R3). Confirma la lectura de Guillermo: las costuras son solapes de colocación.|
  28| | BALTIC-016 |ABIERTO; AUDITADO, FALTA CONFIRMAR|Zonas inundadas que no deberían|Señalado por Guillermo el 04-10. Barrido del terreno d5dadae8: 0 vértices de tierra bajo el mar (0,54 m); planos sobre tierra en 200 vértices (≈7.200 m²) cerca de Narva; 33 grupos de bordes de plano al aire. Falta localizar lo que ve Guillermo (evidence/v30-vanilla-channel-pilot-2026-10-04/diagnosis/flood-edge-pilot.json). Noche 04-10: en las capturas aparecen manchas oscuras con interior granulado sobre tierra, en sitios distintos según el run (candidato R1_aerial; control EDGE1_aerial y FLOOD1; piloto EDGE1); las teselas de superficie son iguales allí, así que es un efecto transitorio de render, candidato a explicar lo visto. Las vistas sobre Narva (FLOOD0/1) muestran grandes láminas someras del Narva (terreno V29), iguales en ambos paquetes. Auditoría sistemática (tools/water/audit_visible_water_v30.py, escrita por GLM y revisada, y tools/water/classify_visible_water_v30.py) del agua visible a más de 3 m fuera del contorno, con el mar a 0,54/1,00/1,25 m (bajamar, pleamar, pleamar con cresta): base 14,7/19,0/22,5 ha y candidato 13,7/17,9/21,2 ha. En bajamar: borde oeste 5,0 ha (artefacto de la máscara de mar v33), costa 3,8 ha (7,7 en pleamar), Narva protegido 1,2 ha, delta 1,0 ha (canales ensanchados desde OSM en BALTIC-013; water_v3 es más estrecho) y astillas de orilla 3,7 → 2,7 ha con el candidato; tierra adentro, nada. Las manchas oscuras no son agua: la tierra de esas vistas está a ≥ 1,40 m y en todo el mapa solo 19 vértices de tierra, todos de playa, quedan bajo 1,25 m. Falta que Guillermo confirme dónde lo vio (audit/zones-base-low.png). Run 3ba786ef: con la cámara fija en EDGE1 la mancha sale en 1 de 5 capturas en 2,5 min y luego desaparece, con la nubosidad del servidor en 0,10: efecto dinámico de render (sombra de nube o carga de texturas), no terreno ni agua. Mañana del 04-10, con capturas de Guillermo, la explicación más probable es esta: build_surface_v30.py pinta el fondo de lagos y charcas casi negro (BED_RGB) con grava, más un anillo de grava de 15 m, y cuando la lámina, que es un objeto, no se dibuja por distancia o carga, queda una mancha oscura granulada. La «lente» de R1_aerial coincide con el lago de diseño de (2270, 7190). Las charcas vanilla usan la misma clase `pond`, así que el aviso «Unknown object class» no es la causa. Arreglo aprobado: fondo con el tono del terreno y anillo de grava solo en ríos y mar (opciones nuevas --bed-tone land y --shore-ring flowing). Pendiente de construir y ver. evidence/v30-shore-crossing-candidate-2026-10-04 Superficie nueva construida en el candidato v2 (build_surface_v30.py --bed-tone land --shore-ring flowing, evidence/v30-polish-candidate-2026-10-04): grava 67,6 → 64,8 M píxeles; en la vista previa, lagos y charcas pierden el fondo negro y ríos y canal lo conservan. Pendiente de ver en motor.|
  29| | BALTIC-017 |ABIERTO; MEDIDO|Agua colgada con diques|04-10, tarde, al unir el Luga con lake_014: el río y los lagos de la cabecera están a ~4,15 m sobre un terreno a ~3,0 m y los sujetan diques a nivel + 0,35 m (regla de orillas del constructor), así que se ven como balsas sobre terraplén. Censo (tools/water/census_perched_water_v30.py, de GLM con correcciones): de 631 masas de agua estancada, 111 lagos (7,0 km²) quedan más de 0,3 m por encima del terreno natural a 12–36 m, y 190 masas tienen diques de más de 0,5 m. Mapa en evidence/v30-polish-candidate-2026-10-04/census/map.png. Arreglo posible: niveles de lago derivados del terreno natural; decisión de diseño pendiente. evidence/v30-polish-candidate-2026-10-04|
```

### `HANDOFF.md` (líneas 3–23)
```
   3| <!-- LIVE-STATE:START -->
   4| project: DayZ_Baltic_12km
   5| updated: 2026-10-04
   6| owner: Claude (Opus 5.5), ejecutor/integrador por petición viva del 03-10 tras revisar el relevo de Codex. Sin concurrencia con Codex ni con Exta.
   7| status: CANDIDATO_V2_PULIDO_DESPLEGADO_SIN_VER; base 1.0 NO aceptada. Tarde 04-10: candidato v2 «pulido» sobre la cadena de Narva: une el Luga con lake_014, libera el último tramo del corredor, suaviza los 17 lagos de la cabecera y estrena la superficie con fondo del tono del terreno. Puertas iguales a las del candidato de Narva y carreteras PASS; sin ver en motor porque la caja la ocupaban otras sesiones. Medido además: cauces frente a Chernarus (doble lámina 0,3–0,5 % en Chernarus frente al 58–75 % de R1–R3; BALTIC-015) y agua colgada en todo el mapa (111 lagos más de 0,3 m sobre el terreno natural; BALTIC-017).
   8| plan: v2 «pulido» aprobado por Guillermo el 04-10 por la mañana (Fondo y anillo; Conectar y liberar tramo; Suavizar esquinas), hecho salvo la vista en motor; Narva en plans/v30-narva-shore-candidate.md; antes plans/v30-shore-crossing-candidate.md (aprobado 03:30 del 04-10, hecho).
   9| candidate: E:/DayZ-Baltic-Build/v30-polish: terreno 88ed0268 (shore-polish); pulido 931632d6 + sd 6817bf78; agua parcheada 1e06bc24 + cauces 0907920a; base la cadena de Narva (mouths-moats e9cb9d9c). La primera construcción, anterior a la revisión de GLM, queda en *-r1. Evidencia evidence/v30-polish-candidate-2026-10-04.
  10| deployed: @DayZ_Baltic_PolishCandidate = mundo f6ca1cb6 + agua 0cca7866 (v2, misión BalticShoreSdfCandidateV1, sin ver en motor; la r1 retirada a E:/DayZ-Baltic-Build/v30-polish/deployed-r1). @DayZ_Baltic_NarvaCandidate = 011a4086 + agua c9ba3bc8 (sin ver). @DayZ_Baltic_ShoreSdfCandidate = 0ab61bab + 6ebc62cb (misión BalticShoreSdfCandidateV1 en mpmissions, sin NM). @DayZ_Baltic_ShoreGrooveCandidate = bd0483a3 + 6ebc62cb (surco libre). @DayZ_Baltic_CauceVanillaPilot = 3e7987be + e56aa9f1 (piloto). @DayZ_Baltic_ShoreWaveV30_Nav = 7c3fd0fd/NM 94be04c1 + 339fa17f, último paquete completo. Conservados ShoreWaveV30, ContinuityV30_Nav, DeltaV30_Nav y canónico 69140d41.
  11| physical: run 40dbee77 en el paquete nuevo: 4/12 PASS (laguna y colinas); casos changed_bank sin ejecutar porque el cliente se cerró. NM nueva: 138 teselas con cambio estructural, todas junto a las orillas tocadas. Repetir IA y grafo tras BALTIC-015.
  12| water: piloto run 8392533a: piezas 100/100 a ≤0,65 mm y ≤4,4e-5°, escala exacta. La regla del motor (tools/water/engine_water_model.py) reproduce 1.940/1.941 filas; a alturas de juego, 0 huecos previstos y parte plana ≤1 cm en 96,5/87,8/83,9 % (R1/R2/R3); faldones ±0,07·escala, como vanilla; R1 a tope deja huecos en curvas. Lectura V2 ejecutada (runs b295208e y 63008090): 0 huecos en tramos (3 previstos en el banco), ≥99,65 % de concordancia; control 337562e3 con 7 huecos en R2. Antes: V4 1.332/1.332 y serie V3 13 someros 302/302.
  13| editor: E:/DayZ-Baltic-Build/editor-v30-delta/native-asc/base_v30_shorefinish.tv4p = terreno 40d8 + 17.637 aguas dedup + 9 puentes; export 5ccb33dc persistido. No reimportar el CSV de agua. Gate estricto FAIL solo por el id del terminador (comparador v2 pendiente).
  14| surface: TB aplazado hasta congelar la base; satélite guardado (TV4P 18:40:38), máscara y Generate Layers sin ejecutar; fuentes en P:/baltic_editor_v30_delta/native_sources_continuity.
  15| runtime_lock: 04-10, tarde: sin runs propios ni lease. La caja la ocupó @SimpleGroup (sesión 98c5c0db; quedó abandonada y el daemon la retiró al cerrarse sus procesos) y después LFPowerGrid (sesión c092f4f7, «con el dueño jugando»); no se tocaron. Antes: Guillermo cerró el run de revisión e484a686, y los runs propios de la noche se cerraron en orden.
  16| backup: editor-v30-delta/backups/water-reimport-saved-20261003 (45 archivos, hashes exactos). No borrar build-temp, junctions ni no seguidos históricos.
  17| bugs: 17 IDs. Nuevo BALTIC-017: agua colgada con diques (111 lagos más de 0,3 m sobre el terreno natural, 190 masas con dique de más de 0,5 m). BALTIC-015: Chernarus encadena canto con canto y gira dentro de las curvas; nosotros solapamos (doble lámina 58–75 %). BALTIC-016: superficie nueva construida, sin ver. BALTIC-007: cabecera del Luga pulida, sin ver. BALTIC-009 visual abierto; BALTIC-014 IA parcial en NM nueva; BALTIC-001/010/011 visuales abiertos; BALTIC-012 reloj abierto.
  18| load: BALTIC-008 pospuesto a un sector mapeado; 80–100 jugadores sin verificar. P15 ferroviario futuro.
  19| env: GIS Python C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env (PYTHONUTF8=1). P: subst a DayZ Projects; P:/baltic_water_v30 y P:/baltic_editor_v30_delta apuntan a E:. Sin concurrencia con Exta.
  20| next: (1) Ver @DayZ_Baltic_PolishCandidate con Guillermo cuando la caja esté libre, con las vistas de evidence/v30-polish-candidate-2026-10-04/camera-poses.json: cabecera del Luga, rectángulos, lake_038, fosos de Narva, manchas de R1_aerial y EDGE1 con la superficie nueva, y SHORE4. Avisar del bloque de cliente. (2) Decidir con Guillermo: cauces vanilla solo en ríos anchos, con encadenado canto con canto y curvas como Chernarus (R2/R3 volverían a planos; hoy solapan por --overlap-all y overlap_from=None, tools/water/fit_channel_pieces_v30.py:263); qué hacer con el agua colgada (BALTIC-017: derivar los niveles de lago del terreno natural o dejarlo); la variante del surco (--groove-may-rise) sigue pendiente. (3) BALTIC-016: que Guillermo confirme las manchas con la superficie nueva. (4) Navmesh, V4/V3 e IA sobre el candidato que se acepte. (5) TB al congelar la base.
  21| git: rama v29-base; piloto bf46492, diagnóstico 6c21b32, lectura V2 994d9d4. Desde la noche del 04-10 se commitea en la rama del worktree claude/codex-handoff-review-74f290 (último: candidato v2 «pulido»), pendiente de merge; sin push.
  22| handoff: C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-04-dayz-baltic-noche-orillas-y-auditoria-agua.md (sección «Tarde del 04-10»); antes 2026-10-04-dayz-baltic-piloto-cauces-vanilla.md.
  23| <!-- LIVE-STATE:END -->
```

### `tools/water/fit_channel_pieces_v30.py` (líneas 1–60, 240–300)
```
   1| """Fit vanilla channel pieces to the pilot reaches of terrain V30 (BALTIC-015).
   2| 
   3| Plan: plans/v30-vanilla-channel-water-pilot.md. Per reach:
   4| - Axis from the water design (tests/water_v3 profiles.npz or navigable_samples.npz), resampled every 2 m
   5|   and oriented downstream; current level = the horizontal plane of the cell under each sample.
   6| - New surface: the running minimum of the current level, interpolated between the foot of every step,
   7|   so it never rises above the current water; the downstream anchor takes the lowest plane under the
   8|   last skirt, so both end skirts slide under the horizontal water that stays.
   9| - Pieces: vanilla straights and 10/30 degree curves chained edge to edge downstream (local -z points
  10|   downstream, as in Chernarus), uniformly scaled to cover the wider wet side plus a margin, pitched so
  11|   the flat level meets the new surface at both edges, without roll. The second half of a reach with
  12|   'overlap_from' overlaps straights by one skirt pair (6 m x scale) instead of meeting edge to edge.
  13| - Horizontal water: channel cells of the reach under a vanilla footprint leave their pieces; a piece
  14|   that keeps other cells is re-meshed (tools/navigation/water_mesh.py) without them, and tile-border
  15|   slivers that touch the removed cells go with them.
  16| - Terrain: wet channel vertices of the removed cells drop by the level reduction, so each keeps its
  17|   current depth; nothing rises; level follows the new surface there.
  18| Also places a calibration pad of four pieces on flat dry ground (--no-pad leaves it out); --overlap-all makes
  19| every reach overlap its straights. Writes <out>/terrain_pilot.npz,
  20| <out>/water (source models + pieces.json for build_v30_package.ps1 -WaterSource), <out>/axes.json and
  21| <out>/report.json with the offline gates. Usage:
  22|   fit_channel_pieces_v30.py --terrain <npz> --water <dedup water folder> --library <library.json> --out <dir>
  23|                             [--overlap-all] [--no-pad] [--sea-cut 0.80]
  24| """
  25| from pathlib import Path
  26| import argparse
  27| import hashlib
  28| import json
  29| import math
  30| import shutil
  31| import sys
  32| 
  33| import numpy as np
  34| from scipy.ndimage import binary_dilation, binary_erosion, gaussian_filter1d, uniform_filter, uniform_filter1d
  35| from shapely import make_valid
  36| from shapely.geometry import LineString, Point, Polygon, box
  37| from shapely.ops import unary_union
  38| 
  39| ROOT = Path(__file__).resolve().parents[2]
  40| sys.path.insert(0, str(ROOT / 'tools' / 'terrain'))
  41| sys.path.insert(0, str(ROOT / 'tools' / 'navigation'))
  42| from v30_common import cell_planes  # noqa: E402
  43| from water_mesh import write_water_mesh  # noqa: E402
  44| 
  45| DESIGN = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\tests\water_v3')
  46| PREFIX = 'baltic_water_v30'
  47| BAND, TILE, SEA_CUT = 0.025, 48, 0.80
  48| CHANNEL, STILL = {3, 5, 6}, {2, 4, 7}
  49| STEP = 2.0
  50| REACHES = [
  51|     # R1 moved from the Luga head (a lake/river level mismatch, not a slope) to the only monotone sloped
  52|     # navigable window: Narva_28, 1.62 -> 0.95 m over 300 m, trimmed clear of its junctions.
  53|     {'name': 'R1', 'source': 'navigable_samples.npz', 'key': 'Narva_28', 'box': (2150, 2285, 7105, 7290),
  54|      'family': 'river', 'overlap_from': 0.5, 'smooth_m': 40.0, 'max_scale': 4.0},
  55|     {'name': 'R2', 'source': 'profiles.npz', 'key': 'river_023', 'box': (8196, 8286, 8892, 9258),
  56|      'family': 'stream', 'overlap_from': None, 'smooth_m': 15.0},
  57|     {'name': 'R3', 'source': 'profiles.npz', 'key': 'stream_0255', 'box': (7176, 7446, 5598, 5862),
  58|      'family': 'stream', 'overlap_from': None, 'smooth_m': 15.0},
  59| ]
  60| PAD = [('river_24_24', 1.0, 0.0), ('river_24_24', 1.0, 2.0), ('stream_14_24', 0.5, 2.0), ('river_24_24', 2.0, 1.0)]
   …
 240| 
 241|     # smoothed axis; half-width each piece must cover = farthest reach cell centre + 1 m
 242|     sm = Axis(np.column_stack([gaussian_filter1d(ax.pts[:, k], reach['smooth_m'] / STEP, mode='nearest') for k in (0, 1)]))
 243|     hw = np.zeros(len(sm.d))
 244|     for r, c in cells:
 245|         s, lat, _ = sm.project(cell_centre(r, c))
 246|         k = min(int(round(s / STEP)), len(hw) - 1)
 247|         hw[max(k - 1, 0):k + 2] = np.maximum(hw[max(k - 1, 0):k + 2], lat + 1.0)
 248|     hw = np.maximum(hw, 2.0)
 249|     head = np.degrees(np.unwrap(np.arctan2(sm.tan[:, 0], sm.tan[:, 1])))
 250|     sm_lo = sm.project(ax.pts[i_lo])[0]
 251|     sm_hi = sm.project(ax.pts[min(i_hi, len(ax.pts) - 1)])[0]
 252| 
 253|     def span_scale(a, b):
 254|         ia, ib = max(int(a // STEP), 0), min(int(math.ceil(b / STEP)), len(hw) - 1)
 255|         turn = float(np.ptp(head[ia:ib + 1])) if ib > ia else 0.0
 256|         return float(np.clip(2 * hw[ia:ib + 1].max() / width, 0.15, reach.get('max_scale', 3.0))), turn
 257| 
 258|     pieces = []
 259|     sc0 = span_scale(sm_lo, sm_lo + 24)[0]
 260|     s_cur = max(0.0, sm_lo - 3 * sc0)
 261|     while s_cur < sm_hi + 3 * sc0 - 1.0:
 262|         assert len(pieces) < 600
 263|         overlap = reach['overlap_from'] is None or s_cur >= sm_lo + reach['overlap_from'] * (sm_hi - sm_lo)
 264|         for k in straights:
 265|             sc = span_scale(s_cur, s_cur + length[k] * 3.0)[0]
 266|             for _ in range(3):
 267|                 sc, turn = span_scale(s_cur, s_cur + length[k] * sc)
 268|             if turn <= 8.0 or k == straights[-1]:
 269|                 break
 270|         span = length[k] * sc
 271|         s_c = min(s_cur + span / 2, sm.d[-1])
 272|         centre = np.array(sm.line.interpolate(s_c).coords[0])
 273|         tdir = sm.tan[min(int(round(s_c / STEP)), len(sm.d) - 1)]
 274|         psi = math.atan2(-tdir[0], -tdir[1])           # local +z points upstream, -z downstream
 275|         pieces.append({'reach': reach['name'], 'type': k, 'scale': sc, 'origin_xz': centre.tolist(), 'yaw': psi,
 276|                        'span_m': span, 'turn_deg': turn, 'overlap': bool(overlap),
 277|                        'lat_mid': float(ax.project(centre)[1])})
 278|         s_cur += (length[k] - 6.0) * sc if overlap else span
 279|         sc0 = sc
 280| 
 281|     # vertical: flat plane through both ends at the new surface
 282|     for p in pieces:
 283|         r_, f_ = axes2(p['yaw'])
 284|         half = p['span_m'] / 2
 285|         up_xz = np.array(p['origin_xz']) + half * f_
 286|         dn_xz = np.array(p['origin_xz']) - half * f_
 287|         l_up = float(np.interp(ax.project(up_xz)[0], ax.d, ls))
 288|         l_dn = float(np.interp(ax.project(dn_xz)[0], ax.d, ls))
 289|         theta = math.asin(max(-0.7, min(0.7, (l_up - l_dn) / p['span_m'])))
 290|         flat = fam[p['type']]['flat_y'] * p['scale']
 291|         y0 = l_up - flat * math.cos(theta) - half * math.sin(theta)
 292|         p.update(level_up=l_up, level_down=l_dn, pitch_deg=math.degrees(theta), y=y0, model=fam[p['type']]['model'],
 293|                  up_xz=up_xz.tolist(), dn_xz=dn_xz.tolist(),
 294|                  matrix=matrix(p['yaw'], theta, p['scale'], [p['origin_xz'][0], y0, p['origin_xz'][1]]))
 295|     # visible step where a piece starts over its upstream neighbour: neighbour's flat plane vs this piece's
 296|     for a_, b_ in zip(pieces, pieces[1:]):
 297|         x, z = b_['up_xz']
 298|         b_['step_m'] = abs(plane_at(a_, fam[a_['type']]['flat_y'], x, z) - b_['level_up'])
 299|     return {'axis': ax, 'smooth': sm, 'level': lv, 'surface': ls, 'mono': mono, 'wl': wl, 'wr': wr, 'tol': tol,
 300|             'hw': hw, 's_lo': s_lo, 's_hi': s_hi, 'pieces': pieces, 'anchors': anchors, 'reach_cells': cells}
```

### `tools/terrain/build_v30_water.py` (líneas 40–60, 205–235)
```
  40|     level = np.full((N, N), np.nan)
  41|     cls[v33["ocean"]] = 1
  42|     level[v33["ocean"]] = SEA_LEVEL
  43| 
  44|     # V29 surface levels (lakes and river bands) on the vertex grid.
  45|     lakes = [(shape(f["geometry"]), f["properties"]["level_m"]) for f in contour if f["properties"]["body"].startswith("lake")]
  46|     bands = [(shape(f["geometry"]), f["properties"]["level_m"]) for f in contour if f["properties"]["body"].startswith("river")]
  47|     lake_lv = raster_vertices([g for g, _ in lakes], values=[v for _, v in lakes], dtype="float32")
  48|     band_lv = raster_vertices([g for g, _ in bands], values=[v for _, v in bands], dtype="float32", all_touched=True)
  49|     lake_m = raster_vertices([g for g, _ in lakes]).astype(bool)
  50|     cls[lake_m & (cls == 0)] = 2
  51|     level[cls == 2] = lake_lv[cls == 2]
  52| 
  53|     def put(geoms, code, lv):
  54|         m = raster_vertices(geoms).astype(bool) & ~np.isin(cls, (1, 2))
  55|         cls[m] = code
  56|         level[m] = lv[m] if isinstance(lv, np.ndarray) else lv
  57|         return m
  58| 
  59|     # Navigable: V29 band levels, extended to the new banks by nearest band vertex.
  60|     nav = [shape(f["geometry"]) for f in bodies if f["properties"]["class"] == "navigable"]
   …
 205|     groove[keep_ground] = False
 206| 
 207|     # One plane per 6 m cell: corners of one cell must not disagree much. Standing water (lakes, ponds) higher
 208|     # than an adjacent different body by > 0.30 m gives that edge vertex to land; flowing water (navigable,
 209|     # rivers, streams) is capped at 0.25 m per 6 m towards its neighbours, lowering only, standing water fixed.
 210|     standing = np.isin(cls, (2, 7)) & ~zone
 211|     flowing = np.isin(cls, (3, 5, 6)) & ~zone
 212|     wetv = (cls > 0) & np.isfinite(level)
 213|     lvp = np.pad(np.where(wetv, level, np.nan), 1, constant_values=np.nan)
 214|     sep = np.zeros((N, N), dtype=bool)
 215|     for dr in (-1, 0, 1):
 216|         for dc in (-1, 0, 1):
 217|             if dr == 0 and dc == 0:
 218|                 continue
 219|             nb = lvp[1 + dr:1 + dr + N, 1 + dc:1 + dc + N]
 220|             with np.errstate(invalid="ignore"):
 221|                 sep |= standing & np.isfinite(nb) & (level - nb > 0.30)
 222|     cls[sep] = 0
 223|     level[sep] = np.nan
 224|     cap = 0.25
 225|     for it in range(4000):
 226|         cur = np.pad(np.where((cls > 0) & np.isfinite(level), level, np.inf), 1, constant_values=np.inf)
 227|         low = np.full((N, N), np.inf)
 228|         for dr in (-1, 0, 1):
 229|             for dc in (-1, 0, 1):
 230|                 if dr == 0 and dc == 0:
 231|                     continue
 232|                 low = np.minimum(low, cur[1 + dr:1 + dr + N, 1 + dc:1 + dc + N] + cap * (1.4142 if dr and dc else 1.0))
 233|         flowing = np.isin(cls, (3, 5, 6)) & ~zone
 234|         new = np.where(flowing & np.isfinite(low), np.minimum(level, low), level)
 235|         changed = flowing & np.isfinite(level) & (new < level - 1e-6)
```

### `evidence/v30-polish-candidate-2026-10-04/census/census.json` (recortado: params, totals, histograma y los 12 primeros de `top`)
```json
{
 "params": {
  "ring_in_m": 12.0,
  "ring_out_m": 36.0,
  "perched_min_m": 0.3,
  "dike_min_m": 0.5,
  "min_vertices": 4
 },
 "totals": {
  "bodies": 631,
  "perched": {
   "count": 111,
   "area_m2": 7002036.0,
   "lake": {
    "count": 111,
    "area_m2": 7002036.0
   },
   "pond": {
    "count": 0,
    "area_m2": 0
   }
  },
  "diked": {
   "count": 190,
   "area_m2": 10712088.0,
   "lake": {
    "count": 173,
    "area_m2": 10704204.0
   },
   "pond": {
    "count": 17,
    "area_m2": 7884.0
   }
  }
 },
 "perched_m_histogram": {
  "edges": [
   "-inf",
   -1.0,
   -0.5,
   0.0,
   0.3,
   0.6,
   1.0,
   1.5,
   2.0,
   "inf"
  ],
  "counts": [
   102,
   178,
   186,
   54,
   49,
   52,
   8,
   2,
   0
  ]
 },
 "top_12": [
  {
   "id": 269,
   "class": "lake",
   "vertices": 128410,
   "area_m2": 4622760.0,
   "level_m": 2.64,
   "centroid_xz": [
    572.675,
    2697.599
   ],
   "bed_median_m": -5.36,
   "bank_median_m": 3.105,
   "bank_max_m": 4.069,
   "ring_median_m": 2.307,
   "ring_p25_m": 2.006,
   "ring_vertices": 6720,
   "perched_m": 0.333,
   "dike_m": 0.797,
   "perched": true,
   "diked": true
  },
  {
   "id": 170,
   "class": "lake",
   "vertices": 54411,
   "area_m2": 1958796.0,
   "level_m": 2.13,
   "centroid_xz": [
    11443.926,
    668.105
   ],
   "bed_median_m": -5.87,
   "bank_median_m": 2.736,
   "bank_max_m": 3.579,
   "ring_median_m": 1.583,
   "ring_p25_m": 1.429,
   "ring_vertices": 3521,
   "perched_m": 0.547,
   "dike_m": 1.153,
   "perched": true,
   "diked": true
  },
  {
   "id": 565,
   "class": "lake",
   "vertices": 2577,
   "area_m2": 92772.0,
   "level_m": 4.84,
   "centroid_xz": [
    8338.836,
    4842.829
   ],
   "bed_median_m": 1.86,
   "bank_median_m": 5.301,
   "bank_max_m": 6.45,
   "ring_median_m": 3.956,
   "ring_p25_m": 3.848,
   "ring_vertices": 1498,
   "perched_m": 0.884,
   "dike_m": 1.344,
   "perched": true,
   "diked": true
  },
  {
   "id": 508,
   "class": "lake",
   "vertices": 576,
   "area_m2": 20736.0,
   "level_m": 4.17,
   "centroid_xz": [
    10605.875,
    4417.76
   ],
   "bed_median_m": 0.391,
   "bank_median_m": 4.805,
   "bank_max_m": 5.484,
   "ring_median_m": 3.338,
   "ring_p25_m": 3.167,
   "ring_vertices": 427,
   "perched_m": 0.832,
   "dike_m": 1.467,
   "perched": true,
   "diked": true
  },
  {
   "id": 242,
   "class": "lake",
   "vertices": 1025,
   "area_m2": 36900.0,
   "level_m": 2.46,
   "centroid_xz": [
    2950.162,
    6412.203
   ],
   "bed_median_m": 0.521,
   "bank_median_m": 2.968,
   "bank_max_m": 3.809,
   "ring_median_m": 2.068,
   "ring_p25_m": 1.812,
   "ring_vertices": 1634,
   "perched_m": 0.392,
   "dike_m": 0.9,
   "perched": true,
   "diked": true
  },
  {
   "id": 574,
   "class": "lake",
   "vertices": 300,
   "area_m2": 10800.0,
   "level_m": 5.05,
   "centroid_xz": [
    8578.94,
    4756.06
   ],
   "bed_median_m": 2.641,
   "bank_median_m": 5.552,
   "bank_max_m": 6.104,
   "ring_median_m": 4.055,
   "ring_p25_m": 3.947,
   "ring_vertices": 362,
   "perched_m": 0.995,
   "dike_m": 1.498,
   "perched": true,
   "diked": true
  },
  {
   "id": 532,
   "class": "lake",
   "vertices": 311,
   "area_m2": 11196.0,
   "level_m": 4.37,
   "centroid_xz": [
    9559.042,
    5445.106
   ],
   "bed_median_m": 2.003,
   "bank_median_m": 5.013,
   "bank_max_m": 5.79,
   "ring_median_m": 3.447,
   "ring_p25_m": 3.366,
   "ring_vertices": 367,
   "perched_m": 0.923,
   "dike_m": 1.566,
   "perched": true,
   "diked": true
  },
  {
   "id": 612,
   "class": "lake",
   "vertices": 656,
   "area_m2": 23616.0,
   "level_m": 6.88,
   "centroid_xz": [
    4792.381,
    1366.271
   ],
   "bed_median_m": 4.478,
   "bank_median_m": 7.486,
   "bank_max_m": 8.254,
   "ring_median_m": 6.48,
   "ring_p25_m": 6.105,
   "ring_vertices": 519,
   "perched_m": 0.4,
   "dike_m": 1.006,
   "perched": true,
   "diked": true
  },
  {
   "id": 171,
   "class": "lake",
   "vertices": 359,
   "area_m2": 12924.0,
   "level_m": 2.13,
   "centroid_xz": [
    11069.214,
    1312.763
   ],
   "bed_median_m": 1.647,
   "bank_median_m": 2.672,
   "bank_max_m": 3.545,
   "ring_median_m": 1.562,
   "ring_p25_m": 1.422,
   "ring_vertices": 1281,
   "perched_m": 0.568,
   "dike_m": 1.109,
   "perched": true,
   "diked": true
  },
  {
   "id": 273,
   "class": "lake",
   "vertices": 310,
   "area_m2": 11160.0,
   "level_m": 2.64,
   "centroid_xz": [
    1194.252,
    26.148
   ],
   "bed_median_m": 0.594,
   "bank_median_m": 3.256,
   "bank_max_m": 3.991,
   "ring_median_m": 1.985,
   "ring_p25_m": 1.756,
   "ring_vertices": 314,
   "perched_m": 0.655,
   "dike_m": 1.271,
   "perched": true,
   "diked": true
  },
  {
   "id": 375,
   "class": "lake",
   "vertices": 293,
   "area_m2": 10548.0,
   "level_m": 3.06,
   "centroid_xz": [
    5519.877,
    9445.72
   ],
   "bed_median_m": 0.547,
   "bank_median_m": 3.676,
   "bank_max_m": 4.453,
   "ring_median_m": 2.452,
   "ring_p25_m": 2.195,
   "ring_vertices": 350,
   "perched_m": 0.608,
   "dike_m": 1.223,
   "perched": true,
   "diked": true
  },
  {
   "id": 499,
   "class": "lake",
   "vertices": 201,
   "area_m2": 7236.0,
   "level_m": 4.14,
   "centroid_xz": [
    10456.955,
    4214.985
   ],
   "bed_median_m": 2.14,
   "bank_median_m": 4.727,
   "bank_max_m": 5.472,
   "ring_median_m": 3.326,
   "ring_p25_m": 3.135,
   "ring_vertices": 269,
   "perched_m": 0.814,
   "dike_m": 1.402,
   "perched": true,
   "diked": true
  }
 ]
}
```

### `evidence/v30-polish-candidate-2026-10-04/joints/joints.json` (solo el bloque `groups`)
```json
{
 "vanilla_river": {
  "pieces": 660,
  "joints": 577,
  "scale_p50": 1.0,
  "along_m_p10_p50_p90": [
   -0.124,
   -0.044,
   -0.008
  ],
  "across_m_p10_p50_p90": [
   -3.537,
   -0.014,
   3.476
  ],
  "heading_deg_p50_p90": [
   0.438,
   36.966
  ],
  "level_m_abs_p50_p90": [
   0.014,
   0.081
  ],
  "overlap_m2_p50_p90_max": [
   1.0,
   2.786,
   66.098
  ],
  "overlap_len_m_p50_p90_max": [
   0.041,
   0.114,
   2.754
  ],
  "gap_m_p50_p90_max": [
   0.0,
   0.0,
   0.667
  ],
  "covered_m2": 292831.97,
  "multi_m2": 967.07,
  "multi_share": 0.003302
 },
 "vanilla_stream": {
  "pieces": 389,
  "joints": 310,
  "scale_p50": 1.0,
  "along_m_p10_p50_p90": [
   -0.143,
   -0.045,
   -0.009
  ],
  "across_m_p10_p50_p90": [
   -3.447,
   -0.397,
   3.116
  ],
  "heading_deg_p50_p90": [
   0.686,
   22.557
  ],
  "level_m_abs_p50_p90": [
   0.019,
   0.145
  ],
  "overlap_m2_p50_p90_max": [
   0.611,
   1.553,
   58.419
  ],
  "overlap_len_m_p50_p90_max": [
   0.04,
   0.105,
   4.173
  ],
  "gap_m_p50_p90_max": [
   0.0,
   0.0,
   0.191
  ],
  "covered_m2": 104349.046,
  "multi_m2": 510.177,
  "multi_share": 0.004889
 },
 "R1": {
  "pieces": 8,
  "joints": 0,
  "scale_p50": 3.696,
  "along_m_p10_p50_p90": null,
  "across_m_p10_p50_p90": null,
  "heading_deg_p50_p90": null,
  "level_m_abs_p50_p90": null,
  "overlap_m2_p50_p90_max": null,
  "overlap_len_m_p50_p90_max": null,
  "gap_m_p50_p90_max": null,
  "covered_m2": 21094.721,
  "multi_m2": 12244.901,
  "multi_share": 0.580472
 },
 "R2": {
  "pieces": 44,
  "joints": 37,
  "scale_p50": 1.475,
  "along_m_p10_p50_p90": [
   -1.923,
   0.01,
   1.284
  ],
  "across_m_p10_p50_p90": [
   -1.28,
   0.082,
   1.142
  ],
  "heading_deg_p50_p90": [
   8.844,
   21.99
  ],
  "level_m_abs_p50_p90": [
   0.037,
   0.162
  ],
  "overlap_m2_p50_p90_max": [
   11.708,
   33.236,
   141.308
  ],
  "overlap_len_m_p50_p90_max": [
   0.535,
   1.727,
   7.74
  ],
  "gap_m_p50_p90_max": [
   0.01,
   1.284,
   5.463
  ],
  "covered_m2": 8821.267,
  "multi_m2": 6452.685,
  "multi_share": 0.731492
 },
 "R3": {
  "pieces": 47,
  "joints": 45,
  "scale_p50": 1.374,
  "along_m_p10_p50_p90": [
   -3.209,
   0.086,
   1.005
  ],
  "across_m_p10_p50_p90": [
   -0.668,
   -0.024,
   0.658
  ],
  "heading_deg_p50_p90": [
   11.381,
   20.584
  ],
  "level_m_abs_p50_p90": [
   0.041,
   0.159
  ],
  "overlap_m2_p50_p90_max": [
   8.558,
   36.835,
   179.154
  ],
  "overlap_len_m_p50_p90_max": [
   0.438,
   2.273,
   8.705
  ],
  "gap_m_p50_p90_max": [
   0.086,
   1.005,
   3.886
  ],
  "covered_m2": 7503.81,
  "multi_m2": 5644.814,
  "multi_share": 0.75226
 }
}
```

---

Recuerda: responde con el formato exacto del apartado «Entregable» del brief de arriba, en español, empezando por «## 0. Crítica del encuadre» y terminando con la línea `FIN-DICTAMEN`.
