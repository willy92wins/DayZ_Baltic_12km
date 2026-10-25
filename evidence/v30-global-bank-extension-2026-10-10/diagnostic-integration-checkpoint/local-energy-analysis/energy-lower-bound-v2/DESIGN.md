# Energy lower bound v2 — corrected physical halfspaces

**Status:** design and synthetic fixtures only. No real LP, no terrain optimizer, no candidate.

The v1 idea must not use prepared NPZ `C/d` as the source of physical rows: the prepared float64 rows have small baseline violations and do not prove they are a superset of the exact crossing contract. V2 reconstructs the physical affine halfspaces directly from the pinned `Crossing`, `Sign`, and D8 witness records, using `Fraction` levels/t values and the float32 baseline/collar as exact dyadic constants. The source contract is `lattice_milp.py` (`_build_sign_rows`, `_build_crossing_rows`, `_add_strict_sign`, `_build_d8_rows`); this new construction uses absolute-height variables, not the MILP's integer/binade encoding. Strict endpoint signs are safely weakened to non-strict inequalities; contact pins stay equalities, represented by two inequalities.

For each source crossing, orient endpoints by `dry_endpoint`, let `dD=Hdry-Ldry`, `dW=Hwet-Lwet`, and use exactly:

- `dD >= 0`, `-dW >= 0` (relaxed strict signs);
- `(1-t_lower)*dD + t_lower*dW >= 0`;
- `-(1-t_upper)*dD - t_upper*dW >= 0`.

D8 rows are `Hcenter-Hwitness >= 0`. Add source `fixed_indices` from the diagnostic as equality rows at the exact float32 baseline (the two raw-only singleton variables must not become free), and absolute inward float32 box rows `x>=lo`, `-x>=-hi`. Substitute any collar/fixed endpoint from the pinned float32 context before emitting rows. These constraints include the continuous relaxation of every physical/f32-accepted point in this 121-variable problem; they do not include SOC face cones or the float32 lattice, which only make the actual feasible set smaller.

The objective tangent/dual formula remains as in v1. Given any nonnegative dual vector for `M x >= b`, compute exact dyadic-rational `r=g-M.T*lambda`; the residual box support term is mandatory. A negative/nonfinite dual is a hard certificate failure, never clipped. The script `certified_tangent.py` contains only generic exact row construction, tangent/dual arithmetic and a conservative CSR evaluation-error bound; it does not import the author, call HiGHS, or load a real terrain artifact.

Before comparing the exact lower bound with the implemented float64 closure threshold, subtract the uniform evaluation error bound for CSR matvec, residual subtraction, squaring and summation over the finite box. If the assumed IEEE arithmetic preconditions, finite range, or outward error check cannot be verified, return INCONCLUSIVE. A proof of impossibility requires `LB - error_bound > 155.94406662416184`; a smaller bound is inconclusive. It can also prove strict improvement impossible only if its lower bound is at least the baseline objective, with the same evaluation-error treatment.

Fixtures cover the exact lower/upper crossing orientation with a fixed endpoint, contact and D8 rows, a source-singleton equality pin, a 1-D analytical dual, a nonzero dual residual whose box correction is necessary, rejection of negative/nonfinite multipliers, and comparison of the CSR error bound against exact rational costs at synthetic points. They do not exercise any real matrix or solve an LP. Target budget for a future certificate attempt remains <=10 s and <=256 MiB; no terrain optimizer call is part of this design.
