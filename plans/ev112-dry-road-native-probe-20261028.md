# Sonda aislada del lecho seco y su extremo en carretera

Estado: SEMANTICA_OBSERVADA; preparación del consumidor completo y revisión pendientes.
Traza: P7/P9/P10/P11, KIT118-VIS-02 y plan
ev112-dry-road-compiled-pair-20261028. Codex ejecutor/integrador;
Fable revisión independiente antes de ejecutar. Ningún cambio de producto.

## Alcance y precondiciones

Comprobar en servidor la reparación numérica93168efe/MLODd13069d5/ODOL351424ab
del primer modelo kit118. Sólo82alturas del lecho seco y sus203prismas cambian.
No acredita la naturalidad de los ríos, el resto de lechos salientes, conducción,
RAM, C1 ni aceptación visual. ST y area_over_tex siguen condicionales hasta
contraste visual; no convertir su dependencia geométrica en fórmula probada.

Requiere consumidor compilado, mutantes y PBO201 terminados y revisados.
Composición debe preservar200modelos/config/prefijo/orden; nada de diagnósticos
Y-only/N-only. Crear una carpeta de mod NUEVA, no sustituir previews existentes.
Mundo10e09e3f y agua97edcafe son los de la prueba física previa Kit7Overlap;
validar sus bytes y origen antes de copiarlos, junto al nuevo PBO201.
La sonda usará navmesh_data_server=true, sin probar navegación o memoria normal.

## Productor y consumidor existentes

[EXACT] missions/BalticVisualProbeV1.BalticTrial/init.c: OnUpdate carga referencias
WRP antes de medir SurfaceY, agua, SurfaceRoadY3D, RV Geometry y Bullet BUILDING;
captura tres referencias de marea en el mismo frame. Reutilizar productor sin
cambiar sus APIs. tools/water/eval_visual_probe_v31.py: parse exige22campos,
IDs únicos, BEGIN/END y reloj creciente; judge separa agua, suelo, Roadway y
colisión. calibrate mide margen Bullet con objeto vanilla y espacio negativo.
Volver a anclar firmas/enum en P:/scripts antes de preparar la misión.

[DESIGN] Casos derivados de fuentes independientes: terreno815ef8b7 con diagonal
nativa, caras Visual/Roadway compiladas a poseWRP real y agua efectiva preservada.
Censar todos los vértices y centroides del primer modelo, sin eliminar los que
fallen; incluir centroides de las203caras cambiadas y testigos GEOS del corredor
viario, ambas juntas y controles mojados/secos inmutables del mismo modelo.
Deduplicar por coordenadas cuantizadas tal como llegan al CSV, conservando todas
las etiquetas y multiplicidad de cobertura. Recalcular expectativas EN ESAS
coordenadas, no en centroides sin redondear. Clasificar puntos ambiguos como
INCONCLUSO, nunca descartarlos o llamarlosPASS. Contar antes de fijar presupuesto.
Incluir controles de regresión ya existentes que intersecten el modelo modificado;
comprobar si sus expectativas cambian por el descenso legítimo de lecho.

No usar sólo lista de vértices editados como universo de prueba. La validación
de área continua corresponde al consumidor offline independiente; la sonda
es muestreo mecánico sobre artefactos reales. No hereda resultados antiguos.

## Criterios y presupuesto propuestos

Calibración vanilla nueva:289puntos porgrupo, espacio negativo sin impactos,
margen en el intervalo vigente0.038..0.042m, dispersión<0.002m.
Suelo<=0.01m, Roadway/RV<=0.03m, agua<=0.05m, margen Bullet<=0.01m,
rayos XZ<=0.01m. Sin rebajar límites del consumidor existente. Agua y estados
seco/mojado conservados; todos los IDs y checks deben cumplir. Crash sólo si
se demuestra muerte del proceso; evidencia incompleta=>INCONCLUSO.

Preparación300s/2GiB, pruebas negativas del consumidor120s. Dos ejecuciones
(calibración y sonda), admisiónFIFO hasta600s poractivación, arranque300s,
medición máximo900s inicialmente sujeto al conteo. Un fallo exige discriminador
concreto y nuevo plan antes de repetir; no retocar umbrales ni excluir puntos.

Usar dayz-test-ingame y lifecycle oficial: dayz_test_run directo on_busy=queue,
takeover=false; sin prelease ni sondeo de ocupación. Adoptar sólo run propio,
verificar proceso/fecha de creación, misión, hash de ejecutable y todos los PBO
cargados. Renovar lease durante operaciones exclusivas; cerrar run exacto y
liberar oficialmente. camera_set vetado, sin cliente ni intervención humana.
Logs deben quedar vinculados al run y a su reloj, con cierre terminal demostrado.

## Cierre de esta unidad

Registrar resultado físico limitado, evidencia y límites; publicar únicamente
código/evidencia validada desde public-repo. Conservar nueve regresiones, C1,
RAM y council ampliado abiertos. La próxima clase de reparación procedural
se elige a partir del censo existente, sin repetirlo ni fingir cierre global.

## Adjudicación de Fable y descubrimiento, 28-10
Revisión143.343s,SOUND-with-fixes, identidadclaude-fable-5-1,0denegaciones.
Dominio descubierto una vez(r2):4134etiquetas→2658posiciones float32 únicas,
819vértices,1520centroides de lecho,24deagua,1771testigos viarios. Los82vértices
y203centroides modificados son secos interiores.42caras deagua de5instancias,
flags0. Algunas inclinadas: primera lectura abortó suponiendo horizontalidad;
r2interpola por triángulo, sin modificar ninguna geometría.
15posiciones se acercan a frontera dentro de la semidiagonalfloat32;5testigos
quedan fuera de la malla trasround-trip. No eliminarlos. La banda propuesta de
1ULP no prueba la semántica interna del motor: se conserva como incertidumbre,
sin tolerancia nueva. Tampoco toda junta entre dosmodelos es automáticamente
ambigua: comprobar alturas/continuidad antes de clasificarla.

Rechazar SERVER_PROBE_PASS con filas INCONCLUSAS como cierre de la unidad;
el binder debe mostrar resultados decisivos y pendientes, midiendo todos losIDs.
Si falla un decisivo, FAIL; evidencia incompleta, INCONCLUSO. No cambiar etiquetas
para ocultar fallos. Un solo modelo3579/instancia19394363 confirmado.

Dato que obliga a un discriminador antes de la sonda completa:1322posiciones con
B<H−0.03m; la prueba anterior6801PASS contenía CERO. No hay evidencia suficiente
para imponer max(H,B) enSurfaceRoadY3D. Próximo plan acotado:
ev112-buried-roadway-semantics-20261028.md.16controles para observar la consulta,
sin rebajar0.03m ni declarar esta semántica probada por la fórmula offline.
Después se revisa el binder/expectativas completos con el resultado real.

## Evidencia nativa y siguiente discriminador, 28-10

Run1bb6c4f6,16IDs completos:8enterrados devuelvenH,8expuestos devuelvenB.
RV veH en enterrados, mientras Bullet BUILDING ve el lecho B. No comparar
Bullet−RV allí como margen: comparar Bullet con la cara B independiente y
calibración vanilla fresca. El consumidor completo aún no está aprobado.

Relectura de las fuentes detecta un error en el descubrimiento de expectativas:
el inventarioA kind1 es Visual, no water_ext Roadway. El dominio r2 nombró esa
altura water_ext. No se ha usado para aceptar agua en motor: los16controles
eran secos fuera de todas las caras. Corregir desde las secciones/texture del
Roadway real, sin asumir una resta constante ni modificar geometría.

Próxima lectura acotada120s/2GiB: superponer TODOS los Roadway del inventarioA
en la caja, reemplazar únicamente las caras de la instancia19394363 por el
candidato verificado y extraer agua por texture water_ext.paa. Conservar
2658IDs, todas etiquetas y puntos fuera de malla; contar interferencias/juntas,
fronteras numéricas y delta Visual−Roadway. No preparar misión completa hasta
que estas expectativas y el consumidor estén revisados. Calibración V3 archivada
verificada, pues la misión actual V4 no coincide con el consumidor V3.
