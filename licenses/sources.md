# Fuentes, licencias y trazabilidad

Consultadas/adquiridas el 29-09-2026. `evidence/source-manifest.json` conserva URL, tamaño, SHA-256, fecha de adquisición y metadatos por archivo. No confundir adquisición con fecha de medición del terreno.

| Fuente | Uso y fecha | Atribución/licencia |
|---|---|---|
| Copernicus GLO-30, AWS release 2021 | 15 teselas DSM; superficie con vegetación/edificios, no DTM desnudo. Alturas ortométricas EGM2008. | produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved |
| ESA WorldCover 2021 v200 | 4 teselas; clases de suelo y color provisional | © ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021), processed by ESA WorldCover consortium. CC BY 4.0. DOI 10.5281/zenodo.7254221. |
| OpenStreetMap, Geofabrik Estonia y Northwestern Federal District | Costa, agua, lugares, frontera y vías. Instantáneas distintas: Estonia 2026-09-27T20:23:36Z; Rusia NO 2026-09-28T20:23:05Z. | © OpenStreetMap contributors, ODbL 1.0. Se preservan IDs/versiones y origen por objeto. Las capas derivadas deben conservar sus obligaciones ODbL al distribuirse. |
| Capturas Google Maps aportadas por Guillermo | Solo referencia visual/encuadre; no satmap de producción ni datos de textura | Se conservan en procedencia y salida del recorte, fuera del paquete de terreno. Las figuras nuevas se generan desde los datos anteriores. |

Los rvmats vanilla se referencian desde la instalación de DayZ; no se redistribuyen sus binarios en el paquete. El material creado aquí no cambia las condiciones de uso de las fuentes o del juego.

- [Copernicus DEM AWS](https://registry.opendata.aws/copernicus-dem/) y [release/readme](https://copernicus-dem-30m.s3.amazonaws.com/readme.html).
- [Descripción y licencia Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).
- [WorldCover](https://esa-worldcover.org/en/data-access) y [dataset 2021 v200](https://doi.org/10.5281/zenodo.7254221).
- [OpenStreetMap copyright](https://www.openstreetmap.org/copyright).
- [Geofabrik Estonia](https://download.geofabrik.de/europe/estonia.html), [Rusia NO](https://download.geofabrik.de/russia/northwestern-fed-district.html).
