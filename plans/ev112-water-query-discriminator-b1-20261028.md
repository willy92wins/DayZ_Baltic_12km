# B1: separar altura de consulta y superficies nativas de agua

Estado: REVISADO_PARA_IMPLEMENTAR_DIAGNOSTICO; lanzamiento todavía no autorizado por gate.
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
:1178 SurfaceRoadY3D(float,float,float,RoadSurfaceDetection); :1196 SurfaceIsSea;
:1197 SurfaceIsPond; :1198 GetWaterDepth(vector); :1199-1202 documentan
GetWaterSurfaceHeightNoFakeWave(vector) y GetWaterSurfaceHeightWithFakeWave(vector).
Ambas buscan agua u objeto bajo el punto, ignorando terreno; no se deduce de ello
que sus resultados sean idénticos a profundidad ni que se separen por un seno.

[EXACT] missions/BalticVisualProbeV1.BalticTrial/init.c:104-116 carga WRP,
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
booleans nativos true/false, clocks no decrecientes, END345 sin truncación ni registros extra.
Los ecos XZ deben volver al MISMO float32 que el estímulo serializado. Para Y,
se propaga sólo el error del formato nativo (seis decimales en vectores, seis
cifras significativas en escalares) y del redondeo float32 de la suma. La fórmula
final se documenta en la adjudicación de código; no usar0.01m para identidad.
Ground conserva0.01m; Roadway conserva0.03m contra A.
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

## Revisión independiente y adjudicación, 28-10

Fable5.1 CLI nativo,173.110s, SOUND-with-fixes. Entradas intactas, FIN_REVISION,
sin denegaciones ni herramientas de escritura. Recibo en
R/water-query-b1-plan-review-20261028/completion.json y copia exacta plan-reviewed.md.
Esta revisión sólo habilita implementar B1 tras las precisiones siguientes;
no sustituye lint/tests/revisión de código ni autoriza admisión del motor.

1. Aceptar clasificación numérica por consulta: WATER_REF si |v-Wref|<=0.05,
   BED_REF si |v-B|<=0.03, GROUND_REF si |v-H|<=0.01; todos los matches se
   conservan, etiqueta AMBIGUOUS si hay varios y OTHER si ninguno. Un valor
   fake desplazado puede no coincidir con ninguno. Estas clases no identifican
   el objeto ni establecen agua accesible. H3 sigue INCONCLUSIVE hasta tener
   evidencia independiente de identidad; se rechaza la afirmación de que esta
   clasificación por sí sola resuelva H3.
   Registrar GetShapeName/GetPosition de la instantánea de objetos ya cargada
   a40m. No añadir una consulta de2m que cambie el estado de carga ni atribuir
   al punto la forma más cercana. Centros cercanos tampoco prueban intersección.
   Registrar objeto null/forma vacía y conservarlos como cobertura incompleta;
   nada de descartar entradas silenciosamente. Antes de implementar, verificar
   firmas Object.GetPosition y Object.GetShapeName en su definición real.
2. Ground fuera de0.01 o Roadway decisiva fuera de0.03 producen
   REFERENCE_MISMATCH para el run completo. Guardar datos y métricas del fallo,
   pero bloquear conclusiones basadas en A. No afirmar que demuestra deriva de
   bytes: identidad equivocada, consulta o proyección incorrecta siguen siendo
   explicaciones distintas. Negativos explícitos en la suite de B1.
3. Comparar entre rondas coordenadas, Ground/Roadway decisiva, sea/pond y
   número/listado de objetos. Diferencias se conservan y marcan confusor con
   lista de IDs/rondas/campos; no borrar rondas ni escoger la favorable.
   Roadway ya incierta sigue incierta, aunque estable; no inventar altura válida.
4. Añadir SurfaceGetSeaWaveCurrent antes/después (game.c:1195, declaración
   verificada) y conservar sus valores. Fase distinta es confusor. Misma fase
   y mismo GetTime no prueban que el motor entero quedara congelado: las APIs
   son opacas y el fake wave local no se identifica con el oleaje global.
5. Rechazar el supuesto de que los47 positivos sean todos vértices: A conserva
   vértices y centroides; conservar sus clases y coordenadas exactas. Tampoco
   predecir NaN en controles: un no-finito invalida evidencia en cualquier grupo.
   Para las tres referencias marinas, añadir superficie con fake y profundidad
   desde noFake+0.25 en el mismo fotograma; registrar coordenadas/origen,
   sea/pond y valor de cada consulta. No afirmar ausencia de objetos sólo por
   sus flags; son controles marinos, no prueba de espacio libre.
6. Añadir low_origin_below_water_ref=(Wref>S+2), usando también la Y efectiva
   float32; si se cumple, la comparación high/low conserva ese confusor. Es un
   hecho respecto a Wref estática, no una detección nativa de inmersión actual.
7. Firma Roadway y líneas de carga corregidas arriba.
8. Preparador genera CSV desde A; consumidor vuelve a contrastar cada ID,
   coordenada float32, B/Wref y expectativa original contra A. Hash de CSV solo
   no prueba ese vínculo. Tests de mutación CSV manteniendo su hash recalculado.

### Predicciones condicionadas; no oráculos de aceptación

| Clase fijada en A | Contraste H1 (altura) | Contraste H2 (fake) | Contraste H3 (objeto) |
|---|---|---|---|
| Mojado positivo, H y B bajo Wref | Comparar depthY0-depthY1 con Y1-Y0; coincidencia sería compatible con dependencia lineal de Y | Comparar residuos con fake y sin fake en las tres alturas | Matches Wref/B pueden ser ambiguos; no atribuir identidad |
| Lecho presente y Wref null (ej.292) | Comparar alturas sin inventar lámina ni esperar NaN | Registrar diferencia entre ambas surface, aunque devuelvan un objeto | Match B permite candidato BED_REF, no demuestra superficie objeto |
| Fallo seco524/528 | Mantener FAIL original; medir si depth cambia entre H+0.01 y S+0.01 | Reducir residuo con fake sería asociación, no permiso para ocultar agua | Conservar matches y ambigüedad B/Wref/H |
| Tres referencias marinas | Comparar depth(noFake+0.25) con alturas conocidas, sin afirmar independencia de Y | Si depth concuerda mejor con fake que con noFake, apoya H2 localmente | Flags no prueban ausencia de objeto; ninguna identidad inferida |

Todas las predicciones se guardan aunque no se cumplan. Ninguna cambia etiquetas,
umbrales ni verdictos del resultado2658. No ajustar bandas después de la captura.
Separar integridad/cobertura de captura de interpretabilidad de cada hipótesis;
el referente de producto y H3 no pasan por obtener345 filas completas.

### Antecedentes localizados después de redactar B1

evidence/v31-pond-layer-2026-10-13/ev112/integration/runtime-b-20261019/data/
water-temporal-runtime-b contiene240 filas históricas, raw SHA256
ee93a3a23ae19f2af8957a6fbced43758bddc16c5e14ee2f5731f9b5f08bcc03.
Se verificaron hash del log y de init.c/points.csv/points.json del binding.
En7/8 puntos el residuo depth-(withFake-ground-0.01) fue<=0.000007m;
en el control1116 alcanzó0.00958m. Mundo751823ac, distinto del actual10e09e3f;
no acredita el mismo mecanismo ni cierre de los puntos actuales.
La propuesta water-temporal-ae/proposal-rejection.json del mismo directorio
padre ya rechazó sustituir la evaluación por flags+NoFakeWave en190 muestras.
No repetir ese cambio ni presentar esta observación como nueva solución.

[EXACT] P:/scripts/4_World/entities/manbase/playerbase.c:7134-7149 consulta
GetWaterDepth en la cabeza para ahogamiento; 3_Game/vehicles/transport.c:526-548
lo consulta en el centro de las esquinas inferiores del vehículo. Son consumidores
operativos que justifican medir diferentes Y; no demuestran la implementación nativa.
La interpretación de terreno H como altura jugable sigue siendo objeto de contraste.

Negativos adicionales del contrato, para tools/quality/test_water_query_diag_b1_ev112.py:
reference_ground_mismatch, reference_roadway_mismatch, round_state_drift,
csv_rehashed_wrong_source, fake_surface_ambiguous, low_origin_below_reference,
missing_object_snapshot, missing_sea_control, invalid_native_bool,
surface_numeric_match_never_identity. Mantener también la lista cerrada anterior.

Anclajes de implementación verificados: Object.GetPosition en
P:/scripts/3_Game/entities/object.c:287 y GetShapeName en:503. El log nativo
7f1e1f0a usa true/false y vectores <x, y, z>; el parser rechazará otras formas.
La referencia previa a0/1 era incorrecta y queda sustituida por esa evidencia.
Implementación acotada: tools/quality/water_query_diag_b1_ev112.py,
tools/quality/test_water_query_diag_b1_ev112.py y nueva misión
missions/BalticWaterQueryB1.BalticTrial/init.c. Preparador/binder/lifecycle aún
deben fijarse y revisarse antes de cualquier despliegue o admisión futura.

## Revisión de código y corrección acotada

Fable5.1,262.578s, SOUND-with-fixes; recibos en
R/water-query-b1-code-review-20261028.26tests finales tras una corrección.
El productor pasó lint de exactamente1archivo; no compilación del motor.

- Fable detectó falta de confusor para instantánea vacía. Repro fortalecido:
  quitar objetos del mismoID en LAS TRES rondas (una sola ronda ya disparaba
  round_state_drift). Se marca object_snapshot_empty, sin afirmar que la causa
  sea necesariamente la carga WRP; siguen faltando datos.
- Codex reprodujo un falso completo al desplazar en+0.005m todos los ecos X del
  ID0 en las tres rondas, manteniendo CSV/fuente. La banda1cm era impropia para
  IDENTIDAD aunque el plan inicial y la revisión la aceptaban. Se elimina esa
  banda para los ecos, manteniendo intactos los umbrales físicos existentes.
- XZ: roundtrip exacto de los decimales nativos a float32. Y: usar el Ground
  del vector (seis decimales), no reconstruirlo desde el escalar de seis cifras.
  Error de entrada H:0.500001e-6 +0.5*ULP32(H). Error permitido de salida:
  errorEntrada +ULP32(Yprevista) +0.500001e-6. Para referencia marina, sustituir
  el primer0.500001e-6 por la mitad de la unidad decimal del escalar de seis
  cifras. Son cotas de serialización/arimética, no tolerancias de aceptación.
  Comprobar también que Ground escalar y vector concuerden con esos formatos.
  Fixtures: desplazamiento5mm X,1ULP X,5mmY y ejemplo nativo de seis decimales.
- El resultado2658, su consumidor y los fallos originales no se modifican.
  El CSV115 sigue teniendo el hash1f75d141ef905e0d1a9aed851310311642e38982104c838fc7dcefaf224ef310.
- Revisión de código sólo del contrato offline. Faltan binder, despliegue sellado,
  control de procedencia del run y prueba de motor; no promover por26tests.
