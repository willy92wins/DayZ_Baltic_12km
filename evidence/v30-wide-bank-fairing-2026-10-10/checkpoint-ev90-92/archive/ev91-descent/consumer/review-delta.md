# Revisión delta consumidor EV91 frente a EV90

**Veredicto:** SOUND para revisión offline del contrato; no encontré un gate retirado ni un camino de falso PASS en el delta congelado. La verificación completa de candidato no se ejecutó en esta revisión.

## Identidades revisadas

- EV90 congelado: `next-method-consumer/verify_ev90.py`, SHA-256 `ef4056bf186255389a899c193e92bfcb062664d317672bdee634656d89ad0b46`.
- EV91 congelado: `ev91-descent/consumer/verify_ev91.py`, SHA-256 `2777752e212034b4043691ac30c9deddd8395f3a88cf557bdb6606ffb9b70333`.
- Fixtures EV91: `ev91-descent/consumer/test_ev91_consumer.py`, SHA-256 `aecd4695447dd1ed1b1833f43d5879f88e7aec9ad3f5ef0c13561bb49fdf3bf6`; el discriminador informa compilación y 3/3 fixtures PASS. No ejecuté esos tests.

## Delta de aceptación

EV91 conserva las 17 claves de gate EV90. Añade solo `EV91_collar_guard_exact_B` y `EV91_D8_no_new_strict_minima8` ([verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:886)). El guard se reconstruye comparando nodos provenientes de stencils y bisagras incidentes, y se exige igualdad exacta con B; el chequeo D8 reconstruye vecinos/testigos desde B, desempata por fila/columna y valida población/matrices/receipt independientemente ([verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:501), [verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:523), [verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:546)). Dimensiones fijadas: 85 variables, 43 guardadas y 42 libres; 350 stencils, 107 collar-stencils, 135 centros D8, 129 testigos y 6 mínimos estrictos heredados exentos.

El recibo exige una llamada SLSQP exitosa con SciPy 1.18.1/status 0, timeout 120 s, identidad del autor y hash de `prepared.json`; coincide con el plan EV91 ([verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:433)). El preflight EV90 sigue anclado a su propio plan/hashes; el plan de autoría EV91 va por separado. No se alteran las cotas ni las protecciones en el consumidor.

El p99 de aceptación sigue siendo exclusivamente bank/interior. La tercera población, `eligible ∩ wet_support`, se calcula y presenta como diagnóstico separado, limitado a bisagras con sus cuatro vértices en la población; no se incorpora como gate ni se presenta como métrica de todo el mapa ([verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:605), [verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:897), [verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:919)).

La ruta del quad plano tampoco se oculta: el helper EV90 fijado conserva `no_new_exactly_constant_2x2_windows`; EV91 incluye `shape_contract` entre los gates y serializa `shape_contract.new_constant_quads` en el reporte ([verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:891), [verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:915)). Así, un quad plano nuevo como el observado por root en `(836,370)` debe producir `shape_contract=false` aunque el discriminador de agua pase. Esto es revisión estática del camino de reporte; no afirma que yo haya reproducido el resultado del candidato.

## Observación menor

En [verify_ev91.py](E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:937), el error de rehash aún dice “during EV90 consumer”. El branch sigue fallando cerrado y el estado/CLI usan EV91; es una etiqueta de diagnóstico obsoleta, sin efecto en aceptación.

## Límites

No lancé el full run ni DayZ. El análisis confirma pins, predicados y serialización esperada, no el resultado empírico del candidato ni render/agua dinámica. El reporte EV91 queda sujeto a que todos los gates offline se ejecuten y al estado pendiente de aceptación visual/runtime.
