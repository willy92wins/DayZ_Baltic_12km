**Veredicto: SOUND-with-fixes.** El consumidor cumple el plan en lo esencial: no importa al productor, rehace cada terna con escalares propios, usa el criterio algebraico distinto de la adjudicación 1 con Fraction (`verify_closed_perimeter_ev112.py:144-151`), coseno 2e-14, 4/16 ULP, esquema cerrado en todos los niveles y rechazo de PASS. Los defectos son de la suite y de un artefacto de publicación, no del contrato numérico.

**Hallazgos**

1. **Metamórficos no verifican el "conjunto geométrico" de giros** (plan 62-63). `tests/test_closed_perimeter_ev112.py:208-230` usan SQUARE, cuyos cuatro giros son 90, y comparan `sorted(absolute_turns_deg)`.
   Consecuencia: un productor que asigne el giro del vértice i al vértice i+1 (o que mida el cierre en el vértice equivocado) pasa 20, 21, 22 y 24.
   Contraejemplo: polígono asimétrico (0,0),(10,0),(10,4),(6,4),(6,10),(0,10) cerrado tiene giros distintos por vértice; con rotación de origen el multiconjunto se conserva aunque el emparejamiento XY esté desplazado.
   Fix mínimo: usar ese hexágono en L y comparar `set((tuple(xy), round(abs,9)))` construido desde `vertex_xy`/`absolute_turns_deg`, no la lista ordenada.

2. **Subdivisión colineal sólo en abierta; nunca sobre la arista de cierre** (plan 63-64). `test_23` (línea 232) es abierta.
   Consecuencia: la propiedad central de Q02A, que el cierre no dependa del origen de la lista, no se prueba cuando la arista (core[-1], core[0]) cambia de vértices.
   Contraejemplo: SQUARE con (0,5) insertado entre (0,10) y (0,0). Debe dar 5 vértices evaluados, giro 0 en (0,5), 90 en i=0 y `closure_turn.is_witness` True; además el consumidor debe aceptar.
   Fix mínimo: añadir ese caso y uno que subdivida la arista (core[0], core[1]) y compruebe que el testigo i=0 persiste.

3. **nextafter sin referente racional y sin el vértice de cierre** (adjudicación 5, 100). `test_19` (199-206) codifica a mano False/True/True sobre una abierta.
   Consecuencia: el rasgo diferencial de esta unidad, el testigo exacto en i=0, no está cubierto en la frontera; y ambos módulos podrían compartir un sesgo en Fraction sin que el test lo detecte (hoy los valores son correctos: atan(1-ε)<45).
   Fix mínimo: calcular en el test `2*dot**2 <= n2a*n2b` con Fraction propio como referente, y añadir un cerrado donde el vértice 0 sea el casi-45: p.ej. core (1,0),(2,y),(2,10),(0,10)… o más simple, rotar el origen de la abierta de forma que el vértice crítico quede en i=0 de un polígono cerrado y afirmar `closure_turn.is_witness` para y∈{1-ε:False, 1:True, 1+ε:True}.

4. **No existe el resumen pequeño para publicación** (adjudicación 6, 101-105). `closed_perimeter_ev112.py:278-280` sólo escribe el JSON completo (108k aristas y giros, decenas de MB).
   Consecuencia: publicar implica recortar a mano el JSON completo, sin hash ni verificación del recorte.
   Fix mínimo: opción `--summary-output` que escriba `{schema_version,status,threshold_deg,input_sha256,summary}` con el mismo `open('x')`, y una comprobación en el consumidor de que ese resumen coincide con el calculado (reusar `expected_summary`, línea 314).

5. **Rama muerta e inconsistencia con cadenas vacías.** `closed_perimeter_ev112.py:193-196` trata `stored==[]` como DEGENERATE, pero `_validate_arrays:115-117` ya rechaza la unidad entera porque 0-1≠Δchain_offsets.
   Consecuencia: una cadena vacía en el censo guardado aborta todo Q02A en lugar de registrarse como DEGENERATE, contradiciendo "cadenas inválidas geométricamente son DEGENERATE" (plan 28), aunque sea coherente con la adjudicación 2.
   Fix mínimo: decidir explícitamente. O eliminar la rama muerta y documentar "cadena vacía => rechazo de unidad", o aceptar Δpuntos=0 con Δsegmentos=0 como excepción y conservar la rama. No cambiar nada sin recibo del censo real.

6. **Tolerancia innecesaria en campo alias.** `verify:246` admite 1e-12 entre `angles_deg` y `absolute_turns_deg`; el productor los copia exactamente (línea 236).
   Consecuencia: pequeña, pero contradice "testigos exactos" y abre una ventana de edición sin detección.
   Fix mínimo: igualdad exacta `float(alias) != float(absolute)`.

7. **Excepciones no-ValueError en uso como biblioteca.** `verify:207` hace `x not in _REASONS` sobre un set; si el reporte trae una lista, lanza TypeError. El CLI lo captura (359), los tests exigen ValueError.
   Fix mínimo: `isinstance(reason, (str, type(None)))` antes de la pertenencia.

**Comprobado y correcto frente al plan**

- Criterios de testigo equivalentes y exactos: |cross|≥dot ⇔ 2·dot²≤|a|²|b|² para dot>0; Fraction antes de restar en ambos.
- Mutante que omite i=0 falla aunque el máximo restante sea idéntico (test_26 con SQUARE, todos 90), vía longitud de lista de testigos (`verify:274`).
- Espiga canonizada a +180 en productor (153-154) y exigida en consumidor (269-272); rango (-180,180] verificado.
- Orden de degeneraciones idéntico en ambos módulos; `closure_mismatch` no suelda; abierta coincidente no se cierra; `closure_turn` nulo exigido en abiertas y degeneradas (301-302).
- Sin PASS: `status` fijo, claves exactas en global/summary/chain/witness/closure.
- SHA externo antes de leer NPZ, `allow_pickle=False`, salida exclusiva con `open('x')`, NaN/Infinity rechazados al cargar JSON.

**Riesgo residual, no bloquea**

Perímetro: productor usa `np.sum` por pares (235), consumidor `math.fsum`. Para la cadena más larga del censo, la suma de discrepancias de hasta 4 ULP por arista más el error por pares podría rozar 16 ULP del total. Es la constante del plan; si ocurre, el fallo conserva recibo y se reevalúa, como exige la sección de ejecución. Sugerencia barata: que el productor también use `math.fsum`, lo cual no viola independencia porque no comparte código ni constantes, sólo la biblioteca estándar.

**Resumen**: el contrato numérico y el esquema del consumidor están bien; antes de ejecutar sobre el censo real conviene aplicar 1, 2 y 3 (suite) y 4 (artefacto de publicación). 5 requiere una decisión explícita, no código especulativo.