param(
    [Parameter(Mandatory=$true)][string]$PackageRoot,
    [Parameter(Mandatory=$true)][string]$Python,
    [ValidatePattern('^[a-z0-9_]+$')][string]$BuildTag='regional_foundation_v1'
)
$ErrorActionPreference='Stop'
$project='P:\DayZ_Baltic_12km_dev'
$package=(Resolve-Path -LiteralPath $PackageRoot).Path
$inputSource=Join-Path $package 'source\BalticTrialWorld'
$receipt=Get-Content -Raw -LiteralPath (Join-Path $package 'stage-receipt.json') | ConvertFrom-Json
if($receipt.status -ne 'DIAGNOSTIC_ONLY_FIRST_EXPORT_STALE_NAV') {
    throw 'A verified foundation stage is required; no build started'
}
$expectedAsc='335554a6ea06f8546eeac5444aec7597eaf45df18be0c69b0baab48a573947b2'
$expectedWater='f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3'
$expectedNm='eb0f131e5fc0f80d81c60b1f332d8ecfa6396cab9e09ffd36cd1c8504885c496'
if($receipt.precision_contract -notin @('strict','native-v9-micrometre')) {
    throw 'Missing or unknown native precision contract'
}
if(@($receipt.native_exports).Count -ne 1){throw 'Exactly one diagnostic native gate required'}
foreach($gate in $receipt.native_exports) {
    if($gate.status -ne 'PASS_NATIVE_EXPORT' -or $gate.terrain_only -ne $false -or $gate.asc_sha256 -ne $expectedAsc) {
        throw 'Wrong native verification scope'
    }
    if($gate.precision_contract -ne $receipt.precision_contract) {
        throw 'Mixed native precision contracts'
    }
    if((Get-FileHash -LiteralPath $gate.wrp -Algorithm SHA256).Hash.ToLowerInvariant() -ne $gate.wrp_sha256) {
        throw 'Native export changed since staging'
    }
}
$sourceItems=@(Get-ChildItem -LiteralPath $inputSource -Recurse -Force)
if(@($sourceItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count) {
    throw 'Source reparse point rejected'
}
$expectedFiles=@($receipt.source_files.PSObject.Properties)
if(@($sourceItems | Where-Object { !$_.PSIsContainer }).Count -ne $expectedFiles.Count) {
    throw 'Staged file count changed'
}
foreach($entry in $expectedFiles) {
    $file=Join-Path $inputSource $entry.Name
    if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) {
        throw "Staged content changed: $($entry.Name)"
    }
}
if($receipt.water_pbo_sha256 -ne $expectedWater -or $receipt.bootstrap_navmesh_sha256 -ne $expectedNm) {
    throw 'Wrong dependency pins'
}
$waterPbo=Join-Path $package 'water-addon\baltic_water.pbo'
if((Get-FileHash -LiteralPath $waterPbo -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedWater) {
    throw 'Water addon changed'
}
$root=Join-Path $project ('build-isolated\'+$BuildTag)
$source=Join-Path $root 'dayz_baltic_12km_dev\tb\narva_trial'
$temp=Join-Path $project ('build-temp\'+$BuildTag)
$output=Join-Path $project ('build-output\'+$BuildTag)
$destination=Join-Path $output 'Addons'
$compiled=Join-Path $temp 'dayz_baltic_12km_dev\tb\narva_trial'
$waterSource=Join-Path $project 'build-temp\regional_water_assets_v2\baltic_water'
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
$include=Join-Path $package 'tools\include.lst'
foreach($required in @($Python,$builder,$include,$waterSource,'P:\DZ','P:\bin','P:\core')) {
    if(!(Test-Path -LiteralPath $required)){throw "Missing dependency: $required"}
}
foreach($fresh in @($root,$temp,$output)) {
    if(Test-Path -LiteralPath $fresh){throw "Fresh build path required: $fresh"}
}
New-Item -ItemType Directory -Path $source,$temp,$destination | Out-Null
Copy-Item -Path (Join-Path $inputSource '*') -Destination $source -Recurse
# Preserve the accepted SAT1M sources. Do not regenerate layers or complete
# materials with a helper intended for older palettes.
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $root $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
New-Item -ItemType Junction -Path (Join-Path $root 'baltic_water') -Target $waterSource | Out-Null
$log=Join-Path $output 'addonbuilder.log'
$previousErrorAction=$ErrorActionPreference
try {
    $ErrorActionPreference='Continue'
    & $builder $source $destination '-prefix=dayz_baltic_12km_dev\tb\narva_trial' "-project=$root" "-temp=$temp" "-include=$include" '-binarizeFullLogs' > $log 2>&1
    $builderExit=$LASTEXITCODE
} finally {$ErrorActionPreference=$previousErrorAction}
$pbo=Join-Path $destination 'narva_trial.pbo'
if($builderExit -ne 0 -or !(Test-Path -LiteralPath $pbo) -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful') {
    throw 'AddonBuilder did not prove success; retain and inspect its log'
}
& $Python (Join-Path $project 'tools\playtest\verify_pbo.py') --pbo $pbo --compiled $compiled --expected-materials 4775 --expected-textures 2048 --out (Join-Path $output 'pbo-verification.json')
if($LASTEXITCODE -ne 0){throw 'Actual packed world failed byte-parity validation'}
if((Get-FileHash -LiteralPath (Join-Path $compiled 'navmesh\baltic_trial.nm') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedNm) {
    throw 'Bootstrap NM changed during build'
}
Copy-Item -LiteralPath $waterPbo -Destination (Join-Path $destination 'baltic_water.pbo')
if((Get-FileHash -LiteralPath (Join-Path $destination 'baltic_water.pbo') -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedWater) {
    throw 'Copied water addon changed'
}
[ordered]@{
    status='DIAGNOSTIC_ONLY_COMPILED_FIRST_EXPORT_STALE_NAV'
    source_receipt_sha256=(Get-FileHash -LiteralPath (Join-Path $package 'stage-receipt.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    world_pbo_sha256=(Get-FileHash -LiteralPath $pbo -Algorithm SHA256).Hash.ToLowerInvariant()
    water_pbo_sha256=$expectedWater
    bootstrap_navmesh_sha256=$expectedNm
    limits=@('Diagnostic only: native reopen and fresh NM remain unverified; no release acceptance.')
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $output 'build-receipt.json') -Encoding UTF8
Write-Output 'Diagnostic first-export content compiled. Native reopen and navigation remain pending. No deployment performed.'
