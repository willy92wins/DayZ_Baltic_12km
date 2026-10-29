# Q03B — reutilizar superficies guardadas sin mezclar épocas

Estado: REVISADO_PARA_PREPARAR_CONTRATO. Fable5.1 nativo70.578s SOUND-with-fixes adjudicado. No autoriza código, apertura de arrays ni ejecución todavía.

## Resultado que necesita el mapa

Q03/Q05/Q11 deben comparar la envolvente completa de lechos y extremos con terreno, todas las capas de agua y carreteras. Q03A localizó caras que ya existen: rehacer toda la extracción sería innecesario. El siguiente paso es ligar esas superficies a sus instancias y declarar exactamente el complemento que falta. Después se podrá medir exposición compuesta por áreas y huellas; una tabla de nombres o un máximo de rayos no la demuestra.

[EXACT] `tools/quality/pilot_visible_surface_ev112.py:185-235` guarda caras mundiales Visual y Roadway de201modelos, IDs de cara/sección, instancia, categorías BODY/CAP y correspondencia de fuente; `:248-256` limita la equivalencia y no certifica normales/UV/render. `evidence/pilot-visible-surface-20261028/report.json` conserva201 modelos,185744caras bed y4760water por cada parVisual/Roadway. El SHA del informe público leído es88bfb4a0643eb3082dea94dfd0094df38919f56dd3cfcae790ee836abc26ab45. No confundir equivalencia de cara no orientada con winding: el modelo kit118_0000 tiene exact_faces=true pero exact_oriented_faces=false frente a MLOD, y true entre Visual/Roadway. Se preserva esta distinción.

[EXACT] `tools/quality/deployed_surface_inventory_ev112.py:140-198,286-300` guarda539009caras de prototipo y17818poses no vegetación; agua proxy sólo del Visual y condicional. El catálogo histórico completo de nombres5509 está medido; el conjunto de caras5443modelos incluidas referencias de proxy es distinto. No deducir ausencia de geometría porque una capa no se guardó. No sustituir este denominador por UNKNOWN.

[EXACT] `deployed-surface-prototypes-20261028/inputs.json` fija WRP compilado0da63d3f, editableb108352f y piloto3d9550bf. B2A posterior fija el mismo WRP pero pilotoef229f32. La igualdad de WRP no implica identidad de modelos. No unir sus geometrías sólo por nombre ni atribuir retrospectivamente la identidad B2A a los prototipos. Las fuentes actuales B3F/RoadB3 no forman parte de este dominio.

## Dominio y contrato previo [DESIGN]

El contrato nuevo elegirá **escena histórica de las superficies guardadas3d9550bf/WRP0da63d3f**, con universo fuente5509 y proxies separados. No candidato5512, ni instalado actual. B2A/B4B0/B4B1 sólo acreditan sus cuentas y contrastes de época; no suministran poses o caras nuevas.

Antes de autoría, fijar externamente por SHA/longitud los manifest históricos, inputs, catálogo, model-sections, proxy-paths, reports y los201 registros models.json; registrar cada eslabón que acredita mundo/paquete y el alcance de ese recibo. No reabrir WRP/PBO/P3D ni extraer vanilla. Identidad física de archivos guardados se comprueba leyendo esos bytes, sin confundirla con identidad actual de proveedores. Si la cadena histórica diverge, INCONCLUSIVE_EPOCH_BINDING, no repinar ni escoger otra fuente silenciosamente.

Fuentes de arrays a enumerar por el manifest sellado, sin glob como selección: `deployed-surface-prototypes-20261028/{surface-prototypes,instances}.npz` y los201 `pilot-visible-surface-extraction-20261028/models/*.npz`. Los SHA declarados son entradas de contrato; el productor nuevo debe comprobar los bytes efectivamente leídos antes de parsear. El consumidor guardado relee esas mismas fuentes por su propio recorrido; no acepta un SHA autodeclarado del productor. Los arrays no se han abierto en Q03A.

La primera unidad Q03B sólo liga datos y produce un índice utilizable; NO ejecuta aún clipping de exposición. Delimita el alcance que permitirá después medir todos los lechos del piloto, no sólo kit118_0000. Ni terreno815ef8/agua nativa b661 ni carreteras se vuelven a censar ahora: sus contratos guardados quedan referencias declaradas. Su apertura/composición y huella vial completa tienen contrato posterior sobre el índice verificado.

## Invariantes de la composición guardada [DESIGN]

1. Catálogo fuente completo y grupo `vegetation_not_inspected` explícito. Joins por índice/modelo/ID literal: un modelo sin caras o sin poses tiene fila terminal, nunca desaparece. Reconciliar17818IDs únicos y cuentas por modelo con catálogo. Proxies se cuentan aparte de las referencias WRP; no sumar5509+5443 como universo.
2. Prototipos: conservar `model/source_model/face/section/lod/kind/vertices/flags/proxy/planarity_m` con sus bytes/tipos y las caras triangulares/cuadrangulares sin reordenar ni soldar. Los43ambiguos se mantienen; ningún TOLnuevo ni reclasificación por ausencia de Geometry. Verificar rangos/finite y filas de padding según formato real, sin confundir padding con vértices.
3. Piloto201: cada `model_index/instance_id` une exactamente una pose guardada y el nombre del catálogo. Verificar cantidades por capa/categoría e IDs por archivo contra models.json. Las coordenadas piloto ya son mundiales: NO aplicar matriz otra vez. Mantener el winding guardado; no convertir la comparación no orientada anterior en orientada. Cero unknown en el reporte histórico no demuestra semántica completa del resto de escena.
4. Preservar bytes, dtype y signedzero originales de matrices; verificar la cabecera, no inferir dtype de almacenamiento sólo por la procedencia float32 del WRP. Forma exigida(17818,12), no(17818,4,3): instance_guard la comprueba antes de guardar. Prototipos locales y piloto mundial quedan separados. No elegir entre raw/plus_center ni row/column por menor exposición. No prometer marcos alternativos cuando una salida anterior ya descartó la transformación necesaria: marcarla y conservar dependencia de Q04.
5. Proxies: siete rutas guardadas,65caras condicionales; conservar cadena completa root/slot/source. Los campos de Proxy `sequence_id/named_selection_index/bone_index/section_index` no guardados son UNKNOWN, no0. Esto NO es el campo META.section: éste sí conserva la sección de la cara hija. Identidad de cara compuesta incluye model/source_model/face/lod/kind/proxy/section y su multiplicidad; no colapsar por(model,face). La expansión histórica sólo cubre aguaVisual descendiente, no todas las geometrías de proxy ni Roadway hija. No repetir expansión ni inventar una nueva pose.
6. Salida por modelo: disponibilidad por capa, instancias ligadas, época, marco, condicionantes y huecos; catálogo completo con estados aunque falte Visual. Nueva lista explícita de entradas para Q03C exposición/Q05huella, sin filtrar por proximidad del avatar ni lista de puentes generados. Ningún array vanilla se publica; sólo identidad y cobertura resumida.

## Recursos, seguridad de lectura y revisión [DESIGN]

Preparar contrato y fixtures literales independientes antes de autor. Establecer los tamaños expandidos desde el formato del escritor y metadata guardada; si no se pueden justificar, hacer una inspección de cabeceras ZIP/NPY separada y revisada, no asumir mmap sobreNPZ. Lista de miembros exacta, sin objetos/pickle, sin rutas externas/duplicadas, tamaño por miembro y suma antes de asignar. Reparse o cambio de identidad bloquea según contrato nuevo; no cambiar lectores sellados. No abrir más modelos, PBO o P: por un campo ausente.

Presupuestos propuestos para cerrar en contrato: autor240s, revisión180s, suite120s; productor120s/512MiB y consumidor120s/512MiB, disco de salidas32MiB. Una ejecución por lado, sin retries internos. Procesar modelos uno a uno; prohibida expansión de539009caras por17818instancias en RAM. Índice de referencias/intervalos, no duplicación masiva de geometría. Techo no es predicción temporal. Al exceder cap, RESOURCE_INCONCLUSIVE; no salida FULL ni aumentar límite.

Positivos/negativos con lector independiente y datos literales: capa sinGeometry conservada, modelo sin caras preservado, ID omitido/duplicado, nombre case/slash/traversal, pose paraotroID, era dePBO mezclada, worldcoords transformadas dosveces, signedzero, windinginvertido, padding alterado, proxy perdido/ciclo/ruta desconocida y ZIP inflado/miembro desconocido. No exigir semántica de renderer para verificar almacenamiento; sí conservar ese límite. Los sintéticos no resuelven los nueve humanos GEOMETRY_UNBOUND. C1NOT_REVIEWED.

Salida posible: VERIFIED_SAVED_SCENE_BINDING_ONLY con cobertura reconciliada por alcance, o REJECTED/INCONCLUSIVE con motivo. En TODOS los casos `world_frame_certified=false`, `exposure_evaluated=false`, `native_acceptance=false`, `build_ready=false`, `map_repaired=false`. El índice no es la reparación. CalibraciónQ04, agua independienteQ08/Q17, Q02Bángulos y carreteras continúan por sus dependencias, sin repetir council ni unidades consumidas.

Esta revisión es del plan de binding y de sus puertas. Antes del código se revisará el contrato externo concreto con fuentes, schema, oráculos y presupuesto cerrados; una aprobación de este documento no habilita abrir NPZ todavía. La investigación Q03A terminó; no se relanza.

## Correcciones adjudicadas y preparación inmediata

La fuente de poses que lee el piloto está explícita en `pilot_visible_surface_ev112.py:157-158`: es `deployed-surface-prototypes-20261028/instances.npz` del manifest. El contrato ligará ese SHA6c0ae3b5 con inputs propios del piloto, manifest y matriz/ID del guardado; NO exigirá igualdad de archivo entre selected-instances.npz c2be1212 e instances.npz6c0ae3b5. Son contenedores distintos: el segundo añade norm/determinant/nonorthogonality. Sí se comprobarán las columnas originales que la cadena declara conservadas cuando ambas fuentes estén autorizadas; no inventar igualdad de ZIP.

El `[0]` del piloto no demuestra que se perdieran instancias duplicadas: `coverage_guard:44-53` exige201modelos y exactamenteuna instancia por cada índice antes de la selección. Contrato vuelve a verificar esas201ligaduras; fuera de ellas declara instancias con/sin Visualbed guardado y nunca `absent` por `NOT_SAVED`. No extrapolar la cobertura de201alresto.

Validar cabeceras ZIP/NPY dentro del productor autorizado es suficiente si el contrato justifica cuotas y schemas ANTES de código. No crear otra extracción o discovery de cabeceras por ritual. Las estimaciones del revisor (<20MiB para201NPZ y forma4x3 alternativa) no son cotas aceptadas: deben derivarse de TODAS las claves que escribe payload.update, incluidas source_grid/source_triangles/categorías, no sólo los seis grupos de caras. Padding sólo por el contador vertices/_n; un vértice(0,0,0) puede ser legítimo. Proxies ya expandidos están en marco mixto/condicional; no aplicar center otra vez.

La próxima revisión se limita al contrato concreto/oráculos; no repetir esta revisión de plan. Q03B todavía carece de contrato y código. Presupuestos propuestos deben quedar cerrados con cotas antes de ejecutar.
