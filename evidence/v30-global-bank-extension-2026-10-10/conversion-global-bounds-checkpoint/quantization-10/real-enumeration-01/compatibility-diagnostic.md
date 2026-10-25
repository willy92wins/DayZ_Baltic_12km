# Compatibility diagnosis: one-ULP shoreline neighborhood

## Result

The pairwise table has all 116 direct crossing records; **none has an empty table by itself**. Under the same ten-node, `{-1,0,+1}` float32 domain, bounds plus the direct pair relations are nevertheless inconsistent. AC-3 empties the domain at `(863,1187)`. A smaller certificate is the direct conflict on `(864,1187)`:

- Record 76, physical P edge `[(863,1187),(864,1187)]`, allows only pairs `[(idx2,-1),(idx3,+1)]`, `[(idx2,0),(idx3,+1)]`, `[(idx2,+1),(idx3,+1)]`. Thus it requires option `+1 ULP` at `(864,1187)` for every option at `(863,1187)`.
- Record 80, physical P edge `[(864,1187),(864,1188)]`, has the second endpoint fixed to the frozen raw context. It allows only `-1` or `0 ULP` at `(864,1187)` and rejects `+1`.
- The same node's options are `5.6719560623168945` (`0x40b580aa`), `5.671956539154053` (`0x40b580ab`), and `5.671957015991211` (`0x40b580ac`). All three satisfy that node's initial inward bounds and unary P/F sign domain; the conflict is between the two direct crossing records, not a box restriction.

This proves no assignment in the tested domain can satisfy all 116 physical crossing constraints while all other cells stay at the frozen raw context. It does not rely on the 59,049-way enumeration, and does not use D8, face cones, or energy to establish the contradiction. It gives no authority to widen the domain or alter the shoreline contract.

## Artifacts and scope

- Pairwise tables and AC-3 trace: `compatibility-diagnostic.json`, SHA-256 `0cb852c2aa3bdd99e7b1dbdfb079df5f9faa65c3db854a3ff1389b25d8b53da7`.
- Reproducer: `compatibility_diagnostic.py`, SHA-256 `3288c1164e4ba261cb426f04d41fac858b786d20fb370f3ea0ed2957d7b8c492`.
- The diagnostic readset is stable: 14 start / 14 end pins, zero differences. The exhaustive run remains `NO_FEASIBLE_NEIGHBOR`, 59,049 assignments, 116.055 s, 157,212,672-byte peak; receipt SHA-256 `899dc5d7e031436d4b53c2eb2bdaf515bf3f32612b3af8c69fba5b8cf5fb208b`. No candidate exists.

## Existing acceptance doors still open

The wet-bank plan requires connectivity of the water and no new minima outside the channel, plus reporting the maximum incident and exposed-area change (`G/wet-bank-pilot/PLAN.md:25`). The prior postsolve consumer explicitly records that water connectivity and outside-channel extrema were not recomputed (`G/wet-bank-pilot/postsolve-consumer/verify_wet_bank_result.py:356-358`); the compiled coverage consumer reports P/F support holes and residuals, but not those two measures or exposed area (`G/wet-bank-pilot/coverage-consumer/check_coverage.py:149-170`).

Existing checks worth reusing: candidate composition requires only the 121 pilot nodes to differ and preserves non-height fields (`verify_wet_bank_result.py:294-306`); compiled coverage binds EV95 objects/deployed water and checks physical/visible support (`check_coverage.py:55-68, 149-158`); preparation recorded 499 retained units and a stable 666-path readset. Pin that preparation/receipt and enforce the unchanged-outside-domain/no-overlap check instead of rehashing all 666 files. For physical P/F crossings, use the direct exact-fraction geometry check: the old `C_cross >= 0` matrix gate has a baseline roundoff residual and is not itself the geometric oracle.
