# Navmesh: carga, generación y empaquetado

## CONTRATO Y FUENTES

La [guía oficial de generación](https://community.bohemia.net/wiki/DayZ:Generating_navigation_mesh)
describe DayZDiag como servidor con `-startNavmeshDataServer`, una misión vacía,
conexión de NavMeshGenerator y guardado de `.nm`. La navegación depende del WRP:
conserva el binario exacto usado para generarla y regenera si cambia.

El [changelog oficial 1.18](https://forums.dayz.com/topic/252788-experimental-update-118-change-log/)
documenta el cierre al no encontrar la navegación configurada. Por eso no basta
la frase histórica de la guía sobre terrenos sin navmesh para afirmar que una
versión actual arrancará con una ruta inexistente o vacía.

## DISCRIMINADORES BARATOS

1. Lee el PBO desplegado y la configuración compilada de CfgWorlds. Comprueba
   identidad del mundo, worldName, Navmesh.navmeshName, prefijo y entrada `.nm`.
2. Distingue proceso vivo, conexión al servidor de datos, World params received,
   misión cargada, generación terminada, archivo guardado y carga del archivo
   propio. El éxito del launcher solo demuestra su contrato, no todos esos pasos.
3. Si una configuración temporal parece ignorada, inspecciona la configuración
   efectiva mediante una sonda temprana. No repitas variantes sin comprobar qué
   configuración consumió realmente el juego.

En DayZDiag 1.29.163709 se verificó un constructor de `modded class DayZGame`
en un addon `CfgMods.defs.gameScriptModule`, dependiente de Game. Registró datos
antes de la carga del mundo/aviso. APIs verificadas en el árbol instalado:
`scripts/3_Game/global/game.c:448` ConfigGetText(path,out string), `:611`
ConfigIsExisting(path); `scripts/3_Game/dayzgame.c:994` constructor DayZGame;
`scripts/1_Core/proto/ensystem.c:397` FileExist(name). Reanclar antes de reutilizar.
Son observaciones locales, sin RPC, actores ni escrituras en el mundo.

FileExist devolvió false para la ruta vanilla con barra inicial aunque el motor
posteriormente cargó esa navegación. No lo uses como prueba suficiente de ausencia
en el VFS; compara con la carga del consumidor y con entradas reales del PBO.

## BOOTSTRAP TEMPORAL VERIFICADO

Caso Baltic: la ruta propia aún no existía y bloqueaba la misión incluso con el
servidor de datos activo. Un addon separado, dependiente de la CfgPatches del
terreno, cambió únicamente Navmesh.navmeshName a la ruta instalada de Chernarus:
`\dz\Worlds\chernarusplus\navmesh\navmesh.nm` (referente en
`DZ/worlds/chernarusplus/world/config.cpp:47`). Mantuvo WRP y GenParams propios.

Esto permitió cargar la misión vacía y recibir los parámetros 12.288km del mundo
en el generador. Es un recurso de arranque, no navegación válida para Baltic.
No redistribuyas/copias la navegación vanilla como resultado del proyecto.
Retira el addon temporal antes de aceptar la carga/IA con el `.nm` propio.

### Empaquetado que anuló el override

Un primer paquete `-packonly` contenía config.bin correcto y config.cpp vacío.
La sonda mostró CfgPatches del bootstrap ausente y la ruta antigua intacta.
Reconstruir mediante AddonBuilder normal produjo un paquete con solo config.bin,
idéntico byte a byte al anterior. La siguiente ejecución mostró CfgPatches
presente, ruta esperada y marcador de misión; el generador recibió los parámetros.

Por tanto, en este caso aceptar el `.cpp` vacío como inofensivo fue incorrecto.
No basta buscar strings en config.bin si el motor no consume esa configuración.
No extrapolar a todos los archivos con .cpp ni a versiones sin ensayo.

Evidencia: runs `904f306e-ecf9-4d22-a7c3-25c0e4bf3cc4` (override ausente) y
`af20e7ce-74c4-4ba3-a095-4de7e5250978` (presente y misión cargada).
PBO bootstrap anterior SHA256 `56f74053ed81109007c81b5deee9baef8cf0bc541bd91b39d7a06af4c79aa0df`;
corregido `a9f497c7772c266997674a4d565f03b5db13254486b5b3b3a22fa8c0d1fed70f`.

## GENERACIÓN Y PRUEBA FINAL

En el launcher compartido usa la opción tipada `navmesh_data_server=true` si la
versión viva la expone; solo servidor. La opción genera el literal fijo, no una
interfaz de argumentos libres. Si falta, una modificación del launcher requiere
alcance autorizado y validación del bundle/registro; no lo evites lanzando el
proceso por otra vía. `dayz_test_run` sin lease previo; adoptar el run y mantener
su lease durante generación y ensayos físicos, renovándolo antes de su caducidad
según el protocolo vivo de DayZ MCP. `dayz_test_close(run_id)` requiere el lease
del dueño para intentar cierre ordenado; si devuelve `stop_required`, liberarlo
y llamar a `dayz_test_stop(run_id)`. `dayz_test_run` y `dayz_test_stop` gestionan
su propio lease y se invocan sin uno previo. Reanclar el contrato vivo: fuente
`tools/dayz_mcp/server.py:3939-3974` y recibos `cleanup.json` de los runs Baltic
del01-10. Cerrar solo el run propio por lifecycle y comprobar session_status.
Si otra sesión tiene el recurso, esperar
su turno; un resultado `takeover_required` no autoriza a cerrar su prueba.

Caso Baltic del01-10: una lancha siguió ejecutándose sin propietario y otra
sesión adoptó/cerró ese run. El audit trail confirmó cierre autorizado de esa
sesión; no fue un crash ni fallo del terreno. Su secuencia incompleta sigue
siendo INCONCLUSA para los sectores sin destino. Evidencia:
`evidence/overnight-2026-10-01/regional-boat-v2/runtime-interrupted/termination-audit.json`.

Conecta a loopback, exige World params received y revisa que el rango corresponde
al mundo propio. Generate all usa sus parámetros; una generación parcial no
acredita cobertura completa. Guarda explícitamente con extensión `.nm` y conserva
estadísticas y hash. No tomes estimación de tiempo o 100% como prueba de archivo.

Empaqueta el archivo nuevo conservando todos los bytes del WRP de generación.
Si el PBO ya contiene una navegación propia anterior, exige su ruta y hash
antes de reemplazarla. El helper Baltic attach_navmesh.py mantiene la negativa
por defecto; --replace-existing-sha256 habilita únicamente ese reemplazo y
compara todas las demás entradas del PBO. Controles sin opción y con hash
incorrecto fueron rechazados antes de crear staging; el reemplazo real pasó
la comprobación de6826 entradas intactas. Esta prueba es de empaquetado.
Al usar `-packonly`, comprueba que no se ha introducido otra vez config.cpp vacío;
preferir FileBank sobre un árbol compilado inspeccionado si es el flujo disponible.
Reabre el PBO final: compara WRP, configuración y `.nm` con sus entradas esperadas.
Arranca sin addon de bootstrap y sin sonda temporal: carga propia antes de IA.
La generación completa y un arranque correcto no demuestran caminos útiles entre
islas, puentes o interiores; esos recorridos necesitan ensayos separados.
# Actores nativos y sondas de diagnóstico

Una ruta de AIWorld no prueba locomoción real. Usa un actor vanilla aislado,
estímulo comprobado y registro de servidor; no fuerces su posición o velocidad
para acreditar navegación. Antes del puente, exige respuesta local al estímulo.
Un ruido puntual puede provocar búsqueda lateral o detenerse lejos del punto:
mantén criterios físicos y distingue timeout de conducta de fallo de navmesh.

Congela también el estímulo. En Baltic V10, AddNoisePos completó10 de19 casos,
pero hubo tres timeouts terrestres y seis fallos de cruce; ocho consultas
FindPath del puente sí pasaron con controlNONE negativo. Sustituirlo por
AddNoiseTarget falló incluso en el control local de25m. Su firma disponible no
acredita que produzca una persecución hasta la coordenada. No cambiar alturas
ni regenerar NM basándose únicamente en ese timeout. Evidencia:
`evidence/overnight-2026-10-01/regional-chase-v1/runtime-complete/`,
`regional-chase-v2/failed-control/` y `bridge-path-v10/`.

Comprueba la huella del soporte separada del corredor de aceptación. Un gate
de±4m puede fallar mientras el actor aún pisa Roadway de±7.1m; no llamar caída
a toda desviación. Tampoco ampliar el corredor para aceptar registros previos:
conservar su fallo y describir el alcance. Usar superficie física registrada y
geometría independiente para localizar caídas reales. Tramos cortos con actores
nuevos, consultas del grafo y persecución continua desde tierra son pruebas
distintas; ninguna sustituye silenciosamente a las otras.

En una persecución con humano controlado, verifica al objetivo con el mismo rigor
que al infectado: trayectoria continua en servidor, velocidad real, salud y piso
físico. Entradas solicitadas de caminar no acreditan marcha lenta efectiva. En
Baltic V10, la continuaV1 paró al superar el humano4m, todavía sobre el puente;
un ensayo adicional V2 congeló tablero principal6m y accesos4m y también falló:
objetivo6.003488m lateral y pico9.236822m/s, infectado en contacto con el tablero.
No confundir este fallo del consumidor con una caídaAI o navmesh inválida. Un
control del mismo humano sin infectado permite comprobar si este último es
necesario para reproducir el síntoma, sin demostrar por sí solo la causa interna.
Preserva los resultados originales y el criterio histórico de carril por separado.
Fuentes Baltic: `continuous-pursuit-v1/runtime-complete/verification.json` y
`continuous-pursuit-v2/runtime-complete/verification.json`, bajo la carpeta
`evidence/overnight-2026-10-01/`. El Roadway principal mide±6m; las aceras llegan
a±7.1m. Ninguno equivale automáticamente a anchura útil sin colisiones.

El control posterior sin infectado pasó el mismo trayecto humano este:294.082m
de avance,973muestras,194.645s,desviación0.357m y pico2.412m/s, sin pérdida de
salud ni contacto.15 negativos rechazados contra el control local real. Eso
acredita caminar por ese puente y orienta hacia la interacción del perseguidor;
no demuestra que solo la colisión/ataque produzca el problema, ni acredita la
IA completa o el regreso. Referencia `bridge-human-control-v1/reference.json`,
resultado `bridge-human-control-v1/runtime-complete/verification.json` en la
misma carpeta nocturna. Mantener abiertos los FAIL de persecución.

[IN-GAME CONFIRMED, asociación observada] En la V3 de Baltic, cuatro casos
salieron de la envolvente del tablero y descendieron sin registrar CHASE;
dos llegaron aY≈11m, pero fallaron el corredor y el cálculo de contacto que usa
esa misma huella estrecha en el verificador. Todos los cruces
aceptados registraron CHASE. Esto orienta el siguiente discriminador hacia
percepción/objetivo móvil, pero no identifica causa raíz. Registrar estado
mental junto a posición y altura evita confundir buscar un ruido con perseguir
al objetivo. Fuente: `regional-chase-v3/bridge-behavior-analysis.json`, bajo
`evidence/overnight-2026-10-01/` del proyecto Baltic. Los seis FAIL originales
se conservan; un gráfico descriptivo no los convierte en PASS.

En Baltic/DayZDiag1.29.163709, el diagnóstico `if (input.GetTargetEntity())
target = input.GetTargetEntity().GetType()` causó access violation nativa en
ObjectGetType, con entidad id0, después de usar AddNoiseTarget. La comprobación
booleana no protegió esa desreferencia. Retirar la lectura permitió terminar
el mismo ensayo sin crash. No culpar al WRP por un fallo originado en la sonda
ni usar GetTargetEntity.GetType como instrumentación segura de ruido sintético.
El mecanismo de la referencia nativa no se aisló; no generalizar a todos los
retornos EntityAI. Evidencia: proyecto Baltic, evidence/infected/noise-v1-crash.txt,
noise-v2.log y runtime.json; las fuentes archivadas conservan ambos casos.

## CONSULTA GEOMÉTRICA FRENTE A CONSUMIDOR FÍSICO

En Baltic/1.29.163709, con WRP nativo y navmesh recién generada, el muestreo
del acceso este devolvía Y≈2.2m donde SurfaceRoadY era9m. WALK y ALL, con distintas
Y solicitadas, reprodujeron la discrepancia. No se aisló el algoritmo interno:
la simplificación vertical es hipótesis, no causa raíz demostrada.

La prueba posterior con infectados vanilla cruzó ambos sentidos sobre el
tablero9m, con salud100 y sin modificar su movimiento después del spawn.
Por tanto, esa discrepancia numérica no demostraba por sí sola una caída o
rotura de la IA. Conservar el gate geométrico fallido; agregar el resultado
del consumidor sin relajar retrospectivamente0.8m ni extrapolar a toda la región.
Evidencia Baltic: `evidence/navigation/native-nav-v2/verification.json`,
`native-nav-seam-v1/engine.log` y `native-chase-v2/verification.json`.

Coloca el objetivo humano y deja que se estabilice antes de crear el actor.
Registra su posición real durante toda la prueba. En el primer ensayo el
objetivo derivó5.25m en el control inicial; se conservó FAIL. Con20s de espera
previa y el mismo límite2m, el segundo registró deriva0 y pasó control/ida/vuelta.
El mecanismo de la deriva inicial no se aisló. El verificador acepta ese registro
real y rechaza ocho corrupciones (salud, posición, objetivo, formato y terminación).

## LÍMITE DEL COMPILADOR EN SONDAS GRANDES

No desenrolles cientos de consultas y escrituras en una sola función generada.
Una sonda Baltic con751 puntos pasó el linter offline pero el compilador del
motor emitió `Too many instructions per function` y el proceso terminó con
access violation. Dividir la misma lista en helpers de32 puntos permitió compilar
y obtener el registro completo.32 es el tamaño ensayado, no un máximo del lenguaje.
El linter no acredita los límites del compilador nativo. Mantén separados el
fallo de instrumentación y la validez del WRP/navmesh. Evidencia:
`native-nav-probe-v1-failed/`, manifiestos native-nav-reference-v1/v2 y misión V2.

