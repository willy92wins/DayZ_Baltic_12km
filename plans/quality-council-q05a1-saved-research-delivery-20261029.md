# Q05A1 — consolidar la evidencia vial guardada, sin repetir investigación

Estado: REVISADO_PARA_CONSOLIDACION_DOCUMENTAL_GUARDADA.

[EXACT] Q05A cerró sin entrega completa dentro120s. session-before-stop.json
registra20fuentes/8247835B y el último lote completo56.509s. La siguiente llamada
falló en la comprobación de deadline ANTES de abrir otras fuentes o escribir
informe. stop.json conserva observación posterior180.834s. No atribuir causa
de latencia ni llamar a esto timeout de un hijo matado; fue una guarda temporal
del investigador local. No se abrieron NPZ ni se ejecutaron censos/geometría.

Los13joins y fuentes están en
E:/DayZ-Baltic-Build/shape-repair-20261025/q05a-saved-bindings-research-20261029,
con frozen-partial.json. La unidad Q05A está CONSUMIDA. Este corte sólo permite
consolidar esos bytes guardados, sin reabrir fuentes originales, completar los
archivos que faltaron ni reanudar el reloj anterior.

## Hipótesis, asientos y resultado [DESIGN]

Los metadatos guardados bastan para un informe parcial útil con identidades
explícitas y lagunas; no bastan para medir/colocar carreteras. Cambia el mecanismo
de entrega: Muse Wonder1.0 CLI nativo en asiento RESEARCH/redactor, lectura de
cápsula cerrada; Codex orquestador prepara cápsula por selectores ya guardados y
actúa como integrador. Contexto compartido del integrador declarado. No otra
investigación física ni nuevo censo/lector. No subagente Codex, council o fallback.

Preparación de cápsula30s/64MiB, por archivo16MiB; copiar hashes y recibos del
snapshot, comprobar13pointers contra4.json y nodos contra7.json. Ningún dato
faltante se deriva de cercanía. No sintetizar filas ni recalcular geometría.
Publicar sólo campos de identidad/estación/rol y huecos, no caras vanilla completas.

Una entrega nativa120s, <=1000palabras más tabla. Revisión del plan90s antes de
la entrega. Sin corrección/reintento automático por noentrega. Informe parcial
válido: SAVED_BINDINGS_PARTIAL_RECONCILED, measurement_ready=false,
placement_ready=false, human_resolved=0,C1NOT_REVIEWED. Q05A permanece fallido
respecto a su entrega temporal. Si falta dictamen o entrega, conservar y retirar
la ruta para esta unidad; no aprobar por el número de observaciones guardadas.

## Comprobación de salida [DESIGN]

1. Separar chain_index, edge_ordinal_in_chain, flattened_road_row_index,
   global_edge_indexUNKNOWN, nodes y pointer. Kit118/76:124–129; contacto49/301;
   Narva71:370–375 son selecciones intencionales. El selector49seco sigueUNKNOWN.
   Ref[1] de overlay es fila de prototipo; no convertirlo en ordinal bed.
2. Comprobar que ambos vecinos de cada tramo se conservan como conectividad,
   sin llamarlos accesos físicos ni fijar longitud/tangente. No suponer que
   columna nodes vacía o surfaces vacía implica ausencia mundial de objetos.
3. Distinguir sha_recomputed en Q05A y hash declarado por manifiesto. Hoy sólo
   se comprueba integridad de copias guardadas, no identidad física actual.
   Registrar derived_from común: overlay y Q03B6 no son dos marcos independientes.
4. B0 local y B2/B3 no se mezclan con kit118. Mantener límites de fuentes no
   leídas: B2 contract.json en la ruta ensayada no existía; falta localizar su
   esquema por manifiesto, no declarar inexistente el contrato. Q03B6 contrato y
   resumen sí se leyeron; índice report completo NO se abrió en Q05A.
5. Dominio A futuro sigue eje mientras no haya polígono guardado de reserva.
   Dominio B futuro sólo tres modelos B0 bajo cuatro hipótesis. No ancho8m/24m
   inventado, no huella/visibilidad/pivote/precedencia nativa ni conducciónPASS.

Integrador verifica las afirmaciones contra el snapshot y conserva verbatim
la salida externa; anota cualquier premisa refutada. No se ejecutan pruebas
geométricas ni se califica la consolidación como reparación. P5/P6/P9/P10/P11 y
Q05 del council se mantienen; siguiente contrato geométrico tendrá plan propio.

## Adjudicación Muse32.625s [DESIGN]

SOUND-with-fixes/CONVERGE condicionado; cinco precisiones obligatorias:

- RECONCILED significa autocontrol documental de copias guardadas, no verificación
  independiente. Recalcular SHA contra frozen-partial fijado externamente y los
  sha_recomputed previos de session-before-stop; no fijar nuevos hashes para PASS.
- Cápsula cerrada a bindings.json, frozen-partial.json,4.json,7.json,
  session-before-stop.json y stop.json. 20 archivos leídos +1ruta intentada ausente.
  No reinterpretar B0/B2/B3/Q03B6 ni buscar el manifiesto que faltó; queda pendiente.
  Excerpt de13pointers y ventanas de nodos, con manifiesto/hash, no todo el censo.
- role sólo desde surfaces de4.json; vacío permanece sinobservación seleccionada,
  nunca ausencia física. Nombres kit118/seco y tresmodelos no se demuestran por
  bindings solo; presentar IDs literales y límites de las asociaciones previas.
- station_m/length_m son valores guardados, no reconciliados geométricamente aquí.
  Los vecinos son conectividad, no accesos físicos ni longitudes de diseño.
- Los techos30/90/120s no son factibilidad probada. Incumplimiento=noentrega;
  nunca aprobación degradada por tiempo. Q05A original sigue fallido respecto a
  entrega y no se reabre. Presupuestos y frenos intactos.

El revisor no recibió frozen-partial en su cápsula; el integrador lo fija antes
de esta preparación. Postimagen editorial del integrador, sin otra review.
