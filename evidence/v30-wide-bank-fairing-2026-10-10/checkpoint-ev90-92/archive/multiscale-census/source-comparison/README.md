# Comparación B ↔ relief3x: diagnóstico, no selector

Se compara la base B congelada con el ASC `relief3x` en los mismos 2048×2048 índices. El ASC declara `NODATA_value -9999`; no se hallaron celdas con ese sentinel y todos sus valores son finitos. `-12` es un valor del raster, no se ha reinterpretado como NoData. Cinco valores fueron contrastados con lectura independiente de tokens de las filas ASCII.

Para cada eje cardinal y d=1,2,4 (6/12/24 m), ambos campos usan `max(0, Hc−max(H−d,H+d))`. El summary incluye distribuciones B−relief3x, cuantiles de prominencia por población, coincidencias de soporte positivo en el mismo eje/escala, y conteos de semillas EV87 con soporte de la fuente en esas posiciones. El NPZ guarda prominencias relief3x y mapas de población/soporte. Las salidas son descriptivas; relief3x es una representación de proyecto, no ground truth ni etiqueta automática de defecto. No establecen umbral ni autorizan cambios de terreno.

Anclas: B `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`; relief3x ASC `ecb2bd99a1751362bfcab0c150f10d18649bf3a50b24ea49a3eb0ffdb48bdf1f`; censo previo `6bdd42b298e538b4ecce3063a8a53e3aafb65b0f15373d78254ea8bc57e0c213`.
