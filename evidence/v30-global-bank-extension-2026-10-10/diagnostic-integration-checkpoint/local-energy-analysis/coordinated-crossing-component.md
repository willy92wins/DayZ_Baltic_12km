# Coordinated crossing component around (858,1184)

**Status:** analytical pinning confirmed; no new candidate, solver call, or grid evaluation.

Inputs are the recovery-02 receipt/ledger, EV94 `prepared-runs/attempt-08/prepared.npz`, and the existing `solve-once/solution.npz`. The reproducible reader is `coordinated_crossing_component.py` (SHA-256 `050e495c32957b769281b9ab716cf316a7c705f3b9069ec7ea9713e3a2366db6`); its JSON result is `coordinated-crossing-component.json` (SHA-256 `9af0fa6dd9caa1f91e1c7144ce8ff2dc8f936202b40254b777714f795663645d`). The script rehashes the prepared data, solution, recovery receipt/ledger, polisher, and prior mechanism report before and after reading.

The energy-only one-ULP move at wet vertex `(858,1184)` raises it by `4.76837158203125e-7 m`. A compensating transfer that lowers `(858,1183)` by the same ULP and raises `(858,1184)` has a favorable exact quadratic objective change from the stored `A`:

`ΔJ = gᵀd + 0.5 ||Ad||² = −1.1089298951105775e−5`.

That energy gain is not feasible under the existing P/F crossing intervals. `C_cross H ≥ d` is affine in the heights, so the active-row implications are exact, not a first-order approximation. At the source state, the following rows have zero slack:

1. On edge `(856,1182)–(857,1182)`, row 10 is active P `cross_lower` and row 19 is active P `cross_upper`. The first endpoint is fixed by the current collar, so these rows require both `δ(857,1182) ≥ 0` and `δ(857,1182) ≤ 0`; hence `δ(857,1182)=0`.
2. On `(857,1182)–(857,1183)`, rows 26/67 then pin `δ(857,1183)=0`.
3. On `(857,1183)–(858,1183)`, rows 74/83 pin `δ(858,1183)=0`.
4. On `(858,1183)–(858,1184)`, active upper row 115 then requires `δ(858,1184)≤0`. The requested upward move is excluded. The original wet-only ULP also breaches the four listed interval rows on this last edge (P/F in two adjacent cells).

These are rows 10, 19, 26, 67, 74, 83, and 115 of the prepared crossing matrix/metadata. Their exact coefficients and cells are in the JSON. A traversal of all baseline-active crossing intervals finds a component of 38 rows over 11 nodes: 9 current variables and 2 nodes fixed by the collar, in rows 856–860 and columns 1181–1187. The pinning proof uses one fixed context node at the component boundary. It does **not** prove impossibility if the fixed collar/domain is redesigned; freeing collar nodes would require re-deriving their physical inward float32 bounds and rebuilding every affected objective, D8, face, and crossing row. That changes the current prepared problem and is not an authorized correction here.

The other energy-only one-node neighbor `(863,1189)` is a separate bound failure: its downward ULP crosses its active inward float32 lower bound. D8 passed on both energy-only neighbors; no D8 relaxation is relevant to these blockers. The allowance is not the obstruction: the proposed two-node transfer lowers the stored quadratic objective, but crossing feasibility rejects it.

**One bounded next step [DESIGN]:** before any further rounding polish, run an active-row component preflight on this 11-node component only. Keep the current collar fixed for the baseline test and fail closed when the pin chain above is found. If a future owner explicitly authorizes a domain change, make that a separate preflight which unlocks only the two identified collar nodes, derives their ordinary physical/inward-f32 bounds, and reconstructs all rows they touch; do not widen ULP radii or alter crossing intervals. It should stop before optimization if the expanded active-row system still pins the target or if D8/bounds leave no admissible direction. Budget: one read of the existing prepared matrices, ≤2 s, no solver or candidate. Positive fixture: a synthetic active upper-edge pair with `C=[−0.7,−0.3]`, `d=[−0.3,+0.7]` has `C·d=0`, validating a coordinated move when no upstream pin exists. Negative fixture: the real seven-row chain above rejects `δ(858,1184)>0` while the collar remains fixed. Both fixtures are embedded in the JSON-producing script.

No float32 tolerance, interval, bound, or D8 gate was relaxed. This result concerns only the current 121-variable prepared domain and the two energy-only records; it says nothing about a redesigned crossing contour or the full feasible set.
