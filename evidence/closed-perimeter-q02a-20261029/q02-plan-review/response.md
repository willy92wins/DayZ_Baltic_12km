**Veredicto: SOUND-with-fixes.** El diseño es correcto en lo esencial (cierre modular, consumidor independiente, sin PASS), pero tiene cuatro puntos que producirán falsos FAIL o estados vacíos si se implementa literalmente.

## Defectos con contraejemplo y corrección mínima

**1. Umbral 45° sobre teselación nativa produce testigos en la frontera exacta.**
La orilla sale de una malla de 6 m con cruces interpolados. Un vértice entre una arista axial y una diagonal da 45° casi exactos; con coordenadas fraccionarias el productor (atan2) puede dar 45.000000000000007 y el consumidor, recalculando con escalares propios y fsum, 44.999999999999993. El consumidor exige "testigos exactos" y declara FAIL por testigo extra/omitido sin que exista defecto. Esto afectará a decenas de cadenas reales, no a un caso raro.
Corrección: definir banda de frontera |θ−45| ≤ 1e-9°. Dentro de ella el consumidor no exige coincidencia de pertenencia al conjunto de testigos, sólo registra `boundary_witness` y verifica que el ángulo recalculado coincide con tolerancia. Fuera de la banda, exactitud total como está.

**2. "Rechazar campos desconocidos" aplicado al NPZ rechaza el censo real.**
El NPZ guardado se escribe con `**seg` (líneas 199-203), o sea claves del extractor que el plan no enumera. Un consumidor que rechace claves desconocidas falla sobre el único archivo que debe leer. Además, `chain_offsets` es necesario para el cruce de conteo y el plan ni lo lista.
Corrección: separar reglas. NPZ: claves requeridas `point_offsets, chain_points, closed, chain_offsets` presentes y bien formadas; otras claves se listan en el recibo y se ignoran. JSON de salida: esquema cerrado, campos desconocidos rechazan.

**3. Terminal no exacto: ¿rechazo de unidad o DEGENERATE?**
Ítem 1 pone "terminal exacto" como validación de archivo (rechaza todo); ítem 2 lo pone por cadena. Si `shore.chain` cierra con tolerancia tipo 1e-6 (la misma que usa `cross_key_endpoints`:65), una sola cadena con pts[-1] a 1e-9 de pts[0] y flag closed=True tumbaría la unidad entera y no se produciría ningún censo.
Corrección: por cadena, DEGENERATE con razón `closure_mismatch` y distancia registrada. Reservar el rechazo global para offsets rotos, shapes incoherentes y hash incorrecto.

**4. Estado NO_RAW_TURN_FINDING con cero vértices evaluados es un falso "sin hallazgo".**
Cadena abierta de 2 puntos: válida, longitud positiva, ningún vértice interior. Según el ítem 4 recibe NO_RAW_TURN_FINDING_NOT_ACCEPTANCE, indistinguible de una cadena medida y limpia. El sufijo NOT_ACCEPTANCE no corrige la confusión entre vacuo y medido.
Corrección: estado `NO_EVALUABLE_VERTEX` cuando evaluated_vertices=0; el consumidor rechaza NO_RAW_TURN_FINDING con evaluated_vertices=0.

**5. Metamórfico "rotación rígida" promete lo que el propio plan niega.**
Rotar un cuadrado 37° en coma flotante convierte estaciones colineales de giro 0 en 1e-14° y mueve vértices de 45° exactos a un lado u otro del umbral. El test afirmaría "conserva conjunto de giros no nulos" y fallaría por ruido, contradiciendo "sin prometer invariancia de ruido".
Corrección: rotaciones de múltiplos de 90° y reflexiones de eje (exactas), o comparación con tolerancia angular 1e-9 excluyendo testigos en banda de frontera. Lo mismo para traslación con coordenadas no representables.

**6. Falta el cruce de conteo contra chain_offsets.**
El plan declara evaluated_edges pero no lo compara con `segments=len(order)` del censo. Es la comprobación más barata contra off-by-one en el recorte de la repetición terminal: para cerrado, len(pts)−1 == segments; para abierto, len(pts)−1 == segments.
Corrección: el consumidor exige igualdad por cadena; desacuerdo rechaza la unidad (es inconsistencia del archivo, no geometría).

**7. Giro de ±180° tiene signo indefinido.**
Espiga [A,B,A,C,A] tras recorte: giro en B con cross=0, dot<0. atan2(0.0,−x)=+180, atan2(−0.0,−x)=−180. Productor y consumidor con operaciones distintas pueden dar signos opuestos y el test "testigo cambiado" fallaría. La inversión de orden también cambia signos, así que el metamórfico de reversión debe comparar valores absolutos.
Corrección: comparar |giro| para pertenencia y valor de testigo; firmado sólo como dato informativo; canonizar 180 a positivo.

**8. La hipótesis se declara pero no se mide.**
Sin un recuento, el resultado será un JSON y nada que confirme o refute "el giro de cierre queda fuera del screen". No hace falta comparar con el screen simplificado (geometría distinta, no comparable).
Corrección: reporte global con tres enteros: cadenas cerradas, cerradas con |giro i=0| ≥45, y de éstas cuántas no tienen ningún otro vértice ≥45. Declarar explícitamente que los conteos crudos no son comparables con chain-diagnostics.json.

## Observaciones menores

- "Cero longitudes" debe fijar umbral. path_array usa 1e-8; dos vértices a 1e-13 producen ángulo basura sin ser cero exacto. Recomiendo el mismo 1e-8 declarado como constante de la unidad.
- Con ≥45 sobre vértices crudos, las listas de testigos serán de miles por cadena. Es útil, no un defecto, pero el "reporte compacto" prometido no cuadra. Guardar testigos en NPZ aditivo y en JSON sólo conteos y hasta N testigos por cadena.
- Longitud por arista: 16 ULP del total no detecta cambios de 1e-10 en una arista, lo cual es irrelevante, pero el test negativo "longitud alterada" debe alterar más que la tolerancia o no prueba nada. Añadir comparación por arista con 4 ULP relativos.
- Cadena abierta con extremos coincidentes: no cerrar es correcto; registrar `endpoints_coincide=True` como dato cuesta nada.

## Lo que está bien

Recorte de UNA repetición más índices modulares cubre bien la pérdida de cierre de la línea 80; [A,A] residual cae en longitud cero. Consumidor sin importar productor ni shape_patterns rompe la tautología principal. Identidad coseno con 2e-14 es acuerdo aritmético legítimo, no umbral de calidad, y el plan lo dice. El mutante que omite i=0 con máximo idéntico es el test correcto para esta unidad. Presupuesto sobrado para 1.030 cadenas.