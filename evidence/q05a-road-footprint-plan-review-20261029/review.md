## Veredicto: SOUND-with-fixes

**CONVERGE:** sí. El siguiente hito correcto es esta ligadura de fuentes guardadas, no reparación, exposición visible ni nueva infraestructura. `measurement_ready=false` y `placement_ready=false` son coherentes con el alcance.

### Hechos leídos en la cápsula

- En [product-spec.md](/C:/Users/guill/OneDrive/Documentos/DayZ%20Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/product-spec.md:11), P9 fija 1 m/0,95 m/24 m para navegación; 24 m no es ancho vial. P10 pospone carreteras físicas y P11 exige empalmes suaves.
- En [Q03C2R1](/C:/Users/guill/OneDrive/Documentos/DayZ%20Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/evidence/source-terrain-water-q03c2r1-20261029/README.md:7), 202,864350488 m² es área por cara, con multiplicidad, sobre terreno fuente y sin huella de agua seleccionada. No es unión mundial, superficie visible ni conflicto acreditado.
- En [el piloto de exposición](/C:/Users/guill/OneDrive/Documentos/DayZ%20Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/tools/quality/pilot_visible_exposure_ev112.py:50), el universo vial es `xy(36428,2)` y `edges(36467,3)`; `rect(width=4)` y discos `r=4` definen la antigua banda de 8 m.
- En [el censo vial-agua](/C:/Users/guill/OneDrive/Documentos/DayZ%20Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/evidence/road-water-census-20261028/README.md:3), hay 770 aristas con contacto en 29 cadenas, no 770 puentes. En [el overlay](/C:/Users/guill/OneDrive/Documentos/DayZ%20Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/evidence/road-surface-overlay-20261028/README.md:10), kit118 intercepta 6 aristas de la cadena 76 y el contacto 49/301 es diagnóstico, no asociación certificada.
- En [RoadB4B1](/C:/Users/guill/OneDrive/Documentos/DayZ%20Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/evidence/road-b4b1-saved-content-20261029/README.md:3), sólo hay equivalencia de contenido guardado; método, precedencia actual, pivote y huella siguen sin probar.

### Hallazgos y modificación mínima

1. **IDs ambiguos.** En [el código del overlay](/C:/Users/guill/OneDrive/Documentos/DayZ%20Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/tools/quality/road_surface_overlay_ev112.py:230) coexisten índice de cadena, ordinal de arista dentro de la cadena, nodos `a/b` e índice global en `edges`.  
   *Fix:* exigir columnas separadas `chain_index`, `edge_ordinal_in_chain`, `global_edge_index|UNKNOWN`, `node_a`, `node_b`. Sin esto, “seis edge IDs” y “49/301” pueden mezclarse.

2. **Dominio A puede reinventar un ancho.** “Superficies contra reserva vial” no define si la reserva es eje, grafo o polígono. Como 8 m y 24 m están explícitamente descartados como ancho útil, una intersección de áreas sería circular.  
   *Fix:* limitar A, salvo polígono guardado identificado, a contacto con eje/grafo: longitud por estación, distancia lateral y lado. No reportar área de cobertura.

3. **SHA incompatible con `LOCATED_NOT_OPENED`.** La tabla exige SHA, pero un archivo no abierto por presupuesto no puede recalcularlo.  
   *Fix:* separar `sha_recomputed` de `sha_declared_in_manifest`; el segundo se etiqueta como copiado, no verificado.

4. **Riesgo de circularidad entre overlay y Q03B6.** El overlay fija transformaciones históricas y exige 539009 caras/17818 poses en [su preparación](/C:/Users/guill/OneDrive/Documentos/DayZ%20Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/tools/quality/road_surface_overlay_ev112.py:210). Si ambas salidas comparten insumos o transformación, no son corroboración independiente.  
   *Fix:* añadir `derived_from` y prohibir contar fuentes hermanas como dos evidencias.

5. **Las cuatro predicciones locales no son transferibles.** En [RoadB2](/C:/Users/guill/OneDrive/Documentos/DayZ%20Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/plans/ev112-road-b2-object-pilot-20261029.md) son hipótesis origen/centro × fila/columna para las piezas B0 y su `bounding_center`. No acreditan la plantilla de kit118.  
   *Fix:* restringir el dominio B a modelos B0 ligados por hash; kit118 queda fuera salvo ligadura explícita modelo-cara-época.

6. **Muestra intencional, no representativa.** kit118/76, 49/301, Narva71 y tramo 49 seco son casos diagnósticos frente a 124 cadenas/36467 aristas.  
   *Fix:* etiquetarlos `MUESTRA_INTENCIONAL_NO_REPRESENTATIVA`; prohibir extrapolar tasas o cierres al universo vial. El mutante “arcén fuera de 8 m” debe declararse sensibilidad diagnóstica, no criterio de aceptación.

### Premisas no comprobables desde la cápsula

Hipótesis, no hechos leídos: contenido y hashes de los tres `local-faces-*.json` privados de RoadB0R1; existencia/alcance de los tres objetos B3; los “201 pilotos” de Q03B6; anchos de piezas de 12/9 m; antiguo conflicto de 23,9566664 m²; tramo 49 “seco”; y el contenido de `road_surface_overlay_ev112.py:294-359`, no incluido en el ancla. Tampoco están incluidos Q05/Q06/Q07 del council, por lo que su exigencia se acepta sólo como premisa declarada del plan.

Con los seis fixes, el plan puede ejecutarse una vez y concluir válidamente en `INCONCLUSIVE_SOURCE_BINDINGS` sin inventar pivote, ancho, joins ni accesos.
