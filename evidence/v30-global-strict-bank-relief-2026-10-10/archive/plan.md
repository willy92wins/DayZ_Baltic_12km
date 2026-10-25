# EV87 — una pasada global de relieve con pendientes preservadas

PROPUESTA, no ejecutar antes de PASS independiente EV86 y revisión de este diseño. Fuente única B/EV82 f9fb23de…; presupuesto acumulado EV79 dbc59ec…; P/F y objetos congelados. EV85 y R permanecen rechazados. El piloto EV86 es un método nuevo con punto medio fijo y preservación estricta de pendientes, no una aceptación retroactiva.

## Dominio y cola

Barrido completo 2048², seis metros por paso. Vértices clase0, sin `other_fixed`, halo de ingeniería ni grandes lagos. `wet_support` por sí solo deja de ser veto; cualquier nodo que esté mojado en cualquier esquina incidente de P, F o mar0.85 sigue fijo. Usar F real por esquina incluso si P es NaN. Cumbres/control/playas/corredor/borde están incluidos en other_fixed y no se liberan.

Semillas: nodos elegibles incidentes a bisagraB>30.0001° que además tengan una prominencia axial estricta >0.1m (sobre ambos vecinos de al menos un eje). Incluye ríos y tierra interior. Orden determinista: máximo ángulo incidente descendente, luego fila/columna. Selección greedy de centros con distancia Chebyshev>=11nodos; ventana7x7, anillo fijo e interior5x5 potencialmente variable. Las ventanas9x9 de evaluación de geometría no se solapan; las caras y bisagras afectadas son disjuntas. Registrar todas las semillas, elegidas y excluidas por solape/protección. No afirmar que una pasada resuelve los nodos excluidos ni todos los defectos visuales.

## Una propuesta por parche

Construir cotas físicas EV79±2m, suelo mínimo permitido, incidenteP/F+.0001 y no-raiseB; añadir intervalo de cruce<=1m B para toda arista P/F/mojada con un extremo variable seco y extremo mojado fijo. Si aparecen dos extremos variables en un cruce, parcialidad de F sin tratamiento demostrado o intervalo vacío, rechazar ese parche y registrar motivo. No copiar cotas históricas que codificaban wet_support fijo.

Usar evaluador vectorizado verificado contra EV85, sin copiar la malla completa durante el solve. SLSQP una llamada por parche, <=150iteraciones; objetivo angular de unión deduplicada y límites angulares/pendientes como EV85. B es la referencia de cada parche: no derivar cotas de un parche ya cambiado. Todas las aristas8vecinos que toquen variables se enumeran completas. El inicio lineal factible se obtiene por LP minimizando la suma de descensos y exigiendo descenso del foco>=0.2m (el punto medio final debe bajar>=0.1m). Si LP no es factible, registrar y pasar al siguiente sin solve.

La salida SLSQP es solo dirección numérica, aunque el solver diga success. Se permite una proyección isotónica float32 explícita, exactamente el método revisado EV85-R, limitada a1e-4m frente al diagnóstico; no buscar otra solución si la proyección viola upper/cotas/fijos. Aplicar una vez el punto medio fijo1/2 B/dirección. Nada de buscar coeficientes, relajar puertas ni repetir el solve.

## Rechazo local antes de integrar

Exigir todos los gates EV86 al float32 final: dominio/metadata, signos ESTRICTOS8vecinos, al menos mitad de diferencias originales descontando solo error de redondeo medido, cero nuevos extremos débiles, foco>=.1m de descenso, energía foco>=1% mejor y unión angular menor, cotas/cruces/componentes, no nuevasbisagras>30.0001, pendientes<=max35/B y máximos por sectorB no peores. El dominio físico seco y húmedo se comprueba por esquina/cara, nunca por clase raster sola.

Para preservar p99 global sin aceptar un empeoramiento oculto: calcular los dos valores ordenados de B que interpolan su p99 en cada dominio (bank e interior secos del consumidor EV82). Cada parche debe conservar o aumentar el número de bisagras afectadas <=cada uno de esos dos valores. Al ser los conjuntos de bisagras disjuntos, sus cuentas se suman y los dos estadísticos de orden globales no aumentan. Además el número local >30 exactos no aumenta en cada dominio. Esto es un filtro conservador de integración; el consumidor vuelve a calcular p99/conteos completos sobre el mapa final.

Condición revisada: membership bank/interior se congela exclusivamente desde B. Afirmar población total de cada dominio y cobertura EXACTA de todas las bisagras potencialmente afectadas por variables, una sola vez, contenidas en su ventana9x9. No seleccionar solo las aristas que ya cambiaron o que pasan filtros. Las fixtures deben verificar esta partición y las cuentas de los dos estadísticos de orden.

Solo integrar propuestas que pasen filtros locales. Los parches rechazados conservan B; no modificar su alcance o parámetros para hacerlos pasar. Las zonas que no cambian no se declaran corregidas. Los dos focosEV86 no tienen trato especial: si una ventana seleccionada los cubre se mide esa nueva propuesta; si no, quedan para el inventario residual. No superponer el pilotoEV86 arbitrariamente a la pasada.

## Presupuesto y consumidor

Una pasada determinista; máximo150iter por solve, tope5s por parche y30min total de autoría. Alcanzar tiempo global detiene con inventario explícito de no procesados; no se publica una pasada incompleta como mapa terminado. Paralelismo de cálculo máximo2procesos locales si memoria lo permite, sin DayZ. No nuevas rondas automáticas.

Los topes de tiempo se imponen desde el proceso padre: cada solve corre en worker subprocess terminable, nunca solo mediante callback de SLSQP. Puede ser worker reutilizable con handshake de preparación antes de recibir tareas locales; iniciar/reiniciar el worker no reinicia la ventana global de30min. Superar5s desde el despacho al worker provoca su terminación y descarte de salida, deja ese parcheB exacto y registraTIMEOUT; solo puede reiniciarse para otro parche. Al deadline global se cierran todos los workers y se marca pasada incompleta. La integración va en orden de cola determinista aun si se calculan dos parches en paralelo. No usar ventanas visibles para helpers.

Consumidor independiente sin importar autor: reconstrucción selector/máscaras por fuente, deltas y protecciones, orden en todos los nodos cambiados y pares fijos, extremos, totalidad de bisagras y pendientes/sectores/p99, P/F topología y cruces, cobertura ODOL sobre TODAS celdas tocadas y su frontera, componentes por ventanas y conectividad global preservada por signos/caras. Verificación de objetos/agua congelados y metadatos. Fixtures anteriores + independencia de ventanas, composición de cuentas p99 positivas/negativas, F parcial y PNaN, fallo de presupuesto y parche rechazado que dejaB exacto.

Después: informe de cobertura de toda la superficie con cambios/pendientes/exclusiones y perfiles por sector. Solo si consumidor pasa se rehacen satélite/máscaras/PAA de toda la huella, se empaqueta y se verifica el terreno nativo. Aceptación gráfica y defectos de render siguen separados. No TerrainBuilder/navmesh antes de congelar geometría.
