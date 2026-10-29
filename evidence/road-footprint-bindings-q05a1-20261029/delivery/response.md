# Informe de consolidación — evidencia vial guardada

## Estado

**SAVED_BINDINGS_PARTIAL_RECONCILED**

`measurement_ready=false` · `placement_ready=false` · `human_resolved=0` · `C1=NOT_REVIEWED`

RECONCILED significa aquí **autocontrol documental de copias guardadas**, no verificación independiente. No se ha leído de nuevo ninguna fuente original, no se ha abierto ningún NPZ, no se ha ejecutado censo ni cálculo geométrico nuevo y no existe en esta entrega un consumidor geométrico independiente.

Las fuentes 4 y 7 se ligaron a pins previos y al `frozen-partial.json` fijado externamente. Esta redacción no afirma lectura propia de los originales. Sólo se contrastan hashes y recibos del snapshot guardado y los `sha_recomputed` previos, sin fijar hashes nuevos para un PASS.

## Antecedente Q05A

Q05A original **no entregó informe completo dentro de 120 s**; no se reinterpreta como PASS ni como timeout de un hijo matado.

Registro guardado: 20 fuentes / 8.247.835 B; último lote completo a 56,509 s; la llamada siguiente falló en la comprobación de deadline **antes** de abrir otras fuentes o escribir el informe; observación posterior en `stop.json` a 180,834 s. No se atribuye causa de latencia. La unidad Q05A está consumida y no se reabre.

## Tabla de los 13 selectores guardados

`global_edge_index=UNKNOWN` en los 13. `station_m` y `length_m` son valores guardados, no mediciones nuevas ni reconciliadas geométricamente aquí. Vecinos = conectividad guardada, no accesos físicos.

| chain | ordinal | flattened | nodes | vecinos prev → next | instanceIDs | modelIDs | roles guardados | station_m / length_m guardados |
|---:|---:|---:|---|---|---|---|---|
| 49 | 301 | 12365 | 12371,12372 | 12370,12371 → 12372,12373 | — | — | — sin observación seleccionada | 882.5100844786467 / 2.9295896457874866 |
| 71 | 370 | 19823 | 19817,19818 | 19816,19817 → 19818,19819 | 16777218,16818274 | 912,938 | bridge, model_water, water_roadway | 1109.9521746513535 / 2.857013476795636 |
| 71 | 371 | 19824 | 19818,19819 | 19817,19818 → 19819,19820 | 16777218,16818274 | 912,938 | bridge, model_water, water_roadway | 1112.8091881281491 / 2.8667281773828965 |
| 71 | 372 | 19825 | 19819,19820 | 19818,19819 → 19820,19821 | 16777218,16787374,16818274 | 912,938 | bridge, model_water, water_roadway | 1115.675916305532 / 2.8805354407088357 |
| 71 | 373 | 19826 | 19820,19821 | 19819,19820 → 19821,19822 | 16787374,16818274 | 912,938 | bridge, model_water, water_roadway | 1118.5564517462408 / 2.8954655103664537 |
| 71 | 374 | 19827 | 19821,19822 | 19820,19821 → 19822,19823 | 16787374,16818274 | 912,938 | bridge, model_water, water_roadway | 1121.4519172566072 / 2.908036747504019 |
| 71 | 375 | 19828 | 19822,19823 | 19821,19822 → 19823,19824 | 16787374,16818274 | 912,938 | bridge, model_water, water_roadway | 1124.3599540041112 / 2.9145547808576944 |
| 76 | 124 | 20542 | 20533,20534 | 20532,20533 → 20534,20535 | 19394363 | 3579 | custom_pilot_roadway | 350.10752639402307 / 3.013882900847428 |
| 76 | 125 | 20543 | 20534,20535 | 20533,20534 → 20535,20536 | 19394363 | 3579 | custom_pilot_roadway | 353.1214092948705 / 3.0137449963342515 |
| 76 | 126 | 20544 | 20535,20536 | 20534,20535 → 20536,20537 | 19394363 | 3579 | custom_pilot_roadway | 356.13515429120474 / 3.013521563515637 |
| 76 | 127 | 20545 | 20536,20537 | 20535,20536 → 20537,20538 | 19394363 | 3579 | custom_pilot_roadway | 359.14867585472035 / 3.0131759045152173 |
| 76 | 128 | 20546 | 20537,20538 | 20536,20537 → 20538,20539 | 19394363 | 3579 | custom_pilot_roadway | 362.16185175923556 / 3.012667228319763 |
| 76 | 129 | 20547 | 20538,20539 | 20537,20538 → 20539,20540 | 19394363 | 3579 | custom_pilot_roadway | 365.1745189875553 / 3.0119572032452533 |

Selecciones intencionales guardadas: chain 76 ordinales 124–129; contacto chain 49 ordinal 301; chain 71 ordinales 370–375. `Ref[1]` de overlay es fila de prototipo, no ordinal bed.

## Límites y unknowns conservados

No establecidos: identidad física actual de la fuente, `global_edge_index`, identidad de cámara, selector seco de chain 49, huella vial, accesos físicos, pivote, precedencia nativa, ancho, visibilidad ni conducción PASS.

La fila chain 49/301 tiene `instance_ids`, `model_indices` y roles vacíos en lo guardado: eso es **sin observación seleccionada**, nunca ausencia mundial o física, y no se la nombra «seco49». El modelo 3579 de chain 76 se presenta por su ID literal; no se le llama kit118 porque esta cápsula no guarda ese nombre. B0 local y B2/B3 no se mezclan con chain 76.

`role` procede sólo de `surfaces` de 4.json. Overlay y Q03B6 comparten `derived_from` común: no son dos marcos independientes. En la ruta ensayada no existía `B2 contract.json`; queda pendiente localizar su esquema por manifiesto, sin declarar inexistente el contrato. De Q03B6 se leyeron contrato y resumen; su índice de report completo no se abrió en Q05A.

No se diseña ancho —ni 8 m ni 24 m—, ni huella, visibilidad, pivote, precedencia ni accesos físicos. Dominio A futuro sigue siendo eje mientras no haya polígono guardado de reserva. Dominio B futuro queda limitado a los tres modelos B0 bajo sus cuatro hipótesis guardadas.

## Siguiente contrato necesario

Por dependencias, sin que esta entrega constituya nuevo permiso, council ni medición aprobada, el siguiente contrato geométrico requerirá plan propio y deberá, en orden: fijar identidad actual de fuentes y manifiesto pendiente de B2; resolver `global_edge_index` y el selector de chain 49; aportar polígono/huella y pivote verificables; y sólo después tratar ancho, accesos, precedencia, visibilidad y conducción. P5/P6/P9/P10/P11 y Q05 del council se mantienen.

END_SAVED_RESEARCH
