$ErrorActionPreference='Stop'
# EV112 AE forest / runtime-margin B terrain world compile derived from: compile_world_ev109.ps1 (evidence/v31-pond-layer-2026-10-13/scripts/ev108-ev109/) with the EV110
# stage and water folders. AddonBuilder needs the P: subst; P:\DZ is read-only and only linked by a junction.
$buildRoot='E:\DayZ-Baltic-Build\v31-pond-layer-20261013\ev112-build-20261018\stage-runtime-b'
$projectRoot=Join-Path $buildRoot 'root'
$source=Join-Path $projectRoot 'dayz_baltic_12km_dev\tb\narva_trial'
$out=Join-Path $buildRoot 'out'
foreach($required in @('P:\DZ','P:\bin','P:\core',$source)) {
    if(!(Test-Path -LiteralPath $required)){throw "Missing dependency: $required"}
}
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out | Out-Null
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $projectRoot $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
New-Item -ItemType Junction -Path (Join-Path $projectRoot 'baltic_water_v30') -Target 'E:\DayZ-Baltic-Build\v31-pond-layer-20261013\ev112-build-20261018\water-prepared-fp49ee\temp\baltic_water_v30' | Out-Null
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$include='E:\DayZ-Baltic-Build\v31-pond-layer-20261013\ev112-build-20261018\build-review-ae-provenance\compile-include.lst'
$log=Join-Path $buildRoot 'world-runtime-b-addonbuilder.log'
$ErrorActionPreference='Continue'
& $builder $source $out '-prefix=dayz_baltic_12km_dev\tb\narva_trial' "-project=$projectRoot" "-temp=$(Join-Path $buildRoot 'temp')" '-binarizeFullLogs' "-include=$include" > $log 2>&1
$result=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($result -ne 0 -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful'){throw "Build failed: $log"}
Write-Output 'Built EV112 AE forest / runtime-margin B terrain world.'
