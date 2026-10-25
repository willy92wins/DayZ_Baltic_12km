param(
    [Parameter(Mandatory=$true)][string]$PackageRoot,
    [Parameter(Mandatory=$true)][string]$Python,
    [ValidatePattern('^[a-z0-9_]+$')][string]$BuildTag='regional_road_v29'
)
$ErrorActionPreference='Stop'
$project='P:\DayZ_Baltic_12km_dev'
$package=(Resolve-Path -LiteralPath $PackageRoot).Path
$inputSource=Join-Path $package 'source\BalticTrialWorld'
$receipt=Get-Content -Raw -LiteralPath (Join-Path $package 'stage-receipt.json') | ConvertFrom-Json
if($receipt.status -ne 'JOINT_ROAD_V29_STAGED_FOR_DATA_SERVER_WITH_STALE_NAVIGATION') { throw 'Verified joint road V29 stage required' }
if($receipt.precision_contract -notin @('native-road-v29-frozen','native-road-v29-canonical-water') -or $receipt.exact_native_persistence -ne $true) { throw 'Wrong precision contract' }
$expectedAsc='ed6cdaa5a1b9100a6f74041e9338f1c21f100a6686f596c73f79f33c4b8662c6'
if($receipt.asc_sha256 -ne $expectedAsc -or (Get-FileHash -LiteralPath $receipt.asc -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expectedAsc) {throw 'ASC changed'}
$expectedProofs=@{
    'independent-consumer.json'='PASS_OFFLINE_EDITABLE_DRY_NETWORK_GEOMETRY'
    'continuous-outline.json'='PASS_OFFLINE_OUTLINE_GEOMETRY'
    'joint-hydrology.json'='PASS_OFFLINE_JOINT_HYDROLOGY_AND_PROTECTED_LAND'
    'landmarks-controls-physical-contract.json'='PASS_OUTLINE_LANDMARKS_AND_CONTROLS'
    'land-controls.json'='PASS_FULL_NETWORK_POSITIVE_AND_NEGATIVES'
    'joint-hydrology-controls.json'='PASS_REAL_JOINT_HYDROLOGY_AND_FOUR_NEGATIVES'
}
if(@($receipt.offline_proofs).Count -ne $expectedProofs.Count){throw 'Six distinct offline proofs required'}
$seen=@{}
foreach($proof in $receipt.offline_proofs) {
    $name=Split-Path -Leaf $proof.path
    if(!$expectedProofs.ContainsKey($name) -or $seen.ContainsKey($name)){throw 'Unexpected or duplicate proof'}
    $seen[$name]=$true
    $expectedPath=Join-Path $project ('tests\regional_road_network_v29\'+$name)
    # P: and the physical work-drive path can name the same file. Compare
    # filesystem identity, not Resolve-Path's drive spelling or content alone.
    & $Python -c 'import os,sys; sys.exit(0 if os.path.samefile(sys.argv[1],sys.argv[2]) else 1)' $proof.path $expectedPath
    if($LASTEXITCODE -ne 0){throw 'Proof path mismatch'}
    if((Get-FileHash -LiteralPath $proof.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $proof.sha256){throw 'Offline proof changed'}
    $gate=Get-Content -LiteralPath $proof.path -Raw | ConvertFrom-Json
    $digest=$gate.candidate_sha256
    if(!$digest){$digest=$gate.asc_sha256}
    if($gate.status -ne $expectedProofs[$name] -or $proof.status -ne $expectedProofs[$name] -or $digest -ne $expectedAsc){throw 'Offline proof scope mismatch'}
    if($name -in @('land-controls.json','joint-hydrology-controls.json')) {
        $requiredCount=if($name -eq 'land-controls.json'){7}else{4}
        if(@($gate.tests).Count -ne $requiredCount -or @($gate.tests | Where-Object {$_.rejected -ne $true}).Count){throw 'Failed offline negative control'}
        if(@($gate.tests.name | Select-Object -Unique).Count -ne $requiredCount){throw 'Duplicate offline negative control'}
        $positiveName=if($name -eq 'land-controls.json'){'independent-consumer.json'}else{'joint-hydrology.json'}
        $positivePath=Join-Path $project ('tests\regional_road_network_v29\'+$positiveName)
        if((Get-FileHash -LiteralPath $positivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $gate.positive_sha256){throw 'Negative controls refer to another positive result'}
    } else {
        if($null -eq $gate.checks -or @($gate.checks.PSObject.Properties).Count -eq 0 -or @($gate.checks.PSObject.Properties | Where-Object {$_.Value -ne $true}).Count){throw 'Failed offline check'}
    }
    if($name -eq 'continuous-outline.json' -and $gate.checks.frozen_v5_runtime_samples -ne $true){throw 'Frozen runtime point preservation required'}
}
$expectedWater='f9a5cdf7461ff09e80a102641289513896011a78b090fdbbd1056f9b985898d3'
$expectedNm='eb0f131e5fc0f80d81c60b1f332d8ecfa6396cab9e09ffd36cd1c8504885c496'
$inputGates=$receipt.native_exports
if($receipt.precision_contract -eq 'native-road-v29-canonical-water') {
    if((Get-FileHash -LiteralPath $receipt.object_restoration -Algorithm SHA256).Hash.ToLowerInvariant() -ne $receipt.object_restoration_sha256) {throw 'Restoration proof changed'}
    & $Python (Join-Path $project 'tools\navigation\canonicalize_road_v29_water_poses.py') --verify-receipt $receipt.object_restoration
    if($LASTEXITCODE -ne 0){throw 'Literal persistence or derived provenance failed'}
    $inputGates=$receipt.build_input_checks
}
if(@($inputGates).Count -ne 2){throw 'Two complete build-input gates required'}
foreach($gate in $inputGates) {
    if($gate.status -ne 'PASS_NATIVE_ROAD_TERRAIN_CONTENT' -or $gate.asc_sha256 -ne $expectedAsc -or @($gate.checks.PSObject.Properties | Where-Object {$_.Value -ne $true}).Count) {throw 'Native proof scope mismatch'}
    if((Get-FileHash -LiteralPath $gate.wrp -Algorithm SHA256).Hash.ToLowerInvariant() -ne $gate.wrp_sha256) {throw 'Native export changed'}
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
    status='COMPILED_FOR_DATA_SERVER_ONLY_STALE_NAVIGATION'
    source_receipt_sha256=(Get-FileHash -LiteralPath (Join-Path $package 'stage-receipt.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    world_pbo_sha256=(Get-FileHash -LiteralPath $pbo -Algorithm SHA256).Hash.ToLowerInvariant()
    water_pbo_sha256=$expectedWater
    bootstrap_navmesh_sha256=$expectedNm
    limits=@('No deployment; fresh navigation generation and regional runtime consumers required.')
} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $output 'build-receipt.json') -Encoding UTF8
Write-Output 'Compiled content verified for the data server. Navigation remains stale. No deployment performed.'
