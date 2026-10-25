# ADMM adapter for the fused matrix-free normal action

Status: small-fixture adapter only. No global solve, candidate, or terrain output.

## Frozen references

- CP source: `../face-slope-cone-pilot/pilot.py`, SHA-256 `d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a`.
- Structured matrix-free rows: `../global-structured-operator/structured_operator.py`, SHA-256 `d3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a`.
- Fused normal action: `../global-structured-operator/optimized-normal/fused_normal.py`, SHA-256 `19a3e3a493f643702e66aaf265c705739535d386412f74659369d7746117ffaa`.
- Real-domain action comparison: `../global-structured-operator/optimized-normal/comparison/run-01/comparison.json`, SHA-256 `db6fa205e2b2b3d824ac07c1ad52d6c54ae6bf12e8b34d1a7093a701f518a965`.

## Change boundary

`solve_admm_matrix_free` mirrors CP `solve_admm` and changes only the x-step operator plumbing. It uses the existing A/C/G matvec and adjoint callbacks, `FusedNormalAction.linear_operator(rho)`, its exact diagonal for the same Jacobi preconditioner, and caches `A.T@rhs` once via `rmatvec_a(rhs_a)` as the sparse CP loop does. The caller supplies CP's pinned `project_discs`; the adapter keeps box/D8/SOC updates, scaled duals, residuals, stationarity, stopping rule, rho adaptation every 25 iterations through 2000, and CG settings unchanged.

Only time budget and peak-working-set limit are explicit runtime settings, with defaults equal to the pinned CP constants; the solver's rho, tolerances, iteration limits, CG controls, and rho schedule are constants copied from the pinned source. The memory snapshot callback is injected. This removes the prototype's hard-coded guard from the adapter without changing its numerical settings. It does not monkeypatch module globals, assemble CSR matrices, or store transposes.

## Fixture contract

The fixture creates a 16x16 terrain and a small variable patch. It materializes CSR A/C/G only inside the test by applying the frozen matrix-free callbacks to basis vectors, then runs the pinned CP solver and the adapter on the same rows, offsets, radii, bounds, and initial point. It compares convergence, primal/dual/stationarity residuals, objective cost, box/D8 feasibility, and active SOC faces within explicit tolerances; bitwise equality is not required. It also checks the fused diagonal and one normal-action result against CSR and rejects malformed operator inputs.

## Memory accounting for the EV95 dimensions

This is an array-liveness estimate, not a measured global ADMM peak. From the pinned sizing receipt, `N=2,712,136`, `mA=11,095,396`, `mC=4,182,435`, `mG=16,760,836`, and one float64 element is 8 bytes. Persistent matrix-free operator data is 493,954,896 bytes; fused boolean row masks add at most 12,582,912 bytes. ADMM split state alone retains `x, z_box, u_box` (65.1 MB), `z_D8, u_D8` (66.9 MB), and `z_face, u_face` (268.2 MB). A typical CG call also retains its RHS and roughly four to five N-vectors (about 108–130 MB). At the projection boundary, `Gx+k`, the `Gx+k+u_face` temporary and projected face output can overlap (up to about 402 MB before counting the persistent `z_face/u_face`); each G row vector is 134,086,688 bytes (134.1 MB decimal), not 200 MB. The fused A action uses three full float64 grids (100.7 MB), three boolean masks (12.6 MB), and returned/transient N-vectors; its explicit `.0625*x` term is 21,697,088 bytes. These simultaneous-array terms give a rough peak scale around 1.4–1.7 GB before Python, allocator, and input overhead; this is not a measured solver peak. The previous pilot's 1.5 GiB cap is not inherited as a global contract.

The real comparison measured one old normal action at 1.1574181 s and one fused action at 0.4707728 s, max absolute difference `2.842170943040401e-14`, process peak 1,037,549,568 bytes. This demonstrates the action speedup only; it does not predict CG iteration count, ADMM convergence, or full-solve time. The fixture's process peak includes both small CSR and matrix-free runs and is not a global memory measurement.
