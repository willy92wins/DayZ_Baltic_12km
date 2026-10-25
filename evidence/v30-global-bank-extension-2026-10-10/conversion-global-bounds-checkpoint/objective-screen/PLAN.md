# Global objective screen before a constrained solve

This is a diagnostic of the existing EV95 dry-domain quadratic objective, not a replacement acceptance problem. The reviewed ADMM adapter is mathematically equivalent on its fixture, but a 0.47077 s normal action and thousands of outer/CG iterations make the proposed 1800 s global solve speculative. Do not spend that full budget without identifying the active constraints.

Run exactly one unconstrained PCG solve of A.T A x = A.T rhs on the same 2,712,136 variables, fixed EV95 surroundings, curvature rows and 0.25 fidelity rows. Use the already reviewed fused a_normal action and exact diag_a Jacobi preconditioner. Keep the pinned CP CG rtol 1e-12, atol 1e-13 and maximum 1000 iterations; start at EV95. Positive fidelity makes the normal positive definite. No ADMM, rho change, modified height bounds or changed water model.

Budget: one invocation, 300 seconds including postchecks, 3 GiB process peak and 6 GiB free physical RAM. A separate sampler latches resource violations; the callback and every stage boundary check it. Failed/timeout runs retain a terminal receipt and no candidate. Emit progress every 25 CG iterations or 30 seconds. Verify exact source/plan/review pins before creating the exclusive run directory and verify them again at the end.

After convergence, evaluate both x64 and direct float32 conversion against the existing prepared box, direct D8 witness order, and all native face radii, with exact counts and maximum violation, no relaxed acceptance. Record affected vertices and objective improvement. For diagnostics only, save the continuous vector in a clearly unaccepted NPZ. It is not a full terrain and cannot be built or deployed. Independent whole-terrain hinge/minimum/coverage consumers remain necessary for any later candidate.

The result discriminates whether the unconstrained objective is feasible and how many constraints bind. If infeasible, it is not a map candidate and no automatic second solve follows. A constrained algorithm or warm start must be reviewed as its own unit. Do not infer global convergence time from this screen.
