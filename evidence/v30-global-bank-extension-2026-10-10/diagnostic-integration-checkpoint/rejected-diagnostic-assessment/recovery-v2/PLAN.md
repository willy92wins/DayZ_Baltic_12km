# Evaluación del diagnóstico rechazado — recovery v2

Este consumidor evalúa únicamente el diagnóstico `rejected-diagnostic.npz` fijado por SHA y su recibo `REJECTED_EXACT_POSTGATES`. Nunca acepta ni promociona el artefacto, no escribe terreno y no ejecuta build o runtime. La geometría se limita al contexto Oredezh 15×15, sus 121 variables, 144 celdas incidentes del núcleo declarado y el inventario compilado local preparado; el informe distingue las celdas incidentes reales de los cambios efectivos.

La versión previa (`before-fix-324877/`) y el error del primer intento se conservan. La transcripción recibida del tool output está en `../run-01/execution-error.json` (no es una salida original del evaluador). El error fue anterior a geometría: `approved_control_sha` identifica `baseline-control.json`, no `check_baseline_control.py`. La fuente real del driver muestra que la aprobación se compara con el campo `control` del archivo de recibo; el control JSON tiene SHA `7cf95dd2061efaf6014ed09149388d171c4b6bc021ee2cefa111c2db2206d068`. El script de control continúa fijado por separado.

`--identity-only` valida los 30 pins, los cuatro hashes aprobados, el recibo rechazado, su readset y el recibo positivo B sin cargar ni evaluar geometría. Su resultado verificado está en `identity-only-run-01.json`; reporta `READ_ONLY_IDENTITY_PASS`, `geometry_executed=false` y `accepted=false`.

Validación del consumidor:

```powershell
$py='C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe'
$d='E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\rejected-diagnostic-assessment-v1\recovery-v2'
& $py -m py_compile (Join-Path $d 'assess_rejected_diagnostic.py') (Join-Path $d 'test_assess_rejected.py')
& $py -m unittest discover -s $d -p 'test_assess_rejected.py'
& $py (Join-Path $d 'assess_rejected_diagnostic.py') --self-test
```

Comprobación de identidad, sin evaluación geométrica:

```powershell
& $py (Join-Path $d 'assess_rejected_diagnostic.py') --identity-only
```

La única evaluación geométrica, si el integrador la autoriza, debe usar un destino nuevo en recovery v2:

```powershell
& $py (Join-Path $d 'assess_rejected_diagnostic.py') --output (Join-Path $d 'run-01\assessment.json')
```

El informe conserva el fallo de energía como puerta explícita y distingue el fallo simultáneo de cualquier otra puerta. No existe estado promocionable. La evaluación es estática e indexada; no confirma visualmente el resultado, el agua dinámica ni el motor.
