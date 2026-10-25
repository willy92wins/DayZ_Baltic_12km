# EV67 — superficie completa sobre EV61

Actualiza la textura y máscara al terreno EV61, conservando sus alturas, agua, objetos y configuración. No es aceptación gráfica ni base 1.0. Despliegue de prueba: `P:/Mods/@DayZ_Baltic_SurfaceAlignedV2`; mundo `37f42c8ec1277fc3a493b423a06fad62a1ea16c8336d3f713967a5eec002b4bd`, agua `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`.

`surface-verification.json` verifica 1024 teselas, 150847524 píxeles y 3968 solapes con alturas triangulares independientes. Cero agua interior compilada con máscara terrestre entre 34445727 píxeles interiores. Las 4323 mezclas DXT de borde anteriores permanecen inventariadas. Cambian 3022 píxeles de satélite y 188 de máscara, incluidos 177 secos. El generador es idéntico a EV28.

`deploy.json`: 14 PAA de satélite y 11 máscaras cambian; las otras 6802 entradas del PBO son exactas. `changed-mips.json` comprueba los 200 niveles de detalle de esos 25 archivos: estructura, payload, descompresión y controles nativos. Los archivos sin cambios conservan la evidencia EV30 por identidad de bytes. Esto no identifica ni cierra el fallo intermitente de streaming BALTIC-019.

Scripts y recibos se ejecutaron en `E:/DayZ-Baltic-Build/v30-surface-aligned-20261009` con el Python GIS. La prueba en cliente de Nazia/Msta/Volkhov y distancias sigue pendiente por indisponibilidad del conector. EV61 sigue siendo el candidato de trabajo con lectura nativa ya ejecutada; EV67 es su actualización de superficie preparada.
