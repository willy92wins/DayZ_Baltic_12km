param(
    [Parameter(Mandatory=$true)][string]$Water
)
# Pack a water folder written by tools/water/build_water_pieces_v30.py (source\baltic_water_v30 and pieces.json) into
# baltic_water_v30.pbo with AddonBuilder, binarizing the pieces into temp\, exactly as step 1 of
# tools/terrain/build_v30_package.ps1 does; tools/water/deduplicate_water_v30.py reads that PBO and the binarized
# models. The PBO is written to <Water>\baltic_water_v30.pbo; nothing is deployed.
$ErrorActionPreference='Stop'
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
foreach($required in @($builder,$Water,'P:\DZ','P:\bin','P:\core')) {
    if(!(Test-Path -LiteralPath $required)){throw "Missing dependency: $required"}
}
$wroot=Join-Path $Water 'source'
if(!(Test-Path -LiteralPath (Join-Path $wroot 'baltic_water_v30'))){throw "No water source in $Water"}
if(Test-Path -LiteralPath (Join-Path $Water 'baltic_water_v30.pbo')){throw "Already packed: $Water"}
$out=Join-Path $Water 'out'
New-Item -ItemType Directory -Path $out | Out-Null
foreach($part in @('DZ','bin','core')) {
    New-Item -ItemType Junction -Path (Join-Path $wroot $part) -Target (Join-Path 'P:\' $part) | Out-Null
}
$log=Join-Path $Water 'addonbuilder.log'
$previous=$ErrorActionPreference
try {
    $ErrorActionPreference='Continue'
    & $builder (Join-Path $wroot 'baltic_water_v30') $out '-prefix=baltic_water_v30' "-project=$wroot" "-temp=$(Join-Path $Water 'temp')" '-binarizeFullLogs' > $log 2>&1
    $code=$LASTEXITCODE
} finally {$ErrorActionPreference=$previous}
$text=Get-Content -Raw -LiteralPath $log
if($code -ne 0 -or $text -notmatch 'Build Successful'){throw "AddonBuilder failed (exit $code); see $log"}
Copy-Item -LiteralPath (Join-Path $out 'baltic_water_v30.pbo') -Destination $Water
Write-Output "Packed: $(Join-Path $Water 'baltic_water_v30.pbo')"
