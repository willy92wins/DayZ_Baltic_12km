# Q03B5 — testigo de cobertura del META guardado

Estado: REVISADO_PARA_CONTRATO_Y_AUTORIA_DIAGNOSTICA. Muse Wonder1.0 nativo30.703s SOUND-with-fixes, adjudicado en evidence/q03b5-meta-coverage-plan-review-20261029. Consumidor inmediato: resolver el rechazo real Q03B4 sin repetir la captura ni bajar su igualdad de conjuntos. Desbloquea índice Q03 para exposición Q03C y huellas Q05; no añade un lector genérico ni certifica naturalidad.

## Hecho y pregunta cerrada

Q03B4 entregó código local853.932s, corrección116.832s y13tests verdes. Su productor único real4.907s rechazó COVERAGE en la conjunción `model_set==nonveg and source_set==set(models)`, después de recorrer META; no guardó diferencias. El consumidor no se lanzó. El recibo no distingue qué igualdad falló, cuántos IDs faltan ni por qué. No repetir ese CLI/carpeta.

[EXACT] `tools/quality/deployed_surface_inventory_ev112.py:140-170` selecciona capas Roadway y Visual de agua, y puede devolver cero caras; `:173-198` expande agua de proxies; `:273-291` conserva catálogo/metadata/poses y concatena las caras seleccionadas. La relación entre inventario completo y modelos con caras seleccionadas debe comprobarse; el mecanismo es pista, no explicación cuantitativa del rechazo observado.

[HIPÓTESIS] Un modelo guardado sin cara seleccionada puede permanecer en catálogo/secciones y no aparecer en META. Alternativas: contrato incorrecto, discrepancia de epoch/IDs, fuente parcial o error de joins. No se decide por proximidad ni se declara corrupción.

## Alcance cerrado y evidencia

Sólo contratoe967, catálogo y model-sections JSON fijados, source writer fijado, recibo de fallo Q03B4 y el NPZ de prototipos4c976c5f. No poses,201pilotos,NPZselected,WRP,PBO,P3D,P:,nuevas extracciones ni recursos instalados. Oráculo literal pequeño ANTES del código: catálogo con modelo sin caras seleccionadas, proxy-only, ID inesperado, conjuntos iguales y desiguales, duplicidad de filas legítima. Contrato nuevo fija hashes completos, nombres/tipos y límites del archivo original; no repina fuentes.

[DESIGN] Reutilizar archive79ef/header0514 sin modificar. Cargar exactamente dos miembros del NPZ bajo su schema concreto e967: vertices539009x4x3f8 yMETA539009x35B. No interpretar vértices ni emitirlos. Una Session por caminante; reservas16MiBstored/128MiBporarchivo/262434599total/35miembros intactas. Se conserva SHA de datos META y de cada JSON leído. La carga de vértices es coste del helper existente, no autorización de geometría nueva.

Productor: contar por model/source_model, diferencias en ambas direcciones frente a catálogo no vegetación y secciones, número de filas, duplicidad de IDs permitida, tablas de conteos por kind y LOD. Guardar TODOS los IDs testigo y cuentas, sin nombres/modelos completos fuera de lo ya permitido. No clasificar ausencia de cara como ausencia física. Para cada diferencia, enlazar sólo metadata guardada del mismo ID (LOD/resolución/cuentas/secciones), estados OBSERVED_SAVED/NO_META_ROWS_IN_ROLE/UNEXPECTED_META_ID. Las causas permanecen NOT_ESTABLISHED.

Consumidor: lectura propia del mismo NPZ/JSON fijados y recorrido por registros META mediante offsets del dtype35 verificado, independiente de `np.unique`/agrupación del productor. Comparar todas las cuentas, IDs de conjuntos y tablas; filas porkind/LOD reconciliadas con total539009, no sólo checksums autodeclarados. Puede compartir helper I/O; mismaNumPy/zlib declarada. No expected generado del productor.

Éxito máximo VERIFIED_META_COVERAGE_DIAGNOSTIC. Conserva Q03B4 REJECTED:COVERAGE y contratoe967 intactos. Ninguna igualdad se cambia a subconjunto en esta unidad. Si procede corregir el contrato, la propuesta posterior deberá citar testigos, explicar qué propiedad de producto se conserva, separar modelos sin caras guardadas de fuentes no leídas y revisar productor/consumidor antes de otro índice. No autoriza nueva captura Q03B4 ni reparación.

## Puertas y presupuesto

Codex planner/integrator; executor local explícito propuesto sólo después de revisión: contrato/oráculos+dos rutinas acotadas300s; code review120s por familia externa; suite60s/256MiB. Una corrección120s por repro cerrado, una recuperación de dictamen ausente120s. Si no entrega o no cumple, retirar sin ampliar ni abrir NPZ.

Plan review120s. Producción UNA vez60s/256MiB y consumidor UNA vez60s/256MiB; salida4MiB, oráculos/schemas/recibos externos fijados. Output exclusivo, sin retries. Rechazos: pin/epoch equivocado, miembro/dtype/cantidad alterado, ID inesperado, conteo co-mutado, set omitido, bool/int, unknownkey y datos de otro archivo. Un ID inesperado se informa como hecho, no se elimina para hacer igualdad; el consumidor rechaza un informe que lo oculte.

No build/DayZ/mapa, no cierre de nueve rechazos humanos, C1NOT_REVIEWED. No repetir council ni catálogos anteriores. Tras resolver esta diferencia, prioridad vuelve a índice usable y medidas de exposición/huellas; ángulos y referentes independientes permanecen pendientes.

## Precisiones vinculantes después de revisión

Una fila por(ID,rol model/source_model). Universos exactos separados: índices no vegetación de model-catalog para model; índices de model-sections para source_model. Guardar cada igualdad y diferencias en ambas direcciones, más mapa índice/nombre ligado por SHA. No fundir universos. Tablas y conjuntos por(kind,lod,proxy) y ambos roles, incluido proxy=-1. Oráculos literales contemplan fuente presente/modelo ausente y viceversa; proxy-only no se presume raíz. Cada causa queda NOT_ESTABLISHED.

El consumidor abre por sí mismo mediante Session, toma bytes C-order del payload META cuyo dtype35 fue verificado y los recorre por offsets explícitos. No usa los campos estructurados NumPy ni grupos del productor para derivar cuentas. I/O/NumPy/zlib compartidos declarados; no independencia de contenedor/NPY. La carga simultánea de vertices/META impuesta por Session debe caber en256MiB medidos; sin ampliar, y vertices no se interpretan. Si conjuntos completos no caben en4MiB, rechazar sin truncar.

Plan/revisión consumidos. Todavía sin contrato/oráculo Q03B5, código ni lectura real. No repetir Q03B4 ni esta revisión; continuar con la unidad acotada descrita.
