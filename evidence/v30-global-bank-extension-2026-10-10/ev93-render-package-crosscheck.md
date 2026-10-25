# EV93 vs investigación de rectángulos grises — lectura acotada

**Resultado:** no apareció un discriminador estático nuevo y barato. `Shadows` ON/OFF/ON sigue siendo el único A/B causal ya preparado; EV77 wire sigue inconcluso y solo informa qué aristas/materiales aparecen en debug. No se abrió cliente ni se reconstruyó el mapa.

## Contraste de build

- EV89 esperaba el preview `@DayZ_Baltic_IncrementalBankPreviewV1`, mundo B `b11c825b6c14ecc5649ac668b40c7dc6c9f52c64c26ddfa748983c04b340c36c`, agua `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`; su propio informe no asegura que ese B reproduzca el defecto. El despliegue EV93 actual es `@DayZ_Baltic_EV93_SelectedBankPreviewV1`: `deploy.json` fija el mundo final `cb4ffc6b7de96c2e9de5c561ac95497b4310ca6f3ae48c6ddab80f6fcd225ab6` y el agua anterior (`build-selected/deploy.json:2-10`). Stage declara alturas EV93, candidate `6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d`, y 18.033 objetos/materiales exactos (`stage.json:2-7`). El lector OPRW dice PASS, WRP compilado `63d947597c5290f41135fa6ac81748f43ac2b57b444ffcf30ab9d22453091133` y agua exacta al baseline (`op_rw_verification.json:2,15,998`).
- Por tanto, el PBO de agua que contiene los cuatro `globalvis_*` no cambió; las alturas/WRP y el PBO de mundo sí son una identidad distinta. No se debe transferir una captura EV73/74 ni dar por reproducido el gris en EV93. En EV89, A debe volver a comprobar hashes y presencia del parche antes de ejecutar B.

## Geometría/P3D contrastada

El `baltic_water_v30.pbo` desplegado se rehashó como `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`; sus cuatro miembros coinciden byte a byte con los SHA del análisis estático: `16812770` `256bee15ac00a8a1837cdb98ca005211ab524269ac33ce73c9b09d7ac2103056`, `16812771` `9516bf9b00a033e141560e0ed0e204bd4370814fd820d7be3abf3818fc0cb03e`, `16812805` `776cf8f1381c042997801f248418192816b54bad25f6084d8762ead0eb6e66be`, `16812815` `a48258ff25622d8987cbb0da0d8fbcdc76ab5a9ce9bed8b66d827f19432fb1c1`. El origen del inventario es `object-boundaries/collect_exact_pairs.py:18,36-41` y sus resultados son `object-boundaries/exact-pairs.json`.

Las dimensiones estáticas pedidas ya se cotejaron en los cuatro modelos: bbox visual y de modelo, esfera/radio por LOD, `geometry_view`, `geometry_sphere`, `can_occlude`, `can_be_occluded`, `can_blend`, alpha/culling flags, `special`, sección y propiedad `lodnoshadow`. Son comunes `geometry_view=255`, `geometry_sphere=0`, flags de oclusión/alpha y material CalmWater; varían topología, bbox y radio. Los radios LOD0 observados son 28,306 / 26,837 / 15,007 / 12,375 m; las esferas declaradas son 28,306 / 26,837 / 16,978 / 16,978 m. No se encontró una esfera declarada más pequeña que el radio LOD0 que apunte a un underbound sencillo. El parser indica `scan_fallback`; son datos estáticos de apoyo, no una lectura de la decisión de culling del motor (`exact-pairs.md:5,11-19`; anexo EV89, `annex.md:17-23`).

EV74 ya probó Terrain Detail `2→4→2`, con readback, sin quitar los parches; eso no selecciona ni revela el LOD gráfico por objeto (`v30-water-rectangles-detail-2026-10-09/README.md:5`; `summary.json:173-174`). EV76 también mostró el mismo fondo bajo el mar en ROI gris y control, de modo que el lecho submarino no discrimina esas apariencias (`v30-water-cause-investigation-2026-10-10/README.md`). La coincidencia entre dos transiciones y bordes P3D sigue siendo correlación, no culling demostrado (`object-boundaries/exact-pairs.md`).

## Dimensiones y posibilidad de refutación

- **Vistas:** material/textura y flags estáticos; bbox/radios/LOD listados; identidad de los cuatro P3D en el PBO de agua actual; igualdad de objetos/materiales al hacer stage EV93.
- **Asumidas o no resueltas:** la pose/build actual reproduce el gris; el motor usa de la manera esperada esos bounds; qué instancia se culla/dibuja en esa distancia; LOD de terreno por celda; orden Z/alpha y contribución de sombras. EV73/74 no midió LOD/culling por instancia.
- **No vistas en una captura válida:** estado visual actual de EV93 y el cambio del parche al alternar sombras. El desktop seguía `all_black`; no hay resultado EV89.
- **Refutación útil:** con el paquete EV93 exacto, si A no reproduce el parche, eso refuta que el A/B pueda explicar el síntoma en ese paquete y se para antes de B. Si A reproduce, la secuencia EV89 A/B/A puede refutar sombras como condición necesaria si el parche persiste en B, o mostrar contribución si desaparece en B y vuelve en A′. No discrimina culling/bounds ni identifica el mecanismo interno de sombras.

No hay un contraste vanilla de P3D geométricamente equivalente en esta evidencia. No hace falta inventarlo para las dimensiones ya medidas; la dimensión restante es el resultado de render/culling del motor, no otro campo estático del P3D.
