$ErrorActionPreference='Stop'
$isolatedRoot='P:\DayZ_Baltic_12km_dev\build-isolated\trial_v1'
$isolatedSource=Join-Path $isolatedRoot 'dayz_baltic_12km_dev\tb\narva_trial'
$workRoot='C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\baltic-build'
$destination='C:\Users\guill\Documents\Codex\2026-09-29\vamos\outputs\baltic-playtest\Addons'
if(Test-Path -LiteralPath $isolatedRoot){throw 'Isolated root exists; choose a fresh trial, do not clean shared paths'}
New-Item -ItemType Directory -Path $isolatedSource -Force | Out-Null
Copy-Item -Path (Join-Path $workRoot 'stage\BalticTrialWorld\*') -Destination $isolatedSource -Recurse
foreach($vanillaPart in @('DZ','bin','core')){
    $target=Join-Path 'P:\' $vanillaPart
    if(!(Test-Path -LiteralPath $target)){throw "Missing vanilla dependency $vanillaPart"}
    New-Item -ItemType Junction -Path (Join-Path $isolatedRoot $vanillaPart) -Target $target | Out-Null
}
$log=Join-Path $workRoot 'addonbuilder-isolated.log'
& 'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe' $isolatedSource $destination '-prefix=dayz_baltic_12km_dev\tb\narva_trial' "-project=$isolatedRoot" '-temp=P:\DayZ_Baltic_12km_dev\build-temp\trial_isolated_v1' "-include=$workRoot\include.lst" -binarizeFullLogs -binarizeAllTextures > $log 2>&1
$builderExit=$LASTEXITCODE
$text=Get-Content -Raw -LiteralPath $log
Get-Content -Tail 30 -LiteralPath $log
if($builderExit -ne 0 -or $text -notmatch 'Build Successful' -or !(Test-Path -LiteralPath (Join-Path $destination 'narva_trial.pbo'))){throw "Build did not produce a successful PBO; process exit $builderExit is insufficient"}
