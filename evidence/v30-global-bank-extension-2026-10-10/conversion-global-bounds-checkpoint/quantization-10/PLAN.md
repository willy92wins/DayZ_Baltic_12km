# Float32 one-ULP shoreline neighborhood diagnostic

State: source and synthetic fixtures only. The real (3^{10}) evaluation has not been run. This is a new, separate diagnostic; it does not revive or rerun the rejected solve.

## Question and frozen domain

Test only the ( {-1,0,+1} )-ULP neighborhood of these ten float32 variables, obtained from the CSR supports of the twenty material crossing failures in `crossing-geometry-fraction-v2.json`:

`(862,1186), (862,1187), (863,1187), (864,1187), (865,1187), (865,1188), (866,1187), (866,1188), (867,1187), (867,1188)`.

There are exactly (3^{10}=59,049) assignments before bounds rejection. Each trial starts from the frozen closed float32 context and changes only these ten cells. Every other context value must remain bit-identical. No height domain, physical bound, tolerance, shoreline definition, or source artifact may be changed.

At runtime, the executor re-derives this set from the five failed native edges: it checks that each edge has four aligned rows (P/F over both incident cells), then unions the corresponding C_cross CSR variable supports and requires this exact row-major set. The neighborhood deliberately excludes three additional CSR-support nodes which affect only matrix residuals near (10^{-15}), while direct P/F geometry finds no crossing drift there. The original `0/3^13` result is invalidated by `quantization-diagnostic-errata-v2.json`; no claim about joint feasibility follows from it.

## Inputs and source anchors

The executor uses only these pinned inputs: attempt-08 `prepared.npz` (`52409a8d074d15ec068bddc6e9265bc3782e84e9d54582b8a6d7b0a6675a787f`), one-call `solution.npz` (`1b7a23ebb3c203427f1c77cb8de6becfca750746e47f5494bba6723b0610eab1`), EV94 baseline terrain (`40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a`), P (`768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0`), F (`f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c`), and `water_v3.geojson` (`caa333e365c2a4511f839937a9d76a5aa157a0ef925d6ee4b5efcc4ebb38f8a9`). The complete map and hashes are recorded in `executor.py` and rechecked before/after enumeration.

`prepare_wet_bank_matrices.py:145-256` defines the P/F endpoint sampling, strict sign limits, and crossing interval inequalities. The independent geometric test instead recomputes each native edge's design intersection from the pinned GeoJSON, and evaluates rational crossing parameters from exact binary endpoint values; it does not use `C_cross` as the physical oracle. The metadata must be aligned by excluding its 32 `sign_only` summaries before indexing the 528 CSR rows.

`verify_wet_bank_result.py:221-238` establishes the D8 witness direction (center >= witness) and face-cone calculation `q=(G @ x + k_G).reshape(-1,2)`, `norm(q) <= radii_G`. `projection.py` (`A990DC2D33FCA4FD2A446B958F0412A2D752A5D3072A85D82058BB634CFAF44B`) defines the inherited energy rule at `evaluate_objective_gates`: new closed cost minus original raw cost must be `<= 1e-7 * max(1, raw_cost)`, and closed cost must remain strictly below baseline cost. The objective is `.5 * sum((A @ x - rhs_A)**2)`. Design-boundary edge intersections are deduplicated only for exactly equal binary64 coordinates; two distinct close intersections remain ambiguous and fail closed.

## Evaluation and order

The executor first checks the positive baseline B and the known negative raw candidate with independent P/F signs and all 116 direct crossing records. It then visits all 59,049 assignments in deterministic lexicographic `(-1,0,+1)` order, recording each assignment and the first failed gates in a JSONL ledger. For every assignment it checks, without tolerance:

1. Each of the ten resulting float32 values remains within its pinned inward float32 bounds; the other 111 variable values and all fixed context cells remain bit-identical to the frozen closed grid.
2. P and F same-sign edges retain their strict sign by exact comparison of the candidate float32 value and the pinned binary64 P/F value (both represented as exact fractions); this does not demand an extra float32 ULP. Baseline-contact endpoints remain bit-identical to their baseline float32 value. Crossing edges retain exact dry/wet signs and pass all 116 direct P/F/design interval checks reconstructed from the pinned sources.
3. Every one of the 150 direct D8 witness pairs satisfies `H[center] >= H[witness]`.
4. All 392 face cones satisfy `norm(G @ x + k_G) <= radii_G`.
5. The inherited closure energy allowance and strict improvement over baseline both pass.

Every assignment receives every gate result, including assignments outside bounds; those still test direct signs, all crossings, D8, cones, and energy. Non-target cells are checked bit-identical after every assignment. The best passing assignment is ranked by (a) total absolute ULP steps, (b) squared Euclidean distance to the stored continuous x64 solution, and (c) the complete row-major tuple `(r,c,step)`, including zero steps. If no assignment passes, record `NO_FEASIBLE_NEIGHBOR`. If one passes, write a distinct `neighbor-candidate.npz` and `receipt.json` with `DIAGNOSTIC_CANDIDATE_UNACCEPTED`; never rewrite or promote any terrain, prepared input, prior solve, or prior report.

## Runtime and checks

One real enumeration, if later authorized, has a 120-second numerical deadline and a 1 GiB peak working-set ceiling. Hash I/O is outside the numerical timer; the assignment ledger is written during the bounded loop. Timeout or memory overrun is terminal and leaves an incomplete receipt; there is no retry, widening, or fallback.

Before real enumeration, `--self-test` and `python -m unittest` exercise synthetic exact crossings, exact binary64 P/F signs without an unnecessary extra ULP, baseline-contact rejection, D8 direction, cone inequality, energy threshold, bounds, ranking tie-breaks, target-only writes, and the 59,049 count. They must not open real terrain inputs or create the real run directory. `--enumerate` is the only real-data mode and requires a fresh fixed output directory; it is prepared here but has not been invoked.

This test answers only whether this exact 10-node, one-ULP set contains a candidate satisfying these local gates. A pass would still need the frozen independent full geometry/coverage consumer; a fail is not authority to expand the neighborhood or alter the design.
