# Discriminadores tras la sonda completa de lecho y carretera

Estado: BORRADOR_PARA_REVISION. Codex ejecutor/integrador; Fable revisión independiente.
Traza: P7/P9/P10/P11/P12/P14, petición de detección y reparación procedural
tras nueve observaciones humanas. No sustituye la aceptación visual ni el council
ampliado posterior. Padre: ev112-dry-road-full-consumer-20261028.md, congelado.

## Evidencia que no se reescribe

Calibración propia 08bcc1a6 y sonda 7f1e1f0a, cerradas oficialmente y sin lease.
R = E:/DayZ-Baltic-Build/shape-repair-20261025.
R/dry-road-full-native-20261028/probe/result.json: FAIL, 2658 IDs,
51 fallos de canal en 47 puntos y 46 canales inconclusos en 21 puntos.
Ground:2658 PASS. Roadway:2638 PASS/20 inconclusos. Agua:43 FAIL.
RV:5 FAIL; Bullet:3 FAIL. Identidad PID/creación/misión/engine/4PBO vinculada.
Calibración nueva: margen0.03999144638858333 m; cinco impactos vanilla,
289 espacios negativos, rejillas completas289+289; contrato existente intacto.

R/dry-road-full-native-diagnosis-20261028/report.json clasifica hechos:
- 41 esperados mojados fallan pond y tienen B>W; los96 mojados decisivos con
  W>=B sí dan pond. Correlación, todavía NO causalidad del motor.
- Dos esperados secos dan pond=false y depth>0 al medir en H+0.01.
- IDs349/350/1425: ambos rayos devuelven la forma de un haya a17–19m sobreB.
  Es un oclusor medido; no prueba que su tronco invada cauce/carretera.
- IDs700/723: RV devuelveH con forma vacía pese aB>H; Bullet alcanzaB.
  Ambos son vértices fuente. Causa aún desconocida, no asumir grieta.

[EXACT] missions/BalticVisualProbeV1.BalticTrial/init.c:114-143:
rayos desdeH+100 aH-10; profundidad enH+0.01; carga WRP en el mismo frame.
[EXACT] P:/scripts/3_Game/global/game.c:1197-1201: SurfaceIsPond,
GetWaterDepth y GetWaterSurfaceHeightNoFakeWave son nativos; la definición no
explica oclusión del lecho ni oleaje de profundidad. No inventar ese mecanismo.
[EXACT] R/discover_dry_road_effective_domain_20261028.py clasifica wet con
W>H, omitiendo B en esa etiqueta; sí conservaB al calcular Roadway.
[EXACT] tools/quality/dry_bed_road_candidate_ev112.py:118-147 congela
caras con cualquier contacto de agua y franja|q|<=4. No borrar estas protecciones.

## Hipótesis y discriminadores; no cambios al mapa

H1 [HIPÓTESIS]: la etiqueta wet del descubrimiento confunde lámina subyacente
con agua accesible sobre el sólido. MedirW>max(H,B) puede describir pond, pero
convertir todos los casos en secos automáticamente ocultaría lechos espurios.
Se exige un segundo referente: huella mojada y roles secos/mojados del estado
anterior fijado y del contrato de producto. La conservación de una fuente que
ya tenía defectos no demuestra buena apariencia ni corrección del generador.

H2 [HIPÓTESIS]: depth enH+0.01 está muestreando bajo el lecho en un punto seco
a altura jugable; fake wave/agua local pueden diferir de surfaceNoFakeWave.
No quitar depth del gate ni permitir profundidad positiva en un control seco.
Discriminar posiciones H+0.01, max(H,B)+0.01 y sobreW, sin cambiar sus límites.

H3 [EVIDENCIA]: el rayo alto intercepta copas en tres IDs.
[DESIGN] Separar acceso a colisión del suelo y oclusión de la columna alta:
conservar el rayo original y añadir otro desde max(H,B)+2m. Dos metros define
un origen experimental, NO una tolerancia de colisión ni permiso para ignorar
árboles. Comprobar que el inicio no está dentro de otro sólido. Las copas no se
eliminan; tronco/corredor/cauce deben comprobarse por geometría independiente.
Un rayo bajo válido no convierte el oclusor alto en PASS de calidad global.

H4 [HIPÓTESIS]: los dos RV en vértice pueden exponer una frontera numérica
o un defecto de Geometry/oclusión. Primero proyectar contra Geometry compilada
REAL en poseWRP, no sólo Roadway o un MLOD previo. Si no explica el resultado,
microrejilla simétrica±0.005/±0.02m y dos orígenes, manteniendo el punto central.
Esos desplazamientos son estímulos diagnósticos; no reemplazan el ID fallido.

## Unidad inmediata A: lectura offline sin cambiar verdictos

[DESIGN] Una lectura de los51fallos,21inciertos y controles positivos emparejados:
1. Proyectar H, B anterior, B candidato y W por la geometría real. Identificar
   qué caras cambiaron, cuáles están congeladas y cuáles ocupan los canales de
   producto. Registrar todas las contribuciones/solapes, no sólo la altura máxima.
2. Para700/723, medir bary y distancia a aristas/vértices en Geometry real,
   winding y soporte continuo. Incluir centroides próximos y vértices PASS.
3. Clasificar los tres rayos que golpean árbol; no podar ni mover instancias.
   Geometría de copa no implica tronco invadiendo corredor; si falta la
   extracción específica del árbol, mantenerlo NO_EVALUADO.
4. Contrastar etiquetas fuente, conservación de agua y expectativas físicas;
   generar listado de preguntas mecánicas que una microsonda pueda resolver.
   Ningún cambio de umbral, borrado de ID, reclasificación a PASS o regeneración.

Criterios A: entradas fijadas por hash; cobertura íntegra de los47puntos fallidos
y21inciertos (sin perder solapes); cada relación trazada a fuente/cara/pose;
comparación original/candidato y positivos. Datos faltantes => INCONCLUSO,
nunca asumir fuente equivalente. Resultado DIAGNOSTICO_OFFLINE, no mapaPASS.
Presupuesto A:120s,2GiB,un hilo numérico. Revisión de plan600s; una corrección
por repro concreto. No barrer parámetros, reabrir aprobaciones ni repetir sondas
completas para tantear. Si A no discrimina, documentar el dato que falta.

## Unidad posterior B, aún sin implementación ni permiso de lanzamiento

[DESIGN] Productor diagnóstico nuevo, consumidor independiente y controles
analíticos/nativos: altura de consulta de agua, rayos alto/bajo y microrejilla
central conservada. Elegir IDs a partir de A más positivos naturales/diseñados;
selección fijada antes de resultados. Registrar EXPECT/ACTUAL por canal.
Antes de ejecutar: fuente vanilla/APIs verificadas, plan actualizado y revisión
de código con positivos y negativos de evidencia, contenido desplegado sellado,
preflight y cola FIFO oficial en otra activación con presupuesto propio.
No cambiar la misión/consumidor2658 ya consumidos ni reutilizar sus salidas.
No llamar un resultado posterior PASS si sólo evita los fallos originales.
La corrección procedural de generador sólo se diseña tras aislar el mecanismo
y mantener agua/extremos/topología/015-45, más regresiones de todos los equivalentes.

