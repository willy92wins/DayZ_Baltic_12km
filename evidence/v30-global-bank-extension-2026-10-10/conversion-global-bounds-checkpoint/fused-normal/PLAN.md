# Exact fused normal-action experiment

Status: implementation and small-fixture validation only. No global action measurement, ADMM solve, or terrain output has run here.

## Frozen references

- `../structured_operator.py`, SHA-256 `d3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a`.
- `../../face-slope-cone-pilot/pilot.py`, SHA-256 `d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a`.
- The current matrix-free global action measurement under `../measurement/run-01` remains unchanged; this folder creates no run directory.

## Contract

Keep the ADMM objective, `rho`, box/D8/SOC projections, tolerances, dual updates and stopping rule unchanged. Replace only the expensive `A.T @ (A @ x)` part of the CG normal action. `C` and `G` continue to use the already validated `matvec_*` and `rmatvec_*` callbacks. The diagonal remains `diag_a + rho*(1 + diag_c + diag_g)`.

For a zero-filled variable delta grid `X`, each active `xx` row computes
`q[r,c] = X[r,c] - 2*X[r,c+1] + X[r,c+2]`, then scatters `(1,-2,1)*q` by grid slices. `zz` is the corresponding vertical stencil. Each `xz` row computes the row value
`q = a*(-NW + NE + SW - SE)`, where `a=sqrt(2)/4`, then scatters `(-a,+a,+a,-a)*q` to its four corners (equivalently, the direct normal stencil has coefficient `1/8` times the signed corner sum at every corner). The active row masks are exactly those represented by the frozen anchor arrays. Finally add the identity-row contribution `0.25**2 * x`. This is the same `A.T(Ax)` algebra, evaluated directly without constructing CSR, coefficients, or transposes.

`FusedNormalAction.matvec(x,rho)` returns
`A.T(Ax) + rho*(x + C.T(Cx) + G.T(Gx))`.
The affine offsets remain outside the normal matrix and continue through the existing `normal_rhs()` contract. No global bound policy is introduced here.

## Temporary arrays and expected effect

The fused A path retains a full delta grid and gradient grid (two `2048x2048 float64` arrays: 67,108,864 bytes total), plus one reusable second-difference workspace no larger than one grid (33,554,432 bytes), three boolean anchor masks (at most 12,582,912 bytes), and the returned N-vector (21,697,088 bytes). The masks are operator metadata; the three work arrays and result are live during the call. It has no A-row output vector (`11,095,396 float64`, 88,763,168 bytes) and no separate A adjoint gradient pass. Existing C/G callbacks retain their prior temporary costs. This is expected to reduce A's two-step temporary traffic; no global time or convergence claim is made until the separate one-shot comparison is reviewed and run.

## Validation

`test_optimized_normal.py` compares (a) fused A-normal against the pinned CSR `A.T@(A@x)`, (b) fused total normal action against both the CSR normal matrix and frozen matrix-free normal action, and (c) the exact diagonal. It includes narrow row/column cases, mixed masks, fully variable masks, D8 ties, and stencil anchors across the column seam. Absolute maximum error must remain below `1e-10`; invalid shape, non-finite input, and nonpositive `rho` must reject. These fixtures do not authorize a solver or alter any global acceptance criteria.
