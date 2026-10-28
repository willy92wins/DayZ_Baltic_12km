# Orillas del piloto: perfiles reales y restricciones de reparación

Estado: EJECUTADO_DIAGNOSTICO_VERIFICADO. Codex ejecutor/integrador; Fable revisor.
Consumidor: siguiente autor de reparación seca de los cuatro cauces. Recibe
perfiles por sección, conflictos y alcance del candidato previo; no un PASS visual.
P9/P10/P11/P14 y nueve regresiones de la visita. Sin cambiar mapa ni tolerancias.

## Evidencia y alcance

[EXACT] Publicado8290f06:201modelos/185744caras, exposición continua frente a
H/agua/corredor verificada independientemente. Kit118 tiene23.956666m² sobre H
en el corredor rectangular±4m,13.478894BODY+10.477772CAP, sin agua Visual encima.
La reserva del gate no equivale a pavimento medido. No volver a censar esas caras.
Herramientas A/B/Visual201/exposición quedan inmutables; consumir manifests.

[EXACT] Candidato1e85c73f sólo139kit7, nunca los26kit118/9cauce65/27cauce131.
Fuente9d8caf0f; candidate en R/dry-bank-visual-water-pilot-20261027/candidate-surfaces.npz.
R=E:/DayZ-Baltic-Build/shape-repair-20261025. Exposición sobre H no equivale a
defecto: incluye orilla diseñada y lecho sumergido. Falta distinguir anchura
del lecho visible respecto a la lámina y elevación de su cresta; no atribuir
automáticamente la captura a un solo máximo ni inventar umbral estético.

[EXACT] tools/water/continuous_stream_pilot_v31.py:287-317 crea39columnas,
agua4.5m y delantal hasta±18m reducido en curvas; eleva orilla sobre H+.02.
:344-361 añade8filas CAP por extremo fuera del NPZ. Fuente/Visual real y
correspondencias completas están selladas en pilot-visible-surface-extraction.
El plan previo protege filas min(station,L-station)≤6, q≤2.25, bordes±18,
water/XZ y máscaras. Sus límites técnicos no son por sí solos una decisión
humana de congelar toda superficie seca añadida alrededor de una carretera.
Conservar agua/extremos y protecciones humanas sigue siendo obligatorio.

## Mediciones de esta unidad

[DESIGN] Leer201grids fuente ya verificados y los cuatro NPZ originales.
Reconstruir exactamente todas las filas por sitio, sin duplicar juntas; añadir
CAP reales. Rechazar falta/discrepancia/solape de filas. Candidato sólo sustituye
Y del cuerpo kit7 donde corresponde; CAP y otros sitios siguen sin candidato.

Perfiles transversales en cada fila guardada (NO cobertura continua longitudinal):
intersectar cada segmento del perfil con la triangulación nativa6m/NW-SE. En
u=x/6,v=(12282-z)/6, cortar en u entero,v entero y v-u entero. Dentro de cada
intervalo H y B son afines; evaluar extremos y raíces de B-H. No sólo vértices.
Mantener todas las partes positivas, sin eliminar por epsilon. Comparar también
B con Y de la lámina real en esa fila. En CAP usar el nivel del extremo como
referencia extrapolada y etiquetarlo: NO afirmar que haya agua sobre CAP.

Guardar por fila/lado longitud de lecho sobre H y sobre el nivel de sección,
extensión proyectada más allá del borde de agua, máximos B-H y B-Wsección,
coordenadas extremas. Longitud a lo largo del perfil y anchura proyectada son
distintas. Agua en XZ cuantizado puede no ser perfectamente collinear con lecho;
usar dirección entre sus dos bordes, sin modificar posiciones. Conservar residuo
transversal, inversión de columnas o degeneración como diagnóstico/INCONCLUSO.
Los perfiles comparan baseline y candidato kit7; no sustituyen un futuro gate
continuo de todas las caras candidatas ni verifican oclusión/render.

Restricciones: reproducir máscara del ensayo seco previo desde inputs originales
hashados del contexto dry-bank-visual-water-setup-20261027/context.json:
reserve/platform/narva/bridge/dam/causeway/ramp, máscaras opcionales históricas,
s3_road_guard, vértices de charcas actuales y radio60m015-45. Conservar motivos
por separado. Su extrapolación a62modelos SIN_CANDIDATO es análisis del contrato
anterior, NO aprobación para editar ni demostración de imposibilidad global.
Interpolación nativa >0 identifica vértices que tocan máscara, no cobertura
completa de triángulos: etiquetar la limitación. La reparación futura necesita
preservación geométrica continua en cada protección efectiva.

Piso anterior H+.02 y Wreal+.025 para puntos previamente secos; techo original,
cuantización1/512, dominios2.25<|q|<18 y CAP≤6. Registrar incompatibilidad de
piso/techo y ausencia de valor cuantizado, sin forzarlas a libres. CAP extra
separado como fijo técnico del piloto antiguo. No cambiar los valores.
Mapear motivos por vértice y por cara mediante source_triangles/bed_source_face.
Consumir áreas del censo publicado: ALL_DRY_PILOT_EXCLUDED, MIXED y ALL_POINT_FREE;
sumas por cara conservan exactamente el total. MIXED no prueba reparabilidad.
En particular, área de carretera en caras totalmente fijas es cota inferior
de exposición que ese contrato congelado no puede retirar. No es un conflicto
con una orden humana hasta contrastar qué parte de la máscara era técnica.

## Puertas y presupuesto

Una revisión de plan≤600s, implementación acotada y revisión de código≤600s.
Fixtures cerradas: perfil plano oculto/expuesto, pico interior nativo omitido por
extremos, cruce por diagonal/rejilla, agua real frente a level, CAPextrapolado,
segmento nulo/invertido, junta duplicada discordante, máscara parcial y clasificación
de caras totalmente fijas/mixtas/libres. Mutante de agua/XZ/candidato fuera de kit7
debe fallar. Sin epsilon para ocultar longitud positiva pequeña.
Preflight≤120s/2GiB, hashes/cobertura y coste sobre filas estratificadas; una
producción≤600s/2GiB. Consumidor independiente GEOS de perfiles≤600s/2GiB:
intersección LineString con triángulos nativos, alturas por sistema baricéntrico,
sin importar generador de cortes/función H del autor. Todas las filas baseline
y candidato. Comparación numérica≤1e-7m para longitud/alcance y≤1e-9m alturas;
son límites de reproducción, no umbrales nuevos de calidad del mapa.
Además reconstruir conteos/particiones de caras desde índices y motivos guardados,
con controles analíticos que no usen máscaras del autor. Se distingue validación
aritmética de máscara de validación contra fuentes, que debe leer inputs originales.
Dato cambiado/cobertura incompleta/degeneración/presupuesto o desacuerdo:
INCONCLUSO, conservar salida; hipótesis y plan nuevos antes de repetir.

Entregable: tabla de restricciones/alcance candidato y diagnóstico de perfiles,
con propuesta concreta para reparación procedimental. Sin build, DayZ,lease,
modificación de geometría ni aceptación visual. No relanzar consumidos.

## Adjudicación previa

Fable5.1 nativo217.469s SOUND-with-fixes, identidad verificada,0denegaciones,
fuentes intactas. Fix1 se resuelve evitando la palabra LEGACY para la máscara
del ensayo seco. NO reconstruimos la máscara del generador v31 con inputs del
ensayo: eran fuentes y umbrales diferentes. El generador original usaba4<|q|<18
y >.99999; el ensayo2.25<|q|<18 y >0. Mantener dominio por vértice/cara, motivos
separados y partición del área de corredor. La bandera ALL_DRY_PILOT_EXCLUDED
sólo se refiere al contrato del ensayo anterior; no se atribuye su causa a
ground+.02 ni se la presenta como máscara original del generador.
Fix2: registrar claves obligatorias/opcionales realmente presentes y sus hashes;
charcas del footprint95f7a2 no se homologan a current_pond del autor v31.
Fix3: toda comparación candidata indica solver success:false/500iteraciones,
cotas satisfechas. No llamarla óptimo. Guardar primeros cruces de H y del nivel
de sección y candidatos sin candidato. Perfiles siguen sin cobertura entre filas.

Revisión de código Fable437.187s SOUND-with-fixes, fuentes intactas,0denegaciones.
Se conservan anchura, residuo transversal y desplazamiento agua-centro por fila;
width<4.5 es diagnóstico de estrechamiento o cuantización, no falla estética.
El cuerpo proyecta los dos bordes REALES; sólo CAP utiliza referencia trasladada.
Repro independiente con agua desplazada.5m daba3/3m en vez de3.5/2.5m; corregido.
Solver se lee del author-report pineado, verificando identidad del candidato.
Consumidor verifica montaje contra cada source_grid, cuerpo NPZ, water/estaciones,
CAPetiquetado y candidato real; negativos agua/cuerpo/candidato/CAPrechazados.
16fixtures fuente y5controles analíticos independientes+4mutantes de procedencia.
Motivos de exclusión solapan y no se suman como vértices únicos. Sigue sin cambio
de mapa ni veredicto visual. Presupuesto original120/600/600s y2GiB permanece.

## Resultado y decisión

EJECUTADO_DIAGNOSTICO_VERIFICADO:4.127perfiles y185.744caras, consumidor GEOS
completo77.063s, productor62.75s,16fixtures+5controles+4mutantes. Evidencia
evidence/pilot-bank-constraints-20261028. No geometría cambiada ni render probado.
El contrato anterior excluye todas las caras con23.956666m² de solape carretera
en kit118 y deja0puntos libres en los62modelos ajenos a kit7. En kit7 reduce
altura, pero conserva alcance emergido cercano a14m por lado. No materializar
como arreglo completo. Conservar1e85 y revisar tratamiento procedural del
delantal/extremos; distinguir máscara técnica de protección humana antes de
proponer una candidata. No rebajar tolerancias ni reinterpretar agua/extremos.
