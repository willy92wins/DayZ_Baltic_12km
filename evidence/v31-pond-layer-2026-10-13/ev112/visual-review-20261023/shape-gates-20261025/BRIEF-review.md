Revisión adversarial independiente, SOLO LECTURA, de los nuevos controles de formas artificiales EV112. Modelo solicitado Fable5.1 por CLI nativo, sondeado PONG hoy. Codex ejecuta e integra por petición viva. No uses herramientas de escritura, shell, MCP, web, agentes ni git. No edites memoria ni ningún archivo dentro/fuera del workspace; responde por stdout, el host conserva el informe. Windows host directo, no bindfs.

Lee estos cuatro archivos completos en el worktree C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c:
1. plans/ev112-shape-gates-20261025.md
2. tools/quality/shape_patterns_ev112.py
3. tools/quality/screen_shapes_ev112.py
4. tests/test_shape_patterns_ev112.py

Si existe, consulta E:/DayZ-Baltic-Build/shape-gates-20261025/s3-v2/report.json y resumen de rivers.json/terrain.json con lecturas acotadas, no cargues JSON grandes completos. Código dependiente solo si un hallazgo lo exige: tools/terrain/wrp0wzd.py, tools/water/streambed_kit_v31.py (centreline_world y rec_frame), tools/water/verify_compiled_stream_pilot_v31.py:40-90, tools/water/audit_stream_visibility_ev112.py:wet_span, tools/terrain/despike_v31.py:prominence.

Contrato: detección offline de patrones geométricos (codo entre piezas, escalera rotada, rectas largas, pirámides anchas, transiciones rectangulares). Los positivos son REVIEW_REQUIRED, bloquean aceptación; NO se afirman defectos universales ni un PASS estético. 53 pruebas anteriores no equivalen a mapa aceptado. S3 tiene hashes fijos y geometría del piloto no se expande ni despliega. Cualquier cobertura incompleta queda abierta. Las máscaras protegidas se etiquetan, no ocultan ni dan permiso de edición. El lote puede cerrar con resultados reales rojos y backlog visual; el objetivo es un verificador que no mienta.

Busca contraejemplos concretos que rompan su propio contrato: pérdida de piezas/empalmes, geometría distinta de la colocada, orientación/trimming incorrecto, falsas alarmas en los controles naturales previstos, bypass por NaN/vacío/cobertura, sensibilidad a dividir/remuestrear y costes descontrolados. Distingue requisito del plan, mejora de alcance y preferencia. No exigir un clasificador universal de estética, todas las ramas/receptores ni validación de render que el lote no afirma.

Devuelve SOUND / SOUND-with-fixes / UNSOUND, hallazgos P1/P2 con path:line, consecuencia y repro ejecutable (snippet unittest o comando propuesto; no lo ejecutes). P1 bloquea solo con repro del contrato; sugerencias sin repro a backlog. Añade límites y lista de rutas externas modificadas (debe ser cero por herramientas de solo lectura). Presupuesto20min; una revisión, sin re-auditoría ritual.
