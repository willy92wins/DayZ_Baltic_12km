# RoadB4A1 — captura de estabilidad de las siete entradas de build

Estado: REVISADO_PARA_IMPLEMENTAR. Fable5.1 nativo79.766s SOUND-with-fixes adjudicado. Unidad de descubrimiento de Q04/P10/P11; no build, composición, DayZ ni modificación de P:.

## Hechos y duda

RoadB4A consumido emitió INCONCLUSIVE_DISCOVERY en1.203s/47MB. PBO instalado34c1 y sus7rangos fijados coinciden con catálogo guardado; tresmodelos y cuatroreferencias internas de build salieron SOURCE_UNSTABLE. Quinta referencia, asphalt_ext de RoadwayLOD3, UNRESOLVED_EXTERNAL. AliasSUBST y cincojunctions históricos identificados. El campo sources_stable sólo cubre fuentes primarias; NO las siete rutas de build.

El extractor perdió en su retorno temprano los metadatos que motivaron SOURCE_UNSTABLE. Por tanto no sabemos qué comparación falló en aquel instante. No se reclasifica R0. Un discriminador posterior de UNA pieza (asf1_25) observa dev/ino/size/mtime iguales entre ruta/handle, handlectime distinto de pathctime pero estable dentro de cada API, SHA7eb9 y firmaODOL54. Esto no aísla causa histórica ni se extrapola a otras6. Todas las lecturas originales se conservan.

## Hipótesis y contrato [DESIGN]

H1: con una captura instrumentada se puede certificar o refutar estabilidad de cada entrada sin confundir diferencias entre APIs con cambio temporal. No hay hipótesis de igualdad semántica entre los assets. No eliminar ni aflojar guardas existentes: conservar EXACTAMENTE stat_tuple/ident_tuple/reparse/mapping y comparar también los dos hashes de lectura del mismohandle. La nueva salida preserva datos incluso al no cumplir.

Nuevo diagnóstico separado lee sólo siete rutas EXACTAS seleccionadas desde R0 y los7SHA instalados del recibo fijado. R0 report/manifest y catálogo/contrato son entradas inmutables; sus pins se comprueban antes de parsear. No repetir catálogo/PBO/RoadB3 ni la CLI RoadB4A. Referencia instalada es la captura R0, no una nueva certificación de instalación actual.

Por fichero: lstat de componentes, os.stat/lstat del archivo, abrir un handle, fstatantes; dos lecturas streaming del MISMOhandle desde0 con SHA/tamaño/prefijo16, fstatentre ydespués, stat/lstatfinal y componentesfinales. Guardar TODOS los valores crudos y razones por igualdad, no sólo una etiqueta. No seguir reparse inesperado; aliasQueryDosDeviceW antes/después debe ser mismo mappingautorizado. Snapshotfresh: sourcebefore/after hashes iguales y todas guardas preexistentes verdes. Si no, INCONCLUSIVE_SOURCE_STABILITY. Si estable, comparar SHA y formato con referenciaR0; MATCH/DIFFER/FORMAT_DIFFERS/UNKNOWN. Nunca declarar INPUTS_MATCH si existe referenciaexterna no cubierta. UNKNOWNpivote/anchoutil/accesos permanece.

## Fuente real [EXACT]

tools/quality/road_build_discovery_ev112.py:107-137 _capture_file,145-155 QueryDosDevice/expected_mapping,167-193 inspect_build,378-399 comprobacionesfinales/report. Definiciones ya revisadas por Fable y corregidas con Muse, tests39coleccionados38PASS1SKIP. Se reutilizan sólo funcionespuramentelector a través de su hash2053b3c8; no se llama run_discovery.
R0 report en road-b4a-discovery-20261029/report.json; fuente ycontrato87a1 en road-b4a-real-inputs-20261029.
Discriminador posterior en road-b4a-stat-discriminator-20261029/report.json.

## Presupuesto y salida

Planreview90s; implementación120s; codereview90s; suite60s. Una captura30s/256MiB, sólo7ficheros build ymetadata, sinreintentos internos. DatosprimariosfueraP inmutables, salidaE nueva. Positivos/negativos: fixtureestable conctime distinto entreAPIperoigual dentro deAPI, cambio entrelecturas conmtime restaurado, sustituciónfileID, cambioancestro/reparse, pinreportalterado, omisión/duplicado/rutaextra, aliasdoble slash yexterna no promovida. Testespera el predicado EXACTO deR0 más hash2; no umbrales nuevos.

Si persisteinconcluso, conservarrazones y revisar mecanismo. Si haydatosestables, publicar descubrimiento conalcance temporal, proponer stageaislado de referenciasinstaladas; nuevo build exigeplan separado. No poda, geometría, exclusiones ni tolerancias alteradas.



# Adjudicación RoadB4A1

Fable5.1 nativo79.766s SOUND-with-fixes; entregado y consumido.

Adoptados: cada lectura debe tener n == st_size antes/después; conservar todos los predicados R0 y añadir hash2. Rutas EXACTAS del campo build.path de R0, que son canónicas C:, no inventar alias diferentes. Rawmetadata y componente concreto que cambia. Tests validan predicado nuevo, no reproducen un fallo histórico sin metadata. Conservar artefacto parcial por fases fsync y recibo del coordinador: un kill durante llamada bloqueada no puede prometer informe completo; salida parcial + TIMEOUT implica INCONCLUSIVE, no reintento. No asumir que haya hidratación ni su causa.

Refutada exigencia de que QueryDosDeviceW devuelva una sola cadena: la documentación oficial indica primera cadena = mapping ACTUAL, siguientes = mappings anteriores no retirados. Rechazar por su mera presencia añadiría un falso FAIL. Fuente:
https://learn.microsoft.com/es-es/windows/win32/api/fileapi/nf-fileapi-querydosdevicew
Conservar opcionalmente MULTI_SZ crudo, juzgar mapping actual; comparar ambos lados mediante win_norm. El código R0 ya hace win_norm en ambos: no falta esa normalización.

No adoptada explicación causal de ctime/OneDrive: no la demuestra esta revisión; sólo campos observados. El predicado R0 ya usa ctime dentro del handle, no entre APIs. Conservamos esta limitación y el dictamen INCONCLUSIVE histórico.

Límite aceptado: cambio revertido completamente entre observaciones puede no verse. No afirmar vigilancia continua ni snapshot atómico global. Cualquier referencia externa sigue abierta. R0 no guarda firma de material PBO, así que no inventarla: para comparar formato usar sólo una firma independiente fijada si existe; de lo contrario distinguir igualdad de hash de diferencia de bytes con formato de referencia UNKNOWN. No atribuir diferencias semánticas.
