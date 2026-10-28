# Reevaluación geométrica tras la visita
Estado: REVISADO_CON_FIXES_INCORPORADOS, 28-10-2026. Consumidor: el siguiente censo
offline y su adjudicación, antes de regenerar el mapa. Codex ejecutor/integrador,
Fable revisión independiente. P7/P9/P10/P11/P12/P14 y nueve observaciones de
evidence/visual-tour-20261027; c1 SIN REVISAR. Bosque y c0 sólo aceptación local.

## 1. Cambio necesario respecto al plan MLOD
El plan ev112-dry-bank-mlod-materialization-20261027 preserva XZ/agua y modifica
alturas de un único kit. Por construcción no puede corregir todas las siluetas
rectas/L, los puentes omitidos o la alineación de carreteras. Su candidato sigue
OFFLINE_CANDIDATE_ONLY, conservado. Se difiere su ejecución hasta cuantificar
el efecto frente a terreno/agua y las regresiones reales. No perder el trabajo,
no presentar su mejora energética como aceptación visual.

## 2. Primera unidad: localizar y medir sin modificar el mapa
[EXACT] tools/water/shore_ramp_v31.py:161 corner_water y :171 extract_segments
reconstruyen cruces agua-terreno en triángulos nativos; :231 chain ensambla por
clave de arista y posición. Este consumidor cubre terreno/charcas/mar nominal,
NO la ocultación por todos los modelos 3D; declarar esa cobertura por separado.
Entradas absolutas fijadas por SHA256:
- E:/DayZ-Baltic-Build/shape-repair-20261025/river-kit7-merged-byteexact-20261026/terrain-buried.npz:
  815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40.
- E:/DayZ-Baltic-Build/shape-repair-20261025/river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint.npz:
  084171b0e29df5c220f9d5aab42a3dc683a2f70a07579f08cd930dfd109e716b.
El stage-report del mundo y su revisión independiente vinculan este terreno
con la fuente visitada; no se vuelve a certificar el paquete nativo en esta unidad.
[EXACT] tools/quality/shape_patterns_ev112.py:38 route_screen analiza rectas,
giros y escaleras con POLICY existente; no demuestra naturalidad ni cubre arcos
uniformes, ni valida por sí solo contornos cerrados.

[DESIGN] Extraer TODO el contorno nativo, guardar segmentos, cadenas, claves y
asignación única de segmentos a cadenas. Inventariar discontinuidades,
degeneraciones y segmentos de longitud cero sin ocultarlos ni contarlos PASS.
Guardar GeoJSON/NPZ y vistas de contexto Narva, relieve oriental, kit118, cauce65,
road49 y cruce4789/5516. Localizar contornos próximos sin atribuirles automáticamente
la foto ni confundir cámara/personaje con las coordenadas del defecto.
Aplicar screen existente sólo como diagnóstico explícito: cadenas cortas o
degeneradas llevan estado distinto de PASS y las cerradas se identifican como
limitación pendiente. No inventar umbrales para redondez/naturalidad.
Comparar NPZ seco original/final contra terreno subyacente: alturas del lecho,
huella XZ y agua iguales/diferentes, incluyendo todos los vértices. Estas medidas
no certifican integración, colisión ni apariencia.

## 2a. Adjudicación de Fable y contrato del censo
Revisión nativa claude-fable-5-1 del 28-10, SOUND-with-fixes, entradas inmutables;
recibo privado visual-geometry-plan-review-20261028/completion.json. Se aceptan
los ocho puntos tras contrastar las definiciones citadas. No hace falta otra
ronda de plan: son correcciones de falsos resultados dentro del alcance.
- NaN en plane significa ausencia de charca, NO corrupción. Rechazar altura
  no finita, dimensiones incorrectas y field no finito donde plane es finito.
- Detectar duplicados por cara y por par de claves antes de encadenar. Comparar
  el conjunto completo de caras mixtas con las caras representadas para detectar
  también omisiones que el generador y chain no descubrirían.
- Inventariar caras con H==W, segmentos nulos y extremos abiertos coincidentes
  bajo claves distintas; no soldarlos automáticamente ni llamarlos normales.
- Capturar degeneración por cadena. En cerradas, screen recibe recorrido sin
  repetir el primer punto: cierre excluido y documentado, sin aceptación estética.
- Límite de recursos del screen: 2048 estaciones simplificadas por cadena y
  20 millones de pares acumulados; lo que exceda queda NOT_EVALUATED_COST.
  Se registra tiempo y cobertura. Estos límites no cambian POLICY ni el censo.
- Comprobar independientemente cada extremo proyectándolo sobre su arista y
  evaluando H-W en la cara con coordenadas baricéntricas; residuo <=1e-9 m.
  Añadir fixture analítica de cruce a media arista y casos H==W calculados.
- El diagnóstico NPZ compara TODOS los vértices, caps incluidos, contra terreno
  815ef8b7; no sólo centro. Mantener XZ/agua y metadatos como invariantes.
- Dominios antes de localizar: Narva L y relieve oriental = terreno candidato;
  Narva orillas = terreno/modelo por resolver; dos lechos y extremo kit118 =
  modelo (NO EVALUADO por contorno nativo); road49 zigzag = desconocido;
  puente desalineado y cruce sin puente = carretera/modelo (NO EVALUADOS).
  La cercanía se reporta como contexto, nunca como asociación confirmada a la foto.

## 3. Criterios de la unidad
PASS significa CENSO_DIAGNOSTICO_COMPLETO, nunca mapa aceptado:
- entradas hash-pinned y sin cambios, universo completo 2047x2047 celdas;
- cada segmento extraído registrado una vez y cadena/localización trazables;
- comprobación independiente de interpolación por triángulo en todos los
segmentos, y cruce en una cara analítica conocida con resultado calculado;
- negativos: NaN en altura, water field incompleto, segmento sin asignación,
segmento duplicado y cruce desplazado deben rechazarse por su motivo;
- reporte separa cobertura real de modelos/puentes/visuales que NO evaluó.
Fallo mecánico REJECTED; timeout/dato faltante INCONCLUSO. Cero cobertura no PASS.

## 4. Presupuesto y siguiente paso
Una revisión de plan y una revisión de código; una corrección por repro
concreto. Un censo de producción hasta600s, 1 hilo numérico y memoria objetivo
menor de2GiB. No variar pesos/umbrales ni relanzar scripts consumidos.
Tras resultados, elegir la primera clase reparable y su generador con evidencia
causal; censo independiente de cruces carretera-agua y mallas de lecho será unidad
separada. No desplegar un arreglo que deje sin explicar los fallos reales.
La reparación conservará autorizaciones de agua/extremos/topología, 015-45/60m,
márgenes secos y límites físicos actuales. Si la forma requiere cambiar una
protección o topología, acotar una propuesta y agrupar decisiones nuevas.
Council ampliado sigue tras trabajo vigente, sin fingir cierre de RAM o visual.

## 5. Resultado y continuación acotada, 28-10
Censo único terminado:107641 segmentos/1030 cadenas, cobertura nativa completa,
residuo máximo1.93e-12m;20 fixtures PASS. Revisión Fable de código SOUND antes
de una corrección propia reproducida: exigir dos aristas distintas y cada una
con extremos seco/mojado. Dos negativos nuevos cerraron esos falsos PASS.
Tiempo total7.36s, pico446562304bytes. Ningún dato del mapa modificado.
Tres cadenas excedieron el límite preventivo de2048 estaciones; se conservan
NOT_EVALUATED_COST en el informe original. Tras medir4599/3308/3204 estaciones,
se autoriza una lectura adicional de esas tres cadenas YA GUARDADAS, usando
route_screen sin cambios, mismos umbrales, hasta5000 estaciones por cadena,
50M pares acumulados y60s. No es un segundo censo ni se reescribe el primero.
Guardar resultado separado con hashes y cobertura; si excede coste, INCONCLUSO.
Ninguna cantidad de hallazgos equivale a defectos confirmados o permiso para
editar máscaras. Primera clase candidata: contornos nativos abruptos; L de
Narva y charca oriental ya tienen correlatos geométricos que deben adjudicarse.
