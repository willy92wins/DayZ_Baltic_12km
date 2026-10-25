# EV90 preflight — solo lectura

**Estado: PREFLIGHT_INCONCLUSIVE.** No se leyó Q ni se ejecutó solver/candidato.

- B `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`; EV79 `dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c`; P `768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0`; F `f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c`.
- La ventana contiene 17×17 vértices y 16×16 celdas. Se escanearon 78 objetos compilados cercanos (78 modelos), usando LOD físico/visible exacto, transforms 0WZD del B desplegado por hash y tolerancias {'physical': 1e-05, 'visible': 2e-05}.
- Celdas con cara sobre P: 61; sobre F: 0; unión: 61. Celdas con intersección de campo desconocido P/F: 38.
- Variables elegibles originales: 98; tras congelar esquinas de discrepancias/campos indeterminados: 62. Foco: `fixed_or_empty_interval`, intervalo float32 inward `[3.73610520362854, 3.73610520362854]`. Reducción focal ≥25% por cotas escalares en ambos ejes: `False` (optimista, no solver).

Ver el JSON para listas por celda, caras de ejemplo, intervalos de cruce, hashes y limitaciones. El estado INCONCLUSIVE conserva los criterios previos cuando hay dominio parcial/indefinido; no se imputa P a F ni F a P.
