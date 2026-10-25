# EV94 focal composition preview preparation

This is a source-only, isolated adaptation of the reviewed EV93 build pipeline. It accepts the independently generated focal composition report plus the focal 36-gate supplement. It does not accept or manufacture an EV93 selection receipt. The accepted candidate is the composed full terrain `30d0ed33…15a1`, based on selected candidate `6e275573…461d`; the adapter requires the exact 499-unit composition and 30,067 changed vertices versus EV82 baseline B, including focal vertex `[840,370]`.

The preparation code preserves EV82 B's object records/materials/header/terminator, copies P and F by exact SHA, validates all non-height NPZ arrays including NaNs, rebuilds only padded surface tiles touching actual changed native cells, checks deterministic tile-list regeneration and generated artifact hashes, and carries the existing full changed-mip, PBO-entry, and compiled/packed/deployed OPRW readback gates. The new isolated destination is `P:\Mods\@DayZ_Baltic_EV94_FocalBankPreviewV1`. No stage, compile, package, preview copy, or mission creation was run while preparing these sources.

The composition report is `global-operator-prototype/real-sector-preflight/focus-unit/composition-run-01/review.json`; the supplement is `.../focus-unit/consumer-run-01/acceptance-supplement.json`. The gate rehashes their source pins (48 composition inputs and 43 supplement sources, including aliases resolved to the same file), requires exact start/end equality, candidate/base paths and hashes, all-true gates, and the inherited status `OPEN_INHERITED_MAP_DEFECTS`. It does not claim that the wider map is complete. The focal build remains a preview-only path; native runtime and visual acceptance are separate.

After review and explicit operation of the build pipeline, the anchored command sequence is:

```powershell
$python = 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe'
$build = 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\build-focal'
$report = 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\global-operator-prototype\real-sector-preflight\focus-unit\composition-run-01\review.json'
$supplement = 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\global-operator-prototype\real-sector-preflight\focus-unit\consumer-run-01\acceptance-supplement.json'
& $python "$build\stage.py" --composition-report $report --focal-supplement $supplement
& $python "$build\build_surface.py" --composition-report $report --focal-supplement $supplement
& powershell -NoProfile -ExecutionPolicy Bypass -File "$build\compile_native_world.ps1"
& $python "$build\package.py" --composition-report $report --focal-supplement $supplement
& $python "$build\verify_packaged_oprw.py" --composition-report $report --focal-supplement $supplement
& $python "$build\check_changed_mips.py" --composition-report $report --focal-supplement $supplement
& $python "$build\prepare_probe.py" --composition-report $report --focal-supplement $supplement
```

The native collector is intentionally dynamic: it binds to the later server-run provenance instead of reusing EV93's historical run ID. Offline source/test checks do not stage a world, build textures, call AddonBuilder/FileBank, deploy a PBO, create a mission, or start DayZ.
