# EV90 preflight — solo lectura

**Estado: PREFLIGHT_READY_FOR_INTEGRATOR_REVIEW.** No se leyó Q ni se ejecutó solver/candidato.

- B `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`; EV79 `dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c`; P `768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0`; F `f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c`. Pin plan `3bde2ce8460f6374830f8ec4ca302e06b7c9a904f36c8778826799ffd6cdd7ea`.
- Ventana: 17×17 vértices, 16×16 celdas. Se enlazaron los 18.024 objetos 0WZD con bounds y PBO desplegado; 78 modelos en la ventana se parsearon para LOD físicas/visibles exactas.
- Excesos confirmados: 195 intersecciones físicas sobre P+1e-5 en 61 celdas; 0 visibles sobre F+2e-5 en 0 celdas. Campo indefinido: 19 celdas únicas (P: 19; F: 19).
- Foco `(840, 370)` toca campos P/F desconocidos en celdas `[839,370]` y `[840,370]`; no es F parcial. La excepción de enterramiento sí se cumple: 87 solapes físicos, clearance mínimo 0.3155503 m; 85 visibles, clearance mínimo 0.3072173 m; todos siguen enterrados incluso bajo la envolvente L32.
- Elegibles semánticos antes de freezes por geometría: 98; después: 85. El foco queda `variable`, intervalo float32 inward `[1.8115131855010986, 4.236104965209961]`; prominencia B EW 1.832301 m, NS 1.787288 m. La caja optimista permite ≥25% en ambos ejes: `True`.

Los excesos sobre P se congelan; las celdas P ausentes dentro de P9 y las F parciales también quedan idénticas a B. P ausente fuera de P9 no se congela por defecto; su exposición física se conserva solo si todas las caras permanecen enterradas bajo L32. La caja es separable y optimista: no es solve acoplado ni prueba energía, prominencia angular, silueta u otras puertas del plan.

Caras que cruzan las celdas del foco: en [839,370], latfix_046_150_0044.p3d cara física 3/6 y visible 5/6; en [840,370], latfix_046_150_0045.p3d cara física 9 y visible 0/1. Los IDs, triángulos nativos NW-SE, polígonos de intersección, áreas y clearances completos están en ocus_unknown_face_records del JSON.
