param()
$ErrorActionPreference='Stop'
$w='C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290'
$b='E:\DayZ-Baltic-Build\v30-smoothing-pilot-20261007'
$python='C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe'
$terrain=Join-Path $b 'dry-18-corrected\terrain_dry.npz'
$surface=Join-Path $b 'surface-dry-18'
$package=Join-Path $b 'package-dry-18'
$hash=(Get-FileHash -LiteralPath $terrain -Algorithm SHA256).Hash.ToLowerInvariant()
if($hash -ne '164ad4ffbe4177c7615d18e95d12920d4d332612e596377963a54e0281fc608d'){throw 'Terrain changed'}
if((Test-Path -LiteralPath $surface) -or (Test-Path -LiteralPath $package)){throw 'Fresh outputs required'}
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
Write-Output 'BUILD: surface of dry-only preview'
& $python (Join-Path $w 'tools\terrain\build_surface_v30.py') $terrain $surface --workers 4 --bed-tone depth-all --bed-surface gravel --shore-ring flowing --landcover smooth --landcover-sigma 1.0 *> (Join-Path $b 'surface-dry-18.log')
if($LASTEXITCODE -ne 0){throw 'Surface build failed'}
Write-Output 'BUILD: package, retaining V12 water'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $w 'tools\terrain\build_v30_package.ps1') -Build $package -Terrain $terrain -Pieces 'E:\DayZ-Baltic-Build\v30-v11\24\water' -Layers $surface -OutsideSynth *> (Join-Path $b 'package-dry-18.log')
if($LASTEXITCODE -ne 0){throw 'Package build failed'}
Write-Output 'BUILD COMPLETE: dry-only preview; runtime pending'
