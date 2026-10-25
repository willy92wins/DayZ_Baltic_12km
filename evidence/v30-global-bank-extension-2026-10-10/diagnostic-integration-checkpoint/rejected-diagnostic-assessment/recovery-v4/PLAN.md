# Recovery v4: corregir la llamada de topología local

Recovery-v4 parte de una copia de v3; las fuentes y los errores previos se conservan en sus carpetas originales. El fallo de la evaluación real v3 está transcrito en `run-01-error-note.json`: el caller v3 (`recovery-v3/assess_rejected_diagnostic.py:411`, SHA `212a540b…`) pasó `bctx/hctx` de 15×15; el helper v3 (`recovery-v3/verify_polished_diagnostic.py:726`, SHA `b496f355…`) recorrió rangos de celdas globales y falló con índice 862. La lectura de `verify_ev87.py:230` confirma que `corner_values` indexa el grid por coordenadas globales. Fue un error del consumidor, no un fallo geométrico ni del candidato; no se guardó assessment. El runner no debe repetirse hasta la revisión de root.

La corrección mínima pasa `base_h` y `h_full`, ambas grillas 2048×2048, a `exposed_topology`. El helper exige ahora shape `(ev87.N, ev87.N)` y valores finitos antes de recorrer caras. El test negativo verifica que el contexto 15×15 se rechace de forma clara; un test positivo valida el contrato de shape en arrays pequeños. No se cambia ninguna puerta geométrica ni energía.

La escritura de reportes ahora serializa primero con `allow_nan=False` y solo abre el destino exclusivo tras una serialización completa. El fixture con `Infinity` confirma que no queda un JSON parcial. Así se conservan errores de serialización en vez de dejar artefactos truncados.

El `preflight-real-run-03.json` copiado desde v3 es histórico de v3 y no valida estos hashes v4. La revisión estática previa del helper en v2 mencionó `verify_polished_diagnostic.py:408`; no corresponde a este bug. La batería v4 ejecutada fue GIS Python: `py_compile`, 14/14 unittest y `--self-test`. No se ejecutó preflight real ni evaluación geométrica en v4.

Archivos fuente v4:

- `verify_polished_diagnostic.py` SHA256 `a3fc62f4e4a6b9ac55400abfddb3e3c8f5e41c83381b31fe71f4f66b35d1f516`
- `assess_rejected_diagnostic.py` y `test_assess_rejected.py` se fijan en el recibo del siguiente preflight; el helper de v4 está anclado en `PINNED` del driver.

El siguiente comando de geometría no está autorizado todavía. Cuando root lo revise, el destino de evaluación debe ser nuevo y el resultado seguirá siendo diagnóstico explícitamente no aceptado; el fallo de energía original permanece como puerta FAIL.
