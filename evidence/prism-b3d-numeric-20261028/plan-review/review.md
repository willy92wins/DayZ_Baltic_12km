**Veredicto: SOUND-with-fixes.** El plan B3D es coherente con las fuentes ancladas y no es tautológico, pero hay cinco precisiones mecánicas que Codex debe fijar en contrato/consumidor antes de implementar. Ninguna mueve controles, cambia etiquetas ni relaja igualdades.

## Verificado en fuentes

- **Lector y EOF.** `tools/water/review_compact_collision_v31.py:16-21` lee 4 LODs y rechaza cola sobrante. Sirve como lector fijado; el consumidor debe seguir exigiendo cabecera `MLOD 257 4` y blobs 0/2/3 byte-idénticos como en `tools/quality/verify_prism_contact_b3_ev112.py:76-78`.
- **Codificación Geometry.** Puntos en `28+16*i` y normales en `28+16*npoints+12*ni` están en `tools/quality/prism_contact_b3_ev112.py:73-75` y `:85-88`. El ancla del plan dice 78-96; corregir a 73-88 (menor).
- **Asignación única.** `verify_prism_contact_b3_ev112.py:67-69` ya exige que puntos, caras y normales cubran exactamente `range(n)`. Esto garantiza que ninguna cara exterior comparte índice normal con las caras incidentes; la condición del plan queda cubierta sin instrumento nuevo.
- **Testigo.** `evidence/prism-b3-quantization-20261028/report.json:907-1128` tiene 17 entradas; 16 pares con residuo y el par 8007/8004 con ambos extremos movidos. Comprobé a mano que en cada par `after_top - after_bottom = 0.3515625` exacto (p. ej. 7742: 0.11279988288879395 + 0.23876261711120605). Incluye un punto base (8007), así que el autor no debe asumir "sólo tapas".
- **Marcos.** `centre_fixed` y `translation_fixed` están en `report.json:1245-1254`; `world_frames_bit_exact: true` y `source_and_predicted_bbox_exact: true` (`:1132-1133`) son los valores que el consumidor debe reproducir, no leer.
- **Controles.** `original_controls` (`verify_prism_contact_b3_ev112.py:23-27`) ya fija 700 dry / 723 wet y origen [8262,7,8934]. Reutilizar tal cual.

## Hallazgos y correcciones

**F1. Definición de "exacto" y alcance de pares.** El plan limita la igualdad exacta a 36 pares. Como los 1508 componentes no seleccionados son byte-idénticos a d130 y d130 pasó el guard exacto de entrada (`prism_contact_b3_ev112.py:36`), el consumidor debe exigir `top - bottom == 180/512` en los 4560 pares, no en 36. Criterio: calcular con `fractions.Fraction(float(np.float32(y)))`; cualquier residuo distinto de cero es REJECTED_MLOD. Es más fuerte, cuesta nada y elimina la ambigüedad "¿y los otros?". Mantener además el chequeo 1e-6 vigente en `components` (`:44`) no sustituye nada; simplemente queda dominado.

**F2. Representabilidad y binding del testigo en el consumidor.** El plan pone en el autor el rechazo de `before` distinto de c769. El consumidor debe repetirlo de forma independiente: para cada entrada, `float(np.float32(v)) == v` para before y after; `before != after`; X/Z before == X/Z after == bytes de c769; índice único y dentro de los puntos de `selected_components`. Repro negativo: testigo con una entrada `after` igual a `before` o con X alterado debe dar REJECTED, no pasar como "sin cambio".

**F3. Grosor exacto también en marcos recentrados.** B3C informó `reported_world_thickness` y `rational_frames_verified` por par (`report.json:20-22`). El consumidor del paso 4 exige identidad bit a bit de ambas rutas de puntos, pero no dice que el grosor siga siendo exacto tras `f32(src - centre_fixed)` y `f32(... + translation_fixed)`. Añadir: en ambos marcos calculados, los 36 pares tocados mantienen diferencia exacta 0.3515625 con Fraction. Es la propiedad que B3C midió y la que motivó el testigo; sin ella el PASS offline no cierra el bucle con B3C. Sigue etiquetado como hipótesis sobre centro fijo.

**F4. Márgenes 700/723 por igualdad, no por tolerancia.** Como X/Z no cambian, `local_margin_m` y `world_float32_margin_m` deben ser idénticos a los del recibo B3 pinned (`prism-contact-b3-consumer-20261028/report.json`, SHA 6b29e213…). Exigir igualdad float exacta con ese recibo y mismo `witness_component`. Es independiente del autor y detecta cualquier contaminación de XZ que el mask de bytes dejara pasar por error de offset.

**F5. Separar INCONCLUSIVE de REJECTED en el consumidor.** El consumidor B3 trata todo `ValueError` como REJECTED_OFFLINE (`verify_prism_contact_b3_ev112.py:199-203`). El plan promete INCONCLUSIVE para lectura/identidad/recurso y REJECTED_MLOD para geometría; implementar el patrón `Inconclusive`/`bind` de `tools/quality/prism_b3_binary_ev112.py:22-31` para que pins, cabeceras, EOF y conteos 9120/12160/1520 no se reporten como rechazo geométrico.

## Detalles menores

- `verify_prism_contact_b3_ev112.py:79-81` desempaqueta `ob[1]` en ambas iteraciones del bucle; inocuo por la igualdad de `:78`, pero el consumidor nuevo debe leer la cabecera de cada blob.
- Máscara de normales: derivarla de `face.vertices[*].point_index` sobre el archivo guardado, no de una lista del autor. Caras laterales verticales pueden no cambiar bits; el mask las permite y la tolerancia 1e-6 vigente (`:59`) decide. Correcto, sólo documentarlo.
- Bbox: `:92` compara min/max de todos los puntos; el testigo no toca extremos según `:1132`. Mantener.
- Orientación de techo: el consumidor offline usa `normals[:,1] < -1e-10` (`:162`) y el binario `> 1e-10` tras invertir. No cambiar; anotar en contrato para evitar "corrección" errónea.
- Contrato nuevo: pinear `report.json` 6e3653bb, c769, d130, recibo B3 6b29e213, contrato-r1 5df50091, lector, autor, consumidor y tests. El autor no debe reverificar los pins internos del report B3C (rutas `C:\temp`, binarios de DayZ Tools); sólo el SHA del propio report.
- Presupuestos realistas: B3C hizo overlay completo en 3.5 s / 239 MB (`:1344-1350`); 180 s / 2 GiB sobran.

## Tests que faltan en la lista

- Positivo: aplicar el testigo real a c769 en fixture y comprobar que los 36 pares pasan Fraction exacta y que `len(mask normales)` coincide con las caras incidentes recomputadas.
- Negativo: testigo con 16 entradas (omitiendo 8007) debe fallar grosor exacto en 8007/8004, demostrando que F1 muerde.
- Negativo: candidato con un byte alterado en la sección TAGG de Geometry debe fallar `unauthorized_bytes_changed`.
- Negativo: recibo B3 con margen modificado en un ulp debe fallar F4.

## Alcance y límites

Nada aquí acredita ODOL, motor ni DayZ; el resultado máximo es OFFLINE_CANDIDATE_ONLY. B3C queda consumido y no se reabre. No se ejecutó nada ni se escribió nada.

Reconfirmación de identidad: Claude Fable 5.1 (claude-fable-5-1), revisor; sólo Read/Glob/Grep usados.

FIN_REVISION