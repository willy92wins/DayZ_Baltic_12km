# Runtime-v2: 24 ausencias de flags frente a agua estática compilada

**Resultado acotado.** De los 24 puntos que la clasificación anterior marcaba con `SurfaceIsSea=false` y `SurfaceIsPond=false` (6 clase 1 y 18 clase 3), el runtime-v2 volvió a muestrear los 6 clase 1 y 5 representantes clase 3, con centro y desplazamientos de 0,05/0,25/1 m durante siete fases. Los centros clase 1 no caen dentro de caras de agua físicas ni visibles del índice; cuatro de esos seis activan `SurfaceIsSea` en alguna fase, dos nunca la activan durante esta ventana. Los cinco centros clase 3 sí caen en caras físicas y visibles compiladas, con la cara por encima del terreno y profundidad escalar positiva, aunque ambos flags permanecen falsos en las siete fases. Esto separa ausencia de cara estática de ausencia de flag, sin demostrar por sí solo visibilidad artística.

## Medición

| Subconjunto | N | Flags en centro | Cara física/visible en centro | Observación |
|---|---:|---|---|---|
| Clase 1, T00–T05 | 6 | `SurfaceIsPond` nunca; `SurfaceIsSea` aparece en 4/6 en alguna fase | 0/6 | En T01/T02 ambos flags siguen falsos las 7 fases; no hay cara compilada en el punto. En T00/T03–T05 el flag de mar cambia con la fase. |
| Clase 3, T06–T10 | 5 de 18 originales | Ambos flags falsos, 5/5 × 7 fases | 5/5 tienen caras físicas y visibles | Las caras contienen el punto; su plano está 0,083–1,919 m por encima del terreno según muestra, y `GetWaterDepth` es positivo. |
| Controles de estanque C01/C06 | 2 | `SurfaceIsPond=true`, 2/2 × 7 fases | 2/2 | Positivo de agua: profundidad positiva en ambas fases de control. |
| Controles secos C00/C04 | 2 | Ambos flags falsos, 2/2 × 7 fases | 0/2 | Negativo seco: profundidad negativa. |

En los seis centros clase 1, terreno/intervalo de nivel sin fake wave/profundidad (m): T00 `0,8278 / [0,6590; 0,8480] / [-0,2380; 0,0108]`; T01 `0,8550 / [0,6590; 0,8480] / [-0,2710; -0,0047]`; T02 `0,8670 / [0,6590; 0,8480] / [-0,2505; -0,0288]`; T03 `0,7625 / [0,6595; 0,8482] / [-0,1939; 0,0878]`; T04 `0,6580 / [0,6595; 0,8482] / [-0,0347; 0,2629]`; T05 `0,6500 / [0,6595; 0,8482] / [-0,0794; 0,2091]`. Los valores de profundidad negativos indican que el API puede devolver nivel bajo el terreno en algunas fases; no se reinterpretan como “hueco visual”. En esta ventana, los 4/6 con algún `SurfaceIsSea=true` fueron T00, T03, T04 y T05; T01 y T02 no lo fueron.

Los centros clase 3 fueron T06 RC(897,395), T07 (898,394), T08 (899,413), T09 (900,413), T10 (901,414). Los planos compilados locales fueron respectivamente 2,125; 2,125–2,150; 2,075; 2,075; 2,075 m. Profundidades mínimas/máximas medidas: T06 `0,8477–1,0133`; T07 `0,3090–0,4358`; T08 `0,7511–0,7827`; T09 `1,1355–1,1940`; T10 `0,0831–0,1416` m. La ausencia de ambos flags no equivale aquí a ausencia de malla de agua.

Los offsets clase 1 no tienen cara física/visible en ninguno de los 144 puntos (48 por anillo). Algún flag de mar apareció en 33/48, 36/48 y 35/48 puntos de los anillos 0,05/0,25/1 m. En offsets clase 3, las 120/120 muestras tienen caras físicas y visibles; algún flag apareció en 0/40, 4/40 y 10/40 por los mismos anillos (en el anillo de 1 m, 9 de mar y 1 de estanque). Los flags runtime y la contención de caras estáticas describen señales distintas.

En el total de 1.953 lecturas: `SurfaceIsSea=true` 530 veces, `SurfaceIsPond=true` 21 veces; 83 de 279 puntos cambiaron algún flag entre fases. En las 1.953 filas, la profundidad coincide con `GetWaterSurfaceHeightWithFakeWave - ground - 0,01 m` con error absoluto máximo de 0,00001 m, compatible con el redondeo del log.

## Procedencia y método

- Log runtime: SHA256 `69f08a129e2dcf38797f50613d50473743622e1cc43fd4e2f0ee69d622797a35`; recibo: run `1afd534d-f1d9-4fe2-b810-f3697c06aef8`, `END;7;1953;30012`, cierre ordenado, sin degradación.
- Puntos: `points.csv` SHA256 `b58fa87e8b8ca462a607f83db9be41b23937125065b1a3bbedc48d4cfb13ab64`; clasificador de 24 casos SHA256 `9dd964d4896166979da56c06d686ed14ed69020d468119931f27762a3dcbf089`.
- Índice existente, completo y revalidado: manifest SHA256 `c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c`; builder SHA256 `d1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e`; 883.308 caras (358.577 físicas, 524.731 visibles). Se usó como broadphase y luego se probó inclusión XZ exacta contra triángulos y plano Y. El WRP fuente permaneció en `3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6`; el PBO de agua runtime coincide con índice `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`. El PBO de mundo runtime es EV95 `f1a148cab3e7d1d63473f0232a0971d45a9fea04e0fb456f01973235f4644b7d`, por tanto no se afirma identidad del PBO de terreno del índice base.
- El orden e identidad de los 279 puntos se verificó en cada una de las 7 fases. Las coordenadas del log están redondeadas a centímetro; el máximo error frente al CSV fue 0,004751 m, y la consulta estática usó coordenadas exactas del CSV.
- La consulta de “arista más cercana” está limitada a candidatos del rango de búsqueda acolchado. La distancia a arista reportada para caras contenedoras es a una arista del triángulo (incluye costuras internas), no distancia global a la costa unificada.

## Límites

Solo se volvieron a sondear 5 de los 18 casos clase 3; los otros 13 quedan **sin medir**. Siete fases abarcan unos 30 segundos, no una envolvente de marea/oleaje. El sondeo es servidor y no prueba render del cliente, forma visual ni aceptación de costa. `SurfaceIsSea=false`/`SurfaceIsPond=false` no significa automáticamente hueco de geometría; a la inversa, la presencia de una cara estática tampoco demuestra por sí sola apariencia correcta.

