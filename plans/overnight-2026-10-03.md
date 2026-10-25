# Sesión de ocho horas: base de terreno y navegación

Autorización de Guillermo del 03-10-2026: trabajar de forma autónoma al menos
ocho horas, PC disponible, hacer bloques completos y revisarlos después.
Ventana de trabajo 04:52–12:52 Europe/Madrid (02:52–10:52 UTC).
Base Git c93e77f; geometría candidata a84dfff0 y paquete 916948ec.

## Trabajo previsto

1. **Preparar el editable.** Apertura limpia de TB y de la copia aislada
   delta_v30_native. Diferir la importación hasta acabar la geometría y su
   superficie, para hacer un único ciclo completo. No repetir el importador
   WRP 0WZD que ya rechazó el formato.
2. **Acabar orillas y agua.** Trabajar sobre una copia regional del candidato:
   transiciones en orillas, bajos secos y contornos; preservar cauces útiles,
   plataformas, islas, costa, Narva protegido y reserva. Aprovechar el inventario
   existente para localizar sectores. No rellenar un canal para bajar una
   estadística ni sustituir la geometría por el piloto Narva rechazado.
3. **Integrar la base final.** Regenerar las fuentes de superficie solo si la
   geometría lo requiere; importar el conjunto final, guardar/reabrir/exportar,
   empaquetar en variante nueva. No sobrescribir canónico ni fuentes originales.
4. **Generar navegación y probar el resultado.** NM ligada al WRP final;
   comprobar carga, puntos de agua/costa, vistas y un consumidor representativo
   de navegación. Agrupar pruebas sobre el mismo despliegue. No repetir las
   anteriores sin cambio o una pregunta nueva que lo justifique.

La revisión cruzada inicial de Opus es consultiva y acotada al orden/prioridades;
no bloquea preparar el trabajo. Codex ejecuta e integra. Sin edificios,
vegetación colocada ni ferrocarril P15. Rendimiento 80–100 sigue pospuesto a un
sector mapeado. FTT se usa solo si aporta directamente a esta base; su catálogo
y recta exportada ya se probaron, no repetirlos por rutina.

Consulta realizada a claude-opus-5-5, solo lectura; respuesta conservada en
`E:/DayZ-Baltic-Build/overnight-2026-10-03-opus.json`. Adoptados: geometría y
superficie antes del ciclo final TB/NM; fijar vértices de triángulos de los
canales, plataformas y cruces; corregir bancos secos primero y elevar fondo
solo fuera del canal y de forma acotada. El recuento de caras >35° localiza
problemas, no sustituye la inspección visual ni exige eliminar cada cara.

## Control de avance

Cada bloque acaba con un artefacto utilizable, un resultado corto y la validación
que le corresponde. En UI: un intento observado y una recuperación distinta;
si no avanza, liberar control y continuar el trabajo independiente. No pasar
la noche repitiendo botones. Nunca tocar procesos/lease de otra sesión.

Antes de introducir un algoritmo nuevo, leer su productor real y congelar el
ámbito; construir la corrección completa y pasar después una tanda de gates.
Fallo físico bloquea promoción. Una pausa temporal de Luga ya estudiada no
justifica repetir el mismo ensayo ni rebajar su umbral.

Al terminar: candidato reconstruible, export y NM identificados si se lograron;
pendientes concretos si no. No llamar versión 1.0 a una base sin consumidor.
Sin auditoría global del vault ni informes duplicados durante los bloques.

Continuación automática: heartbeat existente baltic-sesi-n-de-8-horas, activado
hasta 10:52 UTC. La orden humana de pausar/cambiar tiene prioridad. A las 12:52
cerrar de forma segura la operación propia y presentar resultados para revisión.

## Punto de avance 05:34 Madrid

Relieve nuevo en `E:/DayZ-Baltic-Build/v30-shore-finish-tidal`: NPZ f27aacd3,
50.072 vértices ajustados en orillas, 23 corredores navegables y reserva sin
cambios. Gates de profundidad, bancos, suelo y carreteras conservados; cero
nuevas exposiciones marinas a la cota baja 0,5 m. Revisión offline en
`review/review.json`; todavía sin prueba visual del motor ni NM propia.
Superficie completa y 2.048 PAA preparados; fuentes nativas 12.288² exactas en
`editor-v30-delta/world/native_sources_shorefinish_v2` (la carpeta sin `_v2`
es un intento parcial y no se usa). Save As nativo completado como
`native-asc/base_v30_shorefinish.tv4p`; importación ASC en curso.

## Punto de avance 06:08 Madrid

Paquete aislado `E:/DayZ-Baltic-Build/v30-shore-finish-package`: mundo
`b8179287` y agua `e9b52b8c`, compilación y 6.827 entradas del PBO comprobadas.
No desplegado; contiene todavía navegación V29 provisional, por sustituir.
Biblioteca/CSV nuevos en `editor-v30-delta/water-import-v30`: 13.419 plantillas
con nombres `v30_` distintos y 17.622 instancias; recepción nativa pendiente.
El Save As del editor acabó y la copia está abierta (TB388492), todavía V29.

Bloqueo de herramienta desde 05:43: `node_repl.js` devuelve «failed to write
kernel assets / os error 3» antes de ejecutar cualquier código. Reset no lo
resuelve. C:/TEMP y runtime existen. No hay prueba de causa. Diagnóstico breve
con Procmon no llegó a registrar; se cerraron sus dos procesos propios, sin
tocar procesos de otras tareas. Se solicitó reinicio de Codex cuando el usuario
esté disponible. DayZ sigue ocupado por @LFRider/@LFH2R, sin lease propio.
Continuar fuentes/importación y consumidores preparados; no marcar base completa.

## Punto de avance: corrección integrada tras la revisión de Opus

Candidato vigente de esta sesión: `v30-shore-finish-corrected`, NPZ `73b01bb4`
y ASC `fe5dac8a`. Sustituye al f27 para la siguiente integración, sin borrar sus
artefactos. Conserva 49.717 vértices retocados y los23corredores; recupera márgenes
de5cm/3cm junto a piezas y cancela las ediciones que empeoraban caras pronunciadas.
Terreno, carreteras y revisión agrupada PASS:4.149→4.000caras mixtas >35°, cero
caras nuevas o empeoradas sobre ese umbral. No es aceptación visual del motor.
Opus confirmó dos fallos geométricos, corregidos; su opinión completa y adjudicación
quedan en `overnight-2026-10-03-opus-code-review.json` y
`v30-shore-finish-corrected/opus-resolution.json` dentro de E:/DayZ-Baltic-Build.

Se corrigió además la precisión de `cell_planes` en los consumidores:467celdas
con cotas float32 alrededor de0,8m se omitían respecto al productor float64.
Las piezas existentes no cambian. La sondaV2 conserva los vértices como controles
de altura y usa interiores para agua; un estanque bajo oculto por el mar sin
identificación suficiente quedará INCONCLUSO. Once negativos y un caso inconcluso
del verificador pasan; no son prueba de ejecución en DayZ.

Superficie reconstruida completa; fuentes nativas listas en
`editor-v30-delta/world/native_sources_shorecorrected`. Empaquetado del mundo
corregido en `v30-shore-corrected-package` en curso. No desplegado.

Nueva ruta descubierta: el NavMeshGenerator instalado ofrece `--console` y
`save_path`; ayuda y rechazo por ruta ausente observados. Wrapper preparado en
`tools/navigation/generate_navmesh_console.py`, sin `--kill`. Todavía no se ha
generado NM con esa CLI. Evidencia en `evidence/navmesh-cli-2026-10-03`.

Computer Use: el backend de esta tarea pasó de «failed to write kernel assets»
a «Transport closed» tras cerrar únicamente su node_repl.exe identificado por
el log de arranque, exe/parent/fecha. No se reconectó automáticamente. No insistir
ni tocar otros backends; sigue pendiente el reinicio de Codex solicitado al usuario.
TB388492 sigue conservando la copia V29; sin importación nueva. DayZ continúa
ocupado por el cliente/servidor ajenos @LFRider/@LFH2R, sin run gestionado que
podamos cerrar. La CLI nueva no permite saltarse ese bloqueo de propiedad.

## Ajuste local tras comparar con el diseño aprobado

La comparación independiente contra `water_v3.geojson` encuentra tres lagunas
totalmente ausentes (índices 98, 376, 409) y una casi ausente (408). La causa está
en `build_v30_water.py:164-172`: el radio de 600 m sustituye toda el agua por V29,
anulando incluso lagunas alejadas del puente. Ya ocurría en a84; el acabado de
orillas no lo introdujo. Evidencia: `v30-shore-finish-corrected/design-coverage`.

Se prepara una corrección aislada de esos cuatro polígonos del diseño ya aprobado.
La protección amplia de Narva se conserva salvo sus huellas exactas, con los
vértices del canal útil y margen, plataformas viales, reservas de cruce y naturaleza
todavía fijos. No cambia el recorte ni se diseñan lagunas nuevas. Solo se promueve
si recupera presencia de agua, no introduce agua fuera de las piezas previstas,
mantiene las carreteras y no crea/empeora caras >35 grados. Si el pequeño cuerpo
no cabe sin romper esas invariantes, se conserva el candidato 73b y se deja el
conflicto concreto para revisión, sin ocultarlo como PASS de las 387 lagunas.

## Continuidad de ríos menores y arroyos

El consumidor independiente sobre ejes aprobados encuentra 381 m de río y
12.045,5 m de arroyo secos fuera de las plataformas/reservas viales. Muestrea
cada 0,5 m a marea baja; no equivale a una observación del motor. No faltan piezas
en los peores cortes: la interpolación de caras con esquinas secas cruza el plano
de agua. La prueba de vértices de la fase 2 no cubría ese consumidor.

Corrección propuesta: rebajar de forma local las caras de una franja central
de 1 m, recortada al polígono aprobado, hasta 5 cm bajo el plano menor. Agua,
clases, niveles y piezas conservados. Fondos secundarios hasta 1,2 m bajo el
plano menor, corte máximo 3 m; tierra >=1,4 m y margen >=5 cm sobre todas las
piezas adyacentes. Carreteras, reservas de cruce, Narva, otros cuerpos de agua y
los 23 canales útiles siguen fijos. La naturaleza conserva todo su suelo seco;
solo se permite corregir fondos ya clasificados como río/arroyo dentro de ella.
Es una excepción explícita a congelar toda su altura, sin variar su contorno ni
su clase de suelo/bioma. No se excavan carreteras ni se colocan puentes.

Presupuesto: una proyección monótona acotada (máximo 128 iteraciones), recuperación
de caras pronunciadas por restauración, y una comprobación agrupada. Restricciones
inviables se enumeran; no se amplían cotas para esconderlas. No se promueve si hay
caras >35 grados nuevas/empeoradas, agua nueva fuera de la máscara o pérdida de
cobertura vial. Quedan separados la continuidad geométrica y el aspecto del motor.

## Integración de continuidad y corrección local conjunta

El candidato `v30-watercourse-continuity`, NPZ `40d8cfd9`, queda empaquetado en
`v30-continuity-package`: mundo `572d4124`, agua `371ece8a`. Las cuatro lagunas
recuperadas y las 22.468 alturas corregidas pasan las invariantes locales y las
mismas 76.513 estaciones viales; el FAIL legado de Narva se conserva explícito
por la excepción de las cuatro lagunas. Fuentes del editor, biblioteca de agua
y misiones V3 preparados, todavía sin ejecución ni importación nativa.

La revisión de Opus ha hecho más preciso el diagnóstico: se mide también la
profundidad de 5 cm, dos líneas a +/-0,5 m y el halo de las reservas de cruce.
Los ejes son autoconsistencia del diseño, no un consumidor independiente. En el
eje quedan 30 m secos de río y 399,5 m de arroyo fuera del halo; hay otros tramos
secos en las plataformas y el halo, reportados aparte. Para 5 cm, son 42 y 511 m.
Los bordes de esa franja también conservan interrupciones; no es aceptación total.

Siguiente intento acotado: diez cortes cuyo punto central sería viable con las
cotas originales, pero que reaparecieron tras restaurar caras pronunciadas.
Se mantiene `40d8` intacto. Un optimizador local ajustará conjuntamente profundidad
y norma de pendiente, permitiendo solo rebajar dentro del mismo soporte aprobado
(máximo una diagonal de celda desde el polígono). Carreteras, naturaleza seca,
canales principales y borde siguen fijos, y no cambian clases, niveles ni piezas.
No se amplían las cotas originales de fondo, altura mínima ni corte máximo.

Presupuesto: una resolución por grupo espacial, máximo 10 grupos, 500 vértices
variables, 300 iteraciones y 120 s por grupo. Los grupos inviables se conservan
sin cambio y se explican. Solo se incorporan soluciones con restricciones
cumplidas después de convertir a float32; al final una tanda agrupada de terreno,
carreteras y continuidad. Sin relajación de criterios ni repetir el mismo solver.

Resultado del intento: los diez puntos formaron nueve grupos. Ningún grupo dio
una solución que cumpla todas las restricciones; se conservaron todos sin cambio.
`v30-continuity-slopes/build.json` registra el resultado, no es una nueva versión.
No se afirma inviabilidad matemática solo porque SLSQP no encontrara solución.
El candidato vigente sigue siendo `40d8`, sin relajar las restricciones.

Cobertura vial final ampliada a la referencia histórica: **76.536 estaciones**,
100 cadenas, cero fallos. Las 76.513 de las comprobaciones intermedias usaban
el agua de a84/73b como exclusión; la máscara de V30 original añade 23 estaciones
junto al delta. Todas siguen pasando. Fuente y candidato quedan fijados por hash
en `road-gates-historical.json`; no usar la cifra menor para la aceptación final.

## Reutilización exacta de modelos de agua

El manifiesto de agua contiene 13.434 modelos, pero solo 8.775 hashes MLOD
distintos. Se prepara una deduplicación por igualdad completa de bytes, con
comparación también de las copias ODOL compiladas. No se cambia la forma, la
altura, el material ni el número/orden de las 17.637 instancias: solo el nombre
del recurso al que apuntan los duplicados. El terreno `40d8` queda intacto.

Se genera una copia nueva del agua y del mundo, conservando el paquete `572d`.
Rechazo si una pareja no coincide también en bytes compilados, si cambia alguna
pose/altura/puente/material o si faltan recursos al empaquetar. Comprobar una vez
el bloque completo. Es una reducción de recursos y de biblioteca del editor;
no afirmar FPS, RAM o tiempos de carga mejores sin medición del motor.

Resultado:8.775 modelos y17.637 instancias;4.659 referencias sustituidas por
recursos idénticos MLOD/ODOL. PBO34.254.192→24.715.347bytes. Mundoe556f576,
agua339fa17f, WRPcompilado0255d007; solo cambió la entrada WRP del PBO de mundo,
las otras6.826 entradas son idénticas. Puentes, IDs, poses, alturas y materiales
sin cambio. Copiado en @DayZ_Baltic_ContinuityV30 bajo lease breve ya liberado.
Biblioteca nativa y misionesV4 preparadas; ninguna importación/ejecución todavía.
El arranque06:10UTC fue rechazado por procesos DayZ ajenos, sin run ni cola.

Guía de la siguiente operación agrupada:
[continuación nativa y motor](v30-continuity-native-runtime-resume.md).

## Consumidor de navegación del candidato actual

Preparar una sola misión derivada de la consulta nativa V30 ya ejecutada:
conservar sus13casos (incluidos puente, filtro NONE y separación isla/continente),
reajustando solo Y al terreno40d8, y añadir hasta24trayectos locales en bancos
secos modificados. Selección geométrica antes de recibir ningún resultado del
motor, con separación espacial y recorrido seco. Trazabilidad a P10/P14.
No cambiar terreno ni parámetros de generación para satisfacer el consumidor.

Reutilizar firmas verificadas `P:/scripts/3_game/AI/aiworld.c:65,98,122` y el
lector existente para completitud/controles; añadir identidad de misión y la
distancia vertical de los waypoints a la superficie física registrada. Conservar
0,8m como umbral de diagnóstico local ya usado por el consumidor nativo, sin
afirmar que sea la precisión universal del generador. Una tanda de controles
del lector y linter; ejecución real después de generar/empaquetar la NM exacta.
