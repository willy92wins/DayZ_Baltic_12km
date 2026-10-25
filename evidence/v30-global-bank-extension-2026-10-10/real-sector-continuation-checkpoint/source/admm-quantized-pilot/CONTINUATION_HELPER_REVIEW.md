# Continuation helper: source and fixture record

Status: helper/fixture prepared and synthetically validated; **no real-sector continuation was run**.

Frozen source `solve.py` remains SHA-256 `7e8636bf54ba23f7e23bc2f06464100439468da7b4edca85f96c72d0cd40e149`.

New files:

- `solve_resumable.py` SHA-256 `b852af714667e8b07944a97fbdbaba97fe0c2b90c3a555ff9821ef11fe6791d2`
- `test_solve_resumable.py` SHA-256 `f05a6298cc6e3a891977bed16426bbec411155cfdab15914e1b2882fe475321a`
- `resume-fixture-report.json` SHA-256 `c3b3295fb4e94a1f9eeac13efc5a77d4a041932f312583f2d4d127d86b2c268f`

## Interface

```python
solve(A, rhs, C, d, lo, hi, x0, budget, progress, *, state=None, stop_iteration=None)
```

No state and no explicit stop preserves the frozen `MAX_ITER=10000` default. A no-state run cannot request more than 10,000. A resumed run requires an explicit global `stop_iteration` greater than the checkpoint iteration and at most 20,000. The rho adaptation branch remains the frozen global rule (`it % 25 == 0 and it <= 2000`), so resuming at 10,000 does not restart rho adaptation.

The continuation state requires `x64`, unscaled multipliers `y_box`/`y_d8`, projections `z_box`/`z_d8`, `rho`, global `iteration`, cumulative `cg_iterations`, cumulative `rho_updates`, and cumulative solver `elapsed_s`. Resume reconstructs scaled duals as `u=y/rho`. State vectors, finiteness, feasible projections, positive finite rho, update records, and counters are validated before the loop. The CG counter allows the real observed scale (170,910), bounded by 1,000 CG iterations per maximum ADMM iteration.

`budget` is cumulative solver time, capped at 600 seconds total and 300 seconds additional for a continuation. `elapsed_s` tracks solver time only; the separate 275.814-second process/resource measurement is not substituted for the 271.486-second solver elapsed value. The caller still owns the one-continuation lifecycle and the external wall-clock/resource guard.

The original verifier helpers are exposed through the new module: `load_closure`, `close_float32`, `check_float32`, and `objective`; each loads the pinned frozen module. No acceptance gate or closure behavior changed.

## Fixture

GIS Python `gis-env` `py_compile` passed. The 49-variable synthetic fixture compared untouched-source continuous iterations 1–177 (in-memory stop boundary only) against helper iterations 1–50 plus checkpoint resume 51–177. Vectors and numerical diagnostics matched exactly; objective was `0.06220726744407591` in both. Negative checks rejected malformed shape, NaN, invalid rho/counters, and infeasible projections. A deliberately doubled unscaled dual diverged from the reference; the fixture also rejected no-state extension, >600 seconds total, and >300 seconds additional. A 170,910 CG-iteration checkpoint count was accepted.

The fixture is limited to the `reference49` synthetic problem. It does not establish real-sector convergence, candidate validity, float32 closure, or any map/global acceptance gate.
