# Global dry-terrain solve, proposed numerical unit

This extends smoothing to the complete editable dry domain of EV95. Wet-channel profiles have their own conversion unit and are not released by this plan. Source terrain and water previews remain unchanged until independent consumers pass. The frozen 3 m grid exclusion, bed minimum 1 m and signed-corridor draft 0.95 m remain in force.

## Inputs and bounds

Use EV95 terrain SHA40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a and the 2,712,136-variable mask in sizing run-05 SHA8f5959308923263538440d29dd93960c5331bc8f13c88b61590380c17d6cdfff. The mask protects the compiled-water bbox and P/F/SEA shoreline or partial cells, unknown P9 corridor cells, civil/engineering/road/bridge vertices, large lakes, 499 retained windows plus two-cell halo and the explicit focus. The EV95 delta outside those guards may change. This is one global vector, with no stitched subproblem borders.

Global height bounds retain the earlier global EV79 budget and do not import the local B+0.5 cap:

- lower = max(EV95−2, min(EV79, level+1e−4), min(EV79,1.8), EV79−2);
- upper = min(EV95+2, EV79+2);
- level is the maximum of SEA0.85 and each incident P/F sample, using the original binary64 fields independently.

Round lower up and upper down to the closest float32. Require EV95 inside the box, no infeasible variable, all variable baseline heights above their known incident water levels, and no candidate lower bound at/below those levels. If these conditions fail, stop this preparation and report the nodes; do not alter bounds or the mask silently. The historical run-05 rounding helper was outward and cannot supply these bounds; its counts remain valid per the separate full-grid audit.

## Same numerical problem, efficient implementation

Use the existing curvature/fidelity objective, lexical D8 witnesses and per-native-face cones with radius max(6*tan35degrees, norm(gradient(EV95))). The two native triangle gradients are (NE−NW,NE−SE) and (SE−SW,NW−SW). The CP ADMM/CG equations, rho updates, stopping tolerances and cone/box/order projections remain unchanged. Substitute matrix-free callbacks and the reviewed fused normal only. No global A/At/C/Ct/G/Gt CSR or A.TA is constructed.

References read: CP `pilot.py:453–458,499–556`, SHA d743f5006e0aa6606024a3c3291a74cb52b78f76c1aa5c6dfd95cdd26cdc9d2a; structured operator d3017e58bbae3b71c891fab6892a5bf8d9386ae8a51a451a94c9b05769ac750a; fused normal19a3e3a493f643702e66aaf265c705739535d386412f74659369d7746117ffaa. The real-grid comparison db6fa205e2b2b3d824ac07c1ad52d6c54ae6bf12e8b34d1a7093a701f518a965 measured normal1.1574s→0.47077s with maximum difference2.84e−14. This is not a convergence estimate.

## Before the one solve

Require independently reviewed adapter fixtures against CP, a pinned bounds artifact and an independent review of this plan, domain and driver. A resource estimate must include operator/ADMM/CG/cone-projection temporaries and final float32 closure, and leave at least6GiB physically free. Proposed ceiling:3GiB process peak, with an independent6GiB-free watchdog; reduce allocations if the estimate cannot satisfy both. No launch while another map process from this unit is running.

One numerical invocation has a proposed total1800s ceiling including conversion and the existing deterministic D8 closure, checked at every CG callback and at projection boundaries. Emit progress at least every25 outer iterations or30s, including actual residuals, iteration/CG count, rho and memory; no assertion of future convergence. Timeout, infeasibility or memory guard are terminal for this invocation. Preserve evidence, including the last numerical state if safely available, without accepting it or rerunning with changed settings. A later algorithm change requires its own mechanism and reviewed unit.

## Independent acceptance after convergence

Quantize to float32 once and apply the already frozen D8 closure within the same box. Verify its original energy allowance and improvement against EV95. Then a consumer independent of the author must check the final whole terrain: all other vertices and metadata exact; bounds and D8 by direct comparisons; no newly excessive native slopes; no new >30degree hinges and nonworsening affected-bank/interior p99 under the existing angle contract; no new minima outside channels; every protected/retained vertex exact; P/F and water objects unchanged; water contact/sign/topology and compiled coverage preserved. No gate is excused by convergence or a lower objective.

Any failed consumer keeps the candidate unaccepted. Build and native readback are subsequent stages, followed by valid render and dynamic-water tests. BASE1.0 is not accepted by this numerical unit.
