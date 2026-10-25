# EV86 — perfil conjunto con preservación estricta de pendiente

Propuesta de cambio de método para revisión, todavía sin autoría. EV85 y su única corrección EV85-R quedan cerrados RECHAZADOS, sin promoción. Se preservan sus archivos y presupuestos; no se relanza su SLSQP. Esto sustituye la formulación defectuosa del plan, no modifica el veredicto del experimento.

## Problema demostrado del diseño anterior

El plan EV85 permitía convertir diferencias entre vecinos en empates, pero exigía no crear extremos axiales débiles nuevos. Su optimizador minimizaba quiebros y llegaba a mesetas en los límites de orden. La proyección float32 corrigió doce microinversiones, pero dejó nueve extremos débiles nuevos por empates exactos. Todos los demás gates del consumidor pasaron. Repetir el solve, cambiar tolerancias o ignorar esos extremos no resuelve esa insuficiencia de la formulación.

## Método [DESIGN]

Se construye UNA propuesta como punto medio exacto en float64 entre B y el perfil conjunto EV85-R, después se cuantiza una sola vez a float32:

`H = B + (R - B) / 2`.

El factor 1/2 está fijado aquí por el contrato de conservar al menos la mitad de la diferencia original entre cada pareja de vecinos. No hay coeficiente a optimizar, búsqueda de variantes, segundo solve, reparación de ULP, ni bucle. No se pretende que EV85-R sea producto aceptado: sus alturas son una dirección de suavizado ya comprobada salvo por la aparición de mesetas.

Para cualquier arista donde `B[u]>B[v]`, EV85-R tiene `R[u]>=R[v]`, por lo que `H[u]-H[v] >= (B[u]-B[v])/2 >0`. Igualdades B se preservan porque R las conserva. El argumento simétrico vale si B[u]<B[v]. Así se preservan signos estrictos y no se crean mesetas nuevas en aristas originalmente inclinadas; esto se vuelve a verificar sobre el float32 final (la prueba en reales no basta). Se registra la retención de diferencia real y final. La pérdida respecto al 50% solo puede ser el error de redondeo medido `abs(float32(H[u])-H[u])+abs(float32(H[v])-H[v])`; se comprueba contra esa cota, sin porcentaje arbitrario añadido y sin sustituir el signo estricto requerido.

Los intervalos de altura, suelo, presupuesto, cruce y no-raise son convexos: B y R satisfacen esos mismos intervalos. Su punto medio también los satisface en reales, pero todas las cotas se comprueban otra vez sin relajarlas al cuantizar. Fijos, agua y metadatos se copian exactos. Ambos focos seguirían bajando unos0,86/0,78m, bastante por encima del mínimo0,1m; la autoría debe medirlo.

## Alcance y gates

Mismos dos parches7x7, mismos39variables/220aristas, fuenteB f9fb23de… y presupuesto EV79 dbc59ec…; R a4434bf7… proviene de la propuesta rechazada registrada. No tocar nada más. El selector de agua/ingeniería/grandeslagos no cambia.

Se conservan TODAS las puertas EV85, incluyendo el detector de extremos débiles (sin modificarlo), energía>=1% en cada foco, unión angular menor, p99/conteo/sectors/no nuevas>30, pendientes, P/F/signos/componentes/cruces<=1m y cobertura real ODOL. Además se exige signo estricto de las220aristas y la retención de pendiente definida arriba. Perfiles36m 1:1 para confirmar forma; ningún PASS numérico sustituye aceptación artística.

Fixtures: pico central que se vuelve meseta en R y recupera pendiente en punto medio; V inválida que se rechaza antes de mezclar; cotas convexas; empate B conservado; regresión float32 que convierte un gradiente diminuto en empate debe fallar, no repararse. El consumidor independiente no importa el autor. Presupuesto UNA propuesta y una ejecución del consumidor, sin variantes de factor si falla; si falla, este método se cierra. No DayZ/PBO hasta aceptación geométrica.

Solo tras un PASS se diseñará la extensión sobre la cola global de crestas; cada parche deberá justificar dominio, índices, interacciones y validación. El evaluador vectorizado ya iguala la geometría congelada con error <1,5e-14grados y reduce el coste; eso no valida el producto ni la convergencia global.
