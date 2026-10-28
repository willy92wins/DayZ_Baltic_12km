# Contrato completo de la sonda de lecho seco

Estado: REVISADO_PARA_PREPARACION_Y_SONDA_LIMITADA; ejecución pendiente de sello y gate.
Padre: ev112-dry-road-native-probe-20261028.md; fuentes selladas en
dry-road-effective-domain-20261028. El padre queda congelado como entrada.

## Evidencia y alcance

Discriminador nativo1bb6c4f6:16controles,8GROUND enterrados/8BED expuestos.
RV alcanzaH, Bullet BUILDING alcanzaB aun enterrado. Sin aceptaciónglobal.
La lectura efectiva10.281s conserva2658IDs:2506secos,152mojados,20inciertos
(15frontera numérica+5testigosfuera trasfloat32).39puntos tienen además lecho
cs_kit_118_0012. No asumirque Roadway ajeno equivale a Geometryverificada.
Visual−water_ext llega0.25m: usar textura de Roadway real, nunca Visual−constante.
Se reemplazó sólo Roadway de19394363 por fuente del candidato verificado;
200modelos/agua/H/WRP fijos. Todo esto es descubrimiento, noPASSnativo.

## Consumidor propuesto

[DESIGN] tools/quality/dry_road_native_consumer_ev112.py separa porID cinco
canales:Ground,Roadway,agua,RV,Bullet. Ground<=.01; Roadway/RV<=.03; agua<=.05;
rayosXZ<=.01; margenBulletcalibrado<=.01. No cambia ninguna tolerancia.
Roadway=max(H,todascarasRoadway); RV=max(H,todascaraslecho), no lámina deagua.
Identidad RV admite vacío cuando devuelve terreno; en lecho sólo modelos
presentes en la proyección. Un oclusor ajeno produce fallo, no se oculta.
Bullet: distancia proyectada desde B independiente a contacto con normal n,
dot(contact−[x,B,z],n_normalizada), contrastada con margenvanilla fresco.
Esto es hipótesis geométrica verificable; esquinas/solapes pueden necesitar
un discriminador si falla, no aumentar el margen. Normales ascendentesunitarias.
La muestra16 demostróqué consulta cada API, no toda esta fórmula geométrica.

Incertidumbre de agua afecta sólo agua/Roadway; Ground siempre comprobado.
Fuera de malla o superficie ambigua => canalescolisión INCONCLUSOS, IDsretenidos.
FAILsi cualquier canal falla; INCONCLUSIVE_COVERAGEsi alguno incierto; sólo
SERVER_PROBE_PASSsi todos loscanales de todosIDs decisivos pasan. No aceptación
visual,CCT,conducción,RAM,resto del río o mapa por ningún resultado deestaunidad.

## Preparación y ejecución posteriores a revisión

Derivar bed_shapes de face-info y roadway_faces, excluyendo water_faces;
conservar fuentes/multiplicidad, no sólo lista de puntoseditados. Recalcular
alturastriangulares al recibir posicionesfloat32, ya verificadasen r2. Vincular
fuentecompilada/MLOD/numérica porlaspruebas selladas previas, y todosoutputs.
Calibración V3 archivada en evidence/v31-pond-layer-2026-10-13/ev112/
visual-review-20261023/kit7-contact-repair-20261026/producer/calibration/init.c.
La misión actualV4 no coincide conelparserV3: no intercambiarlas. FuenteV3
intacta; controlesvanilla289+espaciovacío289, .038<media<.042 y rango<.002.
No usar calibración histórica como si fuera nueva. Dosrunsnuevos:calibración
y soncacompleta,modnuevo o modexperimental sellado sin cambiarlo duranteelrun.
ProducerVisualV3intacto, CSV2658IDs, 22columnas estrictas, relojcreciente.

Presupuesto: preparación300s/2GiB; pruebas120s; revisión600s; FIFO600s por
activación; arranque300s; captura900s para2658puntos. Una ejecución por misión.
Si falta materialización, binder o identidad, no entrarFIFO. Reutilizar ciclo
oficial probado en16puntos:aceptaciónpre-FIFO,adopciónexacta,heartbeat,
PID/creationtime/mission/engine/PBO,logfresco,cierreoficial incluso si terminó,
release y estado terminal. Sinoccupancycheck/prelease/takeover/camera_set.

## Contrapruebas implementadas, todavía sin binder nuevo

15tests de canales: enterrado/expuesto positivos, agua/altura/Roadway negativos,
Bulletcomparado conB,noH,identidades/rayo/calibración, IDs, incertidumbrecon
falloGround y puntosfuera conservados. Son sintéticos; aúnfaltan controles de
evidencia nativa real y revisión independiente. No publicarcomovalidadocompleto.

## Adjudicación Fable236.625s, 28-10

SOUND-with-fixes,identidadFable5.1,0denegaciones,entradas estables al revisar.
Aceptado:5puntosfuera de malla mantienen Roadway INCONCLUSO también; agua
sigue separada. No sustituir estos puntos ni considerarlosPASS.
Se añade foreign_bed_support para geometría ajena sin demostrar. En este
dominio se tomó la alternativa más fuerte: ODOL real de0012 leído del PBOef229,
Roadway seco y techo Geometry superpuestos completamente,error0, sin cambiar
tolerancias. Prueba0.625s en dry-road-full-review-claims-20261028/report.json.
Los39puntos sí tienen referente Geometry verificado. No extenderlo a otro modelo.

Mismo discriminador confirma1866caras de soporte triangulares; no hay quads
en este dominio. Preparación exige esa precondición; no hace falta inventar
otra diagonal. Para futurosquads se mantiene la exigencia de discriminarambas.
Un punto1769tiene W−H=0.00246934m y el productor mide depth enH+0.01m.
Antes deejecutar, clasificar como water_depth_numeric la banda [-0.01,+0.02]
deW−H, derivada deH±0.01ya exigido yoffset0.01delproductor. Es cobertura
INCONCLUSA, no tolerancia nueva, noPASS y no modificación del mapa. Roadway
permanece comprobable. Registrar el conteo exacto alpreparar; ningún IDseelimina.

Se añaden contrapruebas de normalno unitaria/descendente,geometríaajena,agua
somera,carasambiguas,identidadcoincidente,wetenterrado yshapeausente. Fixture
nativo16 +sietenegativos pasan con calibraciónHISTÓRICA etiquetada; sirve como
regresión de código, NOcomo calibraciónfresca ni otroPASSmotor.
La revisión noaprueba lanzamiento ni binder, que siguenpendientes.

## Capa de ejecución implementada, pendiente de revisión

R/prepare_dry_road_full_native_20261028.py crea mod y dosmisiones nuevos;
exige adjudicación explícita con hashes antes de crear outputs. R/consume_...
vincula ambosruns porPID/creación,misión,engine,cuatroPBO ylogfresco. La segunda
medición exige calibraciónanterior deOTROrun pero mismoengine/paquetes.
R/check_dry_road_full_gate_20261028.py exige sello antesdeFIFO y hash deesa
calibración para faseprobe; rechaza un outputconlaunch yaexistente.
R/finish_dry_road_full_native_20261028.js usa lifecycleoficial con adopción
exacta/heartbeat/cierre/release. R/capture_dry_road_full_native_20261028.ps1
captura cabecera/END estricto y sólo proceso propio,deadline900s.
22pruebascanales y8controlesbindingpreFIFO pasan,6lifecycle simulados pasan.
Scripts nuevos aún NOejecutados para preparar/desplegar/lanzar. El próximo
revisor comprueba esta capa; su terminación no equivale a aprobar hallazgos.

## Binder revisado y contraprueba adversarial

Fable402s,SOUND-with-fixes,0denegaciones,entradas estables. Corregido conteo
sellado de incertidumbre (21IDs, uno nuevo1769), clave de lanzamiento porfase
y guard de modo. Se conserva cualquier fallo depreparación paraevidencia;
un reintento requiere diagnóstico y namespace nuevo, no reusar ni borrarrestos.

La contraprueba independiente BINDER_CONTROLS_FOUND_GAP sí encontró un camino
de falsaaceptación que la revisión no detectó: cambiar margin_m del resultado
decalibración después depre-FIFO aúnpasaba. Corrección: la salida delgate lleva
accepted_sha256 ycalibration_sha256, queel caller debe incluir en launch.json;
coordinador los comprueba duranteelrun yconsumidor los exigeal cerrar. Cambiar
result.json dela calibración o sello despuésdelanzar invalida la evidencia.
Los mismos siete negativos deidentidad/orden/calibración se repiten contra elfix.
Noafirmar100%certeza por acuerdo de modelos ni porunreporte SOUND.

Adjudicación final Codex:22tests de canales,9binding(incluye positivo,8negativos),
8gatespreFIFO y7lifecycle pasan. Cambio devalorcalibración y deaccepted tras
lanzamiento ya se rechaza. La capa está lista para las dos ejecuciones acotadas
autorizadas porGuillermo, condicionadas al sello y sus hashes. Ningún permiso
humano nuevo requerido.21IDsconincertidumbre se mantienen; el resultado completo
no podrá serPASSmientras sigan sin resolver. Un fallo decisivo dominaINCONCLUSO.
