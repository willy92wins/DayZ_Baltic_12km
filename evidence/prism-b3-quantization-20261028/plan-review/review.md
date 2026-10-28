**Veredicto: SOUND-with-fixes (plan). Código: AUSENTE, no adjudicable.**

`tools/quality/prism_b3_quantization_ev112.py` y su test no existen en W (Glob `**/*quantization*` sólo devuelve el plan; los únicos tests prism son `test_prism_contact_b3_ev112.py` y `test_prism_b3_binary_ev112.py`). La parte "código" de esta revisión queda sin objeto; lo que sigue es adjudicación del plan contra las fuentes citadas, que sí verifiqué.

## Anclas verificadas

- `prism_b3_binary_ev112.py:97` predicción local `(A-centre).astype('<f4')`; `:86-87` mundo `fl32(dec+T)` y `fl32(src+origin)`; `:67` pose exige `T == fl32(origin+centre)`. Coincide con el [EXACT] del plan.
- `compiled_dry_road_gate_ev112.py:32,42` READER_HASHES/read_backend existen como se cita.
- `verify_prism_contact_b3_ev112.py:119-127` plano y base con `<=1e-6`; `prism_contact_b3_ev112.py:36` grosor `== THICKNESS` exacto, `:20` THICKNESS=180/512. Correcto.
- `evidence/prism-b3-binary-20261028/report.json:9-11,79-81`: sólo Y del vértice base difiere (6.576060771942139 vs 6.576061248779297), X/Z iguales, ULP mundial Y 4.768e-7. El rechazo saltó en `compiled_face_counter`, no en `local_recentering_prediction` (`prism_b3_binary_ev112.py:100-101`), luego el ODOL de component1335 SÍ coincide con la predicción local.

## Hallazgos (fixes antes de autorizar)

1. **Afirmación causal encubierta en la hipótesis** (`plan:11-12`). "pierde un bit al restar el centro… y sumar la traslación WRP" atribuye al compilador una pérdida. La evidencia dice lo contrario: el recentrado compilado fue exactamente `fl32(m-c)` para 1335; la discrepancia aparece al componer DOS marcos definidos por el instrumento, `fl32(fl32(m-c)+T)` vs `fl32(m+o)`, que son doble redondeo vs redondeo simple. Ninguno es el del motor. Fix: reformular como "las dos conversiones a mundo float32 del contrato 447d no conmutan para valores no alineados; el residuo local compilador/predicción es 0 en lo censado". El censo debe separar explícitamente residuo local (compilador) de residuo mundial (composición de marcos), por eje y componente. Repro: leer report.json:3 y comprobar que `reason` es face_counter y no local_recentering.

2. **Centro de modelo no fijado en la factibilidad** (`plan:67-73`). Un cambio de Y en Geometry puede mover `bounding_center` si ese vértice es extremo del bbox; entonces cambia T esperado y `pose_check` (`:63-67`) daría INCONCLUSIVE, no un testigo válido. Fix: la factibilidad debe (a) fijar c al valor de ODOL b2c8 y (b) comprobar que ningún Y enumerado toca min/max Y del bbox del modelo (comparar contra `model_info` guardado); si lo toca, marcar ese valor como no elegible, no asumirlo.

3. **Igualdad "exacta" sin definir bit-exacta o valor-exacta** (`plan:77-78`). `face_counter` (`prism_b3_binary_ev112.py:50-53`) compara tuplas Python: `-0.0 == 0.0`. El plan exige probar cero con signo (`:74`) pero no dice qué igualdad aplica. Fix: fijar comparación por patrón de bits (`view('<u4')`) para el censo y declarar que el consumidor B3 usaba igualdad de valor; registrar ambas si difieren. Repro: `collections.Counter([(0.0,)])==collections.Counter([(-0.0,)])` es True.

4. **"Comparar contra ODOL" en el paso 2** (`plan:31`) es parcialmente tautológico. El ODOL sólo contiene locales; el "mundo ODOL" es siempre cómputo del instrumento. Fix: dejar claro que el único contraste empírico es predicción local vs `vertex_raw`; el modelo de redondeo se valida con fixtures Fraction (exactas, round-half-even calculado a mano), no con otra llamada a `astype('<f4')`. Incluir ties exactos (mantisa par/impar), negativos, cruce 8.0 y 4.0 (ULP cambia 4.77e-7↔9.5e-7, relevante porque las Y están en 6.5–7.1), y diferencia float32–float32 que no es exacta en float64 (exponentes muy separados) para acotar la hipótesis `fl32(float64(a-b)) == a ⊖32 b`.

5. **Presupuesto 100k/1M es falsa precisión, no error**. Banda ±1e-6 con ULP 4.77e-7 da 4–5 float32 por esquina; 36 pares. INCONCLUSIVE_DOMAIN_BUDGET es prácticamente inalcanzable; aceptable como guardia, pero el informe debe listar el tamaño real del dominio por par para que nadie lea "100k" como amplitud explorada.

6. **Cobertura del censo**: el consumidor se detuvo en 1335 y recorre `groups` en orden de `named_selections`; los componentes del candidato posteriores no fueron comprobados ni en caras ni en recentrado. El plan (`:23-26`) lo pide bien; añadir que el denominador son 1520 componentes para control y candidato, con conteo de "ya adjudicados por R1" vs "nuevos".

7. **Normales**: el cambio de Y altera las normales geométricas de 8 caras; el autor B3 reescribe `normal_raw`. La factibilidad no escribe nada, pero el testigo debe anotar que una futura autoría tendrá que rederivar normales y que el aislamiento positions_only/normals_only previo no cubre el nuevo Y.

## Lo que está bien

Alcance sólo lectura, sin builds ni DayZ; INCONCLUSIVE por lectura vs FAIL geométrico; dominio vacío = conflicto del par, no UNSAT global; testigo JSON; overlay ±.02/.01 en memoria con `overlay()` (`review_compact_collision_v31.py:45`); X/Z y 700/723 intactos; FEASIBILITY_ONLY sin certificar compilación. Asociación por coordenada local predicha única con componente inconcluso si falla es correcta y no es nearest-neighbour. Grosor 45/128 es exacto en float32 para Y en [4,8) y también al cruzar 8, así que el par base/techo no introduce redondeo propio.

## Decisión para Codex

Aplicar fixes 1–4 al texto del plan (mecánicos, autorizados). Fixes 5–7 son anotaciones de informe. Escribir después el instrumento y su test; esta revisión no cubre código porque no existe todavía. B3B sigue REJECTED_BINARY; b2c8 no aprobado.

Identidad: Claude Fable 5.1 (claude-fable-5-1), revisor; sin Bash, escrituras ni git en esta sesión.

FIN_REVISION