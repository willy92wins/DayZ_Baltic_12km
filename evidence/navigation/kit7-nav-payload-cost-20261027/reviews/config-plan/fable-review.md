**Veredicto: SOUND-with-fixes.** La sonda es barata, read-only y está dentro del encargo, pero tal como está escrita aporta poco más que el config decodificado. Con los arreglos de abajo sí puede rendir un dato nativo real.

**Anclas verificadas**
- `package-kit7-nav8-input-20261027/config.cpp:60,68` cadenas `"true"`; `chernarus-current-config-20261027/config.cpp:48,56` número 1. Correcto.
- `P:/scripts/3_game/global/game.c:449,539,546,612` firmas exactas como cita el plan. `ConfigGetFloat` en `:524` no está en el plan.
- Censo: `result.json:14,906,2111,3347` zero_polygon_tiles=0 en los cuatro NM; cifras Nav8 (2359296/1996338/897066212/1338007300) coinciden con `result.json:5-17`. `controls.json` 9 tests, 0 fallos.
- No pude recalcular los SHA256 de source-hashes.json (sin shell). Lo que afirmo se apoya en el contenido leído.

**Qué distingue y qué no la sonda (mecanismos reales)**
1. `ConfigGetType` devolverá CT_STRING para Baltic y CT_INT para Chernarus. Eso ya lo sabemos por las comillas en el config decodificado. Esta fila no aporta información nueva, solo confirma que el rasterizador conservó el tipo.
2. `ConfigGetInt` sobre la cadena mide una sola ruta de conversión: el puente script del motor. El cargador de navmesh es C++ y lee el ParamEntry directamente; no hay fuente en `P:/scripts` que lo use (grep de `filterIsolatedIslands|GenParams|tileWidth` en scripts: cero resultados). El resultado no es transferible al cargador y el plan ya lo dice en la línea 24-27. Mantenerlo.
3. Solo `filterIsolatedIslandsOnLoad` (filas 1 y 3) es relevante en runtime. `GenParams.filterIsolatedIslands` (filas 2 y 4) es parámetro de generación; el NM de Nav8 ya está generado, así que su representación no puede alterar la RAM de carga. El plan debe decirlo para que nadie lea las filas 2/4 como pista de RAM.

**Fixes obligatorios**
- **Sintaxis de ruta.** El plan escribe `BalticTrial/Navmesh/...` con barras. La API usa clases separadas por espacio y raíz explícita: `"CfgWorlds BalticTrial Navmesh filterIsolatedIslandsOnLoad"` (ver uso vanilla en `5_mission/gui/mapmenu.c:92` y `3_game/constants.c:232`). Con barras, las seis filas darían inexistente y la sonda sería INCONCLUSO en la primera ronda. Añadir una fila de cabecera con `GetWorldName()` y exigir que sea `BalticTrial`.
- **Captura del RPT completo del servidor desde el arranque**, no solo alrededor de las llamadas script. Este es el único canal donde el cargador nativo puede hablar: si el motor convierte una cadena a número en carga de mundo, el patrón RV emite avisos de tipo "not a value"/"bad conversion" con el nombre del parámetro. Grep literal por `filterIsolatedIslands`, `Navmesh` y `navmesh.nm` en ventana de carga. Ausencia de aviso no prueba nada; presencia es evidencia nativa independiente del getter script. Sin este punto, la sonda es solo config decodificado más un dato de conversión script.
- **Controles de conversión de cadena** que ya existen en los configs, sin tocar PBO: `CfgWorlds BalticTrial startTime` (`"12:00"`, nav8 config:41) y `CfgWorlds ChernarusPlus description` (`"Chernarus"`, config:42). Si `ConfigGetInt` da 12 y 0 respectivamente, la conversión es prefijo numérico; si da 0 y 0, cadena no numérica es 0. Esto permite interpretar el valor de `"true"` sin adivinar. Añadir `ConfigGetFloat` a las mismas filas: segunda ruta de conversión, coste nulo.
- **Control negativo**: la fila 7 debe ir también bajo `CfgWorlds` con el UUID como último token, para que la negación pruebe la misma raíz que las positivas.

**Controles y alcance**
- Si `ConfigIsExisting` de `CfgWorlds ChernarusPlus` es falso en el servidor Baltic, las filas 3,4,6 son INCONCLUSO, no FAIL; el plan ya lo cubre en líneas 60-61, pero conviene que el consumidor distinga "control ausente" de "control inválido".
- Presupuestos y FIFO del MCP (líneas 72-77) son adecuados para una corrida sin generación. No necesitan autorización adicional.
- La sonda no toca los 607 ni la RAM; el plan lo declara en 61-62. Correcto.

**Decisión posterior: ajustar redacción**
- Línea 81: "queda refutada" es demasiado fuerte. Un retorno 1 refuta la discrepancia en la ruta script; el cargador nativo sigue sin observar. Redactar: "sin evidencia de discrepancia en la ruta script ni avisos nativos en RPT; cerrar esta línea".
- Línea 83-86: correcta. Añadir que el A/B de una sola propiedad solo tendría sentido sobre `filterIsolatedIslandsOnLoad`, con RAM 1,10 como oráculo y el mismo NM por hash. Nav8 ya es NM/geom 607 PASS con RAM FAIL, así que un cambio de representación que no mueva RAM no cambia el veredicto.
- Sobre la heurística de esquinas de mi revisión anterior: coincido con Codex en no adoptarla ahora. Con Ptotal 1255/1257/1248 en 8/12/12,5 y rutas de 3 a 16 waypoints, un fallo heurístico no cierra el eje de anchos sin oráculo independiente. Queda en cola, no bloquea esta sonda.

**Respuesta a la pregunta**
Merece lanzarse solo si se añaden la sintaxis correcta, la captura del RPT y los controles de cadena. Sin eso, el resultado es equivalente a leer el config decodificado y no justifica una corrida de servidor. Con eso, una corrida puede cerrar la línea "representación string" o producir un aviso nativo citable.

FIN_REVISION