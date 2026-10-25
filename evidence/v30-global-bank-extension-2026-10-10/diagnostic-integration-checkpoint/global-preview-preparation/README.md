# REC global-dry preview pipeline — preparation only

This isolated copy of the reviewed EV95 build path is pinned to the frozen REC run-01 candidate and the V2 independent consumer source. It requires an explicit consumer-report path and SHA256 and accepts only `PASS_GLOBAL_DRY_ROLLBACK_CANDIDATE` with the exact eight V2 gates all true, the pinned REC receipt/candidate identities, and equal start/end source pins. The current V2 attempt is an admission error, so this pipeline is not ready to stage.

Before staging, the copied stage checks the full candidate NPZ schema and all non-height arrays byte-for-byte against both EV95 and EV82 B. It compares the V2-reported changed count against EV95, then independently derives changed vertices against EV82 B. The surface step derives a fresh padded tile list from those final REC-vs-B heights; it does not reuse EV95's 540 tiles or its PAA outputs. EV82 P/F, WRP objects/materials, world PBO and water PBO remain pinned. Surface generation and mips are separate gates from the independent global water/face/object consumer.

The build scripts are prepared but have not staged, generated textures, compiled, packed, copied to the preview mod, created a mission, or run the game. All outputs and the deployment target are new and fail if they already exist. This is not a promotion or native/visual acceptance.

## Future command sequence after a fresh V2 PASS and source review

Run from PowerShell with the pinned GIS Python and a newly produced V2 report. Compute the report SHA from the exact report file and reuse both values at every step:

```powershell
$B = 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\build-global-dry-preview-v1'
$Py = 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe'
$Report = 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\global-operator-prototype\global-dry-rollback\postsolve-consumer\instrumented-v2\runs\<fresh-pass>\report.json'
$ReportSha = (Get-FileHash -LiteralPath $Report -Algorithm SHA256).Hash.ToLower()
& $Py (Join-Path $B 'stage.py') --consumer-report $Report --consumer-sha256 $ReportSha
& $Py (Join-Path $B 'build_surface.py') --consumer-report $Report --consumer-sha256 $ReportSha
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $B 'compile_native_world.ps1')
& $Py (Join-Path $B 'package.py') --consumer-report $Report --consumer-sha256 $ReportSha
& $Py (Join-Path $B 'verify_packaged_oprw.py') --consumer-report $Report --consumer-sha256 $ReportSha
& $Py (Join-Path $B 'check_changed_mips.py') --consumer-report $Report --consumer-sha256 $ReportSha
```

The placeholder is deliberately not a runnable report path. Do not run this sequence until the global consumer returns the exact PASS status, the copied sources pass review, and the V2 report SHA is fixed.
