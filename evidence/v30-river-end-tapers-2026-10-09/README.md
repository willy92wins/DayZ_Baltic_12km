# Finales de río: propuestas rechazadas

**No empaquetar Msta A ni R2.** La preview vigente sigue siendo HaloFixV3. BALTIC-020 continúa abierto. Grib y Volkhov están localizados, pero no se extiende un método que falla ya en Msta.

El candidato A estrecha el extremo durante varias celdas mediante diez subidas de terreno, máximo 0,70 m. Conserva los 830 cuerpos significativos, carreteras, plataformas, navegación y los 351 puntos de control anteriores. A 6 m del corte la sección pasa de 13,5 a 3,8 m; el tramo a partir de 54 m conserva su anchura. Son resultados geométricos, no aceptación.

La comprobación de forma lo rechaza: sobre el contorno nativo, el p90 de giro pasa de 28,68 a 45,68 grados y el giro máximo de 46,50 a 87,76 grados. La figura `msta-native-contour.png` muestra el estrechamiento y los quiebros añadidos. El PASS de `msta-verification.json` cubre exclusivamente sus puertas físicas y de anchura; no suplanta el FAIL de `msta-turns.json`.

R2 corrige un defecto concreto del autor: medía la distancia al final del polígono como si fuese el medio ancho del cauce. La corrección mide secciones transversales y conserva los otros parámetros. Aun así, p90 48,41 grados y máximo 87,93: FAIL. No se ejecutó de nuevo la batería física porque el criterio de forma ya impide construirla. Presupuesto de esta aproximación terminado; no probar otros radios o márgenes.

Terrenos externos reproducibles: A `ae82c27c02627aa89b680fa505312633e0614459b28e869e8026523c3f156546`; R2 `23ffc2ed43fa498b3b849a6f2d7666603649d9603631e6e9ad7bbb78e627927f`. Los deltas exactos, parámetros, scripts, ejes y medidas se conservan aquí. Ninguno se ha desplegado ni promovido a Terrain Builder.

Límite adicional: la nota genérica «Sea unchanged for edits above 1.4 m» del comprobador de topología no aplica a estos cambios, que incluyen alturas inferiores a 1,4 m. Ese comprobador solo prueba los planos de estanque; no certifica la exposición del mar ni el shader. Los niveles del mar no se modificaron.

Siguiente diseño debe ajustar directamente el contorno resultante de los triángulos y las transiciones del talud, con requisitos de anchura/conexión explícitos. No reabrir a ciegas el solver C/C1, que ya falló en R1/R2, ni cambiar la malla de 6 m sin autorización.
