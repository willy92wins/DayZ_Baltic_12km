# Face-slope cone pilot (synthetic only)

## Scope and run boundary

This pilot adds an affine gradient operator `Gx+k` and one radial-disc split per
native 6 m terrain triangle to the EV88 curvature-plus-fidelity objective. The
objective remains exactly EV88 (`xx`, `zz`, `xz` with `sqrt(2)` cross weighting,
and fidelity coefficient 0.25); box and selected D8 lower-halfline constraints
remain. It is a synthetic 64x128 test with two 64-column sectors and free
variables on both sides of their seam. It is not a map author, map preflight,
terrain candidate, slope acceptance consumer, or production contract.
The EV88 synthetic field is rebased to a low 2–4 m range before the local
Narva-like fixture is inserted; no 98 m perimeter cliff is part of the test.

No solver call has been made. The approved next action is at most one synthetic
solve after independent review, with a 120 s numerical timer and a 1.5 GiB peak
working-set ceiling. The source exposes `solve_admm`; the CLI requires the
explicit `--solve-once` switch. Do not use that switch before root review.

## Exact face map

Raster coordinates are `x=6*c`, `z=-6*r`, height `y=B[r,c]`. On each cell:

* Triangle 0 is NW, NE, SE. Its 6 m-scaled physical gradient is
  `(NE-NW, NE-SE)`.
* Triangle 1 is NW, SE, SW. Its 6 m-scaled physical gradient is
  `(SE-SW, NW-SW)`.

Each component is affine in variable heights: `q = Gx+k`. For each face the
radius uses the algebraically equivalent but baseline-safe expression
`R=max(6*tan(35 degrees), ||q_B||)`, avoiding `atan`/`tan` round-trip ULP loss.
Thus the disc implies the proposed native slope cap while retaining the
baseline exactly. The radius is not enlarged by the existing `1e-4 degree`
consumer tolerance. The later
independent consumer must recompute slopes from coordinates / triangle normals;
it must not accept slope results from this `G` implementation.

## ADMM system and KKT

The x step is matrix-free CG on
`A.T A + rho*(I + C.T C + G.T G)`. The RHS includes the affine offset `k` in
the face split. Projections are: box clip; D8 `max(v,d)`; and pairwise radial
projection onto closed Euclidean discs. ADMM rho, tolerances, CG settings,
iteration cap, and 25-step factor-of-two adaptation through iteration 2000 are
copied from the pinned EV88 pilot. Adaptation preserves unscaled multipliers.

Primal residual is the maximum infinity norm across box, D8, and face splits.
Dual residual is `rho*||delta(z_box)+C.T delta(z_d8)+G.T delta(z_face)||inf`.
Stationarity is `A.T(Ax-rhs)+y_box+C.T y_d8+G.T y_face`. Normal-cone checks
reproject each split using its saved multiplier; the face-cone check also records
SOC complementarity `R*||y_face|| - dot(z_face,y_face)`, with zero dual required
for strictly interior discs. These are diagnostics, not a substitute for the
future independent terrain gates.

Numerical limits fixed before any solve: ADMM primal/dual absolute tolerance
`1e-10`, relative tolerance `1e-8`; CG relative `1e-12`, absolute `1e-13`, at
most 1000 iterations; 10,000 ADMM iterations; 120 s numerical time and 1.5 GiB
peak working set. Preflight identity checks use `1e-12` for D8/disc/action,
`1e-11` for coordinate-gradient and normal-slope reproduction. Those are only
fixture checks. The synthetic report requires exact float32 box and D8 after
closure; raw-cast and closed-disc excess counts remain diagnostics, since the
real slope consumer evaluates `max(35,B)+1e-4 degrees` independently. The raw
float32 cast is retained as a quantization diagnostic, then the explicit solve
path applies the
pinned `real-sector-preflight/order-closure/projection.py::project_order` once
to the full synthetic grid, with full-grid float32 bounds, fixed mask, and
`(witness,center)` edges; it does not rerun ADMM. It then calls the pinned
`evaluate_objective_gates` with raw-cast, closed, and B costs evaluated by the
same EV88 A/rhs. It records independent coordinate slopes against
`max(35,B)+1e-4 degrees`; a closure budget or slope-gate failure is terminal for
this one run. The 120 s timer and 1.5 GiB cap include solver plus closure, not
file hashing or output writes. Future real acceptance still requires the
independent consumer. SOC boundary classification uses
`1e-7*max(1,R)` only to label residual diagnostics; it is not an acceptance
tolerance. No real-map gate or tolerance is changed here.

## Preflight and solve

Preflight rebuilds and saves B, the exact EV88 A/rhs rows, selected D8 C/d and
witnesses, G/k/radii, plus the independent check results. It verifies baseline
box/D8/disc feasibility, face-gradient action against a plane solved from the
triangle's XYZ coordinates, at least one free-free curvature stencil crossing
the sector seam, and a Narva-like face where the objective gradient favors
lowering the mobile SE vertex but the face disc forbids that direction. It also
exercises float32 representation, positive/negative radial projections, SOC KKT
sign/complementarity, the x-step operator against a tiny explicit Hessian, and
the pinned order-closure identity on B. None of these preflight checks runs
ADMM.

GIS interpreter:
`C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe`

Preflight only:
`C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe pilot.py --preflight`

Single solve, only after review:
`C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe pilot.py --solve-once`

Outputs are new files in this directory: `prepared.npz`, `preflight.json`, and,
only if explicitly run, `solve-once/`. Existing outputs are never overwritten.
Earlier source-version preflight outputs, if present under
`preflight-attempt-*`, are preserved diagnostics; only root-level files whose
source pins match this plan and `pilot.py` are current.

