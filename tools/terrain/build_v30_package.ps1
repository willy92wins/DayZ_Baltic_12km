param(
    [Parameter(Mandatory=$true)][string]$Build,
    [Parameter(Mandatory=$true)][string]$Terrain,
    [string]$Python='C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe',
    [string]$Pieces='',
    [string]$WaterSource='',
    [string]$Layers='',
    [switch]$OutsideTerrain,
    [switch]$OutsideSynth
)
# Terrain V30 package without Terrain Builder: V30 water pieces (pond planes) packed as baltic_water_v30, and the
# world derived from the accepted V29 package (tools/terrain/derive_world_v30.py) packed with AddonBuilder.
# -Pieces reuses an existing water build folder (its source and temp); -WaterSource packs a prepared water folder
# (source\baltic_water_v30 and pieces.json, as tools/water/fit_channel_pieces_v30.py writes); -Layers replaces data/layers and the WRP
# material table with a phase-4 surface folder (tools/terrain/build_surface_v30.py); -OutsideTerrain adds Chernarus's
# OutsideTerrain class without terrain synthesis (derive_world_v30.py --outside-terrain); -OutsideSynth adds it with
# the synthesis on, as Chernarus has it (--outside-synth).
# Nothing is deployed here; the output is <Build>\out\Addons.
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$include=Join-Path $repo 'packages\baltic-road-v29\tools\include.lst'
foreach($required in @($Python,$builder,$include,$Terrain,'P:\DZ','P:\bin','P:\core')) {
    if(!(Test-Path -LiteralPath $required)){throw "Missing dependency: $required"}
}
if(Test-Path -LiteralPath $Build){throw "Fresh build folder required: $Build"}
$out=Join-Path $Build 'out\Addons'
New-Item -ItemType Directory -Path $out | Out-Null

function Invoke-Builder($source, $prefix, $project, $temp, $log, $extra) {
    $previous=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        $arguments=@($source, $out, "-prefix=$prefix", "-project=$project", "-temp=$temp", '-binarizeFullLogs') + $extra
        & $builder @arguments > $log 2>&1
        $code=$LASTEXITCODE
    } finally {$ErrorActionPreference=$previous}
    $text=Get-Content -Raw -LiteralPath $log
    if($code -ne 0 -or $text -notmatch 'Build Successful'){throw "AddonBuilder failed for $prefix (exit $code); see $log"}
}

# 1. Water pieces and their PBO.
if($Pieces) {
    $water=$Pieces
} else {
    if($WaterSource) {
        $water=$WaterSource
    } else {
        $water=Join-Path $Build 'water'
        & $Python -X utf8 (Join-Path $repo 'tools\water\build_water_pieces_v30.py') $Terrain $water
        if($LASTEXITCODE -ne 0){throw 'Water pieces failed'}
    }
    $wroot=Join-Path $water 'source'
    foreach($part in @('DZ','bin','core')) {
        New-Item -ItemType Junction -Path (Join-Path $wroot $part) -Target (Join-Path 'P:\' $part) | Out-Null
    }
    Invoke-Builder (Join-Path $wroot 'baltic_water_v30') 'baltic_water_v30' $wroot (Join-Path $water 'temp') (Join-Path $Build 'water-addonbuilder.log') @()
    Copy-Item -LiteralPath (Join-Path $out 'baltic_water_v30.pbo') -Destination $water
}
$binarizedWater=Join-Path $water 'temp\baltic_water_v30'
if(!(Test-Path -LiteralPath $binarizedWater)){throw "Binarized water models not found: $binarizedWater"}
if($Pieces){Copy-Item -LiteralPath (Join-Path $Pieces 'baltic_water_v30.pbo') -Destination $out}

# 2. World source derived from V29, optional phase-4 layers.
$stage=Join-Path $Build 'world\stage\BalticTrialWorld'
$outsideArg=@(); if($OutsideTerrain){$outsideArg+=@('--outside-terrain')}; if($OutsideSynth){$outsideArg+=@('--outside-synth')}
& $Python -X utf8 (Join-Path $repo 'tools\terrain\derive_world_v30.py') $Terrain (Join-Path $water 'pieces.json') $stage @outsideArg
if($LASTEXITCODE -ne 0){throw 'World derivation failed'}
if($Layers) {
    & $Python -X utf8 (Join-Path $repo 'tools\terrain\apply_surface_v30.py') $Layers $stage
    if($LASTEXITCODE -ne 0){throw 'Surface application failed'}
}
$root=Join-Path $Build 'world\root'
$source=Join-Path $root 'dayz_baltic_12km_dev\tb\narva_trial'
New-Item -ItemType Directory -Path $source | Out-Null
Copy-Item -Path (Join-Path $stage '*') -Destination $source -Recurse
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $root $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
New-Item -ItemType Junction -Path (Join-Path $root 'baltic_water_v30') -Target $binarizedWater | Out-Null
Invoke-Builder $source 'dayz_baltic_12km_dev\tb\narva_trial' $root (Join-Path $Build 'world\temp') (Join-Path $Build 'world-addonbuilder.log') @("-include=$include")

$pbos=Get-ChildItem -LiteralPath $out -Filter '*.pbo'
$pbos | ForEach-Object { [ordered]@{name=$_.Name; bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Build 'build-receipt.json') -Encoding UTF8
Write-Output "Built: $($pbos.Name -join ', ') in $out (not deployed)"
