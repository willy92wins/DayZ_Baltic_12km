Estado actual29-10: COMPLETADO_PILOTO_NUMERICO_REAL_ONLY. 4cadenas/18943aristas/54consultas;14tests. No censo global/naturalidad/reparación. Plan aprobado porhash conservado en evidence/shore-prefix-pilot-q02b2-20261029/plan-approved.md; contrato84534d48 intacto. Operaciones consumidas.

# Q02B2 — piloto numérico sobre contornos reales

Estado: REVISADO_PARA_IMPLEMENTAR_PILOTO_NUMERICO. Fable117.547s y adjudicación en evidence/q02b2-plan-review-20261029. Adenda normativa al final prevalece sobre ambigüedades del borrador.
Trazabilidad: Q02B/P14 del plan council; Q02B1 publicado3658b025 certifica operaciones, no el mapa. Sin reparación ni clasificación de naturalidad.

## 1. Alcance y fuentes
Nueva unidad separada, no rerun de CLI ni modificación de Q02B1/Q02A/Q02B0/Q17A. Leer sólo NPZ b661 (64MiB máximo, miembros/arrays requeridos <=8MiB, rechazar objetos/duplicados/esquema inesperado), selectores obtenidos del reporte Q02A guardado3fc0b507, contratos y primitivas selladas Q02B1. La descripción anterior suponía selectores en Q02B0: no existen; se usa Q02A guardado y se revalida cada offset/identidad contra NPZ. No recalcular censo.

## 2. Algoritmo y prueba [DESIGN]
Para cada arista de coordenadas binarias exactas, q=dx²+dz² racional. Raíz p48 produce enteros a_i<=sqrt(q)*2^48<=b_i con ambos testigos enteros. Guardar q, a_i,b_i y prefijos A_j=sum(a_i,i<j), B_j=sum(b_i,i<j). Éstos son enteros EXACTOS, no magnitudes intervalares desconocidas.
Un rango [r,s) tiene envolvente [(A_s-A_r)/2^48,(B_s-B_r)/2^48]. Por cancelación algebraica es EXACTAMENTE la suma dirigida de extremos de sus aristas: no se usa resta intervalar cruzada [A_s-B_r,B_s-A_r]. Para vuelta de costura, sumar los dos rangos disjuntos; para reverso se invierte orden de aristas, no sus longitudes. La conmutatividad de suma racional exacta prueba mismos extremos que Q02B1. Nunca restar longitud real desconocida ni estrechar una envolvente por tolerancia.
Cache ligado a SHA del NPZ, ID/offsets/closed, coordenadas float64 little-endian ordenadas, orden de aristas y módulos sellados. Cierre repetido se valida antes de retirar sólo la última copia exacta. Degeneración compara q contra T², T=3022314549036573/302231454903657293676544 (float1e-8), < estricto; cero/short invalidan cadena, no ventanas.
Precomputación nueva por cadena, máximo14000aristas/4096bits/4000000operaciones; contadores por arista con Budget100000 y total sumado, interrumpir antes de exceder total, no levantar límite por consulta. Prefijos enteros prechecks4096bits y operaciones cobradas. Son presupuestos de nueva fase compartida, no permiso para ocultar trabajo de consulta. Registrar operaciones/cachebytes por cadena y consulta.
Consultas por ancla e h: soporte abierto distancias a extremos, cerrado2h<P estricto usando P intervalar. Reproducir estados Q02B1: SUPPORT_UNCERTAIN si intervalo cruza frontera, h0 exacto, igualdad final abierta exacta admitida, no exacta BOUNDARY_UNCERTAIN. Productor localiza segmento mediante prefijos de rangos dirigidos/búsqueda monotónica; acepta interior sólo S_hi<h<N_lo, igualdad puntual de prefijo exacto canónica. Límites sin decisión => incertidumbre. Estaciones t=(h-S)/L y punto por intervalos; luego métricas algebraicas mediante primitivas selladas de productor Q02B1. No atan2: PENDING_CERTIFIED_ANGLE.
Consumidor NO importa el nuevo productor. Lee fuente fijada, verifica q y ambos testigos de cada arista, contabilidad completa/orden/cierre y prefijos. Consulta caminando aristas en orden desde ancla y acumulando extremos directamente (sin usar prefijos del productor), detiene al resolver interior o al superar h; exige mismos extremos/estados/campos de estaciones y métricas. Puede usar primitivas de consumidor Q02B1 (ab1977bc), distintas del productor(ef844931); el esquema/loader se valida en ambos o helper de transporte explícitamente compartido sin pretender independencia de parser. No recalcular raíces por consulta ni emitir transcript duplicado de14k aristas: certificados por cadena una vez, resultados por consulta. Una línea NDJSON/cadena <=16MiB y consulta<=256KiB, total64MiB; EOF/cuenta/orden y claims se comprueban; no resultado truncado aceptado.

## 3. Selección cerrada y contrato externo
[
  {
    "label": "longest",
    "chain_id": 1,
    "closed": false,
    "point_offset": [
      234,
      13655
    ],
    "segment_offset": [
      233,
      13653
    ],
    "core_count": 13421,
    "core_float64_le_sha256": "bf2f14afe8bec522833ae5d583d76e8d722017a8db06e260f895335e352038e2",
    "anchors": [
      0,
      6710,
      13420
    ],
    "prior_degenerate_reason": null
  },
  {
    "label": "first_open",
    "chain_id": 0,
    "closed": false,
    "point_offset": [
      0,
      234
    ],
    "segment_offset": [
      0,
      233
    ],
    "core_count": 234,
    "core_float64_le_sha256": "5f895ed627287bb5bcb86253f3162499b092f157b2c22bb8134d31b05a2e843f",
    "anchors": [
      0,
      117,
      233
    ],
    "prior_degenerate_reason": null
  },
  {
    "label": "short_closed",
    "chain_id": 43,
    "closed": true,
    "point_offset": [
      19914,
      19921
    ],
    "segment_offset": [
      19871,
      19877
    ],
    "core_count": 6,
    "core_float64_le_sha256": "1e560d7e875bcb4f3318cfb15cf6f7dd05e435757141c280c0a1de7eba49ee2d",
    "anchors": [
      0,
      3,
      5
    ],
    "prior_degenerate_reason": null
  },
  {
    "label": "degenerate",
    "chain_id": 85,
    "closed": true,
    "point_offset": [
      23012,
      28297
    ],
    "segment_offset": [
      22927,
      28211
    ],
    "core_count": 5284,
    "core_float64_le_sha256": "8492c008352f8e6ee458a4749054d21c1147a6284e7daa1f9fee664d19cb8d21",
    "anchors": [],
    "prior_degenerate_reason": "short_segment"
  }
]
Anclas únicas [0,n//2,n-1], excepto degenerada0; h=[0,6,12,24,48,96],54consultas esperadas sobre3cadenas y1registro degenerado sin consultas. Las selecciones son clases numéricas, no vínculos de fotos ni muestras naturales positivas. Contrato congela cuatro descriptores exactos, hashes NPZ/Q02A/módulos, h/listas, budgets y scope ANTES del código. Las expectativas reales se descubren, no se prefijan PASS. Fixtures literales guardados Q02B0/Q02B1 para suite nueva comparan estaciones/estados exactos y mutantes; no relanzar sus CLIs.

## 4. Validación y presupuestos
Autor Muse240s, revisor Fable180s, suite120s. Una captura120s/512MiB y consumidor guardado120s/512MiB; sin reintentos internos ni aumento de caps. Revisión del plan120s. No implementación con plan incompleto. Correcciones sólo sobre fallo concreto con nuevo recibo y presupuesto, antes de captura real. Si hay RESOURCE/TIMEOUT: conservar parcial y estado INCONCLUSIVE, no rerun ni aceptación global.
Contraejemplos: cache coord/orden/closed/offset/pin mutados; raíz ausente/falsa y prefijo recortado; resta intervalar cruzada; wrap/reverso y h0; igualdad abierta y frontera incierta; consulta faltante/duplicada/anchor/h cambiados; registro malformado/linea enorme y EOFprematuro; resource oculto; promoción de9humanos/C1/naturalidad; co-mutación de report+certs contra fuente; input fuente cambiado. Positivos: recta exacta, diamante sqrt2 con costura/reverso, espigaAC0, corta cerrada sin soporte, degenerada sin consultas, coincidencia Q02B1 de fixtures y ventanas reales contadas.
Salida REAL_CONTOUR_NUMERIC_PILOT_ONLY sólo si contrato/identidades/certificados/registro completos; estados numéricos explícitos no equivalen a calidad. Consumidor numéricamente inconcluso no promueve piloto completo. NuevehumanosGEOMETRY_UNBOUND/0resueltos,controls4,C1NOT_REVIEWED,naturalpositive0,calibrationfalse. Ningúnmapa/build/DayZ.

## 5. Siguientes frentes
Q03/Q05 y naturales/agua independientes abiertos. RoadB4B exige plan propio de escena/precedencia/recursos/poses/huellas/accesos/oclusores;12recursos de3modelos no cierran5509escena. No sacrificar reparaciones reales por ampliar diagnósticos infinitos: este piloto debe decidir capacidad del censo antes de escalar.

## 6. Adenda normativa de integración

# Adjudicación Q02B2 — 29-10
Fable5.1 nativo117.547s NEEDS-WORK. Revisión de plan sólo texto, recibos e identidad guardados. Codex integrador cotejó contra las definiciones reales; no consenso ficticio ni autorización por etiqueta.
H1 aceptada precisión de redacción, refutado testigo arbitrariamente ancho: Q02B1 sqrt_witnesses:65 y verify_witness:263 ya exigen piso/techo canónicos por desigualdades. Contrato nuevo los escribe literalmente. No exigir a>=1 para arista degenerada0; se permiten0 y se etiqueta degeneración antes de consultar. floor a satisface a²d<=N<(a+1)²d; ceil b satisface (b-1)²d<N<=b²d o b0N0. Con N=q.num<<96. Esto fuerza b-a0/1.
H2 precisar bilateral exactamente como compute_window_core:230-258. Extremo abierto h>0 INSUFFICIENT_SUPPORT; no introducir unilateral/dosestados nuevos ni cambiar Q02B1. Son20consultas de extremos abiertas conh>0, no36. Las otras pueden no tener soporte; es resultado legítimo de piloto de fronteras, no detector de calidad.
H3 aceptado: unidad contador de primitivas Budget/CapB selladas más llamadas tick antes de operaciones enteras nuevas. Copiar su contabilidad existente, no bitoperaciones ni timing. La nueva fase cache tiene total4M; cada arista chequea crédito restante en tick ANTES de operar, no sólo al finalizar. Consulta100000intacta. Cada suma/sub/comparación entera nueva cobra1, precheckbits antes; bignum de funciones selladas usa sus tarifas, sqrt16/comparacionesetc.
H4 aceptado: verificar degeneración real vs selector; divergencia da INCONCLUSIVE_CHAIN_CLASS y no piloto completo. IDs1/0/43 deben no degenerados,85sí; reportar todos los índices cortos y q sin omitir cero. Nunca saltar consulta silenciosamente.
H5 parcial: representación consumida tiene segmentos implícitos por puntos consecutivos; closed_perimeter_ev112.py:4-10 y shore_numeric_discovery:253-266 describen chain_offsets contador, no arraydepares. No inventar firma ni certificar otros arrays chain_order/tri que no se leen. Comprobar cada cache edgeid enlaza corei->core(i+1)%n, closedendpoint exacto, ambosoffsets ybytes. Scopeidentidad de polilínea, no correspondencia de triangulación externa.
H6 rechazado como modificación arbitraria de dominio: subnormales/2^32 no son umbral aprobado. FuenteNPZ fijada y magnitudeQ02B0 max12282; exigir finitos, prechecks4096 bits y diagnosticar RESOURCE si exceso sin rebajar ni excluir coordenadas para PASS. Sin ocultar causa local del recurso.
H7 aceptado explícito: h en frontera [Nlo,Nhi] no puntual exacta =>BOUNDARY_UNCERTAIN. Consumidor debe comprobar mismoestado usando caminata; igualdadexactaelige inicio del segmento siguiente salvofinalabierto con t1.
Resultado de integración: REVISADO_PARA_IMPLEMENTAR_PILOTO_NUMERICO, con adenda literal incorporada antes de contrato/código. La prueba algebraica fue confirmada por revisor. No requirió cambios de producto ni relajación. Presupuestos autor240/review180/suite120/piloto120512MiB/consumer120512MiB. No code ni captura en el momento de este recibo.
