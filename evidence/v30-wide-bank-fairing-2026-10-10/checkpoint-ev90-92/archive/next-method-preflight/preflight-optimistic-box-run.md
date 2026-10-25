# EV90 preflight — solo lectura

**Estado: PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW.** No se leyó Q ni se ejecutó solver/candidato.

- B `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`; EV79 `dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c`; P `768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0`; F `f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c`. Pin plan `3bde2ce8460f6374830f8ec4ca302e06b7c9a904f36c8778826799ffd6cdd7ea`.
- Ventana: 17×17 vértices, 16×16 celdas. Se enlazaron los 18.024 objetos 0WZD con bounds y PBO desplegado; 78 modelos en la ventana se parsearon para LOD físicas/visibles exactas.
- Excesos confirmados: 195 intersecciones físicas sobre P+1e-5 en 61 celdas; 0 visibles sobre F+2e-5 en 0 celdas. Campo indefinido: 19 celdas únicas (P: 19; F: 19).
- Elegibles semánticos antes de freezes por geometría: 98; después: 85. El foco `(840, 370)` queda `variable`, intervalo float32 inward `[1.8115131855010986, 4.236104965209961]`; prominencia B EW 1.832301 m, NS 1.787288 m. Caja optimista de intervalos permite la reducción ≥25% en ambos ejes: `True`.

Los excesos conocidos y los P9 con P ausente se conservan en B. P ausente fuera de P9 no se congela automáticamente. F indefinido solo se considera seguro cuando cada cara real está ausente o sigue enterrada incluso bajo el suelo mínimo permitido; se informa el resultado geométrico por cara. Cotas independientes por nodo son una caja optimista, no un solve acoplado ni prueba de las puertas globales.
