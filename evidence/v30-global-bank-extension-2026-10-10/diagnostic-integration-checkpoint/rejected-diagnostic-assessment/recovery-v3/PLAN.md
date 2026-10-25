# Recovery v3: completar preflight sin ejecutar geometría

Esta copia corrige únicamente la lectura de los readsets de `prepare_wet_bank_matrices.py`. El recibo de preparación tiene 21 claves lógicas; se resuelven por `PATHS` del preparador fijado. `EXPECTED` fija 20 fuentes estáticas y excluye intencionadamente `retained_selection`; esa entrada dinámica queda ligada por el SHA del recibo de preparación y se vuelve a hashear en su ruta resuelta. El readset de retained units tiene 666 claves de ruta absoluta y se valida como tal. El helper original y los intentos anteriores no se editan.

La primera evaluación real de recovery v2 (`run-02-error-note.json` en el directorio v2) falló antes de geometría en 4.096 s: el helper trató la clave lógica `selection` como ruta y produjo `FileNotFoundError`. Era una transcripción del tool output comunicada por el integrador, no un informe generado por el evaluador; no se creó assessment ni candidato. La copia de v3 resuelve los aliases y añade el preparador como dependencia fijada. La recuperación v1 y el primer error de v2 también permanecen preservados en sus ubicaciones anteriores.

`preflight-real-run-03.json` es la comprobación real que carga identidad/aprobaciones, preparación, revisión independiente, 499 retained units, linaje del solve anterior y el NPZ diagnóstico; confirma 121 variables y 114 cambios estructurales. Termina antes de invocar los controles geométricos. `direct_pf`, `d8_check`, `local_new_minima`, `compare_face_inventory`, `exposed_topology` y `coverage_from_index` fueron cotejados estáticamente por revisión independiente contra sus definiciones y callsites: no se señaló otro mismatch de contrato. El preflight no constituye ejecución de esas puertas ni un resultado geométrico.

Verificación usada con GIS Python:

```powershell
$py='C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe'
$d='E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\rejected-diagnostic-assessment-v1\recovery-v3'
& $py -m py_compile (Join-Path $d 'assess_rejected_diagnostic.py') (Join-Path $d 'verify_polished_diagnostic.py') (Join-Path $d 'test_assess_rejected.py')
& $py -m unittest discover -s $d -p 'test_assess_rejected.py'
& $py (Join-Path $d 'assess_rejected_diagnostic.py') --self-test
& $py (Join-Path $d 'assess_rejected_diagnostic.py') --preflight-only --output (Join-Path $d 'preflight-real-run-03.json')
```

El status de este artefacto es `PREFLIGHT_ONLY_PASS_NO_GEOMETRY`; no acepta ni promueve el diagnóstico. No hay autorización ni evaluación geométrica en recovery-v3.
