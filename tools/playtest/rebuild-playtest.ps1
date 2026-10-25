param(
    [Parameter(Mandatory=$true)][string]$PackageRoot,
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$OutputRoot,
    [ValidatePattern('^[a-z0-9_]+$')][string]$BuildTag=('trial_'+(Get-Date -Format 'yyyyMMdd_HHmmss')),
    [ValidateRange(1,65535)][int]$ExpectedMaterials=367,
    [ValidateRange(1,65535)][int]$ExpectedTextures=50,
    [ValidateSet('none','pond_50x50','lake_50x50')][string]$ExpectedWaterObject='none'
)
$ErrorActionPreference='Stop'
$package=(Resolve-Path -LiteralPath $PackageRoot).Path
$root=Join-Path 'P:\DayZ_Baltic_12km_dev\build-isolated' $BuildTag
$source=Join-Path $root 'dayz_baltic_12km_dev\tb\narva_trial'
$temp=Join-Path 'P:\DayZ_Baltic_12km_dev\build-temp' $BuildTag
$destination=Join-Path ([System.IO.Path]::GetFullPath($OutputRoot)) ($BuildTag+'\Addons')
$inputSource=Join-Path $package 'source\BalticTrialWorld'
foreach($newPath in @($root,$temp,$destination)) {
    if(Test-Path -LiteralPath $newPath){throw "Fresh build path required: $newPath"}
}
foreach($required in @($Python,(Join-Path $inputSource 'baltic_trial.wrp'),(Join-Path $inputSource 'config.cpp'))) {
    if(!(Test-Path -LiteralPath $required)){throw "Missing $required"}
}
New-Item -ItemType Directory -Path $source,$destination -Force | Out-Null
Copy-Item -Path (Join-Path $inputSource '*') -Destination $source -Recurse
# Terrain Builder emits empty detail bindings in this four-material palette.
# Complete them in the isolated source before binarizing; originals are backed up.
$materialTool=Join-Path $PSScriptRoot 'complete_terrain_materials.py'
$buildOutput=Split-Path $destination
& $Python $materialTool --layers (Join-Path $source 'data\layers') --apply --backup (Join-Path $buildOutput 'source-material-backup') --out (Join-Path $buildOutput 'source-materials.json')
if($LASTEXITCODE -ne 0){throw 'Terrain detail material validation/completion failed'}
foreach($part in @('DZ','bin','core')) {
    $target=Join-Path 'P:\' $part
    if(!(Test-Path -LiteralPath $target)){throw "Missing vanilla dependency $part"}
    New-Item -ItemType Junction -Path (Join-Path $root $part) -Target $target | Out-Null
}
$log=Join-Path (Split-Path $destination) 'addonbuilder.log'
$include=Join-Path $package 'tools\include.lst'
# Windows PowerShell 5 promotes harmless native stderr to NativeCommandError
# under Stop. Judge the native exit code and complete build log instead.
$previousErrorAction=$ErrorActionPreference
try {
    $ErrorActionPreference='Continue'
    & 'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe' $source $destination '-prefix=dayz_baltic_12km_dev\tb\narva_trial' "-project=$root" "-temp=$temp" "-include=$include" -binarizeFullLogs -binarizeAllTextures > $log 2>&1
    $builderExit=$LASTEXITCODE
} finally {
    $ErrorActionPreference=$previousErrorAction
}
$logText=Get-Content -Raw -LiteralPath $log
$pbo=Join-Path $destination 'narva_trial.pbo'
if($builderExit -ne 0 -or $logText -notmatch 'Build Successful' -or !(Test-Path -LiteralPath $pbo)) {
    throw 'AddonBuilder did not prove success; inspect the complete log'
}
& $Python (Join-Path $PSScriptRoot 'verify_pbo.py') --pbo $pbo --compiled (Join-Path $temp 'dayz_baltic_12km_dev\tb\narva_trial') --expected-materials $ExpectedMaterials --expected-textures $ExpectedTextures --expected-water-object $ExpectedWaterObject --out (Join-Path (Split-Path $destination) 'pbo-verification.json')
if($LASTEXITCODE -ne 0){throw 'Actual PBO verification failed'}
Write-Output 'Build and packed content verified. No deployment or game launch performed.'
