$ErrorActionPreference='Stop'
$buildRoot='E:\DayZ-Baltic-Build\v31-pond-layer-20261013\ev109r\stage'
$projectRoot=Join-Path $buildRoot 'root'
$source=Join-Path $projectRoot 'dayz_baltic_12km_dev\tb\narva_trial'
$out=Join-Path $buildRoot 'out'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out | Out-Null
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $projectRoot $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
New-Item -ItemType Junction -Path (Join-Path $projectRoot 'baltic_water_v30') -Target 'E:\DayZ-Baltic-Build\v31-pond-layer-20261013\ev109w\water\temp\baltic_water_v30' | Out-Null
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$include='C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\packages\baltic-road-v29\tools\include.lst'
$log=Join-Path $buildRoot 'world-addonbuilder.log'
$ErrorActionPreference='Continue'
& $builder $source $out '-prefix=dayz_baltic_12km_dev\tb\narva_trial' "-project=$projectRoot" "-temp=$(Join-Path $buildRoot 'temp')" '-binarizeFullLogs' "-include=$include" > $log 2>&1
$result=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($result -ne 0 -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful'){throw "Build failed: $log"}
Write-Output 'Built EV109R render keys world.'
