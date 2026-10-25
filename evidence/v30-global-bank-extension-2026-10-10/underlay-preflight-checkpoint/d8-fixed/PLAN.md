# D8 witness-sign repair for the exact float32 lattice model

Status: isolated source repair and synthetic/control validation only. The real MILP is prepared as a single one-shot runner but is NOT authorized or invoked here.

## Confirmed defect and correction

The exact terrain inequality for each directed witness pair is `H_center - H_witness >= 0`. In lattice units the row must include `+center_expr - witness_expr`. `_merge_expr_row(row, expr, factor)` applies the same `factor` to both the coefficient map and returned affine constant. The copied pre-fix source instead added the witness coefficients with factor `+1` and subtracted only the returned constant, producing `+center + witness` in the matrix row. A witness that rose one float32 ULP could therefore pass the MILP row while failing the independent exact D8 gate.

The new local copy changes only row assembly to `const += _merge_expr_row(row, ew, Fraction(-1))`. `lattice_milp_before_fix.py` preserves the byte-identical pre-fix implementation for the adversarial regression fixture. The prior model, failed real-run receipt, and model outputs remain untouched.

## Checks before any real call

- Synthetic tests compare the assembled exact rows with the independent float32 D8 gate for variable center/fixed witness, fixed center/variable witness, both variables, and constant-only passing/failing rows.
- A regression fixture proves the preserved old model admits a one-ULP raised witness although the direct D8 gate rejects it; the repaired row rejects that assignment.
- The real B baseline control is regenerated without calling HiGHS and must satisfy the corrected matrix and exact gates.
- The one-shot runner has a create-only output directory and a 60-second/1,000,000-node cap. If exact/direct gates reject a solver incumbent, it writes a clearly diagnostic NPZ with lattice vector and context, marked non-accepted in the receipt. This artifact is not terrain or a candidate.
- No real MILP invocation is made as part of this preparation. A separate root review is required before the one-shot call.

## Scope limits

This repair fixes the D8 row coefficient/constant mismatch. It does not establish feasibility or acceptance of a real MILP solution, and it does not satisfy the remaining shape, global, or compiled/native gates. A future optimal incumbent still requires the exact fraction and direct gates plus the independent geometry consumer.
