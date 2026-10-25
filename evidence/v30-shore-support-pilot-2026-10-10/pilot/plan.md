# EV83 - piloto local de reperfilado de orilla

Estado: diseño revisado por root y Luna; ejecución autorizada por la petición viva de suavizar cauces, orillas y taludes. No es aceptación artística ni autorización para cambiar niveles de lagos. EV82-B permanece desplegado.

## Problema y mecanismo verificado

Los vértices secos (1146,1002) y (2196,1572) pertenecen a wet_support, sin other_fixed ni protección vial. Conservar un cruce exacto hacia un vecino sumergido fijo fuerza delta=0 en ambos. La repetición del selector EV82 no puede corregirlos. El tercer punto (2196,1566) es agua y other_fixed: permanece fijo.

## Alcance y cambio de contrato [DESIGN]

- Fuente única: EV82-B, terreno SHA256 f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0. Presupuesto acumulado referido a EV79 dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c.
- Solo dos vértices secos indicados pueden bajar. Máximo total respecto a EV79 2 m; no subir respecto a B. Todo otro vértice y metadato exacto. P, F, modelos de agua, posiciones, clases y protecciones intactos.
- Sustituir SOLO en este piloto wet_support_exact y contorno exacto por: signos por extremo/cara idénticos, mismas caras mojadas, componentes/conexiones y frontera de los parches idénticos. Todos los cruces P y F incidentes se miden independientemente por celda/triángulo; máximo desplazamiento 1 m (1/6 de celda). No interpolar un F continuo global.
- Mantener suelo original EV79 y presupuesto; agua/fondos, corredores de navegación y otras protecciones inmóviles. El mínimo 0,95 m corresponde a corredores navegables, no a todos los puntos de la orilla.
- Conservar gates angulares de EV82 tomando B como referencia: sin nuevas bisagras >30 grados con la misma tolerancia de clasificación 1e-4; ningún máximo de sector aumenta; pendientes <=max(35 grados, referencia); distribuciones secas p99/count no peores. Energía angular incidente baja, no se sustituye por una métrica global.
- Propuesta determinista por minimización 1D de energía angular por nodo con intervalo factible de geometría y cruces; cuantizar float32 antes de aceptar. No tocar otros nodos para salvar un fallo. No redondear tolerancias después del resultado.

## Criterios del piloto

PASS geométrico requiere todos los invariantes anteriores, descenso >=0,1 m y reducción >=1% de energía de las bisagras incidentes en cada foco. Reportar pendientes, ángulos máximos, distribución y perfiles 1:1, incluso si un máximo no mejora. Si algún foco no alcanza el umbral, marcar parcial/inviable, no declarar ambos resueltos.

PASS de cobertura requiere un consumidor independiente sobre triángulos ODOL físicos y visibles y transformaciones WRP vigentes. Evaluar en todas las celdas afectadas: huella diseñada P y F candidata menos unión compilada expuesta <=0,002 m2 cada una; exposición compilada fuera de su huella diseñada no aumenta más de 0,002 m2 frente a B; cero ganancia fuera de celdas con campo de agua diseñado, cero exposición en caras anteriormente completamente secas. Medir ganancia/pérdida y distancia al contorno antiguo, conservando la franja ganada prevista como cambio de orilla, sin llamarla agua remota. P/F analítico no sustituye el ODOL.

Consumidor con fixtures: cruce desplazado válido dentro del metro; superar 1m rechazado; inversión de signo rechazada; pico angular nuevo rechazado; agujero deliberado en cobertura rechazado. Fórmulas del consumidor independientes del optimizador, dot/cross sobre coordenadas.

## Secuencia y presupuesto

1. Una propuesta local en carpeta nueva, sin empaquetar ni desplegar ni iniciar DayZ.
2. Revisión independiente, cobertura y perfiles. Una corrección permitida solo por error de implementación, nunca cambiando gates.
3. Si pasa, decidir ampliación a los bordes fluviales elegibles con un plan separado y dominios verificados. Si no pasa, preservar B y registrar el bloqueo concreto. No nueva ronda de parámetros ni apertura de protecciones.

Este piloto invalida la prueba anterior de exposición EXACTA en sus celdas; exige la nueva cobertura explícita. El render de teselas grises, shader de tierra, navmesh y aceptación visual permanecen abiertos. No hay prueba gráfica implícita.

## Anclajes leídos

- EV82-B author.py:372-401 presupuesto/suelo; 419-545 restricciones, objetivos y verificación float32.
- EV82-B review-luna/verify.py:127-141 protecciones; 193-200 invariantes; 229-306 dominios angulares.
- EV82-B audit_exposure.py:34-74 clipping de triángulos compilados; su igualdad de área NO sirve como gate de este piloto.
- support-feasibility y revisión independiente local: vecinos fijos y ecuaciones de cruce, con procedencia final verificada antes de ejecutar.

Revisión Luna: viable con estas condiciones; medir todas las aristas incidentes P/F y cobertura por cada campo, no solo etiqueta P ni campo F global.
