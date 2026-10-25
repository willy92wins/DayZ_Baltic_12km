# EV93 selected-bank preview preparation

This is an isolated source adaptation for selection receipts. No stage, WRP compile, surface generation, package, deployment, or mission was run while preparing these files. The legacy `build/` directory was not edited.

The entry contract is the real `ev93.compound-selection.v1` receipt plus the global `crest-extension/verify_selected_composite_v2.py` report. These are distinct from the frozen local selector verifier `verify_selected_composite.py`: the selection receipt must pin that local source at SHA `8cd8f28b7914936bdf86f884b18bd14eb11aeca306f24327851dda340f16a543`, while the global report must identify v2 at SHA `6e661b073e5f27b2475e6b82d75d6a7722d0503a082dcfd51d8f00bd6de9722b`. The common gate requires receipt status `SELECTED`, a candidate whose recorded metadata matches B, a retained crest, the exact compound-pool SHA, and a nontrivial changed-vertex count. It requires report status `PASS_INCREMENTAL_NONREGRESSION`, every gate true, and identical `input_hashes_expected`, `input_hashes_start`, and `input_hashes_end`; every source in the selection receipt's `source_read_set` must also occur with the same SHA in the global report's expected read-set. It then rehashes both sets from disk. Each later artifact carries `ev93_selection_receipt`, consumer report, candidate, pool, selector-source, and global-consumer-source identities. The build keeps the inherited global-contract status open; a preview does not claim map completion.

Baseline WRP, terrain, P/F arrays, world PBO, and water PBO identities are inherited from the checked EV93 preparation. Staging changes WRP heights only, keeps all 18,033 object records, and copies P/F from B byte-for-byte. Surface generation and package/readback steps retain the existing EV82 footprint and mip/OPRW checks. The fresh preview destination is `@DayZ_Baltic_EV93_SelectedBankPreviewV1`; it does not overwrite or promote the incremental baseline. The copied probe preparation preserves the fixed `reference.update({'points': points, ...})` behavior and writes the selected-preview mission header.

After a real selected receipt and the independently reviewed consumer PASS exist, the future command sequence is:

```powershell
$python = 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe'
$selection = 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\compound-selection\runs\<actual-run>\selection.json'
$consumer = 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\crest-extension\consumer-runs\<actual-run>\ev93-review.json'
$build = 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\build-selected'
& $python "$build\stage.py" --selection-receipt $selection --consumer-report $consumer
& $python "$build\build_surface.py" --selection-receipt $selection --consumer-report $consumer
& powershell -NoProfile -ExecutionPolicy Bypass -File "$build\compile_native_world.ps1"
& $python "$build\package.py" --selection-receipt $selection --consumer-report $consumer
& $python "$build\verify_packaged_oprw.py" --selection-receipt $selection --consumer-report $consumer
& $python "$build\check_changed_mips.py" --selection-receipt $selection --consumer-report $consumer
& $python "$build\prepare_probe.py" --selection-receipt $selection --consumer-report $consumer
```

These commands are documented for later operation only; their presence is not authorization to run them. The selected preview PBO, native readback, and in-game appearance remain unverified.
