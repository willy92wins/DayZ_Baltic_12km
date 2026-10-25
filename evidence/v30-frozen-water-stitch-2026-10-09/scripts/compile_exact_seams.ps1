$ErrorActionPreference='Stop'
$buildRoot='E:\DayZ-Baltic-Build\v30-frozen-water-stitch-20261009'
$source=Join-Path $buildRoot 'compile-seams\source\baltic_water_v30'
$out=Join-Path $buildRoot 'compile-seams\out'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out | Out-Null
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$include='C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\packages\baltic-road-v29\tools\include.lst'
$projectRoot=Join-Path $buildRoot 'compile-seams\source'
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $projectRoot $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
$log=Join-Path $buildRoot 'water-seams-addonbuilder.log'
$ErrorActionPreference='Continue'
& $builder $source $out '-prefix=baltic_water_v30' "-project=$projectRoot" "-temp=$(Join-Path $buildRoot 'compile-seams\temp')" '-binarizeFullLogs' "-include=$include" > $log 2>&1
$result=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($result -ne 0 -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful'){throw "Build failed: $log"}
Write-Output 'Compiled isolated global visible water LODs.'
