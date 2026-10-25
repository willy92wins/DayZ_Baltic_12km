# EV85-R — corrección numérica explícita de la salida única

Propuesta para revisión antes de autoría. EV85 permanece SOLVER_FAILED e inmutable. No se repite SLSQP ni se varían sus parámetros, el dominio, los límites físicos o las puertas de aceptación. Esta es la única corrección de implementación de la unidad; no autoriza otra ronda si falla.

## Evidencia del mecanismo

`numeric-analysis.json` reconstruye 220 aristas contra B sobre `diagnostic-vector.npz`: 12 inversiones con máximo 0,000005245208740234375 m y tres cotas cruzadas con máximo 0,0000001847452342218503 m. La solución numérica de SLSQP no satisface orden exacto ni cuantización interior de las cotas. Sus perfiles macroscópicos ya eliminan la V de EV83, pero eso no acepta el terreno. Rechazar la salida inicial fue correcto.

## Reparación propuesta [DESIGN]

Una sola proyección determinista, sin optimizador, sobre las alturas float32 del diagnóstico congelado:

1. Reconstruir los 39 nodos variables y todas sus aristas de ocho vecinos con los nodos fijos que las tocan. Reanclar B, EV79, P/F, D4 y diagnóstico por SHA.
2. Cada nodo variable tiene intervalo absoluto `[B+delta_min, B+delta_max]` del D4 revisado. Redondear el mínimo hacia arriba y el máximo hacia abajo a float32, usando `nextafter` solo cuando el redondeo al más cercano cae fuera del intervalo. Los fijos tienen intervalo puntual B.
3. Agrupar por componentes de aristas cuyos extremos tenían exactamente la misma altura B. Todas las alturas de un grupo deben ser iguales; intervalo del grupo = intersección de intervalos. Si queda vacío, FAIL.
4. Orientar cada arista restante del grupo de menor altura B al de mayor altura B. Es un grafo acíclico: la altura B aumenta estrictamente. Inicializar cada grupo en el máximo entre su cota inferior y las alturas diagnósticas de sus miembros (fijos incluidos).
5. Recorrer grupos por altura B ascendente; subir cada grupo al máximo entre su valor inicial y los valores de sus predecesores. Si supera su cota superior, FAIL, sin bajar otros grupos ni buscar una segunda solución. La monotonía, las cotas inferiores y las igualdades se satisfacen por construcción; la comprobación final vuelve a enumerarlas independientemente.
6. Cualquier movimiento de un fijo, cualquier altura por encima de B o cualquier corrección respecto al diagnóstico superior a 0,0001 m implica FAIL. Este límite es de AUTORÍA de la reparación, no una tolerancia nueva de los gates. Las alturas resultantes son float32 exactas.

No hay segundo solve, mezcla con B, selección de parámetros ni búsqueda de ULPs. `nextafter` solo realiza redondeo dirigido de intervalos, y cada componente se procesa una vez en el DAG. La proyección puede fallar aunque otra solución sea posible: no se la busca en esta unidad.

## Aceptación

No se transforma `success=false` en éxito del optimizador. EV85-R se identifica como propuesta reparada y solo puede aceptarse si pasa TODO el consumidor EV85: cotas, descenso de ambos focos >=0,1 m, orden de las 220 aristas exacto en float32, extremos axiales, agua/celdas/caras/componentes/cruces<=1m, cobertura ODOL, protecciones, energía angular, nuevas >30, pendientes, máximos de sector y p99/conteos globales respecto a B. El estado original y sus hashes se conservan.

Fixtures requeridos antes de aplicar: arista hacia fijo anterior, cadena de tres niveles, igualdad conectada, intervalo sin float32 representable, propagación que excede cota superior (FAIL), límite de corrección (FAIL), redondeo dirigido de ambos extremos, y el diagnóstico EV85 original rechazado por orden. No arrancar DayZ ni empaquetar antes de aceptación independiente.

Si esta corrección falla o deja un defecto de forma macroscópico, cerrar la unidad rechazada; no otra variante automática. Globalización aún pendiente de diseño y revisión separados.
