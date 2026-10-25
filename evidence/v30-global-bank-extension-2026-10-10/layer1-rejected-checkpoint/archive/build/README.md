# EV93 isolated preview preparation

This directory contains offline preparation source only. No EV93 candidate was staged, no build or PBO packaging was run, no preview files were copied, and no mission was created during preparation.

The source was adapted from EV87 `build/stage.py`, `build/build_surface.py`, `build/package.py`, and `build/prepare_probe.py`. The EV93 scripts require explicit paths to the real `fairing-layer1/authoring.json` and independent `consumer-global` report. `ev93_build_common.load_accepted_inputs` fails closed unless the receipt is `AUTHORED_PENDING_GLOBAL_CONSUMER`, the consumer is `PASS_INCREMENTAL_NONREGRESSION`, all consumer gates are true, candidate/prepared/receipt hashes match, and every declared consumer input still has its reported SHA. It records that `OPEN_INHERITED_MAP_DEFECTS` remains open; this package cannot assert whole-map completion.

The inherited identities are pinned in `ev93_build_common.py`: EV82 B terrain `f9fb23de…`, source WRP `3071395e…`, world PBO `b11c825b…`, water PBO `3946db8b…`, plane `768e8e58…`, and visible field `f446a216…`. Staging rewrites only WRP heights and compares all 18,033 object byte records plus header/material/terminator. P and F are copied byte-for-byte from B. The surface step reuses the EV82 affected-footprint helper and its pinned generator/consumer identities, with the real candidate delta and EV93 consumer change count. Packaging targets the fresh `@DayZ_Baltic_EV93_GlobalBankPreviewV1` path; it never overwrites the incremental baseline or promotes the result.

`prepare_probe.py` gates mission preparation on the real EV93 receipt/report, successful stage and surface receipts, the package receipt, and actual PBO hashes at the isolated target. It keeps the EV82 native baseline and recalibrates all 1,212 serialized `points`; the fixed `reference.update({'points': points, ...})` avoids the EV87 omission where recalculated values were not written back. Each calibrated point is independently checked by solving its local NW-SE triangle plane, while point identity and all 1,205 `expected_water` values must remain unchanged. The verifier is adapted from EV87 V2 verifier source SHA `be9a531e…`; its independent parser, thresholds, classifications, and negative controls remain in place under new EV93 output names.

After candidate and consumer PASS are actually produced and separately reviewed, the intended offline command sequence is:

```powershell
$python = 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe'
$receipt = 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\fairing-layer1\authoring.json'
$consumer = 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\consumer-global\runs\<actual-run>\ev93-review.json'
& $python 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\build\stage.py' --authoring-receipt $receipt --consumer-report $consumer
& $python 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\build\build_surface.py' --authoring-receipt $receipt --consumer-report $consumer
```

The remaining `package.py` and `prepare_probe.py` are deliberately later gates. Their presence here is not authorization to run them; preview packaging and mission creation remain outside this preparation task.
