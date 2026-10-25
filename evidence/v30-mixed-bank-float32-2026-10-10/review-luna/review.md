# EV81 consumer review — FAIL_EV81_CONSUMER

Candidate `candidate/terrain.npz` SHA-256: `c0bc7cb9793fb9fd28af184cea72bdafcc6667d46e7e67d9389b9b19659a423b`. Independent offline verifier: `verify.py`; full machine-readable output: `report.json`. No candidate, package, or engine state was changed.

The EV79 full-map gates pass: selector and metadata identity, exact P/F and wet support, no new wet faces, engineering/fixed masks, road controls, lower floor, ±2 m source budget, and native face-slope bounds. The EV80 deployed identity check also passes. The EV81 candidate improves source-relative mixed-any folds >30° from 4,693 to 2,819 and lowers hinge energy on EV81-vs-EV80 changed-incident edges by 17.6975% (17,567 edges).

EV81 nevertheless fails three EV80-relative preservation gates:

- **Six newly >30° hinges** among changed-incident edges (tolerance 0.0001°): diagonal `(r,c)=(903,897)` 28.680325→34.753428° (`x,z≈5382,6864`); diagonal `(1424,1883)` 29.990879→30.858636° (`11298,3738`); diagonal `(1899,1087)` 29.907195→30.273128° (`6522,888`); vertical `(103,1613)` 29.555148→30.805614° (`9678,11664`); vertical `(1899,1086)` 28.755498→31.250393° (`6516,888`); horizontal `(1370,1334)` 27.281431→30.268619° (`8004,4062`). Coordinates are the edge-grid anchor mapped to nearest terrain node coordinates.
- **Bank p99 regresses** from 4.982072° to 5.004888° (+0.022816°); count >30° remains 1.
- **One modified 64×64 sector maximum regresses:** sector `(29,16)` rises from 41.671232° to 42.647964° (+0.976732°).

The failures are real EV80-relative geometric regressions, not a failed ULP fallback or a new-water/support violation: all source/EV79 water-support gates pass, and the measured issue is that EV79-relative constraints permit changes that do not preserve every EV80 improvement. Do not package this candidate under the current EV81 acceptance gates. No EV81 engine/render/material validation was attempted.
