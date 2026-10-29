# RoadC1A1 — recuperar las referencias PNG omitidas

Estado: BORRADOR_PENDIENTE_DE_REVISION. 29-10-2026.

La investigación C1A conservó4776filas de material (una vacía) y leyó4775RVMAT
propios por27.766.367bytes totales en17.688s/42.47MB. Su índice de18rutas NO es
completo: el filtro de sufijos omitió `.png`. Contraejemplo pinado del primer
material, SHA78d24eba..., líneas9/14 Stage0/1: s_000_000_lco.png y m_000_000_lca.png.
No se corrige ni relanza C1A. Su reporte f3eb0ab1... permanece parcial; el rechazo
exploratorio previo del cap4096 también. C1A nunca autorizó build y sigue sin hacerlo.

## Corte único y motivación

P5/P6/P8/P11 requieren recursos reales antes de calibración. Hipótesis verificable:
el manifiesto guardado de4775RVMAT permite recuperar TODAS sus cadenas citadas sin
abrir de nuevo WRP, PBO, P3D, alturas, texturas o configs bin/core. Es necesario
releer esos textos propios por SHA porque C1A guardó hashes pero descartó las
cadenas no seleccionadas. No repetir el catálogo, el censo de objetos ni C0.

Codex executor local explícito240s; revisión externa única de este plan90s;
una ejecución60s/256MiB,<=16MiB textos leídos,<=4MiB salida,<=1MiB/texto,
4775archivos exactos desde reporte externo fijado,<=128strings/texto y32768strings
distintas. Sin retries/correcciones internas: fallo -> parcial/inconcluso, fuentes
intactas. No CLI productivo ni motor. La pequeña rutina es instrumentación de
investigación; autocontrol documental, no prueba de un parser RVMAT semántico.

## Contrato de lectura

1. Pinar reporteC1A completo y reconciliación antes de autoría. Su estado parcial
   no invalida los hashes de los textos que sí leyó. Leer sólo su lista4775materiales;
   no obtener nuevos inputs desde un árbol ni ejecutar funciones de C1A.
2. Cada path debe corresponder exactamente al namespace propio y raíz histórica,
   guardas reparse en cada ancestro antes de abrir. Tamaño<=1MiB y reserva total
   antes de lectura; SHA/tamaño/identidad path/handle/EOF final contra reciboC1A.
   Una diferencia SOURCE_CHANGED, no cambiar el pin ni volver a leer paraPASS.
3. Guardar TODAS las cadenas entre comillas y su línea/orden por material usando
   una tabla de strings; no filtrar por extensión. Sin escapes inventados: si hay
   una comilla escapada o línea con comillas sin cerrar, UNKNOWN_QUOTE_GRAMMAR.
   Es recorrido léxico limitado, no cierre transitivo/material renderer validado.
4. Cadenas con slash/backslash y sin prefijo procedural `#(` se tratan como rutas
   candidatas; permitir sólo namespaces dayz_baltic_12km_dev y dz, reglasC1A.
   Traversal/drive/noASCII/control se rechazan. Otras cadenas quedan explícitamente
   LITERAL_NOT_RESOLVED, no se concluye que no sean dependencias. No fallbackbasename.
5. Sólo localizar por lstat: las rutas PNG/PAA/RVMAT se conservan literales, jamás
   sustituir PNG por PAA aunque exista al lado. Guardar raw/normalizado/path/tamaño,
   LOCATED_NOT_READ/BLOCKED_REPARSE/MISSING/UNRESOLVED_NAMESPACE. Recurso localizado
   no equivale a formato aceptado ni identidad instalada; ningún payload abierto.
6. Snapshot de tabla de strings y usos completo<=4MiB; fsync por fase. Conciliar
   posteriormente la cantidad de usos con la lista guardada, los4775hashes y las
   dos líneas literales del contraejemplo. SHA no demuestra gramática completa;
   no afirmar auditoría semántica independiente. No cerrar includes/bin/core.

Oráculo literal antes de rutina: dos líneas con `a.png` y `b.paa`, ruta `.xyz`
que antes habría sido omitida, `#(rgb,1,1,1)color(0,0,0,1)` y `worldPos`; cinco
cadenas exactas preservadas en orden. El mutante de filtro por sufijos debe fallar
esa igualdad. Comilla sin terminar => UNKNOWN_QUOTE_GRAMMAR. Éstas son comprobaciones
del extractor de cadenas, no tests geométricos ni suite de una librería promovida.

## Término y siguiente decisión

`RECOVERED_QUOTED_MATERIAL_REFERENCES_ONLY` sólo si4775textos pinados completos y
oráculos/reconciliación correctos. Siempre `build_ready=false`,
`dependency_closure=NOT_EVALUATED`, `compiled_terrain_decoder=NOT_VERIFIED`.
C1B de stage/config/compilador necesita contrato y revisión propia: fuente0/3 no
prueba aceptación del control vacío ni terreno/materiales compilados. Si falta
lectorOPRW capaz, cualquier compilación sólo podrá ser una sonda explícitamente
revisada, no preparación de paquete aceptado. No tocarP:, mapa, puentes ni tolerancias.
Nueve humanos0resueltos,C1NOT_REVIEWED; Q03C/Q05/ángulos/referentes siguen abiertos.
