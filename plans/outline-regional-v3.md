# Outline regional V3

Plano: [outline.png](../evidence/regional-outline-v3/outline.png). Estado técnico
y aceptación: [ejecución](regional-outline-execution.md). Esta revisión conserva
el recorte aprobado; no cambia coordenadas ni escala local de ninguna zona.

## Distribución fijada

| Sector | Qué se conserva ahora | Trabajo posterior |
|---|---|---|
| Golfo, costa e islas | Huella de referencia, orillas y cotas de la base nativa | Recorrido regional, puertos y arte |
| San Petersburgo / Neva | Closeup completo, misma transformación XY; protección de 4,81 × 3,83 km | Canales y cruces navegables; ciudad representativa con assets vanilla |
| Narva y frontera | Dos riberas, territorio occidental y piloto de puente elevado | Extender navegación; decidir base/búnker occidental |
| Interior oeste de Gatchina (A) | Colinas selectivas sin desplazar agua ni corredores | Líneas de visión y accesos; máximo regional actual 109,57 m |
| Sur Peipus–Luga (B) | Relieve selectivo compatible con la hidrografía protegida | No forzar el objetivo de altura donde falte espacio |
| Mshinskoye | Envolvente de conservación de 6,04 km² de juego; bosque, humedal y claros reservados | Vegetación vanilla por sectores y medición de carga del más denso |
| Conexiones principales | 11.229 segmentos OSM y franja de protección de 15 m | Selección de vías jugables, rasantes, empalmes y piezas físicas |

La reserva combina los polígonos OSM principal y norte con la envolvente
conservadora de diseño. **No representa un límite legal.** Las zonas de bosque
proceden de WorldCover, no son árboles colocados ni una densidad ya decidida.
El bosque denso se concentrará en sectores, manteniendo claros y humedales
para diferenciarlos visualmente y controlar la carga.

## Archivos editables

- `derived/outline-v3/areas.shp`: anillos de marco, closeup, reserva, piloto y zonas A/B.
- `derived/outline-v3/roads.shp`: líneas principales de referencia; no carreteras construidas.
- `derived/outline-v3/areas_wgs84.geojson`: áreas en coordenadas geográficas para GIS.
- `tests/regional_outline_v1/biome_reservation.tif`: bosque futuro, humedal, claro y agua en la reserva.
- `tests/regional_outline_v3/baltic_regional_outline_v3.asc`: alturas nativas verificadas.
- `tb/regional_outline_v3/narva_trial.tv4p`: proyecto guardado y reabierto.
- `tb/regional_outline_v3/baltic_regional_persisted_v3.wrp`: exportación nativa aceptada.

Los SHP usan **metros de ingeniería TB**, origen E200000/N0; no son EPSG:3857.
Marco 12.288 m; vértices nativos X=200000+6c, N=12282−6r. No desplazar los
datos para confundir los centros GIS con los vértices del terreno.
Cada archivo exportado se relee y se fija por hash en
`evidence/regional-outline-v3/outline-manifest.json`.

## Límites de esta entrega

Agua y rasantes regionales permanecen conservadas de la base; esta capa de
relieve no acredita su ingeniería terminada. El piloto de Narva tampoco prueba
todos los ríos. Antes del mapeado quedan niveles de lagos, continuidad y sección
navegable, corredores de conducción y comprobación del navmesh. Tras colocar
objetos/vegetación habrá que regenerar la navegación y repetir las rutas.
