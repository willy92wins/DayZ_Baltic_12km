# Extensión de crestas EV93 — plan de ejecución del integrador

Autorizada dentro de la petición viva de suavizar orillas, cauces, taludes y relieve general. Es una extensión local medida; no representa toda la superficie ni cierra BASE1.0. Solo se ejecuta después de PASS_INCREMENTAL_NONREGRESSION del consumidor compuesto de fairing-layer1. El código nuevo requiere revisión y fixtures antes de autoría.

## Entradas y modificación de contrato

- B sigue siendo EV82-B f9fb23de. Los 340 deltas aceptados originales (20.201 alturas cambiadas, candidato 37e6d4bd) se conservan exactamente. L/prepared, ledger, results, solution NPZ y deltas originales no se editan.
- Universo nuevo: las 228 filas rejected cuya razón completa es `final gate scalar interpolation rule unavailable: baseline focus is not prominent on both axes`. Inventario 8b8b9a6e:113 EW activos/115 NS activos. Hay 14.186 posiciones con dirección distinta de B, antes de interpolación o aceptación. No todas tienen por qué aceptarse.
- Política `crest-policy/crest_policy.py` SHA 32ab6e0111886907315a0360322df0ff958f80bebcd6493254a2f0f144a3829e y contrato dc1b028860f6c2131f7c2f6220bf159bbc6ffc1d8b9700d6c21b5e468ff8e342. Cambia solo el foco: prominencia reducida al menos25% en el eje activo y cero en el inactivo. Se mantiene cada otra puerta de forma, energía, cotas, drenaje, collar, pendiente, bisagras, agua y navegación.

## Autoría [DESIGN hasta revisión de las fuentes]

Una visita por fila y una única interpolación analítica de su dirección ya resuelta. Cero llamadas al solver, cero barridos de alpha. Se elige el punto medio de la intersección de la cola factible de ambos ejes con el intervalo de energía; singleton en1 y ausencia de intervalo son rechazos. Cast float64→float32 único y revalidación de todos los gates locales. No se aceptan valores teóricos sin comprobar el resultado float32.

Presupuesto de ejecución600s, con registros de avance y tiempos; si se agota, conservar resultados inmutables e indicar INCOMPLETE. Error inesperado no se convierte en rechazo geométrico ni en PASS. Reanudar solo filas sin resultado y con todas las identidades vigentes; no recalcular resultados terminados.

Cada delta nuevo liga el qid, centro, prepared y ledger originales, SHA del result original y solución, valores B, dirección igual al cast del vector de solver, stencils y D8 originales, política y este plan. Las 340 filas legacy se despachan directamente a EV92 original: nunca se fabrica para ellas una razón de rechazo. Manifiesto, recibo y registros nuevos tienen esquema explícito de reutilización.

## Consumidor y salida

El consumidor reconstruye por sí mismo B +340 deltas originales +deltas nuevos, comprueba propiedad y separación de nodos, todos los hashes y puertas locales, y ejecuta el contrato global sobre la composición completa. No importa el autor nuevo. El muestreo índice/ODOL, independiente del candidato, puede reutilizar su PASS previo anclado a las mismas identidades; las comprobaciones de terreno y cobertura del nuevo compuesto siempre se recalculan.

También se generan métricas ANY de las poblaciones de orilla/interior/wet_support. PASS offline permite preparar un preview aislado; no sustituye la lectura nativa del paquete ni la comprobación del agua dinámica. Agua sobre tierra, gris a media distancia, navegación en motor, TB/navmesh y cobertura del relieve general permanecen abiertos hasta sus pruebas correspondientes.
