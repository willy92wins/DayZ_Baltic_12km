# Evaluación del diagnóstico rechazado (solo lectura)

Este consumidor parte exclusivamente del `rejected-diagnostic.npz` fijado por hash y del recibo `REJECTED_EXACT_POSTGATES`. No acepta un artefacto accepted, no crea un archivo de terreno y no ejecuta build/runtime.

Reutiliza funciones acotadas del consumidor anterior para confirmar el preflight de 499 unidades, comprobar cruces/signos PF, medir mínimos y pendientes; usa `consumer-global/verify_layer.py` y el índice EV93 fijado para volver a medir cobertura ODOL en memoria. Reconstruye el coste con la matriz A preparada y compara la energía cerrada con la energía raw bajo la misma fórmula y allowance original. La energía debe seguir fallando; el estado final siempre será diagnóstico no promocionable.

La procedencia del recibo contiene 12 claves en `source_readset_start` y 25 en `source_readset_end`. El comprobador exige que las 12 iniciales permanezcan idénticas, rehash todas las entradas finales y los 14 `input_readset_start`; informa el crecimiento de la lista sin afirmar que ambos mapas sean iguales. Es un readset ampliado durante la ejecución, no una autorización para omitir entradas.

La evaluación cubre únicamente el contexto Oredezh de 15×15, sus 121 variables, las 144 celdas incidentes y las 200 caras compiladas preparadas. El metadato de terreno se hereda de B en una copia de alturas en memoria; no se serializa ni se considera candidato.

Validación preparatoria:

```powershell
$py='C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe'
& $py -m py_compile 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\rejected-diagnostic-assessment-v1\assess_rejected_diagnostic.py'
& $py -m unittest discover -s 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\rejected-diagnostic-assessment-v1' -p 'test_assess_rejected.py'
```

La única evaluación real se propone en una salida nueva:

```powershell
& $py 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\rejected-diagnostic-assessment-v1\assess_rejected_diagnostic.py' --output 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\rejected-diagnostic-assessment-v1\run-01\assessment.json'
```

No ejecutar esa última línea sin autorización del integrador. Un fallo de lectura/pin detiene la evaluación; una puerta geométrica fallida se conserva como tal. No hay estado que pueda promocionar el diagnóstico.
