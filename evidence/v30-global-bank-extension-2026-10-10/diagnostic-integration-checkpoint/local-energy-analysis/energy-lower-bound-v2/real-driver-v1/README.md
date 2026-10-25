# Real energy-bound driver, preparation only

This folder is an additive driver beside the frozen v2 synthetic certificate. It reconstructs a **continuous physical relaxation** for the pinned 121-node diagnostic from exact `CrossSpec`/`SignSpec` records, D8 witnesses, and the exact physical float64 box. Coordinates are converted from global RC to the 15x15 context by the executor's pinned origin; outside-variable vertices are substituted from the baseline context. Strict P/F signs are weakened to non-strict. The prepared inward-float32 rows and `fixed_raw_only_indices` are not used as physical restrictions.

For a crossing, the relaxation contains dry/wet sign halfspaces and the exact interval inequalities

`(1-t_l) d_dry + t_l d_wet >= 0`, `-(1-t_u) d_dry - t_u d_wet >= 0`.

D8 rows are `H(center)-H(witness)>=0`. Objective rows are the exact binary64 values from prepared CSR `A,rhs`, interpreted as dyadic rationals. A HiGHS LP, if later enabled, supplies only a candidate dual; `dual_certificate` rechecks its nonnegative multipliers and computes the residual-box lower bound with `Fraction`. The bound is compared against the actual rounded gate `closed_cost - raw_cost <= allowance`; the threshold includes conservative subtraction-rounding allowance and the CSR evaluator error is subtracted from the certificate.

## Execution status

No real inputs were loaded by the preparation work and no real LP was run. `REAL_LP_ENABLED=False`, the module CLI is deliberately inert, and `obtain_real_dual` also refuses while the recovery-v4 report carries the three pinned failures: energy, protected/civil context, and local compiled-water topology. The v4 report marked protection/civil context false, but subsequent attribution identified that as a consumer false failure: 16 cls5/water nodes were intentionally released and had no effective-fixed/P9/road protection. The local compiled-water topology change is real (one water component is removed, 0.0283188364 m²), and energy still fails. P/F signs/crossings, D8, and box rows pass locally; none of this establishes whole-map physical validity. This driver remains blocked and the LP stays disabled.

The synthetic fixtures exercise exact crossing/sign/D8 rows, global-to-local RC, dual residual support, negative multipliers, threshold rounding, nonfinite values, and per-square/accumulator overflow guards. They do not certify that an LP dual exists for the real diagnostic. Any later real run needs fresh review of the v4 topology/protection attribution and explicit authorization.

