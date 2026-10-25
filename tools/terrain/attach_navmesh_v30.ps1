param(
    [Parameter(Mandatory=$true)][string]$Build,
    [Parameter(Mandatory=$true)][string]$Navmesh,
    [Parameter(Mandatory=$true)][string]$Out
)
# Repack the world of an existing V30 build (tools/terrain/build_v30_package.ps1) with a new navmesh. The staged world
# source is copied to <Out>\root (the build itself is not touched), its navmesh\baltic_trial.nm is replaced, fresh
# junctions point to P:\DZ, P:\bin, P:\core and to the build's binarized water models, and AddonBuilder packs the
# world again. The water PBO is copied unchanged. Nothing is deployed.
$ErrorActionPreference='Stop'
$repo=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$include=Join-Path $repo 'packages\baltic-road-v29\tools\include.lst'
$oldSource=Join-Path $Build 'world\root\dayz_baltic_12km_dev\tb\narva_trial'
$water=(Get-Item -LiteralPath (Join-Path $Build 'world\root\baltic_water_v30')).Target
if($water -is [array]){$water=$water[0]}
foreach($required in @($builder,$include,$Navmesh,$oldSource,$water,(Join-Path $Build 'out\Addons\baltic_water_v30.pbo'))) {
    if(!(Test-Path -LiteralPath $required)){throw "Missing: $required"}
}
if(Test-Path -LiteralPath $Out){throw "Fresh output folder required: $Out"}
$root=Join-Path $Out 'root'
$source=Join-Path $root 'dayz_baltic_12km_dev\tb\narva_trial'
$addons=Join-Path $Out 'Addons'
New-Item -ItemType Directory -Path $source,$addons | Out-Null
Copy-Item -Path (Join-Path $oldSource '*') -Destination $source -Recurse
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $root $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
New-Item -ItemType Junction -Path (Join-Path $root 'baltic_water_v30') -Target $water | Out-Null
$nm=Join-Path $source 'navmesh\baltic_trial.nm'
$old=(Get-FileHash -LiteralPath $nm -Algorithm SHA256).Hash.ToLowerInvariant()
Copy-Item -LiteralPath $Navmesh -Destination $nm -Force
$new=(Get-FileHash -LiteralPath $nm -Algorithm SHA256).Hash.ToLowerInvariant()
if($new -ne (Get-FileHash -LiteralPath $Navmesh -Algorithm SHA256).Hash.ToLowerInvariant()){throw 'Navmesh copy mismatch'}
$log=Join-Path $Out 'world-addonbuilder.log'
$previous=$ErrorActionPreference
try {
    $ErrorActionPreference='Continue'
    & $builder $source $addons '-prefix=dayz_baltic_12km_dev\tb\narva_trial' "-project=$root" "-temp=$(Join-Path $Out 'temp')" "-include=$include" '-binarizeFullLogs' > $log 2>&1
    $code=$LASTEXITCODE
} finally {$ErrorActionPreference=$previous}
if($code -ne 0 -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful'){throw "AddonBuilder failed (exit $code); see $log"}
Copy-Item -LiteralPath (Join-Path $Build 'out\Addons\baltic_water_v30.pbo') -Destination $addons
[ordered]@{
    status='WORLD_REPACKED_WITH_NAVMESH'
    previous_navmesh_sha256=$old
    navmesh_sha256=$new
    navmesh_bytes=(Get-Item -LiteralPath $Navmesh).Length
    narva_trial_pbo_sha256=(Get-FileHash -LiteralPath (Join-Path $addons 'narva_trial.pbo') -Algorithm SHA256).Hash.ToLowerInvariant()
    baltic_water_v30_pbo_sha256=(Get-FileHash -LiteralPath (Join-Path $addons 'baltic_water_v30.pbo') -Algorithm SHA256).Hash.ToLowerInvariant()
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Out 'navmesh-receipt.json') -Encoding UTF8
Write-Output "Repacked with navmesh $new in $addons (not deployed)"
