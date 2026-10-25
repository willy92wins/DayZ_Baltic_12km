# EV112 — navegación de E y sonda definitiva
**37 rutas locales PASS en servidor normal DayZ 1.30, con 108 puntos.**
La generación de E terminó sin cambios en sus tres PBO. El archivo propio
TESM9/VAND12 contiene 966.289 teselas de12,5m; supera el inspector de prefijos
y cobertura. Sus recuentos declarados no equivalen a polígonos decodificados.
El paquete sustituye únicamente el NM: las otras6.826 entradas y el WRP son exactos.

La sonda A encontró13 coordenadas X cero al construir un Vector con
SurfaceRoadY anidado. Se conserva como FAIL. B compara ambas formas en el
mismo run: la forma anidada reproduce13 fallos y las variables escalares
explícitas conservan los108 puntos. Los valores flotantes se leyeron antes
de ToString: no se atribuye el defecto únicamente al texto. No se conoce el
mecanismo interno del compilador/motor y SurfaceY no reprodujo el fallo.

C ejecuta la fuente definitiva sin las llamadas de diagnóstico. Sus37 consultas
pasan y su log coincide byte a byte con la salida corregida de B. El consumidor,
las consultas XZ, expectativas y umbrales permanecen intactos. Fable5.1 emitió
SOUND-with-fixes: comentario acotado a SurfaceRoadY, procedencia B/C corregida,
ejecución C propia y límites del RPT documentados. B conserva su referencia
heredada original y añade execution-reference.json; C usa su referencia propia.

El RPT contiene la excepción de PluginItemDiagnostic al iniciar los plugins MCP
y dos PGFilter sin liberar al cierre de estas sondas. Se conservan los logs:
no se declara una ejecución libre de errores. No hay una línea del RPT que
confirme expresamente la carga del NM. La evidencia local combina paquete
identificado, servidor normal sin bootstrap y consultas nativas positivas y
negativas; no acredita locomoción de actores, contacto cliente ni navegación global.

Identidad: executable_sha256 de MCP usa psutil-exe-v2, un hash de ruta normalizada,
no del archivo ejecutable. identity-schemes.json explica la distinción; los recibos
host nuevos usan executable_file_sha256. Los recibos antiguos se conservan.
No se publican NM/PBO ni datos vanilla. Los .gz conservan los bytes originales;
ORIGINS-runtime.json enlaza su SHA256 descomprimido. Todos los runs propios se cerraron.

Esta navegación pertenece a E. No acredita el terreno F ni una visita visual.

verified-sources/ conserva las fuentes exactas usadas por la validación, incluidas
las terminaciones de línea del host Windows; Git puede normalizar la copia de
trabajo del código. Los hashes de ejecución se contrastan con estos bytes.
