# Contraste de altura de navegación con arroyos vanilla

Estado: plan revisado por Fable5.1 SOUND-with-fixes y conciliado por Codex. Codex
ejecutor/integrador por la petición autónoma vigente. No cambia ninguna puerta
de aceptación de Baltic, tolerancia, consulta, geometría o resultado anterior.

## Evidencia que motiva este paso

[EXACT] Nav8 pasa las607 consultas de kit7 con máximo0,711963 m frente a0,801 m,
pero falla RAM1,265913/1,241333. Nav12 falla tres alturas nuevas; no se midió RAM.
El control original12,5 conserva cuatro fallos y pasa seis RAM nuevas ABBAAB:
ratios0,832329/0,844646, dispersión máxima0,170302%, sin repeticiones. Ambos
bloques comparten ejecutable, configuración, misión normalizada y paquetes
auxiliares. Se publicaron corrección y límites; HEAD público186f336.

[EXACT] Los seis waypoints fallidos de Nav12 se reproducen con polígonos reales
a5,65e-7 m. La física y la grava visual coinciden en esos puntos. Los contadores
empíricos de detalle9:12 son cero en todas las teselas Nav8/Nav12 y también en
las94249 teselas de la malla Chernarus TESM9 realmente medida. Por tanto, ese
censo por sí solo no distingue un defecto de generación de Baltic.
Referencia desplegada: worlds_chernarusplus_nav.pbo SHA
f0503b2bbcca0a5913a6545d6e1b324ef872f48486b7b6960ebeaa1b5b398c2e;
NM0b18d48d6c1e902e41b35b91588e84a3e3068a28df6d71cf6d74a6f80d29a163,
grid307x307, tesela50 m. No usar P:/dz/.../navmesh.nm: es otra copia TESM6.

[HIPÓTESIS] La desviación vertical de FindPath puede aparecer también en
arroyos vanilla, aunque el personaje se apoye físicamente en el suelo. No se
ha probado esa hipótesis ni la locomoción. Un FAIL vanilla no autoriza a borrar
los FAIL de Baltic, rebajar0,801 ni sustituir el contrato aprobado por otro.

El estimador de dos diagonales sigue sin ser oráculo. El diagnóstico fino de
9,5 a10,5 m no aporta un candidato con margen claro en los14 puntos conocidos.
Antes de otra generación, contrastar el mismo observable con el referente
operativo aporta más información que una búsqueda adicional de anchos.

## Prueba propuesta y anclas

[DESIGN] Una sonda de servidor Chernarus actual, solo lectura, sin cliente,
spawn, CE, AI añadida o modificación del mundo. Seleccionar24 piezas vanilla
long_straight, independientemente de cualquier resultado de navegación:
agrupar por leaf/sand/moss, ordenar por(z,x,shape) y escoger8 índices equiespaciados
por familia mediante floor(i*(N-1)/7), i=0..7. La encuesta histórica contiene
218/188/148 piezas respectivamente. Congelar selección, CSV y hashes antes de
lanzar. No sustituir una pieza que falle por otra más favorable.

La encuesta antigua solo localiza posibles piezas; no acredita el contenido
actual. Antes de medir cada pieza, GetObjectsAtPosition y GetShapeName deben
encontrar exactamente un objeto con el modelo esperado y posición3D a<=0,05 m
de la registrada (CSV con tres decimales). Registrar posición y transformaciones
actuales; falta, duplicado o drift deja la prueba INCONCLUSA y no autoriza
seleccionar otra pieza. Archivar las identidades actuales de todos los PBO
vanilla cargados y del ejecutable como en el control RAM.

Fijar radio40 m del lookup en Vector(x,0,z). Cuentan como candidatos únicamente
objetos con el modelo esperado Y posición3D a<=0,05 m; los vecinos más lejanos
del mismo modelo no son duplicados. La encuesta histórica deduplicaba con
redondeo0,1 m y no prueba unicidad actual. Registrar origin y los tres ejes
actuales de ModelToWorld para conservar orientación y escala, sin asumir escala1.

Por pieza: dos rutas nominales de orilla, ModelToWorld(Vector(q,0,-6)) a
ModelToWorld(Vector(q,0,6)), q=-6,+6. Antes de SampleNavmeshPosition, calentar
objetos y fijar Y de los extremos con SurfaceRoadY+.2 del motor actual; registrar
esas Y y los tipos de superficie. No afirmar que los48 tramos son equivalentes
en pendiente o que todos están secos sin observarlo. Añadir control NONE con
los mismos extremos de la primera ruta. Total49 consultas, selección congelada.

Usar siempre SurfaceRoadY(x,z) sin tercer argumento: LEGACY, idéntico al
observable de Baltic. No usar SurfaceRoadY3D UNDER de la encuesta antigua.
La fuente de Y de los extremos sí difiere: en Baltic era max(roof,terreno)+.2
offline; aquí es lectura actual del motor+.2. Declarar esa diferencia.
Extensión comprobada sobre los tres ODOL del water.pbo ACTUAL medido: Roadway
x[-7,7],z[-12,12], los cuatro extremos(+-6,+-6) dentro de sus caras. Evidencia
chernarus-nav-height-reference-20261027/extent-check.json; no usar solo la
geometría histórica para esta comprobación. Esto no prueba que sean bancos secos.

[EXACT] Contrato utilizado en Baltic, a conservar en la sonda de referencia:
missions/BalticKit7NavV1.BalticTrial/init.c:40-41: flags WALK, excluyendo SWIM,
SWIM_SEA y DISABLED; NONE excluye ALL. :68-72 SampleNavmeshPosition radio2 y
FindPath. :84-96 GetObjectsAtPosition radio40, SurfaceY y SurfaceRoadY en cada
waypoint. :87-88 corresponden al observable vertical hoy verificado.
Firmas locales: P:/scripts/3_game/ai/aiworld.c:98,122; global/game.c:923,1177;
entities/object.c:503,873. La encuesta vanilla anterior usa esas lecturas en
E:/DayZ-Baltic-Build/vanilla-tricks-20261013/missions/BalticVanillaTricksV1/init.c.
Releer la firma exacta de cualquier llamada adicional antes de implementarla.

## Interpretación y controles

[DESIGN] Consumidor de diagnóstico separado; no editar verify_kit7_nav_ev112.py.
Exigir mundo/UUID,49 consultas únicas, END49, controles de schema, vectores
finitos,49 identidades de extremos esperadas derivadas de los24 objetos reales,
orden y número de waypoints, filtro NONE sin ruta. Las48 rutas positivas con
sa/sb/path false, extremos incompletos o distanciaXZ>2,1 se registran como
no comparables; no se eliminan del informe. Si ninguna es comparable, INCONCLUSO.
Registrar por ruta y waypoint error absoluto NavY-SurfaceRoadY, contra el MISMO
0,801 m, y NavY-SurfaceY como discriminador. No convertir el resultado en PASS
de Baltic. Separar comparabilidad, integridad de captura y distribución de errores.

NONE requiere sa=false,sb=false,found=false,count=0; inicializar salidas a,b en
vector cero y comprobar que permanecen intactas según aiworld.c:120. Mantener
por waypoint el orden de Baltic: FindPath, warm radio40, SurfaceY, SurfaceRoadY.
La cabecera debe indicar el mundo real ChernarusPlus (observado en las seis
mediciones); el lector puede normalizar el caso, nunca aceptar otro mundo.

Registrar también |RoadY-GroundY| y estratos de superficies elevadas. Si no hay
ninguna, no queda contrastado el mecanismo específico de una plataforma elevada
como kit7. NO convertir todas las rutas a INCONCLUSO por ese motivo: NavY puede
diferir de RoadY aunque RoadY=GroundY. La propuesta de Fable de que separación
RoadY-GroundY>0,801 es condición necesaria para fallar es matemáticamente falsa.
El resultado general del observable se conserva; la comparación de plataforma
elevada se declara no cubierta. No atribuir el error al generador sobre Roadway:
el censo y este contraste no aíslan qué LOD consume ni el algoritmo interno.

Positivos/negativos antes del run: captura completa mínima y error de altura
contado, UUID/mundo erróneos, object missing/drift/duplicate, Q duplicada o
faltante, END incorrecto, waypoint faltante/no finito, NONE encontrado y cambios
de input. Script-validator debe escanear1 archivo real. Revisión Fable de plan
y diferencial operativo antes del lanzamiento; máximo dos rondas de corrección.

Presupuesto: un run nuevo de servidor, observador y captura acotados. Reusar el
patrón revisado de lifecycle con FIFO directo(on_busy=queue,600,takeover=false),
sin comprobar ocupación ni prelease; adoptar solo el run devuelto. Verificar
PID/creación/ejecutable/misión, puenteBOUND, cierre oficial y liberación. Timeout
o identidad incorrecta es INCONCLUSO, nunca aceptar datos parciales ni reiniciar
para obtener un resultado favorable. El banco se libera al acabar la captura.

Si vanilla también excede0,801, solo queda demostrado que el observable no es
exclusivo de Baltic en esta muestra; no prueba ausencia de problemas de actores
ni invalida por sí solo el criterio. Si no excede, el fallo sigue acotado a los
candidatos Baltic observados; no prueba causa única. En ambos casos conservar
el resultado, revisar el mecanismo y plantear el siguiente cambio antes de
modificar un criterio de producto. No autoriza otra generación ni parchear NM.
