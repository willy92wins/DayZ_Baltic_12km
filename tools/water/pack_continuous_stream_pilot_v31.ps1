param([Parameter(Mandatory=$true)][string]$Pilot)
# Isolated pilot build; no deployment and no process lifecycle operations.
$ErrorActionPreference='Stop'
$pilotPath=(Resolve-Path -LiteralPath $Pilot).Path
$prefix='baltic_stream_pilot'
$sourceRoot=Join-Path $pilotPath 'source'
$source=Join-Path $sourceRoot $prefix
$builder='C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe'
foreach($required in @($builder,$source,'P:\DZ','P:\bin','P:\core')) {
    if(!(Test-Path -LiteralPath $required)){throw "Missing dependency: $required"}
}
$out=Join-Path $pilotPath 'packed'
$temp=Join-Path $pilotPath 'temp'
if((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $temp)){throw 'Fresh build directories required'}
New-Item -ItemType Directory -Path $out | Out-Null
foreach($part in @('DZ','bin','core')) {
    $link=Join-Path $sourceRoot $part
    if(Test-Path -LiteralPath $link){throw "Unexpected existing link: $link"}
    New-Item -ItemType Junction -Path $link -Target (Join-Path 'P:\' $part) | Out-Null
}
$log=Join-Path $pilotPath 'addonbuilder.log'
$ErrorActionPreference='Continue'
& $builder $source $out "-prefix=$prefix" "-project=$sourceRoot" "-temp=$temp" '-binarizeFullLogs' > $log 2>&1
$result=$LASTEXITCODE
$ErrorActionPreference='Stop'
if($result -ne 0 -or (Get-Content -Raw -LiteralPath $log) -notmatch 'Build Successful'){throw "Build failed: $log"}
if(!(Test-Path -LiteralPath (Join-Path $out "$prefix.pbo"))){throw 'Missing packed output'}
Write-Output "Pilot packed for binary verification: $out"
