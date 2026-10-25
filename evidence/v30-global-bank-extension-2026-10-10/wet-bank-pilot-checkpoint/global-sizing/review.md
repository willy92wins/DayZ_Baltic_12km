# EV95 global sizing preflight — run-05

Estado: `READ_ONLY_RESOURCE_PREFLIGHT_COMPLETE`. No se ejecutó solver ni se modificó terreno.

## Identidad y método

- Verificador: `preflight_global_resources.py`, SHA-256 `9b997a3ebf64b78828955476eed4c4c57cfc1ca77d998e407adda17ea5a6bfb7`.
- Reporte: `preflight.json`, SHA-256 `b6507c73af2181860c13a04ed1814a1a508d0448cd9b63520854aad029ae0f95`.
- Máscaras: `masks.npz`, SHA-256 `8f5959308923263538440d29dd93960c5331bc8f13c88b61590380c17d6cdfff`.
- El script fue archivado en esta carpeta para que el reporte conserve su fuente reproducible.
- Self-test/py_compile: PASS. El fixture compara las filas y nnz de A, C y G contra las matrices CSR reales de CP en una malla pequeña; el negativo detecta una máscara de variables alterada.

## Resultado de sizing

Con las guardas globales y las 499 ventanas retenidas más halo Chebyshev 2, hay 2.988.565 nodos EV87 elegibles antes de guardas y 2.712.136 variables en el caso principal `EV95_delta_variable`. La sensibilidad que congela el delta EV95 conserva 2.676.213 variables. El foco `(840,370)` se fija explícitamente.

Para el caso principal, A tiene 11.095.396 filas / 29.833.496 nnz; C, 4.182.435 / 5.403.177; G, 16.760.836 / 21.697.088. El CSR combinado ocupa exactamente 811.359.812 bytes con índices/indptr int32 y datos float64; los CSR transpuestos, 715.750.776 bytes. El estimado numérico estacionario es 3.467.287.284 bytes y el techo conservador con duplicación de conversión es 4.994.397.872 bytes (4,65 GiB). Los vectores son estimados; las listas de registros Python no están incluidas y deben evitarse en un futuro constructor.

La preparación tardó 594,4 s. El working set pico medido del preflight fue 1.547.595.776 bytes (1,44 GiB), que solo mide este preflight y no simula el solver. RAM física disponible: 8.646.406.144 bytes al inicio y 8.366.268.416 al final. El sizing deja margen aritmético sobre el estimado, pero no demuestra tiempo de convergencia ni memoria pico del solver.

## Precisión P y correcciones de procedencia

La fuente `plane.npy` es float64. El camino que se corrigió en run-05 conserva ese dtype al evaluar niveles y contactos; el cast interno de `verify_ev87.vertex_levels` a float64 es seguro solo si recibe primero el P original, como ahora. El diagnóstico reproduce el cast float32 anterior sin usarlo para gates: afectaba 323.499 muestras finitas, con error máximo `7,629394538e-7 m`; alteraba 203.989 niveles de vértice, también con máximo `7,629394538e-7 m`. La máscara de cruces P tuvo 84.775 celdas en ambos caminos y diferencia simétrica 0. Esto no autoriza redondear P: los niveles y futuros bounds se calculan con P original.

Run-04 se preserva, pero no es resultado final: usaba P convertido a float32, calculaba el `+0,5 m` sobre EV95 en vez de B EV82 y guardaba la máscara post-guardas bajo la clave `eligible_before_protection`. Su reporte contó 2.988.565 elegibles previos a guardas, pero su NPZ tenía 2.712.136 en esa clave mal etiquetada; run-05 conserva correctamente `eligible_before_guards`.

## Interpretación contractual del tope

Run-05 conserva el escenario de sensibilidad conservador `upper=min(H+2, EV79+2, B_EV82+0,5)`. Ese `B+0,5 m` procede del cap local usado por el piloto/prepare EV94; el contrato global de EV82 `author.py:372-379` define intervalo de paso y presupuesto acumulado EV79 ±2 m, sin aprobar el cap `B+0,5 m` como presupuesto global. Por tanto, las cifras de **matrices/filas/nnz** sirven también al caso global sin ese cap: el cap no añade filas al operador y bajo el cap estricto hubo cero cotas inviables; quitarlo solo afloja el límite superior. No se ha elegido ni aprobado una política global de cotas con este preflight.

Nota de esquema: el reporte crudo describe `lower` y `upper_cap` de forma abreviada; la implementación exacta del run-05 es la fuente reproducible: `lo=max(H-2, min(EV79, level+1e-4), min(EV79,1.8), EV79-2)` y `hi=min(H+2, EV79+2, B_EV82+0,5)`, ambos inward-rounded a float32. El contrato global sin cap local sería `hi=min(H+2, EV79+2)`.

## Límites

El guard de agua es el bbox conservador de las caras indexadas compiladas (480.507 celdas); no se repitió clipping ODOL exacto. Las máscaras P/F/SEA y P9 se reconstruyeron con triángulos NW-SE y P9 por intersección positiva con corredores. No se evaluaron gates geométricos de candidato, rendimiento de solver, cobertura runtime ni extensión artística del operador. El siguiente paso necesita revisión de integrador del dominio y del uso de memoria, y después una medición de solver separada; este reporte es solo preflight de recursos.
