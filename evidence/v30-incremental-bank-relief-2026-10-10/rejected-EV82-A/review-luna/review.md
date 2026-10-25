# EV82 independent consumer — FAIL

Candidate SHA-256: `c2291acac83fa5a1e1bf4bb6a2fd214d2288ce33635de37967df05601616e2c4`. The independent offline consumer is [verify.py](E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-20261010/review-luna/verify.py); its complete output is [report.json](E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-20261010/review-luna/report.json). No candidate, package, or game state was changed.

The consumer confirms the EV79 invariants, original ±2 m total budget, selector and per-node incremental trace, exact P/F, wet support, fixed/engineering masks, road checks, EV80 deployed PBO identity, and EV80-relative slope, bank/interior p99, energy, and sector gates. The trace matches 3,048 edits this pass against EV80 and 4,091 total changed vertices against EV79. Mixed-any folds above 30° fall from 4,693 in EV79 to 2,597. Incident hinge energy against EV80 falls 13.4966%; bank p99 and count and all sector maxima pass.

Two EV80 hinges newly exceed 30°, so both `zero_new_edges_over30_from_at_most30` and `zero_new_edges_over30_vs_EV80` fail:

- Diagonal `(row,col)=(143,1726)`, world hinge `(x,z)=(10359,11421)`: EV80 `30.000000013724588°` → EV82 `31.441660920813348°`.
- Diagonal `(1473,636)`, `(3819,3441)`: EV80 `30.000000015162275°` → EV82 `36.23216932739762°`.

The author’s threshold is `EPS_ANGLE=1e-8` in [author.py](E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-20261010/author.py:35), and it adds the 30° cap only when a reference hinge is `<= 30 + EPS_ANGLE` ([author.py](E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-20261010/author.py:461), with the same condition in float32 validation at line 516). Both EV80 values sit just above that threshold, so they miss the cap. The independent consumer classifies new folds with `TOL_DEG=1e-4` ([verify.py](E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-20261010/review-luna/verify.py:19)); it correctly treats both as at-or-below 30° and catches the regression. Keep the consumer tolerance unchanged; align the author’s classification with the accepted gate before any further authoring.

The final consumer run exited 1 with `FAIL_EV82_CONSUMER`; all other gates passed. This is an offline geometric rejection, not engine/render acceptance. No package or motor validation was attempted.
