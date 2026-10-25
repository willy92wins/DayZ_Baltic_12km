$ErrorActionPreference='Stop'
$buildRoot='E:\DayZ-Baltic-Build\v30-global-water-risk-20261009\halo-fix-v2'
$source=Join-Path $buildRoot 'compile\source\baltic_water_v30'
$out=Join-Path $buildRoot 'compile\out'
if(Test-Path -LiteralPath $out){throw 'Fresh output required'}
New-Item -ItemType Directory -Path $out | Out-Null
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$include='C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\packages\baltic-road-v29\tools\include.lst'
$projectRoot=Join-Path $buildRoot 'compile\source'
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $projectRoot $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
$log=Join-Path $buildRoot 'water-addonbuilder.log'
$ErrorActionPreference='Continue'
& $builder $source $out '-prefix=baltic_water_v30' "-project=$projectRoot" "-temp=$(Join-Path $buildRoot 'compile\temp')" '-binarizeFullLogs' "-include=$include" > $log 2>&1
$result=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($result -ne 0 -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful'){throw "Build failed: $log"}
Write-Output 'Compiled the isolated water halo correction.'
