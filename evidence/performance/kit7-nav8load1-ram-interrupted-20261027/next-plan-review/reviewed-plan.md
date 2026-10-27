# Kit7: diagnóstico antes de otro candidato de navegación

Estado: PLAN_REVISADO_SOUND_WITH_FIXES. Fable5.1 revisó; Codex integra las correcciones contrastadas. Codex ejecutor/integrador por el encargo vigente.
Continúa P7 y el pendiente de RAM. No inicia el council ampliado ni autoriza
otro valor de tileWidth, otra generación, edición del NM o cambio de tolerancias.

## Evidencia que cambia el siguiente paso

[EXACT] Nav8Load1 conserva las 607 consultas y nueve controles nativos PASS,
run f6f09de4-8fe7-4947-a695-c284dc042919. Cambia solo OnLoad a entero1; NM y WRP
permanecen. Evidencia: evidence/navigation/kit7-nav8load1-native-20261027.

[EXACT] El bloque RAM nuevo terminó INCONCLUSIVE_INTERRUPTED_RAM_BLOCK:
dos mediciones válidas, tercera rechazada antes de crear run por
port_in_use_foreign. El coordinador se detuvo; no ejecutó4-6 ni repitió pasadas.
El cierre de ambos runs y la ausencia final de lease/run propios están registrados.
Evidencia: evidence/performance/kit7-nav8load1-ram-interrupted-20261027.
Medianas descriptivas: Baltic4254,57/4649,21MiB residente/privada;
Chernarus3349,37/3733,76MiB. No hay veredicto agregado ni prueba causal del flag.
El candidato no se acepta y no se repite automáticamente el bloque incompleto.

[EXACT] Nav8 anterior pasa607 y falla su bloque completo RAM; Nav12 falla tres
alturas nuevas, sin ejecutar RAM. El original12,5 pasa RAM diagnóstico pero
conserva cuatro fallos de altura. Estos resultados permanecen separados.

[EXACT] inspect_navmesh_v9_ev112.py verifica cabeceras TESM9/VAND12, offsets,
coordenadas y longitudes; declara explícitamente que no decodifica polígonos.
El censo evidence/navigation/kit7-nav12-rejected-20261027/diagnostics/kit7-nav-detail-census-20261027.json observa ceros en los tres
contadores empíricos9:12 de todas las teselas8/12. No demuestra ausencia de toda
estructura de detalle ni el algoritmo de alturas. El censo de payload anterior
no encontró teselas de cero polígonos; eliminar teselas supuestamente vacías
no es una corrección justificada.

[EXACT] Ya existe reconstrucción empírica local: scripts/reconstruct_kit7_nav12_height.py
y diagnostics/kit7-nav12-height-reconstruction-20261027.json bajo
evidence/navigation/kit7-nav12-rejected-20261027. Seis waypoints Nav12 coinciden
con el abanico de sus polígonos, residuo máximo5,6416e-7m. Reutilizar esa
implementación y sus datos; no convertir seis coincidencias en formato general.
También diagnose_kit7_grid_vertices.py y su JSON comparan cinco XY con terreno,
LOD empaquetados y superficies empíricas8/12. Esa implementación observó8m de
forma local; faltan controles del layout para una generalización.

La propuesta del revisor de vértices siempre por debajo del terreno no se toma
como hecho: en(9132,11280), terreno1,000389m y Nav12=2,069922m; el LOD físico
empaquetado da1,908336m y Roadway1,910142m. Además road_y es la consulta de
superficie con Roadway del kit fluvial, no demuestra una carretera del mapa.
Separar terreno, lecho, lámina visual y LOD físicos antes de comparar alturas.

## Pregunta y descubrimiento acotado

[HIPÓTESIS] La simplificación o representación local de los polígonos puede
explicar por qué cambia la fidelidad de altura al cambiar la rejilla. La cuenta
de teselas puede contribuir al coste de memoria; no es un perfil de heap.
No extrapolar RAM lineal ni dar por aislada ninguna de estas causas.

[DESIGN] Trabajo exclusivamente de lectura, sin DayZ ni generación:

1. Localizar definiciones o referencias primarias del payload real y parámetros
   del generador instalados. Registrar qué es definición verificada, observación
   binaria o semejanza con otro formato. La versión upstream de una biblioteca
   no demuestra compatibilidad con VAND12. No inventar campos/firma/offsets.
2. Inventariar los testigos nativos de los fallos originales y de Nav12, las
   teselas que los contienen y los controles Nav8 PASS correspondientes, con
   hashes de NM, log, referencia y terreno. Mantener todos los testigos,
   incluidos aquellos que contradigan una explicación simple.
3. Discriminador: para los vértices reales de las teselas testigo, comparar
   Y con cada superficie física pertinente en su misma XY (terreno y LOD del
   kit), separando lámina visual. Contrastar si el desvío ya existe en los
   vértices o aparece al interpolar entre ellos. Empezar por los cinco XY y seis
   waypoints archivados; identificar qué XY es realmente vértice de cada malla
   y cuál es solo una interpolación. Conservar controles que contradigan la
   hipótesis de vértices bajos. No comparar road_y de otra XY como si coincidiera.
   Si hace falta ampliar: reutilizar el layout empírico104bytes/32bytes del
   script existente SOLO después de revisar límites de cada tile, longitudes,
   índices y coordenadas, con fixtures positivos y corrupciones. Aplicar ese
   layout a8m,12,5m o a todas las teselas sin esas pruebas queda prohibido.
   El diagnóstico local no demuestra selección/simplificación del generador;
   ampliar posteriormente a todos los waypoints disponibles exige su propio
   gate de formato y cobertura, sin elegir únicamente los ejemplos favorables.
4. Si no se verifica el formato o la predicción falla, dejar INCONCLUSIVE con
   el discriminador mínimo que falta. Un informe puede descartar una hipótesis;
   no tiene que fabricar una solución. Elegir después un único experimento
   reversible y revisable basado en esa evidencia, si existe.

## Presupuesto y criterios

Una ronda de descubrimiento de hasta30min de ejecución local, sin ocupar el
banco y sin generar variantes. Como máximo dos hipótesis contrastables;
conservar resultados negativos. Antes de implementar un decodificador, revisar
sus anclas, formato admitido y pruebas; si falta una definición necesaria,
limitarse al inventario y no completar el formato por conjetura.

Entregable: informe de fuentes, testigos y contradicciones, con estado
SUPPORTED_NEXT_EXPERIMENT o INCONCLUSIVE_NO_VERIFIED_MECHANISM. El primero
requiere un plan nuevo revisado antes de editar/generar/probar un candidato.
Ningún estado de este diagnóstico concede PASS de altura/RAM/global.

0,801m, 0,011m, 2,1m, RAM1,10 y dispersión5% permanecen. Un futuro bloque RAM
debe definir presupuesto y datos nuevos completos; no completar ni reutilizar
el bloque interrumpido. Mantener FIFO directo, sin sondeo previo ni prelease;
no elegir otro puerto para eludir una sesión ajena. No modificar DayZ MCP como
parte de este diagnóstico. No desactivar el seguimiento del proyecto.
