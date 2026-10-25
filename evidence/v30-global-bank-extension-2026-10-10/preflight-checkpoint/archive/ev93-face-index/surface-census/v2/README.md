# EV93 native hinge sector census

This is v2, a read-only baseline census of `B` using the exact `edge_angles` and incidence geometry from the SHA-pinned EV87 independent consumer. It counts every native hinge of type `diag`, `vertical`, and `horizontal`; no angle/prominence selector, candidate terrain, solver, PBO, or engine is used. The preceding v1 artifact was preserved under `../rejected-v1/` after review found its `all_eligible` flag incorrectly used ANY incidence.

Each hinge is assigned exactly once to the 64×64-node sector containing its top-left array anchor `(r,c)`. Its full four-vertex footprint remains intact if it crosses a sector edge. The NPZ stores raw float64 B angles and uint32 incidence flags by family, plus per-sector counts, mean angle, mean-square angle, maximum and p99. The JSON records source hashes, global metrics, population masks and reconciliations. Categories with `any_` use ANY of four vertices. `all_eligible` uses AND of all four; `mixed_eligible = any_eligible AND NOT all_eligible`, and the fixtures reconcile `ANY = ALL + mixed` to an independent oracle. Both full EV87 bank/interior populations and their eligible intersections are reported, as is all `wet_support` and `eligible ∩ wet_support`. `any_fixed` means EV87 `other_fixed ∪ engineering_halo`; `any_protected` additionally includes large-lake banks and reserve/platform. Waterline-blocked and non-class-0 are separate diagnostic groups.

Run with the GIS Python:

```powershell
C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe build_sector_native_curvature_census.py --self-test
C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe build_sector_native_curvature_census.py
```

The fixtures compare ANY incidence against an independent four-vertex oracle and prove the sector partition has no omissions or duplicates. For each family they exercise complete classifier cases with 0, 1 and 4 eligible vertices. The full run reconciles every population count by family from sector sums to direct full-array counts. This describes B shape over the 6 m native terrain grid; it is not a correction proposal or evidence that all counted roughness is undesirable.
