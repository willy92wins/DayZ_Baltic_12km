# Q01: conservar rechazos humanos y separar cobertura automática

Estado: REVISADO_PARA_IMPLEMENTAR. Fable5.1 nativo78.641s SOUND-with-fixes,
adjudicado abajo. Unidad documental ejecutable, sin cambios
de mapa, build, motor ni umbrales. Traza: council MUSE-01/GROK-01/GROK-17/CG01,
product-spec P10/P11 y encargo de detectar/reparar todos los casos equivalentes.

## Fuentes leídas [EXACT]

- evidence/visual-tour-20261027/feedback.json:28-47 lista3findings Narva OPEN.
- kit118-feedback.json:12-26 lista2findings OPEN; continuous65-feedback.json:11
  lista1finding. road49-feedback.json:18 identifica ROAD49-RIVER-VIS-01 y su
  rechazo, separado del visto bueno local de la calzada.
- additional-crossing-feedback.json:4-6 confirma rechazo de continuidad, no
  demuestra ausencia de puente. relief-east-feedback.json:5,14 identifica
  rechazo del contorno de charca, no prueba native_spike puntual.
- tour-ended-20261028.json:7-16 conserva C1 NOT_REVIEWED y visual_acceptance
  NOT_GRANTED; bosque/c0 LOCAL_VISUAL_OK; carretera49 local sin pavimento/prueba.
- tools/quality/native_shore_census_ev112.py:34-44 OBSERVATIONS tiene9IDs y
  dominios; evidence/native-shore-census-20261028/observations.json conserva
  asociaciones UNCONFIRMED_CONTEXT_ONLY. Posición aproximada no es localización.
- evidence/road-water-census-20261028/contexts.json muestra aproximación por
  cercanía, no identidad decruce. No multiplicar casos por cada arista cercana.
- evidence/closed-perimeter-q02a-20261029/summary.json es diagnóstico geométrico
  agregado. Su cadena278 no queda vinculada a un defecto humano por proximidad.

Antes de implementar, abrir JSON relevantes y fijar los hashes de fuentes
EXTERNOS en contrato. No inferir un selector de campo a partir de esta prosa.

## Diseño [DESIGN]

Producir nuevo ledger JSON de evidencia con un consumidor independiente. Reusar
los censos guardados, NO recalcular geometría. Contrato cerrado incluye versión,
exactamente9IDs, archivo+JSONpointer de cada finding/veredicto, pins de todos los
archivos leídos y los4controles de alcance: bosque,c0,carretera49,C1. Preparador
del integrador fija selectores explícitos desde lectura real; productor no busca
recursivamente cualquier campo id (hay IDs de puentes de referencia en reportes).

Cada caso conserva: id, source_sha256, source_pointer, human_verdict OPEN_REJECTED,
report_status literal, scope, ubicación/contexto SIN convertir avatar en defecto,
capas requeridas y evidencia automática tipada. Dominio puede ser unresolved;
no asignar a una sola capa porque un screen sólo mida esa capa.

Estados de evidencia automática de esta unidad: NOT_EVALUATED,
CONTEXT_ONLY_UNCONFIRMED, FINDING_UNRESOLVED, MATERIALIZATION_DIFFERENT. No usar
NOT_DETECTED como sinónimo de NOT_EVALUATED; se reserva para un detector que
consume la capa correcta, cubre el caso localizado y no lo detecta (fuera de
esta unidad si no existe ese enlace). No marcar FOUND sólo por vecino cercano.
Campos de evidencia llevan path/hash/pointer y límite; mantener las referencias
a modelosVisual/agua/terreno/cruces diferenciadas. Si una fuente no aporta una
medición, estado explícito; nunca rellenar un PASS.

En esta unidad ningún caso puede cerrarse: no hay nueva reparación ni reaceptación
humana. Estado agregado OPEN_HUMAN_REJECTIONS;9casos distintos exactos, cero
resolved, C1NOT_REVIEWED, bosque/c0 local, carretera49localconpendientes.
No extrapolar ni reasignar un visto bueno a otra dimensión. Nueva aceptación
futura necesita otra unidad y evidencia de reparación/consumidores, no editar
un booleano. Incluir versión observada Kit7Nav8Load1 y no atribuir esa aceptación
a candidatoQ02/RoadB3 que no estuvo en la visita.

Consumidor vuelve a leer bytes de fuentes fijados y ledger guardado. No importa
productor ni obtiene su lista de IDs del ledger. Comprueba universo/IDs/selectores,
veredictos literales, referencias, estados/totales y controles de alcance contra
contrato externo y fuente. JSON rechaza claves duplicadas/desconocidas, NaN,
omisión, coincidencia de nombre sin hash, ficheros ausentes o hash alterado. Un
correlato no pasa a asociación confirmada sin evidencia externa nueva. Hash y
parseo usan mismos bytes. Destino exclusivo, no sobrescritura de censos.

## Validación, presupuesto y parada

Plan review180s; implementación Muse240s; code review180s; suite120s. Una ejecución
real productor y consumidor60s/512MiB cadauno. Sin reintentos internos. Si falla
una ancla/selectores o no hay referencia necesaria, conservar fallo con límites,
revisar hipótesis y una nueva unidad antes de variar esquema; no bajar barra.

Tests positivos desde fixtures literales independientes con3Narva+2kit+4otros
y cuatro controles. Negativos: borrar/duplicar/intercambiarID, alterarhash,
referenciarID de puente anidado, consolidar2lechos como1, promoverC1, convertir
LOCAL_VISUAL_OK enGLOBAL_PASS, confundir calzada49conrío49, asociar cercanía como
confirmación, usar otra versión observada, FIELDunknown/NaN/duplicateJSON,
clasificarSIN_COBERTURA comoPASS, inventar cierre/humanacceptance. El consumidor
debe rechazar mutantes aunque productor no se ejecute. Revisión humana de tabla
fuente→ledger antes de publicación. Resultado es cobertura explícita y rechazo
durable, no un nuevo número de tests como certificado del mapa.

Fuera de esta unidad: Q02B calibración naturalidad, Q03 escenas compuestas,
Q04 piloto compilado/nativo y Q05 cruces. Continúan en el plan general; Q01 no
los sustituye ni autoriza reejecutar scripts consumidos.

## Adjudicación de revisión, obligatoria antes de código

1. Contrato fija literal por ID, no normalización libre: Narva/kit/cont65OPEN;
   road49river/reliefeastVISUAL_REJECTED_BY_USER;
   crossingUSER_REJECTED_ROAD_INTERRUPTED_BY_RIVER. Cuando exista status del
   archivo y del finding, ambos pointers con literal propio. Sin statusglobal
   real no se inventa uno. Hashes repinados no permiten cambiar aFIXED en esta
   unidad; cualquier cierre requiere contrato de fase posterior revisado.
2. Incluir forest-feedback.json ycauseway-c0-feedback.json como fuentes primarias
   de LOCAL_VISUAL_OK; flagsglobalesfalse yámbito local explícitos. Road49pina
   /road/status,/road/paving,/road/driving,/road/global_road_acceptance,
   /road/bug_005_closed y además el texto propio distinto de /road49 en tour-ended.
   No igualar literales diferentes ni usar el resumen en lugar de las fuentes.
3. Subconjunto80/108 del cruce yabsence_proven:false sólo contexto sin confirmar;
   noNOT_DETECTED. Añadir mutantefalseensubconjunto→ausencia certificada. Mantener
   road49 /river_findings/0/river_source_id:null. No asociar río por cercanía.
4. Esquema cerrado con TODAS las claves requeridas, sin defaults: agregado
   status,case_count9,resolved_count0,c1_verdictNOT_REVIEWED,
   visual_acceptanceNOT_GRANTED,cases,scope_controls,source_pins. Caso exige
   id,human_verdict,source_bindings,scope,location_status,required_layers,
   automatic_evidence. Fuente/vínculo exige path,sha256,pointer,expected_literal;
   cada evidencia automática exige state,bindings,limitation. Tipos estrictos,
   no bool como entero. Contrato es referente de universo/valores, no ledger.
5. Capturas locales son REFERENCE_ONLY: conservar hash declarado y existencia
   documental sin afirmar lectura deimagen. No son pins de archivos de entrada
   que estaunidad deba abrir. Imagenanotada sinruta sigue noarchivada; no inventar
   pin ni lectura opcional que cambie resultado entrehosts. Pinar losJSONfuente
   y mod/world/pilot/water de feedback como versión observada. Revisor propuso
   verificarimagen si existe; se acota a otraunidad porque aquí no es requisito.
6. Tabla explícita dominio→estado para nativeobservations. ConsumirJSONcompleto
   leído al preparar contrato; susnearest no son localización. Contexts ysummary
   Q02 son referencias diagnósticas separadas, nunca mecanismo de cierre.

No códigoQ01 todavía. La revisión de plan está consumida; siguiente paso preparar
contrato con selectores/pins, implementar autor/consumidor y ejecutar negativos.
