**Veredicto: SOUND-with-fixes.** La receta respeta el alcance: no elige pivote, no escribe WRP, no infiere ancho útil, fija hashes y rechaza fixtures autogeneradas. La derivación cerrada de `fixtures.json` cuadra con el código: mapeo fila (x,y,z)→(−z,y,x), columna (z,y,−x), ORIGIN = T+M(q+bc) con bc=(0,0,12.5) y bc curva literal. He recalculado los doce literales y coinciden con la definición. No hay falso PASS estructural. Sí hay riesgos de falso FAIL y dos huecos de verificación.

**Bugs y fixes concretos**

1. **Falso FAIL probable en `test_road_b2_recipe_ev112.py:46-47`.** Las áreas 300/225 de B0 se midieron en coordenadas locales (magnitud ≤25 m, ULP ≈2e-6). La receta mide sobre vértices mundiales float32 a magnitud ~300 (ULP ≈3e-5, redondeo ≤1.5e-5 por coordenada). Con perímetro ~74 m el error de área acumulable es del orden de 1e-3 m², mientras `places=4` exige 5e-5. Puede fallar por cuantización legítima, no por error de hipótesis. Fix: comparar con `delta` derivado del propio `world_ulp_m` publicado (p.ej. perímetro × ULP mundial) y documentarlo; esto no rebaja ninguna tolerancia de geometría del plan.

2. **Falta la aserción de área de la curva (209.4229046).** El test sólo comprueba bbox > huella en `curve_90`. El área B0 medida existe y no se reextrae; añadir la aserción con la misma tolerancia escalada, para las ocho combinaciones hipótesis/rol (la rotación en Y no cambia el área XZ).

3. **Literales de fixture no representables en float32.** 285.79664611816406 y 314.20335388183594 caen exactamente en un empate de medio ULP float32 (fracción 26104.5/32768). `road_b2_recipe_ev112.py:36-37` redondea el literal y el cálculo desde el mismo float64, así que la comparación bit a bit pasa, pero el "literal" no es el valor float32 que realmente se publica. Fix: escribir en `fixtures.json` y `derivation.md` los literales ya redondeados a float32 (o anotar el redondeo esperado), para que la fixture siga siendo independiente del cast del generador.

4. **`derivation_sha256` nunca se verifica.** `recipe.json:92` lo fija pero `predict` sólo comprueba fixtures y caras. La adjudicación exige archivar la derivación separada; añadir `require(sha(recipe['derivation'])==...)` y registrar la ruta en `inputs`.

5. **No existe salida INCONCLUSIVE.** El plan permite RECIPE_HYPOTHESES_READY o INCONCLUSIVE_DISCOVERY; el código sólo levanta ValueError (`hypotheses_not_distinct`, `invalid_polygon`, `resource_budget`). Además `main` crea el directorio de salida antes de calcular, así que un fallo deja un directorio vacío que bloquea la repetición por `fresh_output`. Fix: capturar fallos de receta y escribir `report.json` con estado INCONCLUSIVE_DISCOVERY y la razón, sin `world-faces-private.json`.

6. **`invalid_polygon` (línea 65) puede abortar por caras verticales.** Un cuadrilátero de arcén o extremo proyectado a XZ puede dar un "bow-tie" con área >0 e `is_valid` False. No es falso PASS, pero es un FAIL por proyección, no por datos. Mantener el rechazo (no descartar caras en silencio) pero emitirlo como INCONCLUSIVE con instancia/rol/índice de cara.

7. **Presupuesto 2 GiB no comprobado.** Sólo se mide tiempo, y después del trabajo. Mínimo: registrar pico de memoria (`tracemalloc` o `resource`) en el informe; el límite se declara pero no se observa.

**Observaciones menores, sin bloqueo**

- `require(np.linalg.det(matrix)==1)` con igualdad exacta: válido para las tres matrices de permutación de la UNIDAD1 (det LU da 1.0 exacto), pero fallará con rotaciones no axiales futuras. No cambiar ahora; anotar en el plan que es un criterio de esta unidad.
- Comparación `uint32` bit a bit distingue −0.0 de 0.0; no afecta a estas fixtures pero conviene documentarlo.
- `roles=={'Visual','Roadway'}` rechaza modelos con LODs adicionales conservados; coherente con B0, pero el error debería nombrar los roles hallados.
- Las comprobaciones de `test_transpose_matrix`, `test_bad_rotation`, `test_shift_center_breaks_literals` y `test_literal_not_generated` son correctas y cubren los negativos exigidos por la adjudicación.

**Verificado:** definición RAW/ORIGIN, doce literales, separación >0.03 m y >10 ULP sobre el conjunto de tres poses, pins de hash, no asignación de IDs, materiales y máscaras preservados, `usable_width='UNDETERMINED'`, lista de no observados completa. **Asumido:** `bounding_center` de los JSON B0 es el del ODOL, no recalculado. **No observado:** ejecución real de los tests, motor, WRP, conducción.

FIN_REVISION