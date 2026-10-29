Revisión adversarial de Q02B2, sólo lectura, sin herramientas, sobre el texto del plan.

**Veredicto: NEEDS-WORK.** La prueba de prefijos es correcta y los marcos de índice cuadran, pero el contrato tiene huecos que permiten emitir REAL_CONTOUR_NUMERIC_PILOT_ONLY con un productor vacío, y deja sin definir unidades y estados que el plan exige congelar antes del código.

## Lo que verifiqué y es correcto

**Prueba de prefijos exactos (§2).** Con a_i, b_i enteros y A_j, B_j sumas enteras exactas, A_s minus A_r es exactamente la suma de a_i en [r,s) para r ≤ s. La envolvente [(A_s−A_r)/2^48, (B_s−B_r)/2^48] coincide con la suma dirigida de extremos por arista. La resta cruzada [A_s−B_r, B_s−A_r] sería estrictamente más ancha y el plan la excluye. Costura cerrada como suma de [r,n) y [0,s) es correcta. Reverso como rango [k−m,k) con A_k−A_{k−m} preserva extremos por conmutatividad. Sin objeción.

**Marcos de índice (§3).** Comprobados a mano:

| cadena | puntos NPZ | core | segmentos | consistente |
|---|---|---|---|---|
| longest, abierta | 13421 | 13421 | 13420 | sí, n−1 |
| first_open | 234 | 234 | 233 | sí |
| short_closed | 7 | 6 | 6 | sí, cierre repetido retirado |
| degenerate, cerrada | 5285 | 5284 | 5284 | sí |

Anclas [0, n//2, n−1] cuadran en las tres cadenas con consultas.

**Constante T.** float64(1e-8) tiene exponente 2^−27 y significando 6044629098073146 = 2×3022314549036573, luego T = 3022314549036573/2^78 es la representación exacta. Verifiqué exponente y el doble del numerador por consistencia, no los dígitos del significando bit a bit.

**Consumidor sin prefijos.** Acumular extremos caminando aristas desde el ancla es independiente de los prefijos del productor y debe dar los mismos enteros. Correcto.

## Hallazgos

**H1 (§2, testigos). Falta exigir estrechez y positividad de a_i, b_i. Bloqueante.**
Contraejemplo: productor emite a_i = 0 y b_i = 2^4096−1 para toda arista. Cumple a_i ≤ sqrt(q)·2^48 ≤ b_i, el consumidor "verifica ambos testigos" y los acepta, todos los prefijos cruzan frontera, las 54 consultas salen SUPPORT_UNCERTAIN, productor y consumidor coinciden exactamente, contrato/identidades/certificados/registro completos, y se emite REAL_CONTOUR_NUMERIC_PILOT_ONLY. Además a_i = 0 provoca división por cero en t = (h−S)/L.
Fix mínimo: el consumidor verifica a_i² ≤ q·2^96 ≤ b_i², a_i ≥ 1 y b_i − a_i ≤ 1 en racionales exactos; cualquier violación invalida el certificado de cadena, no la consulta.

**H2 (§2, soporte en abiertas). Semántica de soporte para anclas de extremo indefinida. Bloqueante para el contrato.**
Con anclas 0 y n−1 la distancia a un extremo es cero. Si el soporte es bilateral (ventana ±h), sólo h=0 tiene soporte en esas anclas y 36 de las 54 consultas son triviales por construcción. Si es unilateral, el plan no dice qué dirección se reporta ni cómo se mapea a los estados Q02B1. Contraejemplo: dos implementaciones conformes al texto producen estados distintos para (longest, ancla 0, h=6).
Fix mínimo: fijar en el contrato resultado por dirección (forward, backward) con estado independiente cada una, y declarar el mapeo a los estados Q02B1.

**H3 (§2, presupuesto). "Operación" no tiene unidad definida.**
Con 14000 aristas y total 4000000, el promedio es ~285 operaciones por arista. Si una operación es una operación bignum, isqrt por Newton cabe; si es por bit o por dígito, nada cabe y todo termina en RESOURCE. El contador es inauditable sin unidad.
Fix mínimo: definir operación como llamada contada a una primitiva aritmética sellada (suma, mul, divmod, isqrt, comparación) y publicar la lista en el contrato.

**H4 (§2, degeneración sobre cadenas seleccionadas). Estado no definido.**
Si longest contiene una arista con q < T², el plan dice que invalida la cadena. No existe estado de salida para "cadena seleccionada invalidada en Q02B2 pese a prior_degenerate_reason null", ni se dice si el piloto completo sigue siendo emitible con 0 o 1 cadenas vivas.
Fix mínimo: estado CHAIN_DEGENERATE_DISCOVERED con índice de arista y q; el piloto completo exige las tres cadenas con consultas vivas, si no INCONCLUSIVE.

**H5 (§1/§3, identidad de segmentos).** "Revalidar offset/identidad" no dice qué se comprueba del arreglo de segmentos. Contar 13420 entradas no prueba que el segmento k una los puntos k y k+1 de la misma cadena.
Fix mínimo: verificar por segmento los dos índices de punto contra point_offset, y la clausura exacta bit a bit del último punto en cerradas, con rechazo explícito si difiere.

**H6 (§2, acotación de 4096 bits).** Coordenadas float64 pueden tener exponentes grandes o diminutos; q·2^96 y las sumas de 14000 aristas sólo caben en 4096 bits si se acota el exponente de entrada. Sin cota, un NPZ válido pero con coordenadas extremas dispara RESOURCE e INCONCLUSIVE sin diagnóstico.
Fix mínimo: rechazar en carga coordenadas no finitas, subnormales o con |x| ≥ 2^32, y registrar el motivo.

**H7 (§2, frontera).** El test interior S_hi < h < N_lo es correcto, pero el plan no dice que BOUNDARY_UNCERTAIN se aplique también cuando h cae en el hueco [N_lo, N_hi] entre dos segmentos consecutivos de la búsqueda monotónica. Es consistente con el texto, pero debe ser explícito para que el consumidor pueda exigirlo.

## No verifiqué

- Semántica real de estados y primitivas Q02B1 (ab1977bc, ef844931): asumí los nombres del plan.
- Que el hash core_float64_le_sha256 y los offsets de Q02A correspondan al NPZ b661.
- Viabilidad de 120 s/512 MiB para verificar 13420 testigos en racionales: parece holgado pero no lo medí.
- Las métricas algebraicas "selladas" y su comparación exacta.
- Mapa, calidad, naturalidad y C1: fuera de alcance y no acepto nada de eso por estas pruebas.

## Cierre

La prueba y los marcos son sólidos. El contrato no puede congelarse hasta cerrar H1 a H4; H5 a H7 son correcciones pequeñas de texto. Con esos siete puntos cerrados, el plan pasaría a SOUND-with-fixes sin cambio de alcance.