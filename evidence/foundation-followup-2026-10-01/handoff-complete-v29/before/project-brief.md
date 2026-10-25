# DayZ Baltic 12km Brief

> **Rol**: contexto **estable** del proyecto (stack, convenciones, paths,
> gotchas, do-not-do). Estado vivo y progreso NO van aquí: viven en el
> HANDOFF del repo dev y en [`_estado-proyectos.md`](../_estado-proyectos.md).

## Current State

- Status: **ABSORBIDO 2026-09-29 (decisión de Guillermo)** — el proyecto pasa a ser nuestro: el vault mantiene la memoria y el trabajo futuro se ejecutará en nuestra máquina/pipeline. El material heredado de Exta queda como punto de partida (`[ASSUMPTION]` hasta verificación propia).
- Relación con Exta (`extanator`, id `227245168443654145`): **autorizado** en `DISCORD_ALLOWED_USERS` (añadido 2026-09-29, gateway reiniciado). Puede haber **handoff de vuelta** en el futuro (pasarle el testigo), pero **nunca concurrencia**: o trabajamos nosotros o trabaja él, nunca los dos a la vez sobre el mismo material.
- Active objective: mapa DayZ funcional ~12×12 km que **condensa la región báltica** de la captura (golfo de Finlandia, San Petersburgo, Narva, Luga, Peipus/Ilmen), fiel a la distribución a escala, con assets vanilla primero.
- Last useful context: [research completo heredado](research/2026-09-29-mapa-condensado.md) + [contrato inicial heredado](procedencia/project-brief-exta.md). Origen: transcript del PM en [`procedencia/transcripcion-pm-exta.txt`](procedencia/transcripcion-pm-exta.txt).
- Estado declarado al cierre del research de Exta: base 12,288 km generada (costa, lagos, relieve, bosques, zonas urbanas) e importación en Terrain Builder **en curso cuando se agotaron los créditos de Codex**. Sin edificios, sin carreteras físicas, sin pruebas in-game, sin WRP ni PBO entregados.
- **Referencias geográficas recibidas 2026-09-29 (Guillermo)**: dos capturas de Google Maps en [`procedencia/`](procedencia/) — `referencia-google-maps-a-san-petersburgo.png` (noreste: San Petersburgo, Ládoga, Neva, Kotlin) y `referencia-google-maps-b-narva-luga-peipus.png` (suroeste: Narva, Luga, Peipus, Ilmen, costa de Ust-Luga/Sosnovy Bor). Ambas sin coordenadas ni escala visibles: georref por localidades.

## Procedencia

- **Autor**: Exta (`extanator`, Discord id `227245168443654145`), comunidad externa. PM autorizado puntualmente por Guillermo el 2026-09-29.
- **Material recibido**: `DayZ_Baltic_12km_1.rar` (3 ficheros: README, project-brief, research) + `message.txt` (transcript del PM con el desarrollo completo). Guardados en [`procedencia/`](procedencia/).
- **No verificado por nosotros**: todo lo declarado en el material heredado son afirmaciones de otra IA (Codex en la máquina de Exta). Tratar como `[ASSUMPTION]` hasta validación propia (R2 del vault).

## Stack / Dependencies (declarado en el material heredado)

- Runtime: DayZ + DayZ Tools (Terrain Builder 1.31, Terrain Processor 1.0.0.3, AddonBuilder) en la máquina de Exta.
- GIS propuesto: Copernicus GLO-30 + OpenStreetMap (Rusia NO + Estonia) + ESA WorldCover 2021 + Sentinel-2 L2A, procesados con QGIS/GDAL y scripts reproducibles → Terrain Builder.
- Plugin evaluado: Big G' Terrain Tools (beta, QGIS ≥3.32, celda mínima 3,75 m) — como acelerador en proyecto desechable, no como pipeline.
- Descartado para el primer prototipo: `4096 × 3 m` (4× muestras y choca con el límite del plugin). Propuesta técnica: `2048 × 2048 celdas de 6 m = 12,288 km por lado`.
- QGIS en la máquina de Exta: **no operativo confirmado** (carpeta residual sin ejecutables). Python global 3.14.4 sin paquetes GIS.

## Encuadre aprobado por Guillermo

- **2026-09-29: límites v0 aprobados** («ok a los limites»). Toda la referencia regional y el acercamiento íntegro de San Petersburgo, con Narva, frontera y territorio occidental para el lore. Prioridad al agua, zona natural y conexiones; assets vanilla primero.
- **2026-09-30: relieve selectivo aprobado**. Se permite exagerar alturas por zonas, incluso por encima de×3 y sin fidelidad a la escala Z, en favor de la jugabilidad. XY, agua/islas, closeup, conexiones, navegación y carreteras lisas siguen siendo restricciones. Sustituye la elección binaria×1/×3; cotas concretas y agua regional se diseñan y validan en el repo, P12/`plans/selective-relief.md`.
- **2026-09-30: reserva y biomas (P13)**. Conservar la reserva natural como zona clave, con árboles muy densos en ciertos sectores, claros, transiciones y humedales. Proteger el terreno ahora; colocar vegetación después según P10 y medir rendimiento del sector denso. Perímetro de conservación por contrastar; no confundir el marcador aproximado con un límite legal.
- Fuente de esta decisión: [decisions/decision-log.md](decisions/decision-log.md). El KML y las coordenadas de referencia están fijados por SHA-256 en la evidencia enlazada allí; la transformación GIS conserva el marco aprobado mediante una escala única de Web Mercator a metros locales. La interpretación local de TB ya fue medida: véase la convención al final y el HANDOFF para su estado de aplicación.

## Decisiones heredadas cerradas (por Exta con su usuario)

1. Región completa **condensada** (~18-20×), no recorte real de 12 km.
2. Distribución fiel a la captura a escala; costa, lagos, posición de ciudades y conexiones principales prioritarias.
3. Edificios y anchuras de carretera **a escala humana** (no comprimidos); poblaciones con representación reducida.
4. Primera versión **vanilla** (edificios y vegetación).
5. Encuadre georreferenciado con 11 localidades reales contra Google Maps (@59.46725,30.9108599); error medio ~7 px sobre 1.095 px de ancho.
6. Dos variantes de relieve previstas (escalado físico vs moderadamente exagerado), sin coeficiente Z cerrado.

## Enlaces internos

- [[AI/10_Projects/DayZ_Baltic_12km/research/2026-09-29-mapa-condensado|Research heredado (destilado)]]
- [[AI/10_Projects/IberiaMap/IberiaMap|IberiaMap]] — proyecto hermano de mapa real comprimido; su research de viabilidad (Game Terrain Tools, Arma3_QGIS) es cross-referencia directa.
- Estado vivo: [HANDOFF del repo dev](<C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/HANDOFF.md>), en `P:\DayZ_Baltic_12km_dev`.

## Do-not-do

- No tratar las afirmaciones del material heredado como verificadas. La base propia se procesó e importó aquí; los gates posteriores de juego, agua y navegación están en la matriz y el HANDOFF vivo. No usar este brief estable para deducir qué prueba está pendiente.
- No re-descargar geodatos de producción sin fijar antes el encuadre definitivo (advertencia del propio research heredado).
- No adoptar Big G' Terrain Tools sin prueba en proyecto desechable.

## Entorno propio y convención de desarrollo

- Objetivo de capacidad confirmado por Guillermo: **80–100 jugadores**, experiencia tipo Chernarus; hardware y rendimiento sin validar.
- Repo: `P:\DayZ_Baltic_12km_dev` (ruta física `C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev`). GIS Python 3.12.14 aislado, dependencias fijadas; no depende de QGIS.
- Fuentes propias: Copernicus GLO-30 AWS 2021, WorldCover 2021 v200 y OSM Estonia/Rusia NO. Originales fuera de OneDrive, referenciados por SHA-256. Fuente inmutable, generación y retoques separados.
- Plano: una escala global XY conserva el encuadre y el acercamiento de San Petersburgo. Metros de ingeniería TB, no UTM; origen (200000,0). Dos variantes Z históricas para comparación; criterio vigente de relieve selectivo aprobado30-09, con cotas regionales por diseñar.
- Assets vanilla primero y anchuras humanas. Agua elevada, canales y cruces requieren prueba del consumidor. No deducir jugabilidad de la red OSM.
- Prioridad30-09: terreno, agua, cauces navegables y navmesh base antes del mapeado. Ríos para lancha vanilla con margen para barcos medianos; puentes elevados. Carreteras lisas con rasantes y empalmes suaves, después probadas con vehículos. P9/P10/P11 del repo y decisiones del30-09; la navegación se regenera tras colocar los objetos.
- [Sesión de fase 0](../../30_Sessions/2026-09-29-dayz-baltic-12km-base-geografica-fase0.md) · [informe y paquete](<C:/Users/guill/Documents/Codex/2026-09-29/vamos/outputs/baltic-phase0/informe.md>).

## Convención de Terrain Builder verificada aquí

[WORKS, MECHANISM UNKNOWN] Proyectos nativos en `tb/registration_probe` y `tb/baltic_physical`; el guion en la carpeta de salida del marco fue rechazado, el subrayado aceptado. Zona 31N únicamente como contenedor de metros de ingeniería, sin georreferencia UTM real. Malla observada a −3 m E/+3 m N de los centros GIS (celda 6 m); el ensayo analítico pasa, pero la corrección productiva necesita gate de costa. Importar agua como contornos segmentados para conservar huecos/islas; los polígonos originales son autoridad. No dar por fiel el DBF reexportado. Fuentes intactas; binarios TB preservados fuera del índice Git con manifiesto. [Sesión y evidencia](../../30_Sessions/2026-09-29-dayz-baltic-12km-importacion-tb-buldozer.md).

## Corrección del alcance de la observación UI — 29-09-2026, Narva

La fórmula UI precedente es histórica y **no predice la malla nativa medida en Narva**. Las consultas de Buldozer (289 puntos de cuadrícula + 289 de perfil separado) corresponden a X=200000+6*col, N=6*(2047-row), diagonal NW-SE; esto coloca los vértices nativos a −3/−3 m de los centros GIS en este ensayo. No se ha demostrado como regla global ni aplicado al terreno de producción. Se conserva el registro UI como evidencia de lo observado, no como API numérica del motor. Estado de aplicación y ensayo local: HANDOFF del repo y [sesión Narva](../../30_Sessions/2026-09-29-dayz-baltic-12km-narva-ensayo.md).
