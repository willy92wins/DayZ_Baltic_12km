param([Parameter(Mandatory=$true)][string]$Stage,[Parameter(Mandatory=$true)][string]$Pilot)
$ErrorActionPreference='Stop'
$stagePath=(Resolve-Path -LiteralPath $Stage).Path
$pilotPath=(Resolve-Path -LiteralPath $Pilot).Path
$project=Join-Path $stagePath 'root'
$source=Join-Path $project 'dayz_baltic_12km_dev\tb\narva_trial'
$out=Join-Path $stagePath 'out'
$temp=Join-Path $stagePath 'temp'
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$water='E:\DayZ-Baltic-Build\v31-pond-layer-20261013\ev112-build-20261018\water-prepared-fp49ee\temp\baltic_water_v30'
$pilotModels=Join-Path $pilotPath 'temp\baltic_stream_pilot'
$include='C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290\packages\baltic-road-v29\tools\include.lst'
foreach($required in @($source,$builder,$water,$pilotModels,$include,'P:\DZ','P:\bin','P:\core')) {
    if(!(Test-Path -LiteralPath $required)){throw "Missing dependency: $required"}
}
if((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $temp)){throw 'Fresh build directories required'}
New-Item -ItemType Directory -Path $out | Out-Null
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $project $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
New-Item -ItemType Junction -Path (Join-Path $project 'baltic_water_v30') -Target $water | Out-Null
New-Item -ItemType Junction -Path (Join-Path $project 'baltic_stream_pilot') -Target $pilotModels | Out-Null
$log=Join-Path $stagePath 'addonbuilder.log'
$ErrorActionPreference='Continue'
& $builder $source $out '-prefix=dayz_baltic_12km_dev\tb\narva_trial' "-project=$project" "-temp=$temp" '-binarizeFullLogs' "-include=$include" > $log 2>&1
$result=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($result -ne 0 -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful'){throw "Build failed: $log"}
Write-Output "World compiled for readback: $out"
