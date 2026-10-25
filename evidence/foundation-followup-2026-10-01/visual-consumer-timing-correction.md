# El consumidor anterior ignoraba los tiempos congelados de V4

La referenciaV4 se escribió antes del lanzamiento y declara poses90s,
captura60s y métricas10..70s. El consumidor heredado tenía constantes25s y
10..40s, aunque la referencia ya contenía esos campos en versiones anteriores.
Por eso NevaV4/capture-attempt-01 conserva FAIL de tiempo de captura y ventana
de métricas; no era un cambio de pose, clima ni una aceptación por imagen.

Se corrigió el consumidor para leer esos campos explícitos, con valores
anteriores como compatibilidad, y rechazar ventanas fuera de la pose. Se
mantienen tolerancias2s/3mm y todas las comprobaciones de cámara/restauración.
No se modificaron la referencia previa, la misión, el addon ni los registros.

NevaV4: reference-timing-verification.json PASS,17negativos, incluidos tiempo
de captura desplazado y muestras antes/después de la ventana. El control de
referencia antigua25s/10..40s también pasa; visual-consumer-old-timing-regression.json.
La captura nativa DDS y la inspección de píxeles Sky siguen siendo gates separados.
