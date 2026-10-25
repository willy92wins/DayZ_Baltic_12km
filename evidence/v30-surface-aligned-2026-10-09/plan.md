# EV67 — texturas de toda la superficie sobre EV61

Actualizar la correspondencia de máscaras y satélite tras los cambios geométricos aceptados de Nazia, Msta, Volkhov, masas aisladas y dominios secos. La fuente es EV61 (terreno 7bcfae76, P 768e8e58, F f446a216); no incorporar EV63/65/66, todos rechazados. Esta unidad mantiene alturas, planos, modelos de agua, puentes, materiales y navmesh exactamente. La edición final de Terrain Builder continúa pendiente de geometría aceptada.

Una generación de las 1024 teselas, con el mismo generador y parámetros de EV28: depth-all, grava, anillo flowing, landcover smooth sigma1.0, planos físicos explícitos por hash. No alterar la paleta para ocultar defectos del agua o del streaming.

Consumidor independiente EV28 sobre todos los 150847524 píxeles: triángulos nativos, cero máscara terrestre en agua nominal de fuente, cero mezcla terrestre compilada a >=4 píxeles del borde. Decodificar cada PAA, comprobar 3968 solapes, alfa, paleta y negativos de píxel real. Inventariar mezcla DXT de borde y cuantización del satélite. No repetir controles de API inalterada; su hash y evidencia EV28 se fijan.

Sustituir únicamente las entradas PAA s_/m_ que correspondan; probar identidad de las restantes y de los PBO/WRP de geometría. Paquete nuevo SurfaceAlignedV2, sin reemplazar el anterior. Vistas válidas en motor en las tres orillas cambiadas; esto no cierra el shader global ni los pliegues aún abiertos.
