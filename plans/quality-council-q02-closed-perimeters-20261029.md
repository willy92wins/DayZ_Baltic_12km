# Q02A — Cobertura de giros en perímetros cerrados guardados

Estado: REVISADO_PARA_IMPLEMENTAR. Fable5.1 nativo117.5s SOUND-with-fixes;
adjudicación técnica a continuación. Unidad offline aditiva, sin autoría de mapa.
Deriva de P14 y de Fable C02, Muse COB-03, Grok C03, Argon COB-03 y ChatGPT CG02.
El council se adelanta por la petición humana del 29-10; no cierra EV112.

## Hechos y alcance

`tools/quality/native_shore_census_ev112.py:78-90` quita el punto terminal de
los lazos y marca `closure_turn_evaluated=False`; `shape_patterns_ev112.py:38-72`
calcula sólo giros interiores. El censo guardado contiene 1.030 cadenas y
107.641 segmentos. Su productor serializa point_offsets/chain_points/closed en
`:199-203`. Se consume ese NPZ existente, sin regenerar el censo ni tocar helpers
sellados. El README nativo:27-29 reconoce la omisión de cierre.

Hipótesis verificable: un giro en el comienzo/cierre queda fuera del screen
abierto; un consumidor cíclico lo medirá sin depender de dónde empiece la cadena.
Esta unidad NO mide naturalidad, arcos, L/U completos, modelos ni carretera:
son Q02B/Q03/Q05 del plan del council. Una ausencia de hallazgo nunca da PASS.

## Diseño acotado [DESIGN]

Dos módulos nuevos en tools/quality y una suite nueva, sin modificar código previo.
1. Productor: validar NPZ sin pickle, SHA externo antes de leer, offsets enteros
   monótonos, terminal exacto, cerrado booleano y coordenadas finitas Nx2. Censo
   de todas las cadenas por su ID guardado, sin excluir máscaras. No filtrar ni
   inventar cadenas. Cadenas inválidas geométricamente son DEGENERATE con razón;
   archivo malformado o identidad incorrecta rechaza la unidad entera.
2. Para cerrado exigir último punto igual al primero, quitar UNA repetición
   terminal y medir cada vértice i entre aristas (i-1,i) y (i,i+1), índices
   modulares. Abierto mide sólo interiores y todos sus segmentos. No RDP ni
   remuestreo: preservar vértices y coordenadas, reconocer expresamente que los
   giros son de la teselación nativa. Cero longitudes o menos de tres vértices
   distintos en cerrado => DEGENERATE. No cerrar una cadena abierta.
3. Medir longitud de todas las aristas (incluido cierre), ángulos absolutos por
   atan2(cross,dot), giros firmados, número y testigos >=45 grados (POLICY actual)
   con índice de vértice original y XY. Registrar giro de cierre i=0 por separado
   y declarar evaluated_vertices/evaluated_edges. No aplicar 60m a segmentos
   crudos como si fuesen el detector existente de rectas simplificadas.
4. Estado por cadena DIAGNOSTIC_FINDINGS / NO_RAW_TURN_FINDING_NOT_ACCEPTANCE /
   DEGENERATE. Reporte global DIAGNOSTIC_ONLY, sin campo PASS de mapa. Incluir
   todas las cadenas exactamente una vez, input SHA y versión del algoritmo.
   No reclasificar ni sobrescribir el screen previo.
5. Consumidor separado: releer NPZ y JSON guardados, validar identidad/esquema,
   IDs completos/únicos y degeneraciones desde las coordenadas; recorrer cada
   terna con escalares independientes del productor. Verificar ángulos mediante
   identidad coseno=producto escalar/(normas), longitud por math.fsum, cierre,
   testigos exactos y umbral por ángulo escalar atan2. Tolerancia numérica para
   coseno 2e-14 (acuerdo aritmético, NO umbral de calidad); longitud <=16 ULP del
   total esperado. Rechazar resultados no finitos, campos desconocidos, testigos
   extra/omitidos/cambiados e intentos de aceptación. Consumidor no importa al
   productor ni shape_patterns; tests literales usan ángulos/perímetros conocidos.

## Pruebas / aceptación

Positivos analíticos: cuadrado con 4 giros 90/perímetro40, triángulo 3 giros120,
polilínea abierta en L con 1 giro90, círculo poligonal fino sin giros>=45 (sólo
este screen; no naturalidad). Negativos: NaN, offset malformado/no entero,
hash incorrecto, falta cierre, segmento nulo, pérdida/duplicación de cadena,
giro de cierre omitido, testigo desplazado, longitud/coseno alterados, PASS falso.
Metamórficos: rotar origen de lista/revertir orden/rotación rígida/traslación y
subdivisión colineal conservan perímetro y conjunto geométrico de giros no nulos;
las nuevas estaciones de subdivisión tienen giro cero. Sin prometer invariancia
de ruido ni de una teselación que cambie la geometría.
El mutante que omite i=0 debe fallar el consumidor incluso cuando el máximo de
otros giros sea idéntico. Degeneraciones se conservan como datos, no como PASS.

## Ejecución / presupuesto

Revisión de plan 180s; implementación delegada 420s; revisión de código 180s;
suite 120s; productor real y consumidor 120s/2GiB cada uno, un censo aditivo sobre
NPZ guardado. Salidas exclusivas y hashes del código. Fallo implica conservar
recibo y reevaluar causa, sin retries internos ni relajar límites. No DayZ,
build, lease, paquete, nuevos PBO ni cambio a 607PASS/47FAIL/21inciertos.
Publicar sólo herramientas propias, pruebas, reporte compacto y procedencia;
no redistribuir NPZ/binarios vanilla. Comprobar suite en checkout público antes
del commit/push autorizado. Q02A aprobada no autoriza reparaciones geométricas.

## Adjudicación de revisión (prevalece sobre ambigüedades anteriores)

1. Se rechaza relajar pertenencia a testigos mediante banda1e-9grados. Se conserva
   umbral45 exacto usando las coordenadas float64 COMO racionales exactos. Para
   vectores entrante/saliente: testigo si dot<=0 o abs(cross)>=dot. El consumidor
   usa criterio algebraico distinto: dot<=0 o 2*dot**2<=norm2(a)*norm2(b).
   Ambos con Fraction de coordenadas antes de restar; sin sqrt ni atan en la
   decisión. El ángulo float queda informativo y se valida por coseno2e-14.
   No probar igualdad de etiqueta al aplicar rotaciones que redondean geometría.
2. NPZ requiere point_offsets/chain_points/closed/chain_offsets; enumera otras
   claves sin rechazarlas. JSON nuevo sí tiene esquema cerrado. Validar
   diferencias point_offsets-1==differences chain_offsets por cadena.
3. Falta de repetición terminal en cadena closed => DEGENERATE closure_mismatch;
   no intentar soldar. Offset/shape/hash inconsistentes rechazan toda unidad.
4. Cero vértices interiores evaluables => NO_EVALUABLE_VERTEX; nunca sin hallazgo.
   Espiga180 se canoniza a+180; reversión compara valores absolutos. Cerrado con
   menos de3vértices distintos es degenerado. Longitud de arista<1e-8 como
   path_array existente => DEGENERATE short_segment; no se alarga ni se borra.
5. Metamórficos exactos90grados/reflejo/traslaciones enteras/subdivisión exacta;
   rotaciones no representables sólo comparación numérica, no igualdad de clase
   cerca45. Tests de nextafter a ambos lados45 con referente racional independiente.
6. Resumen separado cuenta cerradas, cierre con testigo y cierre como único
   testigo. No comparar ese conteo crudo con el screenDP histórico. Todas las
   aristas y testigos quedan en JSON completo (no truncar evidencia por tamaño);
   resumen pequeño para publicación/lectura. Perímetro y longitudes por arista
   se contrastan con16ULP/4ULP respectivamente como acuerdo aritmético.
7. Endpoints coincidentes en abierta se registran pero no convierten en cerrada.
8. Control de independencia: productor y consumidor no comparten cálculo,
   validación ni constantes importadas. Fijar45,1e-8 y coseno2e-14 explícitos en
   contrato de esta unidad; no modifica POLICY anterior ni geometría.
