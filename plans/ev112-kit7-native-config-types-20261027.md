# Kit7: comprobar la lectura nativa de la configuración de navegación

Estado: EJECUTADO_DIAGNOSTICO_VALIDO. Implementación revisada Fable5.1 y
prueba nativa completa; ambos flags Baltic dan int/float0, controlesPASS.
Ver evidence/navigation/kit7-native-config-types-20261027. No cierre de RAM.
Codex ejecutor/integrador por la
petición autónoma vigente. Experimento diagnóstico previo a otra generación;
no es el council ampliado ni modifica el mapa o sus criterios.

## Descubrimiento y pregunta

[EXACT] El config de entrada de Nav8 declara
`filterIsolatedIslandsOnLoad="true"` y
`GenParams.filterIsolatedIslands="true"` (archivo local
`E:/DayZ-Baltic-Build/shape-repair-20261025/package-kit7-nav8-input-20261027/config.cpp:60,68`).
El config del Chernarus actual medido usa el número1 en ambos campos
(`.../chernarus-current-config-20261027/config.cpp:48,56`). Nav12 conserva las
dos cadenas. La diferencia de representación está observada, no aislada como
error ni como causa de consumo de memoria.

[EXACT] El censo de los cuatro NM por hash no encuentra teselas con cero
polígonos. En Nav8,1996338 de2359296 teselas declaran un polígono; ocupan
897066212 de1338007300 bytes. Los totales coinciden con los inspectores
archivados y pasan nueve controles. No es un perfil de heap ni demuestra
ahorro posible. No se eliminarán teselas ni editará el NM.

[HIPÓTESIS] El getter numérico puede interpretar la cadena "true" de manera
distinta al número1. Comprobarlo no demuestra qué getter usa el cargador de
navmesh, si ejecutó un filtrado o si libera memoria. La implementación nativa
del cargador no está disponible en las fuentes inspeccionadas.

[EXACT] APIs reales: `P:/scripts/3_game/global/game.c:449`
ConfigGetText(string,out string); `:524` ConfigGetFloat(string);
`:539` ConfigGetInt(string);
`:546` ConfigGetType(string), que devuelve una constante CT_*;
`:612` ConfigIsExisting(string). Registrar el valor numérico de tipo sin
inventar el valor de las constantes. Son lecturas del servidor; no RPC ni
estado de cliente.

## Diseño mínimo y alcance

[DESIGN] Una misión nueva server-only sobre el paquete Nav8 EXACTO ya
funcional; no recompilar ni modificar PBO, NM, terreno o configuración.
Tras OnInit y una espera acotada, registrar mundo, UUID y nueve lecturas.
Exigir mundo `BalticTrial`. Las rutas de API llevan clases separadas por
espacios y raíz `CfgWorlds`, nunca barras; por ejemplo
`CfgWorlds BalticTrial Navmesh filterIsolatedIslandsOnLoad`.

1. BalticTrial/Navmesh/filterIsolatedIslandsOnLoad.
2. BalticTrial/Navmesh/GenParams/filterIsolatedIslands.
3. ChernarusPlus/Navmesh/filterIsolatedIslandsOnLoad.
4. ChernarusPlus/Navmesh/GenParams/filterIsolatedIslands.
5. BalticTrial/Navmesh/GenParams/tileWidth (control8).
6. ChernarusPlus/Navmesh/GenParams/tileWidth (control50).
7. `CfgWorlds BalticTrial startTime`, texto"12:00".
8. `CfgWorlds ChernarusPlus description`, texto"Chernarus".
9. Campo deliberadamente inexistente bajo `CfgWorlds BalticTrial Navmesh`,
   con UUID como último token, control negativo.

Para los ocho existentes: ruta literal, existencia, tipo, bool de retorno y
texto de ConfigGetText, entero de ConfigGetInt y float de ConfigGetFloat.
Las dos cadenas conocidas permiten describir la conversión sin inventar
que deba ser por prefijo: sus valores numéricos se observan, no se imponen.
Para el inexistente no llamar
a los getters restantes: registrar sentinelas documentados. El consumidor
exige cabecera/UUID/mundo, rutas e índices exactos, nueve filas y END9, controles
numéricos Chernarus=1 y tileWidth8/50 en getters int/float, textos de control
exactos, negativo inexistente, finitud y ausencia
de duplicados. Conservar valores imprevistos y mensajes del motor; un retorno
inesperado no se sustituye por el valor deseado. Distinguir control ausente
de control inválido; ambos impiden aceptar la captura como comparable.

El flag de GenParams pertenece a la generación del NM: su lectura actual no
puede regenerar el archivo Nav8. Una eventual prueba sobre carga se limitaría
a filterIsolatedIslandsOnLoad. No atribuir al getter script la semántica de
lectura del cargador nativo, cuya implementación no se ha verificado.

Conservar el RPT completo desde el arranque, unido a PID/creación/misión.
Extraer líneas con filterIsolatedIslands, Navmesh, navmesh.nm y mensajes de
conversión, con contexto e índices. Diferenciar carga de mundo y llamadas de
la sonda únicamente si el log permite atribuirlas; si no, origen INCONCLUSO.
No asegurar que el motor emite un patrón concreto ni que ausencia de aviso
pruebe una conversión correcta. No publicar el RPT completo sin saneamiento.

ConfigGetInt sobre una cadena es una lectura diagnóstica; si el motor emite
un aviso o error de conversión, conservarlo como observación. No afirmar que
la misión carece de errores por haber escrito END. Sin salida completa o con
controles inválidos: INCONCLUSO. Esto no ejecuta ni sustituye las607 consultas
de aceptación; tampoco constituye un benchmark.

## Identidad, revisión y presupuesto

Antes de lanzar: verificar el Nav8 desplegado (mundoac088ccb…, piloto3d9550bf…,
agua97edcafe…), ejecutablea500be80…, bridge7078c2e4… y paquetes vanilla de la
referencia actual; conservar hashes completos en el manifiesto. Misión/lector
nuevos y UUID nuevo, validación estática de un archivo y controles positivos
y negativos del consumidor. Revisión independiente antes de la sonda.

Una corrida, sin generación ni repetición favorable. Presupuesto de arranque
300s, captura120s, observador600s. FIFO directo de DayZ MCP sin preconsulta de
ocupación ni prelease; adoptar únicamente el run propio, heartbeat, identidad
de PID/creación, observador y cierre oficial con liberación en finally.
Ausencia de cliente y cierre comprobados. Hasta dos rondas de corrección de
instrumentación antes de lanzar; un fallo nativo se conserva y replantea.

## Decisión posterior

- Si los getters de Baltic devuelven1 igual que Chernarus: no hay discrepancia
  en esa ruta script. Sin aviso nativo independiente, cerrar esta línea sin
  cambiar config; el consumidor interno del cargador sigue sin observarse.
- Si devuelven0 u otro valor con controles válidos: hay una discrepancia
  nativa de conversión, no una causa raíz de RAM demostrada. Antes de cambiar
  el producto, preparar y revisar un A/B aislado únicamente de
  filterIsolatedIslandsOnLoad sobre el mismo NM, con las607 consultas y RAM
  propio como oráculos; este plan no autoriza automáticamente esa modificación.
- Si la sonda es inconclusa: corregir la instrumentación o documentar el
  límite; no regenerar ni conceder PASS.

En cualquier caso permanecen: Nav8 altura607PASS/RAMFAIL, Nav12 tres alturas
FAIL sin RAM y original12,5 RAM PASS con cuatro alturas FAIL. No rebajar
0,801/0,011/2,1 ni RAM1,10; no derivar un PASS del ejemplo vanilla. El council
ampliado sigue en cola tras el cierre del trabajo vigente.
