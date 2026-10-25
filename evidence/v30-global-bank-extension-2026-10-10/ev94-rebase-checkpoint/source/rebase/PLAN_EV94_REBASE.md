# EV94 — rebase de un sector sobre la composición focal aceptada

Estado: diseño para revisión + preflight sin solver. No produce ni exporta terreno.

## Base y linaje fijados

La base exacta es `focus-unit/author-run-01/candidate-terrain.npz`, SHA256 `30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1`. Se acepta para este alcance focal por `focus-unit/composition-run-01/review.json`, SHA256 `a5a5aaa1f1f2c06c646bbd54a41ea8fd89d8dee8ffa14d2e59af4d7bc07b05e3`, estado `PASS_FOCAL_COMPOSITION_INCREMENTAL`; su suplemento `acceptance-supplement.json` SHA256 `fab5c76e2f1a7a5935cf70bfaa08dedd4500411e4c2ac11670dc7fccc4b89e7f` declara `PASS_FOCAL_DELTA_OFFLINE_COMPLETE_GATESET`. Ambos informes dejan `global_contract_status/map_status=OPEN_INHERITED_MAP_DEFECTS`: esto no significa aceptación global ni visual.

La composición focal debe ser idéntica al candidato EV93 seleccionado (SHA256 `6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d`) en todo salvo `(840,370)`, cuyo valor se fija a `3.278029680252075` en float32. Los metadatos y cada campo NPZ salvo `heights` deben ser byte-exactos con EV93. El recibo focal debe enlazar exactamente el candidato, el reporte EV93 seleccionado (`656e676e38817592ed96d13ddeb1693d2a9bead152770256b0b21e665cedf8ec`) y la selección `selection.json` SHA256 `3b22dcc381b34b8d7c3e6641d3c919658f0fe7377594a859e3d5c064cf92ba0b`.

## Dominio y fijaciones

Una sola caja: vértices `[712,968) × [242,498)` (256×256), con contexto Dirichlet de dos vértices por lado (260×260). La única modificación futura sería un único solve fresco sobre este sector. Se recalculan dominio, RHS, matrices, cotas, testigos D8 y cierre float32 a partir de la base focal; no se reutiliza `preflight-run-03-continuation/prepared.npz` ni ninguna matriz/cota de EV82-B.

Se fijan exactamente las 499 unidades `retained_unit_ids` de `compound-selection/run-02/selection.json`. Para cada unidad, el preflight resuelve el `window_rc` 17×17 desde el resultado fuente original: directamente para las 332 unidades legacy; para las 167 crest, desde su `source_result_path` con SHA ligado en el target. Rechaza ventana ausente/no 17×17, ref/hash distinto, unidad no retained o variables fuera de ventana. La máscara fija es la unión de cada rectángulo y su halo Chebyshev de dos vértices. Los valores congelados son los de la base focal, preservando también el cambio aceptado de `(840,370)` donde corresponda. El vértice de foco `(840,370)` se añade de forma explícita a la máscara fija aunque otra protección ya lo cubra; el informe separa ese pin explícito de los solapes de máscara.

Además se fijan las protecciones semánticas EV87, soporte real de caras/agua de `water-support-mask.npz`, celdas de carretera y las nueve instancias de puente de `civil-run-01.json`, y esquinas de celdas P9 desconocidas intersectadas por el corredor firmado. No se sustituye `wet_support` por una aproximación; el orden de unión de máscaras es diagnóstico y sus conteos pueden solaparse. Ningún contacto/huella ni reserva/plataforma/civil se libera por quedar fuera de las ventanas seleccionadas.

## Reconstrucción del preflight

- Cotas completas: original de presupuesto EV79 `v30-narva-dry-bank-relief-20261010/candidate/terrain.npz`; presupuesto absoluto acumulado `EV79 ±2 m` y piso exacto del plan `min(EV79, max(SEA=.85, P, cada esquina F)+1e-4)`, con NaN tratado según `vertex_levels`; infinito es error. Se recalculan respecto a la base focal actual las cotas de paso de `original_budget_interval` EV82 y el cap superior EV82 `H <= B_focal + 0.5 m`; las cotas finales son la intersección de ambos contratos, el piso y `min(EV79,1.8)`, todo redondeado hacia dentro a float32 con `d8_sparse_pilot.inward32_lower/upper`. El informe conserva por separado cotas EV79 acumuladas, intervalo EV82 relativo a B, cap `B+0.5`, piso y cota inward final, y registra cuál limita. No se omite el cap de +0.5 m al resumir el presupuesto.
- El EV87 selector se reconstruye contra la altura focal y los mapas originales (`cls`, `other_fixed`, `engineering_halo`, `large_lake_banks`, P/F). El dominio móvil excluye también ventanas+halo2, soporte de agua, celdas civiles y P9. El primer seed fijo es `(840,370)` si sobrevive; si no, menor `first_layer_id` sobreviviente de la cola ya congelada. No se busca otro seed por el resultado de una solución. Si no hay supervivientes, estado terminal `NO_SURVIVING_SEED`, sin matrices ni ejecución.
- Para el dominio superviviente se regeneran los stencils EV88 (incluido xz central), RHS con contexto fijo focal, matriz CSR, testigos D8 deterministas sobre focal, exenciones existentes y cotas inward. El preflight comprueba que la base focal satisface sus propias cotas/testigos; cualquier violación o intervalo vacío detiene el caso antes del solver.
- Cierre float32 [EXACT]: fijar el helper `order-closure/projection.py` SHA256 `a990dc2d33fca4fd2a446b958f0412a2d752a5d3072a85d82058bb634cfaf44b`. `project_order(raw, lower, upper, edges, baseline=..., fixed=...)` recibe todo el contexto local flatten, con aristas testigo→centro, y límites iguales a la altura focal en los nodos fijos. El preflight lo prueba con la propia base factible y exige salida byte-exacta y corrección cero. Tras un futuro solve se repetirá sobre el raw float32 completo, con el gate de coste/budget original; el test de base no anticipa éxito del solve.

El preparado persistirá base local, máscara fija/variable, bounds, x0, stencils, matrices CSR/RHS, testigos/exenciones y recibo de hashes. Reporta conteos separados de elegibilidad, unidades/ventanas que tocan sector, máscara fija por familia y unión, variables finales, stencils, dimensiones/nnz y memoria/disco usados. Incluye `artifact_bytes_total` y falla cerrado si supera 2 GiB; el preflight sólo se publica como `PREFLIGHT_READY_ONLY` con readset inicial/final estable y hashes recalculados después de escribir.

## Presupuesto y puertas para cualquier ejecución posterior

Requiere revisión del plan/preflight antes de ejecutar. A lo sumo una llamada nueva y fresca, sin estado ni continuación. Se carga el módulo aislado `admm-quantized-pilot/solve.py` con su hash fijado y se cambia únicamente su global `MAX_ITER` de 10,000 a 20,000 antes de una llamada a `solve(A,rhs,C,d,lo,hi,x0,budget,progress)`. No se usa `solve_resumable.solve(..., stop_iteration=20000)`: ese API rechaza explícitamente un estado fresco por encima de `frozen.MAX_ITER`. El resto del solver, tolerancias, rho/equilibrado y CG permanece idéntico al módulo fijado. Presupuesto numérico/wall 600 s, pico de working set del intérprete ≤1.5 GiB y ≥3 GiB de memoria física disponible inmediatamente antes. Salida fresca y aislada, ≤2 GiB; cualquier fallo conserva artefactos y no se reintenta.

El futuro consumidor independiente debe reconstruir KKT y cierre, exigir mejora estricta del objetivo afectado y cierre dentro del allowance cuantizado, no nuevos mínimos D8, mantener los 499 rectángulos+halos y el resto de fijaciones exactos, recalcular forma/agua/civil/corredor alrededor de las variables nuevas y actualizar la cobertura global. Ningún PASS previo de EV93/EV82 se hereda como aceptación del candidato nuevo; un PASS local/preflight no es build, readback nativo, revisión visual ni aceptación BASE1.0.

## Fuentes verificadas para las APIs

- `real-sector-preflight/solve_real_sector.py:177-207,214-236,311-...`: niveles P/F/SEA, intervalos inward y P9. Se reutilizan funciones puras seleccionadas; su `build_preflight` original usa B y no se invoca.
- `v30-mixed-bank-incremental-fixed-20261010/author.py:369-374`: `water_floor_bound` y `original_budget_interval` EV79.
- `v30-global-bank-extension-20261010/constrained-pilot/d8_sparse_pilot.py:68-108`: D8, centros/testigos y redondeo inward.
- `global-operator-prototype/prototype.py:19-49`: colocación de stencils y ensamblado CSR/RHS.
- `global-operator-prototype/real-sector-preflight/order-closure/projection.py:51-...`: proyección exacta al retículo float32 con límites y grafo de orden.
- `v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py:237-...`: niveles/protecciones EV87 y guard del PBO desplegado.

Salida objetivo: `ev94-rebase/preflight-run-01/`. Este plan no autoriza solver ni composición de un nuevo candidato.
