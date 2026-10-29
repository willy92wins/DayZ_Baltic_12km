**Veredicto: SOUND-with-fixes.** Revisión estática sin ejecución. La cadena contrato externo → ledger pinado → proyección exacta → fixtures validados con `Fraction` cierra bien contra co-mutación y falsos PASS. Hay un hueco de binding en la suite y varios defectos menores.

**Verificado analíticamente (sin ver los bytes de puntos):**
- `closed_l`: aristas 36/4/16/16/4/36, área doble 40, giros [+,+,+,−,+,+] correctos para L_POINTS.
- `rational_arc` y `circle_shore`/`circle_designed`: aristas 20/10/10/20, área doble 140 y pertenencia exacta a r²=25 correctas para el octógono pitagórico.
- Los cinco metamórficos de `tests/test_geometric_corpus_ev112.py:115-150` tienen arrays esperados independientes y son correctos (rotación 90° preserva signo, inversión invierte signo y área, shift cíclico reindexa (j+2)%6, subdivisión por puntos medios con `//` es exacta porque todas las sumas son pares).
- Tipos bool: `closed`, `vertex_count`, signos de giro, coordenadas y contadores excluyen `True/False` por `type is`; `_eq` es estricto en tipo.
- Cierre: flag obligatorio, endpoints coincidentes rechazados en abiertos y cerrados, segmento nulo rechazado, NaN rechazado tanto en JSON (`parse_constant`) como en `_frac`.
- Sin imports autor→consumidor. Solo el test importa ambos.
- No hay autoría, DayZ, lease ni asociación foto/coordenadas. `human_references` es proyección literal del ledger; coordenadas, `AVATAR`, préstamo de ámbito y promoción de C1 fallan por desigualdad con la proyección.

**No verificable desde aquí:** bytes de los 11 archivos de puntos (solo hashes), estructura real del ledger (el consumidor exige `required_layers` y `automatic_evidence`, `verify_geometric_corpus_ev112.py:19`), y el primer punto de `straight_arc` (la limitación afirma que está fuera del círculo; con aristas 25/20/10/10 y giro +1 en índice 1 un candidato consistente es (5,−5), pero (10,0) daría giro −1).

**Hallazgos (orden de severidad):**

1. **La suite no pina el hash externo congelado.** `tests/test_geometric_corpus_ev112.py:19-20` recalcula `contract_sha()` del archivo vivo. Si alguien reedita `contract.json` y los puntos de forma consistente, toda la suite sigue en verde. Contraejemplo: cambiar `context` de `circle_shore` a `DESIGNED_STRUCTURE` en el contrato y regenerar; `test_build_and_verify_report` pasa. Fix mínimo: en `test_build_and_verify_report` añadir
   ```python
   self.assertEqual(contract_sha(), '5416dbef4547a5dad0fa40c0da90337ec003ebdd73dc61f149a9c8174ed5394a')
   ```

2. **Condición muerta sobre `case_ids`.** `verify_geometric_corpus_ev112.py:251` solo falla si la lista difiere de la literal **y además** está malformada; una lista distinta de 9 strings únicos pasa. La línea 382 encadena `or ... and ...` y acaba siendo equivalente a la 384. Fix: sustituir 251-254 por una comparación directa con la lista literal (o eliminar la literal y dejar solo unicidad/longitud, pero decidir una cosa).

3. **Reversión colineal cuenta como "sin giro".** `verify_geometric_corpus_ev112.py:150-154` clasifica det==0 como no-giro, incluido el caso antiparalelo. Contraejemplo: `measure([[0,0],[4,0],[2,0]], False)` devuelve `nonzero_turns: []`, igual que `long_straight`. Fix mínimo: tras calcular `det`, si `det == 0` y `vin[0]*vout[0]+vin[1]*vout[1] < 0`, `_fail('reversal edge not allowed')`.

4. **Presupuesto total de vértices no se exige en el consumidor.** `verify_geometric_corpus_ev112.py:504-511` limita 20 fixtures y 4096 por fixture, pero el total ≤4096 solo vive en el test (66). Fix: tras el bucle, `if total > 4096: _fail('corpus: total vertices exceed 4096')`.

5. **Resolución difusa de fuentes.** `verify_geometric_corpus_ev112.py:402` prueba primero `root/<pin_key>` (el archivo vivo de evidence, no la copia congelada en `sources/`) y cae a coincidencia por nombre base en 402, 421 y 437. El hash evita falsos PASS y la ambigüedad falla cerrada, pero contradice el plan de que `sources/` conserva los bytes verificados. Fix: ordenar candidatos `sources_root/pin_key`, `sources_root/basename` y eliminar el candidato `root/pin_key`.

6. **Co-mutación contra contrato anterior solo probada indirectamente.** `test_source_pointer_wrong_sandbox` falla por literal del puntero, no por hash viejo; el único test con hash externo distinto es `'0'*64` (línea 197). Fix: en el sandbox, mutar contrato+puntos+corpus y verificar con el hash original; debe fallar en `contract_sha256 mismatch`.

7. **Menores.** `verify_geometric_corpus_ev112.py:143` `prev` sin uso. Línea 271 permite features vacías en contrato mientras 203 las rechaza en corpus (falla cerrado, pero inconsistente). `main` (530-532) etiqueta cualquier excepción, incluidos OSError, como `REJECTED_CORPUS`. `tests/...:146` asignación sobrescrita en 147. `build_geometric_corpus_ev112.py:168-172` traga toda excepción al comprobar que el contrato está fuera de la salida.

**Sobre el alcance Q01/calibración:** `natural_positive_count=0`, `calibration_ready=false`, `resolved_count=0`, `c1_verdict=NOT_REVIEWED` y `visual_acceptance=NOT_GRANTED` se exigen en contrato, ledger, corpus e informe; `source_pins` del ledger debe igualar los 12 del contrato (línea 364). Los controles se copian literalmente y la salida no emite PASS/FAIL de mapa (`map_acceptance: NOT_EVALUATED`). El código no requiere calibración natural para verificar datos. Correcto.

**Recomendación:** aplicar 1, 2 y 3 antes de congelar; 4 a 6 en la misma pasada si el presupuesto de 240s lo permite. Ninguno exige reejecutar mapa ni reetiquetar casos humanos.