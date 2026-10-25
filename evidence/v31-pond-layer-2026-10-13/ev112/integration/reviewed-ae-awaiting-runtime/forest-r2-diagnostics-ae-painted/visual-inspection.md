# Inspeccion offline AE — 2026-10-19T18:13:50.032338+02:00

Inspeccion real de siete PNG mediante view_image, completada antes de reservar semillas181–190.
Fuente `0fef87eec16f4a609b33482ac438fc33f07e48c1db3d12810a3d0bd7501c658a`; registros `2e86b4a79d243ec43f68ba70dd0492e88a434963814a4b1b47c8965823709b37`.
Rasters finales del PBO AE; binding de diagnosticos `681c0e829c16ac74296ef74d1f576cab03736bd0ab757f530c8c6fc861d41bf7`.

## Observaciones

- former-dark-patch-west y north: el suelo forestal oscuro observado coincide principalmente con zonas arboladas; los claros extensos, agua y corredores abiertos se distinguen. Los marcadores muestran transiciones de densidad y claros internos, no una mancha oscura continua sin arboles en estos recortes.
- bog-personal-view: islas de musgo abiertas y bordes menos densos que el bosque exterior. La linea amarilla marca la mascara, no una medicion de copas ni de navegabilidad.
- largest-rim-10.0 y largest-rim-25.0: se ven concentraciones locales moderadas cerca del borde; no se aprecia un punto saturado o geometria colapsada. El segundo recorte esta cerca del borde occidental del mapa; no sustituye los dos recortes interiores adicionales.
- component2381 y4304: ambos completamente dentro del mapa, renderizados a0,25m/px, simbolos de centro de arbol de radio0,40m. Musgo amarillo abierto; el anillo cian conserva arboles dispersos. No se observa una acumulacion puntual explosiva en estos dos casos de compensacion alta. Factores forestales62,1930/59,3951 y31/42 pixeles vivos respectivamente; el factor nominal no se convierte en densidad realizada.

## Medidas frescas y limites

Percentiles1/5/50 de distancia al otro arbol mas cercano, en metros:

| Zona | Arboles | p1 / p5 / p50 |
|---|---:|---|
| rim_outer | 89530 | 0.876186 / 1.351127 / 3.259144 |
| rim_inner | 18134 | 0.940068 / 1.464037 / 3.698686 |
| core | 12578 | 1.003722 / 1.668775 / 4.403671 |
| livonia_forest_edge_40m | 1357411 | 0.560151 / 1.269068 / 3.976206 |

Los conteos dentro de10/25m incluyen al propio arbol. Maximo en rim_all30/101; medianas9/40. No son FPS ni medidas de colision de copas.
Interseccion de object-gap con turbera: exterior1,186982%, interior0,797572%, nucleo0,566812%, calculadas de nuevo sobre AE. No se impone ni afirma un limite nuevo de1% en todas las zonas. Livonia borde40m es referencia comparativa, no una turbera equivalente.

Conclusion acotada: inspeccion offline completada sin un nuevo defecto visual concreto en estos siete planos. Se puede ejecutar la bateria de semillas nuevas; no se acredita aceptacion visual del usuario, prueba en juego, rendimiento ni ausencia de defectos en vistas no inspeccionadas. La revision independiente OT7 sigue pendiente.

| Imagen inspeccionada | SHA256 |
|---|---|
| former-dark-patch-west.png | `36851b9b5c3237813312755edc1879d6c99445625b772147103331e11a9d91c0` |
| former-dark-patch-north.png | `33a1ef773a81daec663089c2f61acff6a31e774d8ac6cb13fbcb2a188b836473` |
| bog-personal-view.png | `ad6a8c774e472978d9fd7626bec2c9ffae8403a1cb17ca07add2ba4a9647e105` |
| largest-rim-10.0.png | `25a58998d7ca887280de980df6b5883316701a5d52e19d832b69873edc9444ae` |
| largest-rim-25.0.png | `eb8b94a341e0ed7b01afaa92270bf9cac0297829d4a9fb7ae9f5f7e700f9c896` |
| rim-component-2381.png | `8f58d3d13125fe56536ba100fb113aafa05de5ff8f15485f2a1e32d19d756904` |
| rim-component-4304.png | `8f72f3d24a3df22f69970f073296a25e12c294c7bda3e836bbe7b2e94b61f713` |
