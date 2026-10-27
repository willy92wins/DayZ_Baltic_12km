# Kit7: diferencias de altura dentro de los polígonos

**Diagnóstico local; aún no hay mecanismo de generación ni corrección verificados.**
No se inició DayZ, no se generó ni cambió ninguna malla y no se modificaron límites.
Se reutilizó la reconstrucción empírica archivada; no se creó un decodificador
VAND12 general ni se extrapoló el layout a todo el mapa.

Se ampliaron las superficies empaquetadas a 52 coordenadas de 6 modelos. Son 48
observaciones de vértices de las mallas de 8/12 m; 31 tienen Roadway del kit y 17 no.
Ninguno de los 48 vértices muestreados está bajo el terreno. En los 31 comparables, la diferencia nav-Roadway es
positiva: 0,0194–0,1200m para 8 m y 0,0110–0,1598 m para 12 m. Los 17 casos sin Roadway
se conservan con terreno y sus límites. Los 5 puntos anteriores se reproducen con
la misma implementación, no son un control independiente. Los 6 controles de
superficie nativa sí son independientes: residuo máximo observado 4,0e-7 m.

Los seis waypoints Nav12 se reconstruyen con su único triángulo del abanico
geométrico, sin escoger el triángulo por su coincidencia con Y nativa. En los
tres fallos, la descomposición local da:

|Consulta/índice|Error nativo|Diferencia superficie–cuerda|Sesgo interpolado de vértices|
|---|---:|---:|---:|
|piece116left/1|0,856856m|0,993497m|+0,136642m|
|piece116right/1|0,923148m|1,017099m|+0,093951m|
|seam116right/0|0,818588m|0,916121m|+0,097533m|

Los tres casos PASS de Nav12 comparten esta interpolación: errores 0,552710,
0,555381 y 0,081625 m, por debajo del mismo umbral. No se postula otro mecanismo.

La cuerda interpola las superficies conocidas en las XZ de los vértices; no es
la superficie real dentro del polígono. La diferencia entre ambas, menos el
sesgo positivo de los vértices, reproduce el error observado. Esto contradice
la explicación simple de vértices hundidos en estos casos y localiza la
aproximación en el interior de esos polígonos. No identifica cómo el generador
selecciona/simplifica polígonos ni qué parámetro lo corrige.

Se contrastó después la geometría de 8 m ya archivada de 12 teselas, sin nuevo
decodificador binario. Finitud, pertenencia de vértices, límites XZ y cardinalidad
comprobados. Los seis puntos nativos de Nav8 tienen exactamente la misma XZ y
superficie consultada que Nav12; su abanico reconstruye Y con residuo máximo
4,1887e-7m. Los tres fallos Nav12 quedan en0,004105/0,101196/0,020752m con Nav8.
Se conservan dos contraejemplos: piece116right/0 empeora 0,555381→0,651269m y
seam116right/1 empeora 0,081625→0,711670m. No hay mejora monótona ni predicción
para otra rejilla, y este contraste no resuelve RAM. En cada caso solo había
un triángulo candidato; no se probó una selección entre superficies superpuestas.

Límites: superficies nativas en 6 waypoints, no en todas las esquinas; otros objetos
no inventariados: en la esquina (9137,9; 11268) se usa terreno a 1,634 m al no
haber Roadway conocida; otra superficie omitida alteraría la descomposición.
Detalle local de 8/12 m, sin cobertura de 12,5 m ni global. Roadway
aquí es el LOD del kit fluvial; no demuestra carreteras del mapa. No hay ahorro
RAM medido ni base para modificar binarios, subir vértices o probar otro ancho.

La ayuda del generador instalado, verificada por SHA y ejecutada con --console
--help, no muestra controles de refinamiento en su CLI. Esto no prueba que no
existan en otros canales. La [documentación primaria de Bohemia](https://community.bistudio.com/wiki/DayZ:Generating_navigation_mesh)
expone GenParams y recomienda conservar los parámetros de generación salvo el
nombre de archivo y la semilla; no ofrece en esa página un control de detalle
que permita especificar una corrección. Consulta: 2026-10-27. No se inventa una API.

La triangulación en abanico presupone convexidad, que no se comprueba en este
lector; los residuos la validan solo numéricamente en los seis puntos. El gate
binario no se reejecuta: se hereda del script archivado
[diagnose_kit7_grid_vertices.py](../kit7-nav12-rejected-20261027/scripts/diagnose_kit7_grid_vertices.py),
su JSON por hash y [deployment-parity.json](../kit7-nav8load1-native-20261027/deployment-parity.json),
que liga la malla 360a… con la corrida Load1 cerrada. Los puntos nativos proceden
de esa corrida, no de esta reconstrucción. Los tres diagnósticos comparten el
mismo presupuesto de 30 min de la fase vertex-surfaces; no se reinició el plazo.
publication-errata.json corrige la terminología de límites de los resultados
crudos, que se conservan byte por byte.

La coincidencia entre superficie nativa y empaquetada en los seis puntos
permite interpretar la diferencia de cuerda como una propiedad geométrica local;
no es una medida adicional independiente del lector.

Siguiente gate: verificar una vía para conservar la fidelidad local con menor
coste, mediante definiciones del generador o del formato y un plan nuevo
revisado. El diagnóstico termina INCONCLUSIVE_NO_VERIFIED_MECHANISM; el resultado
local de interpolación no es aceptación. Nav8Load1 mantiene config+607PASS y
RAM incompleto; el council ampliado sigue detrás del trabajo vigente.
