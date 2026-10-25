# Recovery-v5: corregir la máscara de protección efectiva

## Alcance

Copia independiente de recovery-v4. Corrige únicamente el falso fallo del gate `protected_and_civil_context_exact`; conserva sin cambios los gates de energía, topología y todos los demás. No ejecuta evaluación ni cambia el diagnóstico v4, el solver o los datos.

## Contrato aplicado

En `prepare_wet_bank_matrices.py:407–428`, la excepción explícita de liberación es `(cls == 5) & water`; `nonreleased_fixed = other_rebuilt & ~((cls == 5) & water)`. La máscara `effective_fixed` vuelve a incluir reservas, plataformas, halo, márgenes de lago, Narva, P9 y carretera. Por tanto el consumidor calcula el veto semántico como `other_fixed_context & ~((cls == 5) & water)` y prueba por separado `effective_fixed_context`, P9 y carretera. El collar continúa comparándose bit a bit contra B por la lógica existente. La excepción de clase 5 nunca anula un veto efectivo, vial o P9.

`other_fixed_context` bruto y el conteo de intersección se guardan solo como diagnóstico, incluyendo el conteo de la parte liberada. El gate usa la máscara no liberada y los vetos independientes.

## Casos de prueba

- Positivo: el cambio toca `other_fixed_context` únicamente en un nodo `cls=5/water`, sin solape con effective/P9/road; pasa la máscara no liberada.
- Negativos: el mismo nodo de excepción también está marcado en `effective_fixed_context`, o en carretera, o en P9; cada caso falla su veto independiente.
- Negativo adicional: un cambio en `other_fixed_context` que no pertenece a `cls=5/water` falla.
- Collar falso falla fuera de esta función y mantiene el gate existente.

## Evidencia preservada y límites

Recovery-v4 y su assessment no se modifican. Su diagnóstico de protección raw16 permanece en `recovery-v4/diagnosis/assessment-v4-failure-diagnosis-v2.json` (SHA256 `99a63b2ea9b32d8cc4ed16b48d3d6df3918942467ee0f6961a013c0eb70f414d`). La topología local del objeto `16804567/7443` y el fallo de energía permanecen sin tocar; recovery-v5 no los perdona.

Los fixtures y `py_compile` validan solo el cambio de máscara. Esta fuente está congelada para una evaluación final; no se ha ejecutado assessment real.
