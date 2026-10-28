**Veredicto: SOUND-with-fixes.** El plan es coherente con el código y la evidencia que cita. Tres correcciones concretas y verificables antes de implementar; ninguna requiere cambiar tolerancias, agua ni protecciones.

**Verificado contra fuentes**

- La fórmula de cortes es correcta. El interpolador nativo (`tools/water/streambed_kit_v31.py:270-277`) usa c=x/6, r=(12282-z)/6 y divide en fc>=fr. La diagonal es r-c constante, es decir v-u entero, con ZTOP=12282 en la línea 175. Cortar en u, v y v-u enteros cubre todas las aristas nativas.
- Las referencias a `continuous_stream_pilot_v31.py` son exactas: 39 columnas y delantal ±18 reducido en curvas (287-295), piso H+.02 y techo sólo en superficie protegida (313-319), 8 filas CAP por extremo fuera del NPZ (344-362), redondeo 1/512 (329, 363).
- El hash del candidato 1e85c73f y su alcance kit7 coinciden con el author-report en R; libre 49470 puntos, cero infeasibles y cero sin valor cuantizado.
- Kit118: 13.478894 BODY y 10.477772 CAP en el corredor coinciden con el summary publicado. La lámina por fila es constante por construcción, así que B-W es afín por segmento.
- La extracción expone `source_grid`, `source_triangles`, `bed_source_face` y `source_category` (`tools/quality/pilot_visible_surface_ev112.py:224-225`), suficientes para reconstruir filas y juntas sin regenerar CAP.

**Fixes requeridos**

1. **Dos máscaras y dos umbrales distintos, no una** (`plans/ev112-pilot-bank-constraint-feasibility-20261028.md:56-68`). El plan mezcla el contrato legacy de v31 y el del ensayo seco. Son diferentes en dominio, umbral y fuente:
   - Legacy v31: dominio libre 4<|q|<18 (`continuous_stream_pilot_v31.py:313`), fijación por `tri_h(protected)>.99999` (316), con piso=techo=ground+.02 en esos puntos. Los puntos con |q|≤4 y |q|=18 quedan fijos al perfil de diseño W+cross, no a ground+.02.
   - Ensayo seco: dominio 2.25<|q|<18, exclusión por `touch>0`, además cap≤6, infeasible y quant_bad (`E:/DayZ-Baltic-Build/shape-repair-20261025/pilot_dry_bank_visual_floor.py:41-56`).

   Propuesta mínima: definir por vértice `LEGACY_FIXED = ¬(4<|q|<18) ∨ fixed_surface(>.99999)` y `CANDIDATE_EXCLUDED = touch(>0) ∨ cap ∨ infeasible ∨ quant_bad`, y estratificar siempre por dominio |q|≤2.25, 2.25–4, 4–18, =18. Control: suma de vértices por clase = 39×filas por sitio; el área de corredor kit118 debe quedar repartida por dominio y clase y sumar exactamente 23.956666. Sin esto, "cota inferior que el contrato congelado no puede retirar" (línea 73) atribuye a ground+.02 superficie que en realidad es perfil de orilla diseñado en 2.25<|q|≤4.

2. **Pinear la fuente de la máscara y sus claves opcionales** (`plan:56-59`). El ensayo seco lee reserve/platform/narva/bridge/dam/causeway/ramp de `rectangle-pilot-f-merged/terrain-buried.npz` (hash caa53980 en context.json), añade `v31_road_repair`, `v31_road_mesh_repair`, `v31_continuous_pilot` sólo si existen (`pilot_dry_bank_visual_floor.py:34-35`), y modela charcas como `c2v(isfinite(plane))` del footprint, mientras v31 usó `c2v(current_pond)` de su propia ejecución (`continuous_stream_pilot_v31.py:232`). El plan debe registrar qué claves estaban presentes, motivo por motivo, y etiquetar la equivalencia charca/footprint como no demostrada. Control: tabla motivo→vértices tocados→caras totalmente fijas, con hash del NPZ leído.

3. **Etiquetar la no convergencia del candidato** (`plan:53`). El author-report dice `success:false`, 500 iteraciones, `bounds_satisfied:true`. Toda comparación baseline/candidato debe llevar esa etiqueta; no es un candidato optimizado sino acotado.

**Mejoras no bloqueantes**

- Añadir fixture: misma geometría, máscara legacy y máscara candidato distintas en un vértice, verificando que las particiones divergen como se espera. Motivo: es el error más probable al implementar el fix 1.
- En perfiles, registrar además el primer punto por lado donde B cruza W+0 y donde cruza H, para que la futura reparación tenga ancho de orilla visible por fila sin convertirlo en cobertura continua. Motivo: es el dato que el siguiente autor necesita.
- Dirección de reparación procedural, para que el entregable no sea sólo tabla: por fila, la orilla seca objetivo se expresa como función de ground y de la cresta de lámina, con pines legacy enumerados por motivo. La decisión sobre qué pines de s3_road_guard o reserve son técnicos y cuáles humanos queda explícitamente fuera y marcada como pendiente de contraste, como ya exige la línea 74-75.

**Lo que se mantiene**: tolerancias, agua, extremos, CAP como fijo técnico, límites 1e-7/1e-9 como reproducción y no calidad, INCONCLUSO ante degeneración, presupuesto 600s/2GiB. El volumen de trabajo (≈2400 filas de cuerpo más 64 CAP, 38 segmentos por fila) cabe holgado en el presupuesto.

FIN_REVISION
