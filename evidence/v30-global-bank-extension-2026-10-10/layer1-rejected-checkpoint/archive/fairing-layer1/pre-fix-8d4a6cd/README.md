# EV93 fairing layer one author

`author.py` is the explicit, offline author for the approved 703-window first-layer queue. It neither touches terrain data nor invokes a solver on import. `--prepare` validates the complete read-only preflight and writes a pinned `prepared.json`; the currently visible partial ledger is rejected. It does not assume a READY count. `--execute` requires the exact approved prepared SHA and makes at most one EV91 solve per READY window. An exclusive marker prevents retries after a solve begins; a timeout, solver error, or unresolved marker leaves the stage `INCOMPLETE`.

Accepted local deltas are reconstructed from the immutable B plus per-window detail and must pass the EV91/EV92/shape and local geometry gates before composition. Once a solver returns, its solution vector, float32 direction, matrix hashes, canonical stencil bytes, witnesses, bounds, and source identity are saved to a per-attempt `.solution.npz` before geometric gates run. A geometric `rejected` row retains that artifact path and SHA with `solve_calls=1`; unexpected validation or write exceptions are `error`, not geometric rejects. Non-READY preflight rows preserve B. A completed composed candidate is only `AUTHORED_PENDING_GLOBAL_CONSUMER`; it is not a map-wide acceptance.

Run with the GIS environment only:

```powershell
$py='C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe'
& $py 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\fairing-layer1\author.py' --prepare --preflight-ledger 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\preflight-segment02\window-ledger.jsonl'
& $py 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\fairing-layer1\author.py' --execute --approved-prepared-sha '<reviewed-prepared-sha>'
```

No `--prepare` or `--execute` command was run as part of this implementation. The fixtures reconcile the actual complete ledger and reconstruct one pinned READY detail. One isolated two-variable QP fixture calls the pinned EV91 spawn solver to verify Windows child-process imports; it does not read or write terrain.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
Push-Location -LiteralPath 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\fairing-layer1'
& $py 'test_author.py' -v
Pop-Location
```

`prepared.json` contains the ordered 703 queue rows, selection and exclusions through the queue binding, preflight header/final state, detail paths and hashes, all source pins, runtime versions, and baseline identity. Accepted and geometric-rejected results both persist the common solver record: node coordinates, B, physical and solver bounds, guard, D8 witnesses and matrix hashes, canonical stencils as lossless UTF-8 JSON bytes, solver vector, and direction float32 values. Accepted results additionally carry the final float32 values, alpha rule, shape/energy/angle/slope/hinge reports, and a hashed delta NPZ. Result events append to `ledger.jsonl`; each invocation appends its terminal `event=final`. Started markers are immutable and forbid retry; a result JSON and its solution/delta artifact are written once per queue row.

Outer queue `window17` uses `[r0,c0,r1,c1]`; queue/ledger details normalize to half-open `[r0,r1,c0,c1]` and cross-check geometry. `window_rc` and `core_rc` in prepared/results use the latter order. The local slope contract is `H <= max(35°,B)+1e-4°`; no weak-extrema or legacy EV87 checks are added.
