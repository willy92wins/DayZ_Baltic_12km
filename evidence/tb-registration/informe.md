# Registro de coordenadas y referencias de Terrain Builder

29-09-2026 · DayZ_Baltic_12km · continuación de la importación propia.

## Resultado medido

Las seis anclas regionales conservan su posición al importarlas y exportarlas desde Terrain Builder: error máximo **0,000006440 m**, tolerancia 0,0001 m. El proyecto mantiene el recorte aprobado y la escala global de San Petersburgo/Narva. [Datos y exportación auténtica](anchors-roundtrip.json).

La malla de TB coloca las cuatro muestras del probe **3 m al oeste y 3 m al norte** de sus centros raster GIS. En cada control se seleccionó un único vértice con la altura esperada; la misma prueba centrada en el punto GIS seleccionó cero vértices. No se editaron alturas. [Observaciones y hashes de ocho capturas](mesh-registration.json).

| Control | Centro GIS E,N (m) | Vértice TB inferido E,N (m) | Altura observada (m) |
|---|---|---|---|
| NW | 200069, 717 | 200066, 720 | 15 |
| NE | 200675, 663 | 200672, 666 | 25 |
| SW | 200123, 105 | 200120, 108 | 35 |
| SE | 200639, 159 | 200636, 162 | 45 |

Las coordenadas de los SHP sí se leyeron numéricamente en propiedades. Las coordenadas del vértice se infieren de esos puntos, los rectángulos de selección y la separación de 6 m; TB muestra cantidad y altura de la selección, no una propiedad numérica de XY del vértice. Esto acredita el comportamiento observado en esta instalación; no aísla su implementación interna ni prueba otras versiones o tamaños de celda.

La fórmula respaldada para este caso es `X = xllcorner + columna × 6`, `Y = yllcorner + filas × 6 − fila × 6`. Una exportación ASC puede conservar todos los valores y la cabecera sin demostrar la colocación visual de la malla. Por eso este ensayo complementa la comparación ASC anterior.

## Adaptación de SHP

Se copiaron nueve capas a `derived/tb_vectors_v1`, conservando byte por byte SHP/SHX/DBF/CPG. Solo cambia el PRJ de las copias: utiliza el contenedor 31N exportado por el propio TB. **No es una reproyección geográfica**: siguen siendo metros locales del mapa, no coordenadas UTM de Estonia/Rusia. [Manifiesto de copias](adapter-manifest.json).

El PRJ original LOCAL_CS provocó un aviso `CVectorObjWKTImportDialog::EnumerateDatum(935)`. La importación con el WKT del consumidor permitió medir las anclas. No se atribuye una causa interna del aviso sin código o experimento adicional.

El exportador SHP de TB convirtió los campos numéricos auxiliares lon/lat a enteros y cambió anchos de campos. **La geometría pasa; el roundtrip completo de atributos no pasa.** Conservar los archivos fuente como autoridad; no sustituirlos por SHP reexportados desde TB.

## Polígonos de agua: fallo real y adaptación de referencias

La importación de `water.shp` produjo `Renderer - Too many vertices!` y `CVectorFormatLoader::Load(727) [AssertNoDlg] area`. El proceso siguió vivo; no fue un crash. La escena se guardó aparte como `tb/regional_refs/regional_refs.tv4p`. Su exportación auténtica contiene **17.302 de 17.310** polígonos: faltan ocho de los más complejos. [Diagnóstico](water-import-diagnostic.json) · [error capturado](water-import-error-dialog.png).

Además, una pieza de Peipus (índice fuente 1199, `relation/1318060`) pasa de nueve huecos a cero en el roundtrip. Su contorno exterior coincide exactamente, pero añade **48,868869 m²** de relleno donde había huecos. Esto identifica una pérdida de geometría que no se detectaría contando solamente entidades. No se ha aislado si ocurre en la importación, la representación interna o la exportación. [Medición](water-hole-loss.json).

La adaptación usa `water_outlines`: todos los anillos exteriores e interiores se guardan como líneas de hasta 2.048 puntos, compartiendo el extremo entre tramos. Son **19.346 anillos y 19.384 segmentos**, con todos los puntos originales conservados. No se simplifica, desplaza ni suaviza ninguna orilla. La capa poligonal defectuosa queda oculta y conservada como diagnóstico. Los polígonos GIS siguen siendo la autoridad para áreas y superficies de agua futuras.

**PASS del consumidor:** los 19.384 segmentos exportados desde TB conservan los 19.346 anillos originales, incluidas las islas. Se compararon **732.225 puntos**, sin segmentos ausentes ni diferencias de longitud, con error máximo **0,000006600 m** (tolerancia 0,0001 m). Solo se normalizan puntos consecutivos repetidos. El total incluye extremos compartidos entre segmentos; la fuente contiene 732.187 puntos. [Comparación completa](water-outlines-roundtrip.json).

También se observó truncado de nombres UTF-8 en DBF exportado (corte de una secuencia multibyte). Los nombres del export no sustituyen a los originales. Los identificadores ASCII de la prueba se verifican por separado.

## Prueba de adaptación de alturas

Se preparó un terreno desechable de 128² × 6 m con la superficie analítica `z = 100 + (X−200000)/6 + Y/12`. El candidato remuestrea los centros GIS en las posiciones de vértice observadas. Los cuatro controles deben dar 171 / 267,5 / 129 / 219,5 m; la versión sin adaptar tiene un error de +0,25 m en cada uno.

**PASS de importación, construcción y exportación real de TB:** 16.384 alturas conservadas exactamente; las **16.129 muestras interiores** coinciden con la fórmula independiente, error máximo 0 m. Los cuatro controles exportados dan 171 / 267,5 / 129 / 219,5 m. El control negativo sin adaptar mantiene +0,25 m. Los bordes superior e izquierdo usan prolongación constante y quedan fuera de esa igualdad analítica (error máximo 0,5 m en el borde). No se repitió aquí una medición UI de XY: se utiliza el registro empírico del probe anterior. [Resultados](vertex-sampling-roundtrip.json). **No se ha aplicado este remuestreo al terreno regional.** Una corrección de producción debe evaluar costa, máscaras y bordes; promediar alturas ya recortadas puede suavizar una orilla estrecha.

## Límites

Las capas SHP son referencias de edición: todavía no son carreteras, puentes ni superficies de agua funcionales. Los avisos anteriores de TB/Buldozer siguen abiertos. No se ha demostrado jugabilidad, CE, navmesh ni capacidad de 80–100 jugadores. No hay WRP/PBO de este proyecto.

Durante esta continuación se detectaron procesos cliente/servidor DayZ de otra tarea; se dejaron intactos. No se lanzó otra sesión de juego para Baltic.

## Estado recuperable y continuación

`tb/regional_refs/regional_refs.tv4p` está guardado y reabierto. `water_outlines` es la referencia de orillas; `water` permanece oculta por pérdida de geometría. Carreteras, ríos, costa, frontera, detalle de Narva y seis anclas están en capas de referencia. El terreno regional y su sat/mask conservan sus valores originales. [Reapertura](regional-refs-reabierto.png).

El ensayo de alturas está guardado en `tb/vertex_sampling_probe/vertex_sampling_probe.tv4p`. Los manifiestos de preparación dicen NOT_TESTED porque se generaron antes de importar; el resultado actual del consumidor está en los JSON de roundtrip enlazados arriba.

La escena regional procede de Save As: comprobar su carpeta de salida antes de regenerar, pues puede conservar `tb/baltic_physical`. El paquete preserva ambos proyectos y sus dependencias locales. Ningún render aislado prueba agua funcional ni rendimiento. Git conserva herramientas, fixtures y evidencia ligera; los binarios nativos se entregan en el archivo con hashes.

Próximo tramo: evaluar una copia del relieve para muestreo en vértices y cuantificar cambios de costa/canales antes de aplicarla; después medir y colocar el cruce vanilla de Narva en un sector desechable. Seguir `plans/terrain-builder-import.md`. No ensanchar ni alterar materialmente la silueta aprobada sin decisión del usuario.
