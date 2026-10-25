# EV92 consumer adapter — prepared, not run

Status: source and in-memory fixtures ready for root review. No EV92 authoring, candidate creation, solver, or full consumer run was performed.

## Frozen inputs

The adapter checks these final approved pins before a full evaluation:

- plan `../plan.md`: `242010094113e888203ca9a995b050887ea7190da9bfe4a3bd2d82e3946f1a43`
- author source `../author_ev92.py`: `818376c2fca9123473b862ece174f4277ffebf3568eb8875863e354e7e2fe4fd`
- prepared `../prepared.json`: `a2e9f18b1e77db5d3ce90cb4d928464c775167f2e1c0ff99c2776d1cca0e802d`
- frozen EV91 consumer: `5e726b93642f5db531193a8f1d85afabd139c7b9ac3afca4479df793afd53668`
- EV91 attempt-02 report: `594b1985cd8b75c5e3b17c3ea5262a162c4e23ea50474051285713ef132df061`
- EV91 sorted gate-key set: 27 keys, canonical SHA256 `8b5fe00ddb0fbb045bfb1c9981aa95cb5b204574683fbb8bc792ff4b15d9ca2e`

EV92 alpha is the approved stable midpoint `0.6769237551186755`. The consumer independently derives exact rational stencil moments from B and frozen H91, computes the plan-prescribed stable energy root plus focus roots, and rejects any differing prepared/receipt rule or alpha. It reconstructs only `float32(B_float64 + alpha * (H91_float64 - B_float64))` with a single final cast. This is a materiality rule, not a claim that all gates will pass.

The prepared manifest is not required to self-pin. Its source-pin check covers authoring inputs; the EV91 evaluator and baseline report are independently hash-checked by the consumer. The fixture confirmed the supplied prepared source-pins match the frozen inputs.

## Gate reuse adapter

`verify_ev92.py` hashes the unchanged EV91 evaluator and the exact attempt-02 gate set. It validates EV92 provenance and full-grid interpolation before loading the EV91 module. The explicit scoped projection temporarily redirects only `verify_authoring_receipt` and `WET_DIAGNOSTIC_PATH`, authenticates the original EV91 receipt using the original validator, and substitutes only candidate path, SHA, and changed-vertex count for the EV92 candidate. The EV91 evaluator and its 27 gate functions remain unchanged. Both module bindings restore in `finally`; the returned report labels this compatibility projection and states that H92 was not produced by SLSQP. The wet-support diagnostic is routed under EV92 consumer `runs/`.

## Fixture result

`test_ev92_consumer.py` uses actual pinned B, H91, and prepared artifacts but constructs the expected interpolation only in memory. It tests the approved scalar rule and 27-key identity, one-cast reconstruction, malformed source pin, one-ULP alpha change, nonzero solver-call claim, one-height mismatch, non-height mutation, and adapter restoration after both success and exception. It asserts the EV92 candidate path remains absent.

GIS Python command used:

```powershell
C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe -m py_compile E:\DayZ-Baltic-Build\v30-wide-bank-fairing-pilot-20261010\ev92-damped\consumer\verify_ev92.py E:\DayZ-Baltic-Build\v30-wide-bank-fairing-pilot-20261010\ev92-damped\consumer\test_ev92_consumer.py
C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe E:\DayZ-Baltic-Build\v30-wide-bank-fairing-pilot-20261010\ev92-damped\consumer\test_ev92_consumer.py
```

Full EV92 evaluation remains pending candidate and receipt creation plus root review. A gate failure must be preserved; no alternate alpha or repair is authorized by this consumer plan.
