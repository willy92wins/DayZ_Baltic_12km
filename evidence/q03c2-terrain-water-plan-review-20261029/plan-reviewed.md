# Q03C2 — partición conjunta del lecho frente a terreno fuente y agua seleccionada

Estado: BORRADOR_PENDIENTE_DE_REVISION. Codex planner/integrator y executor local
explícito para este corte una vez revisado; una lane externa Muse CLI nativo.
No nuevo council. No cambia producto, geometría, terreno, colocaciones ni P:.

## Resultado que desbloquea [DESIGN]

Medir, para las1520 caras completas de kit118_0000 ID19394363/model3579/pose13844,
qué parte está por encima, en contacto o debajo del TERRENO FUENTE, cruzada con
las tres clases de agua seleccionada Q03C1. Entregar nueve áreas racionales por
cara y testigos de altura/celda, para elegir después una reparación fundada.
No sumar restas independientes de áreas: el solape conjunto exige una partición
geométrica. No llamar visible a lo que puede ocultar otro modelo, vegetación o
agua nativa. No acotar al corredor histórico8m ni afirmar pavimento12/9m medido.
Q03/Q11 y P9/P10/P11 son la intención; Q05 añadirá huella vial y ambos accesos.

## Anclas comprobadas [EXACT]

Q03C1 consumido:201pilotos/4760water,1520triples verificados por sustracción frente
a arreglo de rectas. Sumatorio CON multiplicidad37.45741951018598m² cubiertos,
3.0365742489692926m² con agua sólo inferior y457.8056221008301m² sin huella
seleccionada. No equivale a exposición; nueve rechazos humanos siguen abiertos.
Contrato43c95b5d, consumidor y métricas se fijarán completos en contratoQ03C2.
Los helpers/source snapshots Q03C1/Q03B6/header/archive quedan sellados.

tools/quality/pilot_visible_exposure_ev112.py:24-26 fija SHA del terreno815ef8b7
y agua nominal084171b0. Líneas137-146 leen heights y exigen2048x2048; esta nueva
unidad sólo añade TERRENO, no agua nominal ni sus planos. El NPZ fuente exacto
E:/DayZ-Baltic-Build/shape-repair-20261025/river-kit7-merged-byteexact-20261026/terrain-buried.npz
tiene12875883bytes observados por stat; SHA histórico completo:
815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40.
merge-verification.json de esa carpeta conserva terrain_byte_exact y el pin.
No demuestra alturas del WRP decodificadas ni identidad actual del motor.

tools/quality/pilot_surface_refinement_ev112.py:7-8 define OFF=(00,01,10,11)
y TRI=(0,1,3)/(0,2,3). Líneas64-80 usan grid6, top=(n-1)*6,
XZ=(6*c,top-6*r), diagonal NW-SE. Líneas91-99 distinguen B-H positivo,
negativo y contacto planar idéntico. Su aritmética float y tolerancias NO se
importan; sólo anclan convención histórica fuente, no prueba de triangulación
compilada. La medición propuesta se etiqueta SOURCE_GRID_NW_SE_ASSUMPTION.
source_grid del NPZ piloto es la malla del lecho; NO es el campo de alturas.

evidence/pilot-visible-exposure-20261028 conserva23.9566664m² relativos a un
corredor±4m. Sus CLIs/censos201modelos están consumidos; no se ejecutan ni se
reclasifican. Esta nueva dimensión conjunta exacta se limita a un lecho completo.

## Contrato y carga acotados [DESIGN]

Antes de autoría geométrica: pins Q03C1 contrato/consumer/manifest/métricas y
recibos, Q03B6/e967 y todos sus helpers, terreno/merge-verification y anclas.
Reutilizar el enlace histórico3d955 y pilotos YA MUNDIALES, sin transformar.
No PBO/P3D/WRP nuevo ni censo global. Aceptación del terreno fuente sólo porSHA.

Dentro de la preparación del contrato se autoriza una inspección de cabeceras
ZIP/NPY del único NPZ terreno pinado, sin cargar arrays ni medir geometría:
snapshot/identidad/hash, máximo16MiB almacenado,35miembros,16384B porheader,
128MiB expandido porarchivo,262434599B total de sesión. Cerrar TODOS los esquemas
observados y su cota antes de código; heights debe ser finito f4/f8 y2048x2048.
No asumir otros nombres/descriptores ni mmap. Si el archivo no cabe, rechazo y
plan propio, no ampliación. Inspección60s/256MiB única, recibo/hash previos; no
otra fase genérica de lectores. Arrays sólo tras revisión de código y suite.

Una sesión acumulada por caminante para201pilotos y terreno, límites originales.
Retener heights como array y reservar sus bytes reales antes de asignar; no
convertir toda la cuadrícula a Fraction ni crear8millones de caras. Generar sólo
celdas que intersecten la proyección de cada bed por índices enteros acotados.
Retención lógica de arrays64MiB como presupuesto NUEVO explícito de esta unidad
(incluye heights f8=32MiB y copias bed/water<=16MiB); RSS512MiB separado.
No cambia cap de archivo/sesión ni el presupuesto racional por cara.

## Algoritmos y significado [DESIGN]

EjeXZ y alturaY. Cadafloat fuente se convierte exactamente a racional binario.
Por cara: intersectar con triángulos fuente de celdas cerradas. Cara fuera de
[0,12282]^2 rechazada, nunca clamp de geometría. Fronteras de celdas compartidas
tienen área0; rango de celdas conservador incluye borde final sin indexar2048.
Suma de partes terreno debe ser EXACTAMENTE el área bed; no tolerancia.

Productor: sustracción/intersección convexa propia. En cada parte terreno cortar
por B-H; si plano diferencia idénticamente0 toda el área es CONTACT, si no la
recta de igualdad tiene área0 y separa ABOVE/BELOW. En cada región cruzar unión
de footprintwater y unión(W>=B) por sustracción comoQ03C1, con reservas globales
por cara de todas listas vivas. No sumar pares superpuestos como unión.

Consumidor: recorrido propio de índices/celdas fuente desde sus lecturas; para
cada intersección construir arreglo de rectas de lados, B-H y W-B, clasificar
puntos interiores racionales. No importa geometría del productor ni usa sus
celdas/pares para reducir el denominador. I/O, NumPy/zlib y Budget compartidos
declarados; sustracción vs arreglo siguen independientes. Reusar primitivas
selladas está permitido; no modificar ni relanzar CLIs Q03C1.

Nueve slots=(ABOVE_SOURCE,CONTACT_SOURCE,BELOW_SOURCE) x
(SELECTED_WATER_AT_OR_ABOVE,SELECTED_WATER_ONLY_BELOW,NO_SELECTED_FOOTPRINT).
Igualdad W==B sigue cubierta; igualdad B==H ocupa CONTACT sólo en región planar.
Por cara sum(nueve)=áreaXZ y cada suma marginal de agua debe igualar EXACTAMENTE
el tripleQ03C1 pinado. No tomar esas igualdades como sustituto del consumidor.
También mínimo/máximo B-H en vértices de la partición fuente y IDs de celda/cara.
Los resultados NO prueban falta de agua mundial, visibilidad/render, volumen de
relleno, navegabilidad, exposición de una fotografía ni aceptación del mapa.

## Oráculos externos y negativos [DESIGN]

Congelar geometrías/resultados literales antes de código, no esperados del
productor. BasebedXZ(0,0),(12,0),(0,12),B=1,área72. H=0/1/2 coloca72 en
ABOVE/CONTACT/BELOW; combinar con watercompleta superior/inferior/ausente.
Plano H=x/6: ABOVE54/CONTACT0/BELOW18. Con W=x/6, ABOVE con agua sólo inferior54
y BELOW con agua a igual/mayor altura18; los otros siete slots0. No producto de
marginales. Derivar a mano cada fixture exacto antes de congelar.
Pico sólo interior a una celda (vérticesbed no detectan), cambio de diagonal,
costura exacta, esquina/borde final delgrid, varias celdas, agua deotro modelo,
duplicidad deagua, winding/permutación/subdivisión y signedzero.
Mutantes: Y/Z intercambiados, fila invertida, diagonalcontraria, una celdaomitida,
doblecelda, terreno pinadocambiado, fuente_grid confundido, epsiloncerca de0,
contacto clasificadoabove, watermarginalalterado, IDs/cifrasbool, descriptor,
presupuesto antes deoperar, parcialpromovidoFULL y co-mutación informe/recibo.

## Presupuestos, puertas y salida [DESIGN]

Preparacióncabeceras60s/256MiB única; Codexexecutor local900s contrato/oráculos+
código (máximo adaptador + productor + consumidor + test). Reviewexterna180s
incluye contrato; suite120s/256MiB. Una corrección180 por repro cerrado y una
recuperación180 por dictamen ausente, no bucle infinito. Sin aprobación ficticia.
Una producción120s y consumidor120s/512MiB,32MiB salida, sin reintentos internos.
Mantener4096bits/100000operaciones/1024fragmentos/8192vértices porcara y caminante;
contabilizar todas partes acumuladas porcara, no reset porcelda. Si no cabe:
RESOURCE_INCONCLUSIVE/parcial, no subida ni descarte de área paraPASS.

Payload y receiptSHA/longitud/secuencia fsync, prefijo sin huecos comoQ03C1.
FULL sólo1520caras con nueve áreas verificadas/marginales/IDs/alturas; cualquier
degenerado/estado de recursos/cola sinterminal impideFULL. Estado final
MEASURED_SOURCE_TERRAIN_SELECTED_WATER_ONLY o VERIFIED_PARTIAL_SOURCE_PARTITION.
terrain_source_evaluated=true sólo tras medición; compiled_terrain_evaluated,
exposure_evaluated,native_acceptance,map_repaired=false. Humanresolved0,C1NOT_REVIEWED.

Después: testigos para decisión técnica de transiciónlecho/terreno conservando
protecciones; Q05 huella vial real y ambosaccesos pendiente de poses/pivote.
Q08/Q17 referentes independientes, Q02Bángulos y carreteras siguen abiertos.
