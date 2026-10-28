# Superposición de carreteras, agua y puentes desplegados

Estado: REVISADO_CON_FIXES_INCORPORADOS. Codex ejecutor/integrador por petición viva;
Fable revisor independiente. Deriva de P8/P9/P11/P14 y de ROAD-CROSSING-VIS,
BRIDGE-ALIGN-VIS y KIT118-ROAD-OVERLAP de la visita. Sólo diagnóstico offline.
No mueve puentes, agua, alturas ni extremos; no sustituye la revisión visual.

## Descubrimiento que cambia el diseño

[EXACT] El paquete visitado narva_trial.pbo f0e0e6b9 contiene exactamente el
WRP compilado0da63d3f, origen editableb108352f. Las identidades de2578398
objetos y sus5509modelos coinciden. Evidencia privada reproducible en
E:/DayZ-Baltic-Build/shape-repair-20261025/deployed-world-geometry-discovery-20261028.
El filtro inicial de rutas omitió agua por separadores Windows; su catálogo
completo sigue intacto. No se usa ese subconjunto de28piezas como universo.

La continuación geometry-payload-discovery-resolved-20261028 normalizó rutas,
conservó el complemento y leyó5443payloads, incluidos6proxies, sin fallos de
LOD/índices/secciones.17818objetos no vegetales:28puentes(4modelos),2presas,
201pilotos,10264charcas y7323streambed(6352agua y971piedras, confirmar por
proxies/materiales al consumir).72modelos vegetales/2560580instancias quedan
explícitamente fuera; no son prueba de ausencia de Roadway por su nombre.
717poses de piedras varían respecto al editable, máximo9.536743e-7; no se
acepta su igualdad. El consumidor usa la pose COMPILADA real. Puentes, presas,
pilotos y agua restante mantienen bits de pose; registrar también esta identidad.

[EXACT] Lectores: tools/vegetation/prune_visual_forest_v31.py:14/25 (0WZD),
tools/terrain/package_visual_forest_ev112.py:29 (OPRW heurístico acotado),
tools/playtest/attach_navmesh.py:21 (tabla PBO; loader entero no apto para1.67GB).
La sonda streaming acotada verificó tabla y payload; no elevarla a decoder PBO
universal. Rechazar compresión o firma no soportada, no adivinar.
ODOL utilizado: C:/temp/moto_lanes/review_g3/tools/odol_reader.py,
SHAfa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57,
from_bytes(data,strict=True):961. Índices de secciones comprobados por caller.
No modificar ni promover ese lector externo en esta tarea.

## A. Consumidor de superficies reales

[DESIGN] Extraer prototipos de cada modelo no vegetal desde su payload ligado
por SHA al PBO de la visita y matriz de cada instancia desde el WRP compilado.
Conservar todas las caras Roadway, inclusive las de presas, piedras y lechos;
etiquetar origen/función, NO contarlas automáticamente como tablero válido.
Roadway = resolución serializada3000000028082176.0, igualdad exacta; no nearest.
Los9modelos sin esa LOD (6proxies y3grupos de piedras) quedan sin Roadway en el
inventario; no fabricar caras ni tratarlos como fallo por esa ausencia.
Agua visual: LOD de menor resolución visual, caras con material exacto
dz/water/streams/data/water_streambed.rvmat o
dz/water/ponds/data/pond_moss_1.rvmat. Comparar igualdad tras normalizar barras
Windows/POSIX y minúsculas, conservando también el texto original. Igual para
texturas y referencias de proxy; incluir estas variantes en fixtures.
Conservar secciones sin material y con
material desconocido como inventario, sin convertirlas en agua por substring.
Cada cara lleva modelo, instancia, LOD, sección e índice fuente.
Los28objetos de modelos de puente son candidatos de soporte; una presencia
nominal o un bbox nunca constituyen cobertura ni continuidad.
water_ext.paa nunca se clasifica como soporte de puente. Las secciones con
textura vacía se conservan; no son motivo para omitir una cara del tablero.

[EXACT] tools/water/verify_compiled_stream_pilot_v31.py:44-65 aplica ODOL
almacenado + pose compilada(origin+bc), comparándolo con MLOD+origin.
En general, Vworld=Vstored @ matrix[:9].reshape(3,3) + matrix[9:]; NO añadir
otra vez el centro al objeto raíz. Verificar con muestras MLOD originales de
pilotos. No existe MLOD vanilla original disponible de los cuatro puentes:
comprobar sus poses editable/compilado y rotación/traslación/escala analíticas,
sin fingir otra fuente independiente. Registrar normas de los ejes, determinante
y no ortogonalidad de todas las matrices de instancia.

[HIPÓTESIS] Los proxies vanilla usan Vparent=(Vchild+child.bc) @ Rproxy + Tproxy,
y luego la transformación del padre. extract_streambed_geometry_v31.py:105-114
emplea esa convención con orientación casi identidad y redondeo. Esta unidad
debe conservar orientación completa y floats originales. Contrastar contra
su cache existente sólo como detección de discrepancias, no prueba independiente
de motor. Si no hay evidencia independiente que fije el marco, etiquetar agua
proxy CONDITIONAL_PROXY_FRAME; no cerrar cruces que dependan de ella.
Probar analíticamente proxies con rotación, centro no nulo y jerarquía; rechazar
ciclos o dependencias no resueltas, no omitir la rama.

Caras degeneradas, verticales en XZ, no finitas, cuádruples no coplanares o
cóncavas: registrar y no convertir en superficie funcional silenciosamente.
Para quads convexos coplanares, fan0-1-2/0-2-3 da el mismo plano y huella;
comprobar esa condición. Para otras, retener geometría y marcar ambigüedad
de triangulación; no imponer diagonal asumida del motor.
No expandir94millones de caras visuales de lechos vanilla: sólo agua del proxy
y Roadway para esta unidad, sin reclamar auditoría de lecho visible completo.

## B. Superposición sobre TODO el eje de carretera

[DESIGN] Consumir124cadenas/36467aristas del grafo independiente ya fijado y
guardado; no partir de crossings-ev106 ni del listado de puentes generados.
Revalidar multiconjunto/IDs/longitud con graph_guard, herramientas del censo
tools/quality/road_water_contacts_ev112.py:111. Consumir los intervalos de agua
nativa guardados y comprobar sus hashes; añadir contactos de TODA agua3D.

Broad phase por bbox de instancia calculado desde vértices reales; intersección
incluye bordes. Indexar con STRtree; nunca producto cartesiano17818x36467.
Incluir transformación completa del proxy en su bbox. Narrow phase por caras proyectadas; conservar intervalos t y
altura lineal baricéntrica, tangencias y coincidencias, no muestreo por pasos.
Cachear sólo instancias candidatas; no crear un STRtree de millones de caras.
Registrar también aristas completamente secas para acreditar el universo.
Unir intervalos solapados por unión geométrica, nunca por sumar longitudes ni
cerrar huecos pequeños. Agua nativa, charcas, piloto y proxy quedan separados,
con estados de evidencia explícitos, evitando doble cuenta en su unión.

Superponer caras Roadway del puente/presa y todos los demás soportes por
categoría. Donde exista agua y falte soporte de puente, emitir
WET_AXIS_WITHOUT_BRIDGE_ROADWAY, con intervalos y referencias; NO titular
automáticamente puente ausente, pues faltan intención de vado y calzada real.
Si hay soporte, medir altura sobre cada lámina y desnivel en juntas con terreno;
no dar PASS por cobertura XZ ni escoger sólo la cara de mayor altura.
Mantener todas las capas coincidentes/contradictorias y el estado INCONCLUSIVE
si un marco/triangulación/LOD requerido no está resuelto.
Medir desplazamiento lateral/ángulo del eje respecto al tablero como magnitudes,
sin inventar umbral de alineación. Detectar discontinuidades de cobertura exactas
en extremos y juntas, incluidos nodos compartidos entre cadenas.

El ancho pavimentado/importado no está vinculado a este grafo. Por tanto esta
unidad no certifica calzada completa, accesos, gálibo navegable, conducción ni
aceptación de un puente. No declarar c1 ni ningún defecto visual cerrado.

## C. Criterios y presupuesto

Una unidad nueva completa tiene: hashes y poses fuente trazables; inventario
total con complemento; cada cara/instancia considerada o excluida con motivo;
aristas/cadenas completas; ninguna dependencia omitida como PASS; resumen de
intervalos y contexto de Narva,kit118 y4789.51465/5516.52197. Coordenadas locales
XZ en metros, no WGS84. Contexto cercano no identifica automáticamente la foto.

Tests independientes: clipping Shapely contra solver analítico baricéntrico;
puente retirado, girado, desplazado, sumergido, hueco entre módulos, dos capas,
carretera cortada totalmente entre muestras, tangencia, extremo de cadena,
water-Roadway no confundido con puente, proxy rotado/centro no nulo,
malformación/omisión de modelo/LOD, rutas Windows/POSIX/case, quads ambiguos.
Mutaciones de pose/IDs/payload deben invalidar procedencia. Pruebas positivas
de cruce con tablero y agua, cruce diseñado sin agua, sin convertirlas en
aceptación universal. El umbral numérico existente1e-9m del residuo del solver se conserva. En juntas
reportar separación y ULP de las coordenadas float32 como medidas, sin inventar
umbral de aceptación ni afirmar que todas las juntas tendrán separación. Intervalos
inciertos se etiquetan, no se eliminan ni se fusionan para lograr PASS.

Antes de producción: revisión independiente de plan y código/fixtures;
una corrección conjunta por hallazgos reproducibles. Presupuesto por etapa
de extracción y superposición:120s/2GiB del PID real, outputs nuevos. Si la
estimación excede, particionar sin perder cobertura y revisar presupuesto antes,
no relanzar a ciegas. Revisión600s máx; falso PASS reproducido o fallo de recursos
detiene esa unidad y conserva evidencia para hipótesis nueva.
Publicar sólo código/tests/metadatos/informes validados, jamás payloads vanilla,
NPZ masivos ni historial privado. Sólo desde public-repo. Después el diagnóstico
alimenta un plan de reparación revisado, conservando protecciones y tolerancias.

## Adjudicación independiente — 28-10-2026

Fable5.1 por CLI nativo,247,797s, SOUND-with-fixes, entradas sin cambios,
Read/Glob/Grep, sin permisos denegados ni escrituras. Se incorporan sus fixes
1-7 y9 tras comprobar fuentes. Dos precisiones al fundamento del revisor:
- No se acepta la afirmación universal de que ninguna junta coincidirá: se
  medirán todas, conservando ceros reales y magnitudes sin nueva tolerancia.
- La supuesta cancelación exacta proxy-child.bc del punto8 es incorrecta en
  los datos leídos: long_straight tiene proxyY0.46019527316 y child.bcY
  -0.344225406647; la variante _2 tiene proxyY0.423894166946. No se anulan.
  Se conserva la orientación completa y CONDITIONAL_PROXY_FRAME; no inferir
  marco de motor de esa cancelación ni cambiar la fórmula para forzarla.

Anclas del grafo en el checkout PRINCIPAL (no este worktree):
C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev.
- tests/regional_foundation_roads_v6/reference.npz:
  94ecbca61bd5ba9ba61f89b765b043676a4a65703729a0b69009ae233984a1c2.
- evidence/regional-foundation-v1/road-grade-chains-v6.json:
  b31fb7d72398981ee98132ce59eab48c4aa404043718475fbb2725b13de1b824.

La etapaA produce prototipos con identidades de cara, semántica y matrices;
la etapaB los consume tras verificar. No ejecutar B sin cobertura de A y sus
estados inconclusos. Ninguna etapa declara reparación aceptada del mapa.

## Etapa A: revisión de código y puerta de ejecución

Fable5.1,186,859s, SOUND-with-fixes; fuentes congeladas durante revisión.
Se han incorporado en una única corrección conjunta:
- Manifiesto con barras Windows/POSIX y detección de alias duplicados.
- JSON/NPZ leídos una vez y ligados a su hash; recomprobación de manifiesto,
  entradas, mundo, paquetes y lector al finalizar el cálculo.
- Ruta completa de proxies por modelo y ranura, conservando ramas repetidas y
  jerarquías; el índice se publica con proxy-paths.json. No sólo última ranura.
- Pruebas de caras múltiples y degeneradas retenidas, Roadway hijo excluido del
  agua proxy, nietos y centros no nulos, manifiesto real y mutación de instancias.
- Residuo de coplanaridad guardado por cara. No se cambia1e-9 ni se transforma
  AMBIGUOUS en PASS. Las afirmaciones de residuo inevitable del revisor son
  hipótesis de riesgo, no mediciones; se registrará la distribución real.

23 pruebas fuente pasan. Producción A autorizada por este plan revisado:
una ejecución de deployed_surface_inventory_ev112.py,120s/2GiB, salida nueva
E:/DayZ-Baltic-Build/shape-repair-20261025/deployed-surface-prototypes-20261028.
No ejecutar B todavía: requiere revisar la precisión adicional siguiente.

## Precisión propia pendiente de revisión para B

Intersección XZ con una lámina no significa agua expuesta. Las placas pueden
prolongarse bajo una orilla seca. Antes de clasificar el eje como mojado,
particionar también por caras nativas y resolver Wmodelo(t)-Hnativo(t).
Separar BURIED_MODEL_WATER, EXPOSED_MODEL_WATER y contacto/equivalencia, con
sus intervalos y ambigüedades. No sumar bbox ni contar una placa enterrada como
carretera inundada. Probar placa ancha bajo orillas secas, W elevado sobre la
misma huella, cruce H-W dentro de una cara y placa estrecha entre muestras.
Esta ampliación no cambia A ni autoriza aún implementación/ejecución de B.

## Resultado de A — EJECUTADA_Y_VERIFICADA

Una extracción39,343s,539009caras/17818instancias.23tests fuente PASS.
Consumidor independiente44,031s: cobertura por cara/modelo y matrices exactas;
201pilotos contrastados contra MLOD fuente actual, máximo error de vértice0m.
Los primeros consumidores rechazaron por procedencia antes de geometría:
145hashes antiguos y19copias temporales distintas. Resolución verificada:
base201paquete46244e7f más19reemplazos Geometry-only conservando otras superficies
para obtener3d9550bf. La comparación final usa esa cadena y fuentes actuales,
no los PASS históricos rechazados. No ejecutar otra vez A ni sus consumidores.

43caras siguen AMBIGUOUS (maderas, tramos curvos/inclinados y piedra curva),
residuo máximo0,354368843m. No es prueba de defecto del mapa: falta resolver
triangulación del motor o calcular límites conservadores para ambos casos.
B permanece pendiente de revisión de agua enterrada y tratamiento de estas caras.
