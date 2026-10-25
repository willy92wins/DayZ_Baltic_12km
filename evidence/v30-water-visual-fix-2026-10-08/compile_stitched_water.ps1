$ErrorActionPreference='Stop'
$buildRoot='E:\DayZ-Baltic-Build\v30-water-visual-fix-20261008\stitched-water'
$source=Join-Path $buildRoot 'compile\source\baltic_water_v30'
$out=Join-Path $buildRoot 'compile\out-v2'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out | Out-Null
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$include='C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\packages\baltic-road-v29\tools\include.lst'
$projectRoot=Join-Path $buildRoot 'compile\source'
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $projectRoot $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
$log=Join-Path $buildRoot 'water-addonbuilder-v2.log'
$ErrorActionPreference='Continue'
& $builder $source $out '-prefix=baltic_water_v30' "-project=$projectRoot" "-temp=$(Join-Path $buildRoot 'compile\temp-v2')" '-binarizeFullLogs' "-include=$include" > $log 2>&1
$result=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($result -ne 0 -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful'){throw "Build failed: $log"}
Write-Output 'Compiled restored flat water models.'
