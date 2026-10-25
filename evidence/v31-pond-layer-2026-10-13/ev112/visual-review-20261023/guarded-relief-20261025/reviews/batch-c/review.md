**Veredicto: SOUND-with-fixes.** El candidato C puede conservarse offline pendiente de bosque/compilación/sonda/vista. Antes de integrar hay que cerrar cuatro puntos; ninguno invalida la geometría ya auditada.

**Correcto**
- Unión por clúster: componentes 8-conexas de dist≤4 a objetivos fijos; `use` restringido al clúster, `h[sl][use]=` escribe por vista, `base=h0[sl]` siempre. `repair_guarded_shapes_ev112.py:38-47,87`.
- Caps solapados: `hi` toma el mínimo de techos de todos los picos miembros, `lo` el máximo de suelos de pozos; `lo>hi` → INFEASIBLE_BOUNDS sin resolver. `:51-65`. Clústeres mixtos 10/16/28 quedaron sin aplicar.
- Puertas globales sobre el terreno final (protecciones, ápices, carreteras, orilla, mar, picos/pozos nuevos/agravados, pendiente, aristas, esquinas de agua) cubren las interacciones entre clústeres que las pruebas locales con relleno h0 no ven; fallo cerrado a FAIL global. `:90-103`.
- Verificador de prominencia independiente del solver (census_pyramids vs despike.rings). `:40,74`.
- Solver: solver-used.py y actual difieren solo en docstring en las líneas comparadas (`:18-27`); tests pozo y libre-infactible existen (`tests/test_shape_repair_constraints_ev112.py:76-92`).
- Evidencia: report PARTIAL, 81/66, 14 checks true; overshoot-audit 66 grupos, 0 violaciones, mutante detectado por grupo. Cluster 35 (1024,254) rechazado solo por energía pura; correcto no aplicarlo.

**Fallos a tratar antes de integrar**
1. **Procedencia de `free/road/shore`.** El autor las toma de `guarded-relief-discovery/domains.npz` (`:31`) y el generador de ese discovery no está en `tools/`. El solver original deriva `free` con exclusiones v31_*, disco015-45 y guard de carretera (`repair_free_shapes_ev112.py:91-96`). Hay que archivar el script de discovery y demostrar que su `free` es idéntico o subconjunto. Sin esto, "protecciones exactas" solo se prueba contra una máscara de origen no auditado.
2. **Guard anti-sobrepaso solo para objetivos factibles.** Los techos/suelos se aplican únicamente a miembros del clúster (`:32,54-63`); los 1402 extremos protegidos no factibles a ≤24 m no reciben corona, y la auditoría externa solo mira los 66. Elevar un vecino por encima de un ápice no objetivo baja su prominencia, así que ningún check lo detecta. Extender el cap (o al menos contar sobrepasos) a todo extremo protegido con pk0/pt0>0,3 en `near`.
3. **Etiqueta SOLVER_INFEASIBLE engañosa.** Los 8 casos son "Positive directional derivative for linesearch" (`report.json:353` etc.), fallo numérico de SLSQP, no infactibilidad probada. Renombrar a SOLVER_FAILED; no describirlos como infactibles.
4. **Hash del autor.** `author_sha256` del report corresponde a author-used.py, que no contiene `no_new_overshoot_exact`; el archivo actual sí (`:52,60,63,77`). Documentar que el candidato es anterior a ese guard y que su equivalente es overshoot-audit.json.

**Menores**
- `members` por representante (`:45`); añadir aserción de que todos los `target_vertices` de cada grupo comparten etiqueta de clúster, si no, un ápice recibiría `target_clear` sin su cap.
- Falta test unitario del ensamblado de caps (pico y pozo solapados → INFEASIBLE_BOUNDS).
- 2048 fijo en `:46`.

**Pendiente externo:** huella/P11 en curso; bosque, binario, sonda y vista conjunta siguen abiertos. Navmesh U2 no acepta C. 66+15 son factibilidad; 66 grupos aplicados, 15 abiertos.
