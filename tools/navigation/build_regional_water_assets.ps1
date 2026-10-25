param([ValidateSet('v1','v2')][string]$Version='v2')
$ErrorActionPreference='Stop'
$project='P:\DayZ_Baltic_12km_dev'
$key="regional_water_assets_$Version"
$root=Join-Path $project "build-isolated\$key"
$source=Join-Path $root 'baltic_water'
$out=Join-Path $project "build-output\$key"
$temp=Join-Path $project "build-temp\$key"
foreach($path in @($root,$out,$temp)){if(Test-Path -LiteralPath $path){throw "Build exists: $path"}}
New-Item -ItemType Directory -Path $source,$out,$temp | Out-Null
Copy-Item -Path "$project\tests\regional_foundation_water_assets_$Version\source\baltic_water\*" -Destination $source
foreach($part in @('DZ','bin','core')){New-Item -ItemType Junction -Path (Join-Path $root $part) -Target (Join-Path 'P:\' $part) | Out-Null}
$log=Join-Path $out 'addonbuilder.log'
$previousErrorAction=$ErrorActionPreference
try {
    $ErrorActionPreference='Continue'
    & 'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe' $source $out '-prefix=baltic_water' "-project=$root" "-temp=$temp" '-binarizeFullLogs' > $log 2>&1
    $code=$LASTEXITCODE
} finally {$ErrorActionPreference=$previousErrorAction}
Get-Content -LiteralPath $log -Tail 8
if($code -ne 0){throw "AddonBuilder failed: $code"}
