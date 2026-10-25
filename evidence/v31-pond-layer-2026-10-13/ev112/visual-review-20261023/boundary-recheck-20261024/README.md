# EV112 — nueva ejecución de controles y borde forestal

**53 pruebas, cero fallos/errores/omisiones. Bosque de borde todavía INCONCLUSO; mapa no aceptado.**

La sonda de216 puntos sí se ejecutó sobre el PBO R con los tres hashes fijados. Run `e45f4ab7-c974-4168-8de8-b712a08a1a3a`; registro completo BEGIN216/END216, cierre ordenado y liberación del lease comprobados. [Registro](results/boundary-probe.log), [lifecycle](results/lifecycle-close.json), [análisis corregido](results/boundary-analysis-v2.json).

El campo histórico `clamped_hypothesis` estaba mal nombrado: `streambed_kit_v31.tri_h` limita índices pero extrapola las fracciones. El cálculo de raíces `geom.h_at` limita las coordenadas. Las120 muestras norte/este —incluidas24 raíces— concuerdan con este último a menos de0,000026m. Los controles con coordenadas negativas sur/oeste no concuerdan: desviación de hasta1,05121m. Eso refuta un clamp universal; no demuestra que los árboles estén mal colocados.

Los3.727 discos pendientes se mantienen.388 cruzan sur/oeste,200 de ellos con disco de tronco; otros388 alcanzan más allá del mundo por norte/este. Los rangos completos llegan a X−8,923..12294,583 y Z−4,585..12298,307. Las216 medidas no cubren esos discos. [Las raíces, radios y embebido de todos estos árboles son idénticos en R y S3](results/boundary-r-s3-parity.json); también coinciden las cinco filas/columnas de terreno del borde.

## Nueva sonda preparada

`BalticForestBoundaryR.BalticTrial` contiene269.968 puntos para los3.727 árboles: todas las raíces, perímetros con separación máxima0,25m y cuadrícula interior de0,5m. Generador reproducible desde el WRP R y sus modelos fijados, sin cambiar árboles. Verifica ausencia de planos pond en la banda y usa el umbral existente de tierra no-pond a1,0m.

El consumidor rechaza NaN/Inf, IDs duplicados o ausentes, booleanos/expectativas inválidos, reloj decreciente, muestras obligatorias omitidas, hashes de PBO/misión que cambien, coordenadas diferentes del CSV y registros de otra sonda mediante UUID. Compara raíz con tolerancia0,005m, apoyo con0,01m y margen de agua con1,0m. Su mejor resultado posible es `SAMPLED_BOUNDARY_CLEAR`, nunca un PASS del disco continuo ni del bosque completo. Los seis tests nuevos incluyen contraejemplos de raíz flotante, apoyo insuficiente, agua y log ajeno.

[Suite53](results/tests-expanded.json) y log adjunto. Validador Enforce:1 archivo inspeccionado,0 errores y0 warnings. [Preflight](prepared/preflight.json) correcto, sin ejecutar la misión. [Preparación y hashes](prepared/preparation.json). Puntos y CSV comprimidos sin pérdida, con SHA original en compressed-inputs.json; los archivos ejecutables originales permanecen en la misión y E:/DayZ-Baltic-Build/qc-council-20261024/forest-boundary-full-r.

El banco está ocupado por una prueba ajena `@StorageLogger`/`@StorageLoggerTest` (servidor y cliente). No se lanzó la sonda ampliada, no se tomó lease ni se alteraron procesos. Estado propio `none`, ambas colas vacías. El bloqueo anterior LFSkateboard ya no describe el estado actual.

## Continuidad

El [council anterior](../council-20261024/README.md) conserva su evidencia histórica intacta. Carreteras S3:77.559 secciones y130.534 intervalos,0 incumplimientos. S3 sigue sin compilar/desplegar mientras el soporte no esté cerrado. Pilotos:35 modelos desplegados y33.060 componentes cerrados; no equivalen a aceptación de todos los ríos.

Al quedar libre el banco, verificar `session_status` y hashes; ejecutar prepared/launch.json por la herramienta oficial, adoptar el run, recoger registro nuevo, cerrar ordenadamente, liberar y confirmar estado. Mantener heartbeat durante la medición. Consumir el log con tools/vegetation/eval_forest_boundary_probe_v31.py y los puntos originales. Un fallo medido es un contraejemplo que hay que corregir; un muestreo sin fallos no cierra automáticamente la geometría continua.

Después: cerrar soporte, compilar/verificar S3 y nueva sonda completa; revisión visual/caminar antes de extender pilotos, extremos/receptores,015-45 y271 labios pendientes; carreteras físicas/cruces/navmesh/conducción y A/B Chernarus. No hay medición nueva de FPS ni aceptación global. Sin commit/push por estas puertas abiertas; cambios ajenos preservados. No se modifica memoria Codex.
