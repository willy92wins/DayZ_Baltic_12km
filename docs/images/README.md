# Cartografía de presentación

La imagen principal del README, [zona-real.png](../reference/zona-real.png), es
la captura aportada por Guillermo para mostrar el área de inspiración. Se conserva
íntegra, sin recortar ni modificar. Su procedencia y hash constan en
[source.json](../reference/source.json). **Cartografía: Google Maps.** Su SHA-256
coincide con `referencias/regional.png` en [la aprobación original](../../evidence/aprobacion.json),
cuya procedencia figura en [las fuentes](../../licenses/sources.md). Las atribuciones
OSM/ESA de esta página corresponden a las figuras generadas que se describen a continuación.

`baltic-region.png` muestra el recorte geográfico aprobado. `narva-saint-petersburg.png`
acerca dos de sus áreas: Narva/Ivangorod y San Petersburgo/Kotlin. Son ilustraciones
cartográficas elaboradas desde los datos GIS del proyecto, con colores interpretativos.
No son imágenes de satélite ni capturas de DayZ. Las vías dibujadas son referencias
geográficas; no acreditan carreteras construidas ni agua navegable en el juego.

El mapa regional conserva los límites de [la aprobación](../../evidence/aprobacion.json).
Los acercamientos tienen escalas distintas. No se han dibujado frentes militares
ni límites de loot: la línea discontinua representa la frontera administrativa OSM.
Los rótulos de ciudades se anclan a sus nodos OSM, identificados en
[map-sources.json](map-sources.json).

## Atribución

- **© OpenStreetMap contributors**, datos bajo [ODbL 1.0](https://www.openstreetmap.org/copyright).
  Costa, ríos, masas de agua, carreteras, frontera y localidades proceden de las
  instantáneas Geofabrik de Estonia y Rusia noroccidental adquiridas para el proyecto
  el 29-09-2026. Se aplican sus obligaciones a los datos derivados; estas imágenes
  son obras cartográficas producidas a partir de ellos.
- **© ESA WorldCover project 2021. Contains modified Copernicus Sentinel data (2021),
  processed by ESA WorldCover consortium.** Cobertura del suelo WorldCover 2021 v200,
  bajo [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  [Dataset y cita](https://doi.org/10.5281/zenodo.7254221).
  Modificaciones: recorte, reproyección y representación mediante una paleta propia.

Los originales, fechas y licencias se describen en [las fuentes del proyecto](../../licenses/sources.md)
y en [el manifiesto de adquisición](../../evidence/source-manifest.json).
Las dos figuras generadas no incorporan capturas de otros mapas ni recursos
visuales del juego; la captura aportada se conserva como archivo independiente.

## Reproducción

Desde la raíz del repositorio, con el entorno GIS fijado en `requirements.lock` y
los datos procesados de fase 0 disponibles:

```text
python -I tools/render_readme_maps.py --data-root <raíz-de-fase0> --output docs/images
```

El renderizador comprueba que el raster de referencia conserva el recorte aprobado
y registra hashes de entradas, script e imágenes en `map-sources.json`. No descarga
datos ni modifica el terreno. Los archivos GIS grandes permanecen fuera de Git;
el manifiesto permite identificar las entradas exactas de esta publicación.
