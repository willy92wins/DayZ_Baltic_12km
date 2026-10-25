# Checkpoint 09-10, 03:12 UTC

La unidad física está guardada en `5d73fb0`. La preview actual sigue siendo HaloFixV3: mundo `b30ca647`, agua `4ac3cb01`, terreno `e7daa6c6`. La base 1.0 no está aceptada.

## Diagnóstico gráfico

Referencia de materiales: run `6978a917-f2e4-49b4-b29b-53fa98cfcced`, texturas cargadas, cámara R1 exacta. No hubo una reproducción estable y clara del residual calibrado. Cierre orderly y lease liberado. El log confirma `#water`, `#shore`, `#shoreFoam`, `#shoreWet`.

Marcador R1: run `4b7927c5-e0dd-4fe8-8a83-42b7479bafda`. El cliente cargó las referencias de material nuevas y terminó con `C0000005 ACCESS_VIOLATION`. El servidor cerró por lifecycle; run retirado y lease liberado. El diagnóstico cambiaba erróneamente el shader de orilla a Terrain. Esa diferencia es una hipótesis del crash, no una causa aislada. No se obtuvo un control gráfico positivo ni una comparación válida. El añadido nunca entró en el paquete del mapa.

R2 está preparado en `@BalticShoreMarkerR2` conservando shaders, etapas y coordenadas de Shore/ShoreWet. Solo falta ejecutar la comparación controlada. No sustituye la referencia ni autoriza un cambio de material definitivo.

El siguiente arranque fue rechazado por `port_attribution_unknown`. Windows mantiene UDP 2316 con PID 138984, el cliente de diagnóstico ya terminado; no aparece proceso vivo ni WerFault asociado. `session_status` devuelve owner nulo, cola vacía, cero runs y banco ocupado por ese puerto. No se han detenido procesos ajenos ni el conector. Se ha pedido una reconexión para comprobar si libera la referencia; su resultado está pendiente.

Recibos y capturas: `shore-material-lifecycle.json`, `frames/shore-material-baseline`, `frames/shore-material-marker`; RPT del crash conservado. Los hashes de los dos PBO de HaloFixV3 siguen exactos.

## Inventario de juntas

`water-connections.json` revisa todas las aristas de las 404.457 celdas de estanque activas. Encuentra 12.215 aristas con agua en ambos lados y distinto plano, y 704 fronteras con niveles distintos pero separación de terreno seco. Siete contactos tienen salto superior a 35 cm; máximo 40 cm. No son 12.215 defectos visuales confirmados: los 538 modelos ya unidos siguen incluidos en la predicción de planos fuente.

El grafo grueso de celdas tiene 731 grupos y no se usa como prueba hidráulica: una celda puede contener dos triángulos mojados desconectados. El consumidor triangular independiente encuentra 842 componentes, 830 de al menos 1 m², e incluye un negativo de dos esquinas mojadas opuestas.

El campo visual conectado candidato evita nuevas conexiones entre las 704 separaciones, pero seis esquinas superarían el desplazamiento previsto de 35 cm, máximo 57,01 cm. Estado `FAIL_FIELD_NOT_FOR_AUTHORING`; no se han cambiado modelos. Cuatro esquinas están enterradas y dos están en el mismo arroyo estrecho: antes de otra propuesta hay que resolver ese dominio y medir las partes realmente visibles, no suavizar cuerpos distintos ni mover el umbral para obtener PASS.

La medición posterior del dominio visible está en `visible-field-domain/report.json`, con todas las coordenadas en `faces.csv.gz`. Examina las 4.190.209 celdas y recorta exactamente los 33.592 triángulos que cambiarían. El problema no se limita a esquinas enterradas: desplazamiento máximo 38,9857 cm sobre agua ya visible y 57,0100 cm sobre la superficie propuesta; 0,1693 y 3,7757 m² respectivamente superan 35 cm. Respecto a los planos fuente, aparecerían 1.660,0567 m² y desaparecerían 1.667,0927 m² de superficie proyectada, incluidas caras mixtas de orilla. No son daños aplicados ni una medida del shader. Cinco controles analíticos pasan, incluidos inundación nueva de 6,48 m² y pérdida de 4,5 m². Se mantiene el rechazo del campo: no autorizarlo excluyendo esquinas ocultas.

## Otros pendientes

Los once archivos de las correcciones históricas 002/003/004/006 se han vuelto a contrastar con sus hashes y siguen exactos; esto no renueva la aceptación de la IA sobre una geometría posterior. Estado completo por ID en `bug-status-current.md`.

El piloto de finales de Msta y su corrección R2 se rechazan por empeorar los giros del contorno nativo. Resultados y deltas en `../v30-river-end-tapers-2026-10-09`. No se empaquetan ni se extienden a Grib/Volkhov. Siguen pendientes forma global, juntas visuales, residual, teselas, finales, grandes lagos, TB y navmesh.
