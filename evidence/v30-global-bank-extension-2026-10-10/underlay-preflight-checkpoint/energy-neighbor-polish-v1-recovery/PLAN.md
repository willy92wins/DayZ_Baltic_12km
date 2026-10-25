# Pulido energético de vecinos float32 — preparación, sin ejecución

Estado: código y fixtures solamente. No se enumeró la instancia real; no se cambió el candidato rechazado ni se llamó a HiGHS.

## Base fijada

- Modelo D8 corregido: `../lattice_milp.py`, SHA256 `2a62d1d73af6d71af97b60b5512787a653a3637d1c54f8eb001c9d905252e396`.
- Resultado de partida, solo diagnóstico: `../real-run-01/rejected-diagnostic.npz`, SHA256 `2209df7542098403ceda8e27e87c91935a9832527f04663fdf8f5d8ac70149ae`; recibo original `../real-run-01/receipt.json`, SHA256 `f540fb0e8672886c8c70a2af7c8d6ae16c3698ce7d0392e97d9ccc2d50e00902` (rehash directo del archivo vivo).
- La línea base rechazó solamente `closure_energy_and_improvement`: baseline 279.1855928129427, raw 155.94405102975674, cerrado 155.9440734841285; allowance fijo `1e-7 * max(1, raw)` = 0.000015594405102975674. La diferencia cerrado−raw es aproximadamente 0.00002245437176, por encima del allowance.
- Fuentes de evaluación exacta/directa: `../candidate_model.py`, `../lattice_milp.py`, `../../../../float32-neighborhood-v1/executor.py`, y `../../../../convert_components.py`; los hashes vivos se vuelven a comprobar antes y después de evaluar.

## Regla única

Para cada uno de los 121 nodos, generar a lo sumo dos grids: solo ese nodo en el float32 inmediatamente inferior y solo ese nodo en el inmediatamente superior. No añadir el candidato original como alternativa, no variar dos nodos a la vez y no iterar. El orden fijo es índice variable row-major y después paso `-1`, `+1`.

Cada grid pasa por las filas racionales completas y `exact_gates` del modelo fijado (bounds, fixed, signs, crossings y D8), además de los gates directos fijados del executor (bounds, P/F, 116 cruces, D8, conos y energía). El coste es `0.5*||A*x-rhs||²`, calculado por la misma función congelada. Una alternativa solo es elegible si mantiene todos esos gates, `closed_cost - raw_cost <= 1e-7*max(1,raw_cost)` y `closed_cost < baseline_cost`.

Entre elegibles se escoge el menor coste cerrado; los empates se resuelven por fila, columna y paso (`-1` antes de `+1`). La selección es un único cambio ULP respecto al diagnóstico; no se usa búsqueda coordinada ni una segunda ronda. Si no hay vecino elegible, termina `NO_FEASIBLE_ONE_ULP_NEIGHBOR`, sin ampliar el radio.

Un resultado posible se escribe como artefacto de diagnóstico separado, con `accepted=false` y `terrain_written=false`; no sustituye el recibo rechazado ni autoriza consumo gráfico. Un resultado sin vecino no escribe grid candidato. Límite total de la enumeración: 60 s para ≤242 evaluaciones y cero llamadas de solver.

## Fixtures requeridos

Cubrir exactamente 2N vecinos ordenados, cambios de un solo nodo, saltos `nextafter` en ambas direcciones, coste mínimo con desempate determinista, igualdad y exceso de allowance, no mejora frente al baseline, rechazo por cada familia de gate y salida sin vecino sin ampliar búsqueda. Los fixtures ejercitan las funciones de producción de generación/selección y no el loader real.

La validación estática previa del recibo exige el estado rechazado, `accepted=false`, `terrain_written=false`, filas Fraction y gates exactos/directos aprobados salvo `closure_energy_and_improvement`, y el enlace SHA/path al diagnóstico rechazado. Sus pruebas usan recibos sintéticos; no sustituyen la lectura con hash del archivo real durante la enumeración.

Esta preparación no demuestra que exista un vecino que cierre la brecha. La comprobación real, si la aprueba raíz, tendrá una sola evaluación y preservará todos sus rechazos.

## Recuperación tras run-01

La fuente original `energy-neighbor-polish-v1` y su `run-01` quedan intactos. Ese intento terminó `ERROR` tras dos vecinos porque `CandidateLatticeMILP.exact_auxiliary` lanzó `ValueError: fixed lattice value mismatch at 1` para un ULP que viola un nodo fijo. El registro y recibo preservados están en `../energy-neighbor-polish-v1/run-01/`; el segundo grid no fue evaluado y no hay resultado de enumeración.

Esta copia recovery solo transforma ese error en un rechazo de vecino cuando coinciden ambas condiciones: el mensaje completo es `fixed lattice value mismatch at <índice>` y el gate exacto `fixed` ya es `false`. Cualquier `ValueError` distinto, o un mensaje coincidente con `fixed=true`, se vuelve a lanzar. Se conserva el mismo diagnóstico, pins, orden y límite de hasta 242 vecinos/60 s; la copia tiene su propio `run-01` vacío y no se ejecuta como parte de preparación.

Los fixtures llaman al `CandidateLatticeMILP` real pinneado con una expresión fija y una perturbación ULP, pasan por `evaluate_grid` y comprueban que queda rechazo explícito; negativos confirman que errores inesperados no se tragan. No es evidencia de que el presupuesto energético tenga solución en los vecinos restantes.
