Revisión independiente, sólo lectura, sobre el plan y las fuentes pegadas. No abrí más ficheros ni ejecuté nada.

**Veredicto: SOUND-with-fixes.** La separación medida/aceptación, el pin del NPZ, la no soldadura y la ausencia de PASS/NATURAL son correctas. Hay cinco huecos que impedirían implementar sin reinterpretar, y la puerta numérica sigue abierta.

## Hallazgos y cambios mínimos

1. **Puerta numérica pendiente (bloqueante antes de autoría).** "32 ULP" no está definido cuando la referencia es 0 (estación 0, desviación de un punto colineal) y el consumidor reconstruye por otro algoritmo, así que el error de prefijo compensado frente a caminata de aristas no es de 32 ULP del valor sino del orden eps·max(|coord|, L_cadena)·k. Cota justificada por propagación de primer orden, fijada antes de ver el mapa:
   - posiciones, longitudes, estaciones, desviación: absoluto `1e-9 m` (eps·1e4 m·~50 operaciones ≈ 1e-10, margen 10x). Requiere consignar en el reporte el máximo |coord| y la cadena más larga del NPZ para confirmar que la premisa de magnitud se cumple.
   - giro y curvatura: condicionados por 1/cuerda. Declarar `|Δθ| ≤ 4·1e-9 / min(|AB|,|BC|) rad` y curvatura relativa `1e-8`, con UNDEFINED si cualquier cuerda `< 1e-8 m` (misma frontera de degeneración que `closed_perimeter_ev112.py:65`, reutilizada como constante, no como código).
   Si no se acepta esta derivación, hacer un discovery acotado de 30 s: productor y consumidor sobre los seis oráculos, registrar la discrepancia máxima, congelarla con margen 10x antes de tocar el NPZ.

2. **Fixtures incompatibles con h fijo.** `open_l.json` mide 7 m y `rational_arc.json` ~17.9 m; con h=6 casi todas las ventanas serían INSUFFICIENT y el oráculo no prueba nada. Cambio: permitir conjunto h parametrizable en pruebas (p. ej. {1,2,3}) manteniendo {6..96} pineado sólo para producción, o escalar fixtures nuevos por factor entero. Además, "U con cuerda nula" es infactible para una U simple: A y C caen en piernas paralelas y nunca coinciden. Sustituir por una espiga ida-vuelta `(0,0),(6,0),(0,0)` con B en la punta, que sí da |C−A|=0, o por un lazo abierto autotocante.

3. **Convención de frontera no congelada.** "sumas de giros interiores" exige fijar si B cuenta y si un vértice exactamente en s±h cuenta. Fijar: interior = vértices con `s−h < s_v < s+h`, B incluido, A/C nunca. Estación exactamente en vértice: `(segmento que empieza en ese vértice, fracción 0.0)`, con índice modular en cerradas. Sin esto, productor y consumidor divergen legítimamente.

4. **Tamaño del reporte frente a 1 GiB.** El plan exige exactamente todos los vértices × 5 escalas × 2 direcciones con procedencia, pero no conoce N. Un JSON anidado puede superar memoria y los 180 s antes del primer censo. Cambio: leer sólo shapes del NPZ con `np.load(mmap_mode='r')` en el discovery, estimar filas, y publicar el reporte completo en NPZ/NDJSON de filas planas con un `summary.json` cerrado que lleve su SHA, como ya hace Q02A con `full_report_sha256`.

5. **Cadenas con `closure_mismatch` y cortas.** El plan dice conservarlas con razón pero no si se ventanean. Fijar: cadenas con razón de degeneración no reciben ventanas, aparecen con estado DEGENERATE y cuentan en cobertura; no se tratan como abiertas.

## Comprobaciones

- **Datos reales:** pin por SHA y lectura exclusiva del NPZ correctos. El endpoint repetido debe retirarse por igualdad exacta, nunca por tolerancia, coherente con Q02A.
- **Contrato:** esquema cerrado y estados UNDEFINED/INSUFFICIENT bien separados de ausencia de fallo. Añadir `h_set`, `max_abs_coord`, `max_chain_length` al encabezado.
- **Numerics:** hypot y sumas compensadas adecuadas. La curvatura de tres puntos no es la de un círculo inscrito; el plan ya lo advierte.
- **Independencia:** consumidor sin importar productor ni Q02A/Q17A, con cargador propio. Metamórficos: reversión debe invertir signo de giro, desviación y curvatura; dejarlo explícito.
- **Performance:** viable con búsqueda binaria sobre prefijos; el riesgo real es el punto 4.
- **Cobertura:** la falta de oráculo para periodicidad es aceptada; no hay afirmación de detección.
- **Camino cerrado:** no toca mapa, máscaras ni etiquetas; no promueve Q01; no compara con los 11921 giros. Peligro residual: que las escalas h se filtren luego como tolerancias. La bandera `calibration_ready=false` lo mitiga sólo si Unidad2 queda bloqueada por discovery propio, como ya exige el plan.

## Hipótesis física frente a puerta numérica

Son cosas distintas. La puerta numérica (punto 1) es verificable y debe cerrarse ahora. La hipótesis de que ventanas multiescala separan giro de celda y cambio persistente no se prueba con estas medidas ni con fixtures sintéticos; requiere el referente natural de Unidad2, que hoy no existe y no debe inventarse. Lo correcto es implementar Unidad1 como instrumento diagnóstico y dejar la hipótesis explícitamente NO_EVALUADA en el reporte.

Con los cinco cambios incorporados al plan de código, la unidad puede pasar a autoría dentro de los presupuestos declarados.
