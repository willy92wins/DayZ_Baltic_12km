**Dictamen Q03C1 (recuperación, revisión en seco sobre los cuatro R0 + contrato + oráculo): SOUND-with-fixes / CONVERGE.** Modelo servido: claude-fable-5-1 (Fable 5.1, CLI nativo). Sin herramientas, sin lectura de NPZ ni de los pins externos en E:\; todo lo que depende de Q03B6 real queda como supuesto declarado, no como verificado.

**Qué revisé y qué sostiene el veredicto**

- **Contrato y oráculo preceden al código.** Los 20 casos literales del oráculo los recomputé a mano con las fórmulas del plan (72, 36/36, 18/54, 2/70, 4/68, costura 72, contactos 1, degenerados INCONCLUSIVE, bed vertical DEGENERATE). Ninguna expectativa deriva del producto. El test ancla oracle.json por el SHA pinado en contract.json y el io sellado por digest.
- **Independencia de caminantes.** El productor hace unión por sustracción convexa incremental (`subtract`, producer líneas 46-60); el consumidor construye arreglo de rectas normalizadas enteras y clasifica centroides de celdas (consumer 85-105). Sólo comparten I/O, Budget y validadores. Las orientaciones de recta las verifiqué algebraicamente en ambos: valor positivo = lado interior para triángulo CCW tras normalizar por determinante, y el plano afín no depende de la orientación.
- **Casos de borde de altura.** Delta idénticamente 0 (contacto pleno): productor conserva todo en `clip` con `va>=0`; consumidor descarta la recta (0,0,0) y clasifica cubierto. Delta constante no 0: por signo. `height_zero_on_edge`: `above` degenera a segmento, `subtract` lo ignora por área 0; consumidor no parte y centroide da negativo. Ambos dan 0/72/0.
- **Contactos.** Par reportado sólo con área positiva; intersección no vacía de área 0 cuenta contacto, sin extremos W-B. Metamórficos comparan áreas/estados, no identidad de pares.
- **Caps y reservas.** `Budget.op` reserva bits según la fórmula literal del contrato antes de la operación Fraction; `reserve` se invoca antes de cada `append` en `clip`, `subtract`, `half` y en el bucle de celdas; `normalized` reserva antes de cada producto entero. Contadores de pieces/vertices separados por caminante. `retained` se reserva antes de materializar filas.
- **Rastro parcial.** Payload fsync, receipt exclusivo después, `prefix` exige secuencia contigua con recibos íntegros, huérfano no cuenta, truncado tolerado sólo en seq k. Consumidor sólo da FULL con manifest presente, verificados==1520 y cero no verificados. Un terminal RESOURCE_INCONCLUSIVE en cualquiera de los dos lados nunca promueve.
- **No falso PASS numérico.** `semantic` compara áreas, pares y contactos exactos; los tests de co-mutación (área, omisión de par, min_W_B, duplicado, contacto, clave, header claims, manifest promovido, fuente mutada) rechazan con REPORT/IDENTITY. `unpack` exige racional canónico sin bool.
- **consumer Q03B6.** `historical` liga `contract_sha256` del consumer guardado y pina report por bytes/SHA externos; no inventa `report_sha256`. Correcto.

**Fixes recomendados (no bloqueantes, un ciclo de corrección opcional)**

1. **selected_water_io_q03c1.py:112-113 — tipo de dtype no afirmado.** `v[:,3,:].view('<u8')` sólo es válido si `v.dtype=='<f8'`. Hoy lo garantiza indirectamente el predicado de descriptores (línea 106), pero si un descriptor fuera `<f4` el view lanzaría ValueError y saldría INTERNAL_ERROR en vez de GEOMETRY. Impacto: código de rechazo incorrecto, no falso PASS. Cambio mínimo: añadir `v.dtype==np.dtype('<f8')` y `ids.dtype.kind in 'iu'` al `need` de la línea 112.
2. **selected_water_producer_q03c1.py:97 — invariante de partición tautológico.** `covered=total-uncovered` y `below=uncovered-nofoot` hacen que `covered+below+nofoot==total` sea identidad algebraica; lo único que vigila son los `>=0`. No es falso PASS porque el consumidor recomputa las tres áreas por arreglo independiente, pero el mensaje INTERNAL_ERROR 'partition' promete más de lo que comprueba. Cambio mínimo: sustituir la igualdad por `uncovered<=total and nofoot<=uncovered`, o añadir que la suma de áreas de `cover` no supere la de `foot`.
3. **selected_water_io_q03c1.py:105 — `specs[p['archive']]`.** Un archivo del índice ausente en los specs de escena produce KeyError → INTERNAL_ERROR; debería ser IDENTITY. Cambio mínimo: `need(p['archive'] in specs,'IDENTITY','spec')`.
4. **Comparaciones de signo sin `q.cmp`** (producer `clip` 38-39, consumer `half` 32-34, bucle de celdas 90). Son comparaciones contra 0, sin producto cruzado, así que no violan la cota de bits; pero no cuentan como op. Documentar en contrato que los tests de signo son gratuitos, o tickear una vez por `clip`/`half`. No cambia resultados.

**Supuestos no verificables en seco (declarados, no fallos)**

- Que `Reader.open` de saved_scene_io_q03b6 devuelva `(arrays, actual)` con `actual` igual en forma a `arraydigestmap`, y que `desc` use claves `*.npy` (líneas 105-108 asumen ambas cosas).
- Que los 201 pilotos tengan miembros `water*` y que el 3579 tenga `bed*`; un KeyError saldría como INTERNAL_ERROR, no como falso PASS.
- Que ningún bed real agote 100000 ops/4096 bits con 4760 candidatos; el presupuesto es techo, el estado parcial está bien manejado si ocurre.
- Los 14 tests en 3.672s prueban fixtures, no datos reales; la captura 201 NPZ sigue siendo la primera prueba real de carga de campos.

**Adjudicación**

SOUND-with-fixes, CONVERGE. Ningún repro cerrado bloquea la captura; los puntos 1-3 son una corrección única opcional de 180 s que no altera resultados numéricos ni los oráculos. La captura 201 NPZ puede proceder con este dictamen y la suite; su producto debe pasar por el consumidor antes de cualquier lectura de áreas. Claims permanecen terrain/exposure/native/map = false, human_resolved 0, C1 NOT_REVIEWED. Nada aquí autoriza mapa, terreno ni fallo físico.
