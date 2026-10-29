## Dictamen: SOUND-with-fixes

### Hallazgos

1. **La dependencia 5509 queda resuelta sólo para CALIBRACIÓN.** El par `control0 + candidato3` en copias aisladas hace que cualquier compilación futura dependa de las tres piezas viales y de los recursos terreno/materiales del prefijo, no de los 5.509 modelos del mapa. Esto es un cambio de diseño válido. No transfiere aceptación al mapa completo ni cierra oclusores, precedencia, colocación, agua, P9/P11 ni recursos B4A3. RoadC0 no compila: deja el problema correctamente separado para RoadC1.

2. **Preservación del prefijo bien planteada.** Copiar byte a byte los `17.307.629` bytes con SHA `d16b5139...807a5` desde la fuente `b108352f...e6d08c364678ee` de `286.261.435` bytes conserva terreno y materiales. El parseo acotado por cursor en `verify_road_object_pilot_ev112.py:159-225` y la definición de prefijo en `author_road_object_pilot_ev112.py:159-196` respaldan derivar el offset en vez de confiar en una cifra suelta. Los límites encajan: prefijo `<32 MiB`, fuente `<512 MiB`, salida conjunta aprox. `34,6 MiB <64 MiB`.

3. **Terminador opaco correctamente tratado.** Se copia literal y se exige `56 B`, longitud `0` y EOF, sin atribuirle semántica ni aceptación por Binarize. La cautela sobre escena vacía es necesaria y está declarada.

4. **Independencia del consumidor suficiente.** No importa autor ni su parser, carga el contrato por SHA externo, recorre el prefijo con cursor propio, compara rangos contra la fuente por chunks y decodifica registros secuencialmente. El negativo de reporte+hash co-mutados sin poder engañar la comparación contra fuente cierra el bypass principal. La herencia del censo de 2,5M objetos desde B3 es legítima **sólo** porque la fuente está pinada por SHA/tamaño; no es un recenso y el plan no lo finge.

5. **Sentido de los controles correcto.** Control y candidato comparten prefijo y terminador y difieren sólo en los tres registros `19394564-566` (`asf1_25`, `asf2_25`, `asf1_10 100.p3d`), con identidad y rotaciones de 90°. En RoadC1 eso permitirá atribuir diferencias al contenido vial, pero un rechazo del control0 no distinguirá entre prefijo, terminador o escena vacía: esa interpretación debe pre-registrarse allí, no en RoadC0. Descartar el writer OPRW apoyándose en el lector heurístico de `package_visual_forest_ev112.py:29-64` es correcto.

### Fixes previos a código

- **F1 — Matrices como bytes, no como enteros JSON.** Las matrices de ANCLAS vienen como enteros y perderían `-0.0` o cualquier bit no entero. El contrato congelado debe fijar `matrix48_hex` por objeto, además de ID, `raw_name_hex` y longitud total de registro. Los oráculos con signed-zero no sustituyen este pin de la fuente B3.
- **F2 — Cadena B3 original resoluble.** Antes de codificar, fijar ruta del export-manifest y SHA `7454f8b7...1f9382`, y su relación con el saneado `fdee65cb...69948`. Si esa ruta no se localiza, el estado es bloqueado/inconcluso; el contrato saneado solo no ancla los literales.
- **F3 — Desambiguar “prefix_bytes”.** Renombrar en el contrato nuevo `terrain_material_prefix_bytes=17307629` frente a `source_pre_terminator_bytes=286261379` (`286261435-56`). La colisión ya detectada es el error de implementación más probable.
- **F4 — Terminador exacto también en el autor.** El parser piloto acepta como terminador cualquier ID con longitud `0` (`author_road_object_pilot_ev112.py:209-215`). Autor y consumidor deben exigir igualdad byte a byte con `terminator_hex` pinado, no sólo longitud `0` en EOF.

### Convergencia

**CONVERGE**, condicionado a F1-F4 dentro de la congelación previa ya prevista. Son precisiones de pin, no cambios de diseño. Con ellas, el resultado admisible es únicamente `VERIFIED_ISOLATED_SOURCE_PAIR_ONLY`.

### Limitaciones de esta revisión

Revisión sólo de la cápsula entregada, sin lectura externa ni ejecución. No afirmo compilabilidad, cierre de recursos, aceptación de Binarize, pivote nativo ni validez en DayZ. Las cuatro hipótesis raw/origin × fila/columna siguen abiertas y corresponden a testigos posteriores.

END_ROADC0_REVIEW
