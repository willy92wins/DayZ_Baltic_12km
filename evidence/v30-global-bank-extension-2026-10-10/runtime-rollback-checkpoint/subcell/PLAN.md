# EV95 subcell water-flag probe — preparation only

## Purpose and boundary

Prepare a fresh server-only mission to discriminate the six class-1 `P/F`-unknown samples and the five class-3 samples whose terrain is below every exact compiled physical face at the sample XZ. The probe samples around each exact point; it does not change terrain, water data, weather, date, time multiplier, or mission world state. It will not be launched by this preparation task.

The mission is `BalticEV95SubcellFlagsV1.BalticTrial`; its fresh output prefix is `$profile:baltic_ev95_subcell_flags_probe_20261010.log`. It runs only when `GetGame().IsDedicatedServer()` and the world name is `BalticTrial`. It uses `MissionServer`, no RPC, no player movement, no object placement, and no terrain writes.

## Pinned inputs

The point set is derived from EV95 `anomaly-classification/classification.json` (SHA `9dd964d4896166979da56c06d686ed14ed69020d468119931f27762a3dcbf089`). The EV95 terrain is `40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a`; P is `768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0`; F is `f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c`. EV95 `deploy.json` SHA is `f5a9c8185812e0b77a804ef9811e0405b5a7969f8ccfc19b85cc29d23cac03ca`; its `water_pbo_exact` flag is true and water PBO SHA is `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`.

Static face context comes from the COMPLETE EV93 index manifest SHA `c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c`, built from source WRP SHA `3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6` and the same water PBO. Exact point-in-triangle checks are retained in selection metadata; bbox candidates are not treated as hits. This index covers the exact 18,024 `baltic_water_v30` objects, not the nine other world objects.

## Samples and timing

Eleven anomaly centers are included: all six class-1 points and the five class-3 points whose terrain height is below all containing physical faces by more than `1e-5 m`. For each center, sample the center and the eight `[dx,dz]` combinations in `{-r,0,+r}² \ {(0,0)}` at `r=0.05, 0.25, 1.0 m`: 25 points per center, 275 total. Add four exact-point controls taken from the already passing EV95 native risk readback: two pond-positive controls and two dry/no-water controls. Total: 279 unique points.

Take seven complete samples at approximately `t=0,5,10,15,20,25,30 s` of simulation time. Preserve the actual `GetTime`, sea level, current/max sea wave, and wind readings per batch and per sampled point. The cadence measures only the observed ~30-second interval; it does not certify the full tide/wave envelope. Query in bounded chunks of 32 points per `OnUpdate` to limit a single server-frame workload. The mission records actual elapsed times rather than assuming a cycle duration.

Each point record includes ID/role/offset, XZ, `SurfaceY`, `SurfaceIsSea`, `SurfaceIsPond`, `GetWaterSurfaceHeightNoFakeWave`, `GetWaterSurfaceHeightWithFakeWave`, and `GetWaterDepth(Vector(x, ground+0.01, z))`. This matches the existing native probe's `GetWaterDepth` query height and adds the fake-wave height readback. Positive controls must be pond-positive in the pinned baseline; dry controls must have both flags false, a no-fake surface below terrain, and negative depth. These controls are diagnostics, not acceptance gates for the six class-1 points.

## Interpretation

Compare center and offset readings against the compiled physical/visible-face containment and edge-distance metadata. A flag transition within 0.05–1 m of a compiled face edge is evidence of a spatial transition, not automatically an error. Stable false flags where both faces and scalar water are present remain a runtime/API classification question. A positive scalar with no P/F and no indexed face remains unresolved; do not infer a water polygon from NaN fields or scalar height alone. Report observed ranges and any phase variation, not an envelope guarantee.

## Validation before handoff

The generator must rehash its pinned inputs before and after building the point set and reverify the COMPLETE index shards. It must produce exactly 279 unique sample IDs, validate four controls against the native snapshot, and record the eleven target face identities and minimum barycentric edge distances. The mission source must pass the existing Enforce/native-probe lint for one real source file (nonzero source count), with the lint JSON pinned in `native-probe-lint.json`, and static checks for dedicated-server/world guard, no environment mutation, and one fresh log prefix. No server launch, DayZ run, staging, PBO build, or terrain write is part of preparation.

Authoritative API precedents are the EV95 mission source `build-wide-slope/missions/BalticEV95WideBankV1.BalticTrial/init.c` (SHA `8428ddfc5a951767928b8736528489bc577bc4083eb351d71c0a4380cbac8077`) and the existing temporal mission `DayZServer/mpmissions/BalticAnomalyTemporalV1.BalticTrial/init.c` (SHA `b9485174501c93bb151731cb421a14a01705d7302983cb2605c93f886e361354`). Both use the same water APIs; the temporal source logs no-fake/fake height, depth, sea level, current/max wave, and wind.
