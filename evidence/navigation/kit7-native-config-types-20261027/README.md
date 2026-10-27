# Lectura nativa de los flags de navegación

**Diferencia confirmada en getters script; causa del consumo RAM todavía sin
probar.** Run2e1e9c77-222e-438c-955e-55b2f0ec0371, Nav8 intacto, nueve campos
capturados con identidad/UUID y controles válidos. Sin cambio de PBO, NM,
terreno, geometría ni tolerancias. No es un benchmark ni una repetición607.

|Campo|Baltic|Chernarus|
|---|---|---|
|filterIsolatedIslandsOnLoad|texto"true", int/float0|número1, int/float1|
|GenParams.filterIsolatedIslands|texto"true", int/float0|número1, int/float1|
|tileWidth|8|50|

Los textos"12:00" y"Chernarus" se recuperan correctamente y ambos dan0 por
getters numéricos; el campo inventado no existe. No se supone la semántica
nativa del cargador ni conversión por prefijo. El lector pasa15controles
positivos/negativos; misión1archivoPASS; lifecycle13casos+2mutantes y8controles
de finalización de comandoPASS. Revisión independiente Fable5.1 integrada.

RPT completo184líneas conservado en el build privado: cero coincidencias del
patrón de conversión/Navmesh. Script log44líneas vinculado por UUID: cuatro
avisos de zonas ausentes antes de los marcadores, ninguno entreBEGIN/END.
Se publican resúmenes con hashes/índices, sin los logs completos. Ausencia de
coincidencias no demuestra ausencia universal de avisos ni filtrado correcto.

El único run se cerró oficialmente, observador registró salida-1 después de
CLOSE_INTENT, válida bajo el contrato revisado; lease liberado, sin run propio
ni comandos pendientes.118paquetesvanilla y4PBOde mods ligados antes/después.

Siguiente plan revisado: variante experimental que cambia únicamente OnLoad
a número1 sobre el mismo NM. Exige otra prueba607 y RAMNUEVAcontraChernarus;
no cambia GenParams ni regenera. Su cobertura seguirá siendo local hasta
ampliar testigos. El plan y la revisión explican esa limitación.

Nav8 mantiene607PASS y RAMFAIL1,265913/1,241333. No se ha obtenido aún una
variante que cierre ambos gates. Council ampliado sigue en cola detrás del
trabajo vigente. Esta evidencia se publica sin declarar cierre de EV112.
