$ErrorActionPreference='Stop'
$buildRoot='E:\DayZ-Baltic-Build\v30-navigation-contract-20261008'
$projectRoot=Join-Path $buildRoot 'world\root'
$source=Join-Path $projectRoot 'dayz_baltic_12km_dev\tb\narva_trial'
$out=Join-Path $buildRoot 'world\out'
New-Item -ItemType Directory -Path $out | Out-Null
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $projectRoot $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
New-Item -ItemType Junction -Path (Join-Path $projectRoot 'baltic_water_v30') -Target 'E:\DayZ-Baltic-Build\v30-continuation-20261008\junction-fix-r2\water\temp\baltic_water_v30' | Out-Null
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$include='C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\packages\baltic-road-v29\tools\include.lst'
$log=Join-Path $buildRoot 'world-addonbuilder.log'
$ErrorActionPreference='Continue'
& $builder $source $out '-prefix=dayz_baltic_12km_dev\tb\narva_trial' "-project=$projectRoot" "-temp=$(Join-Path $buildRoot 'world\temp')" '-binarizeFullLogs' "-include=$include" > $log 2>&1
$result=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($result -ne 0 -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful'){throw "Build failed: $log"}
Write-Output 'Built world with corrected isolated high beds.'
