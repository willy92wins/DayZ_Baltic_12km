# B1: separar altura de consulta y superficies nativas de agua

Estado: BORRADOR_PARA_REVISION; no implementar ni lanzar aún.
Codex ejecutor/integrador por petición viva; Fable revisor independiente.
Padre congelado: ev112-dry-road-native-discriminators-20261028.md, unidad A
publicada en bf9322d. Traza P9/P10/P11/P14 y nueve observaciones humanas.

## Decisión de alcance y motivo

Los 43 fallos de agua conservan B anterior=candidato en su soporte local.
Esto no valida B ni las etiquetas de agua; el referente de producto sigue
INCONCLUSIVE_PRODUCT_REFERENCE. No se autoriza corregir el mapa con este resultado.
La API nativa documenta que surface puede devolver agua O superficie de objeto;
depth y surface sin fake wave no tienen un contrato de equivalencia demostrado.

Se divide el diseño B del padre: B1 mide agua a distintas alturas. B2 abordará
oclusores y RV700/723 cuando exista un control independiente del espacio libre
en los orígenes bajos. A no extrajo geometría de árboles, por lo que no puede
certificar esos orígenes; lanzar rayos bajos ahora y llamarlos válidos sería
un falso PASS. B1 no elimina ese requisito ni resuelve colisiones.

## Hechos y contratos verificados

[EXACT] P:/scripts/3_Game/global/game.c:923 GetObjectsAtPosition(vector,float,
out array<Object>,out array<CargoBase>); :1176 SurfaceY(float,float);
:1178 SurfaceRoadY3D(float,float,RoadSurfaceDetection); :1196 SurfaceIsSea;
:1197 SurfaceIsPond; :1198 GetWaterDepth(vector); :1199-1202 documentan
GetWaterSurfaceHeightNoFakeWave(vector) y GetWaterSurfaceHeightWithFakeWave(vector).
Ambas buscan agua u objeto bajo el punto, ignorando terreno; no se deduce de ello
que sus resultados sean idénticos a profundidad ni que se separen por un seno.

[EXACT] missions/BalticVisualProbeV1.BalticTrial/init.c:114-128 carga WRP,
espera100ms y refresca en el fotograma de consulta. Conservar ambas cargas.
[EXACT] R/dry-road-native-discriminators-a-20261028/selected-points.json tiene
115 IDs:47 fallidos,21 inciertos y47 positivos elegidos antes de calcular A.
R = E:/DayZ-Baltic-Build/shape-repair-20261025.

## Hipótesis que se intentan distinguir

H1 [HIPÓTESIS]: parte del contraste depth/surface procede de consultar bajo B.
H2 [HIPÓTESIS]: parte del contraste procede de fake wave en depth.
H3 [HIPÓTESIS]: surface devuelve un objeto distinto de la lámina prevista.
Una diferencia entre llamadas no prueba por sí sola causalidad. Se necesitan
controles positivos y simultaneidad; si quedan explicaciones equivalentes, se
conservan. La ausencia de diferencia tampoco prueba la semántica general.

## Unidad B1, sólo diagnóstico

[DESIGN] Nuevo productor MissionServer, sin clientes/RPC/jugadores/objetos nuevos,
sin cámara, movimiento ni cambios de geometría. Datos sólo servidor; salida en
perfil del run propio. Nuevo nombre de misión/log para no mezclar sondas.
No modificar misión, consumidor ni resultados2658, ni el piloto guardado.

Conservar los115 IDs y su expectativa original, no seleccionar después de medir.
Tres rondas completas de115 puntos en orden fijo:345 registros. Cada punto
refresca WRP y consulta todos sus canales en un único OnUpdate. Registrar reloj
antes y después, ronda/ID, coordenadas usadas, ground, Roadway, sea/pond y cuenta
de objetos. Si las consultas cruzan el reloj del motor, marcarlo explícitamente;
no simular simultaneidad ni descartar la fila para conseguir consistencia.

H es SurfaceY medido; B es effective_bed de A fijado por hash, o H si es null.
Wref es water_ext de A si existe; sólo estímulo geométrico, NO referente de producto.
Definir S=max(H,B) sin reclasificar el punto. Tres orígenes para profundidad:
Y0=H+0.01, Y1=S+0.01, Y2=max(S,Wref si existe)+0.25. Echo de las coordenadas
efectivamente usadas y de cada origen; no inferir las alturas a posteriori.
Consultar ambas surface nativas desde H+100 y S+2. Estas consultas bajas son
datos opacos: NO rayos de aceptación, ni garantía de origen libre de sólido.
No derivar una cota de agua aceptada de ellas sin aislar qué superficie devuelven.
Mantener la misma fecha, tiempo meteorológico y tres referencias marinas que el
productor2658. No variar parámetros ni podar/mover árboles.

## Consumidor y evidencia

[DESIGN] Preparador separado fija hashes de A, resultado2658, productor, CSV,
engine, misión,4PBO y su propio código. Consumidor estricto: cabecera/version,
BEGIN345, IDs/rondas exactos y únicos, orden fijo, datos finitos, vector3 completo,
booleans0/1, clocks no decrecientes, END345 sin truncación ni registros extra.
Los ecos de posición deben coincidir con los estímulos serializados float32:
se usa la banda existente XZ0.01 sólo para la precisión del log nativo, no para
desplazar puntos ni relajar geometría. Orígenes Y también deben concordar con
las operaciones float32 del productor dentro de0.01m, nunca usarlos como test
de calidad física. Ground conserva0.01m; Roadway conserva0.03m contra A.
Estas tolerancias no sustituyen ni relajan agua0.05m, RV0.03m o Bullet0.01m del
consumidor original. B1 no emite PASS de esos canales ni los reevalúa.

Registrar por ID/ronda: nfHigh,nfLow,fakeHigh,fakeLow; depthY0,Y1,Y2;
diferencia fake−nf por origen; depth−(surface−Y) para ambas versiones y alturas;
relación con H,B,Wref,ground/Roadway y estados originales. Mostrar todas las
filas, incluido signo/variación temporal; no elegir sólo la combinación que ajuste.
Un reloj que cambie entre llamadas se conserva como confusor; toda conclusión
que requiera simultaneidad queda INCONCLUSIVE en ese grupo.

Estados: CAPTURE_COMPLETE_DIAGNOSTIC_ONLY si esquema, cobertura, vínculo y
referencias Ground/Roadway decisivas coinciden; INCONCLUSIVE_DIAGNOSTIC si
algún confusor/cobertura física sigue abierta; INVALID_EVIDENCE ante esquema,
hash, identidad, finitud o recuento inválidos. El informe original siempre FAIL,
producto INCONCLUSIVE_PRODUCT_REFERENCE, B2 pendiente, nunca mapaPASS.
Las20 referencias Roadway ya inciertas del padre se conservan como inciertas;
no se exige que coincidan con una altura que el padre no puede decidir.

## Puertas antes de lanzamiento

Revisión del plan, después implementación y revisión de productor/consumidor/
preparador/lifecycle con pruebas analíticas independientes y negativos:
log completo345; faltaID; duplicado; ronda ajena; orden alterado; NaN/Inf;
vector incompleto; bool inválido; END ausente; conteo incorrecto; coordenada
u origen incorrectos; reloj reverso; cambio de reloj conservado como confusor;
deriva de misión/CSV/paquete/engine/A; recibo de otro run; residuo negativo y
positivo conservados; positivo con misma etiqueta original y fallo sin reclasificar.
Dato ausente no se convierte en cero ni PASS. Medir exactamente un archivo en
script_validator, no aceptar0archivos. Ese lint no prueba compilación del motor.

Presupuesto antes de ronda1: diseño/revisión600s; preparación offline120s/2GiB;
test suite120s; una corrección por contraejemplo ejecutable, sin barrido de
parámetros. Revisión final600s. No DayZ en esta activación; futura admisión FIFO
oficial hasta600s, ejecución/captura180s desde disponibilidad del servidor,
heartbeat y cierre oficial de nuestro run. Si falta cobertura, diagnóstico
INCONCLUSO y propuesta concreta del dato faltante; no repetir todo automáticamente.
Antes de la admisión futura: plan/código revisados, hashes desplegados verificados,
preflight vigente y gate de inputs; sin sondear ocupación ni preadquirir lease.
No publicar aceptación del mapa ni integrar candidato por completar esta captura.
