# EV93 layer consumer: coverage and focused fixtures

`verify_layer.py` now reconstructs the unknown-face lower envelope from each accepted window's **physical inward bound** (`patch["bounds"]`). It deliberately does not use `solver_bounds`: those may pin guard nodes to B for the author solve, while the unknown-face certificate must retain the EV90/EV91 physical L32 at those same nodes.

Source contract: `E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010/ev91-descent/consumer/verify_ev91.py:326-332` takes `domain['lower']` and maps it over `domain['variables_set']`; lines 354-359 construct `min_clearance_L32_m` from that lower envelope. The consumer helper `physical_lower_envelope` mirrors that input contract without importing author code.

For unknown compiled-face intersections, the consumer serializes tuple identities as JSON records with an explicit `key` list. Its contract is layer-specific: unknown physical/P faces require nonnegative clearance in B, candidate H, and L32; unknown visible/F faces retain the stricter `>2e-5 m` clearance. The indexed fixture exercises actual triangle clipping, unknown-face recording, both thresholds, and JSON serialization.

Run local validation with the GIS environment only:

```powershell
& 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe' -m py_compile 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\consumer-global\verify_layer.py'
& 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe' 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\consumer-global\verify_layer.py' --self-test
```

`fixture-report.json` records the actual output and source hashes. The real EV92 pilot fixture exercises one local window (85 variables, 350 stencils, 42 changed heights), verifies a positive contract and rejects a one-ULP guard mutation. It also distinguishes physical lower bounds from solver-pinned guard bounds. The indexed unknown-face fixture checks a physical face at +1e-5 m (accepted), −1e-6 m (rejected), and a visible face at +1e-5 m (rejected by the stricter threshold). These are local consumer fixtures only; the EV93 703-window/global candidate evaluation was not run here.


## Segmented author ledger

The author ledger is append-only and may contain intermediate `INCOMPLETE` checkpoints before its final `AUTHORED_PENDING_GLOBAL_CONSUMER` event. The consumer validates each checkpoint against the number of already classified rows and its exact `unprocessed_qids`; it requires the terminal event to classify every prepared queue row and match final state counts. It does not require a single `COMPLETE` event.

The real ledger smoke used 705 events: 490 results followed by an `INCOMPLETE` checkpoint with 213 remaining, then 213 more results and the terminal pending-consumer event. The parser accepted all 703 unique rows and reproduced counts 340 accepted, 311 rejected, 49 not authored, 3 inconclusive, 0 timeout, and 0 error. The prior parser rejected this valid segmented history; its source is preserved at `pre-terminal-parser-fix/verify_layer.py`. The original attempt-01 ERROR report remains unchanged. This smoke validates ledger parsing only; the full EV93 candidate evaluation remains `NOT_RUN`.


## EV93 face-index query labels

The production `FaceRangeIndex.query_cell/query_window` API accepts layer names `physical` and `visible`; the shard `kind` array stores codes 0 and 1. `direct_vs_index_cell` now passes the API label and uses the matching numeric code only for the independent shard scan. A focused fixture invokes the real class methods for both labels and checks that numeric `kind=0` is rejected by the API. The prior attempt-02 error (`unknown face kind: 0`) is preserved as an adapter error, not a candidate verdict.


## Direct exposure smoke

The consumer now resolves the B WRP from `verify_ev87.B/package/.../baltic_trial.wrp`, uses `BOUNDS_JSON`, and passes the existing workspace/model paths to `_compiled_exposure_pair`; deployment identity uses `B/deploy.json`. These names/signatures were checked in the frozen EV87 and coverage-contract sources. A bounded smoke ran `verify_index_against_direct` only on cells `(832,362)` and `(128,1918)`: the indexed face identities matched exhaustive shard selection, and physical/visible exposed geometry matched the independent ODOL reader with symmetric difference 0.0 m² for both cells. Attempt-03's prior missing-attribute error is preserved separately; no 703-window/candidate evaluation was run.
