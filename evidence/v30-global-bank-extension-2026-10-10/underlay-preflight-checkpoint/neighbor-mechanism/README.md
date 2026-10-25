# Recovery v2: por qué no hay vecino ULP admisible

**Resultado acotado:** el ledger termina `NO_FEASIBLE_ONE_ULP_NEIGHBOR` tras evaluar los 242 vecinos de un único nodo (`±1 ULP`). Ninguno satisface conjuntamente energía y todas las restricciones exactas/directas. No se escribió un artefacto de diagnóstico pulido. Esto no demuestra inviabilidad de movimientos coordinados ni del dominio local completo.

La fuente reproducible `inspect_no_neighbor.py` revalida el recibo/readset y ledger, reconstruye el modelo exacto mediante el polisher fijado, vuelve a evaluar solo los dos vecinos que pasan el gate de energía y comprueba sus filas Fraction y gates directos. No llama al solver. Resultado en `mechanism.json`.

Los dos vecinos pasan energía porque `closed_cost - raw_cost` es menor que el allowance `1e-7 × max(1, raw_cost)`:

| Variable | Cambio | Coste cerrado − raw / allowance | Bloqueo conjunto |
|---|---:|---:|---|
| índice 14, `(858,1184)` | `+4.7683716e-7 m` | `1.5285030e-5 / 1.5594405e-5` | Falla cuatro filas exactas de cruce P/F y el gate directo de los 116 cruces. |
| índice 74, `(863,1189)` | `−9.5367432e-7 m` | `5.0777548e-6 / 1.5594405e-5` | La altura base ya coincide con el límite inferior `8.341360092 m`; el siguiente float32 inferior queda fuera de bounds y del segmento de retícula. |

Para `(858,1184)`, las cuatro filas fallidas son los extremos superiores de los intervalos de cruce de P/F en dos celdas adyacentes: ids 22/23 y 28/29. En los cuatro casos el límite superior es el cruce de referencia base. Subir el endpoint mojado mueve el parámetro de cruce hacia fuera de ese intervalo entre `6.95e-8` y `7.53e-8` de la arista, equivalente a aproximadamente `0.42–0.45 µm` sobre una arista de 6 m. Los signos P/F se conservan. Bounds, D8 y conos pasan; el bloqueo es el límite de cruce, no D8.

Para `(863,1189)`, las puertas de cruces, signos, D8 y conos pasan; el descenso se rechaza porque intenta cruzar un límite inferior activo. Los contadores de rechazos del ledger se solapan y no deben sumarse como partición; entre los 242 vecinos hubo 240 rechazos de energía, 30 de cruce, 25 de bounds, 23 de D8, 2 de signos, 79 filas exactas fallidas y 0 elegibles.

**Límite:** solo se verificó esta enumeración determinista de 242 cambios aislados de un ULP. No se probó ajustar más de un nodo a la vez, cambiar el paso, ampliar bounds ni resolver el conjunto factible completo.
