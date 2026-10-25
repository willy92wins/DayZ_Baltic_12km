$ErrorActionPreference='Stop'
$project='P:\DayZ_Baltic_12km_dev'
$root=Join-Path $project 'build-isolated\static_shape_v2'
$source=Join-Path $root 'dayz_baltic_12km_dev\tb\narva_trial'
$out=Join-Path $project 'build-output\static_shape_v2'
$temp=Join-Path $project 'build-temp\static_shape_v2'
foreach($path in @($root,$out,$temp)){if(Test-Path -LiteralPath $path){throw "Build exists: $path"}}
New-Item -ItemType Directory -Path $source,$out,$temp | Out-Null
Copy-Item -Path "$project\packages\baltic-static-shape-probe-v2\source\BalticTrialWorld\*" -Destination $source -Recurse
# Copy only the compiled world subtree, never the junction-bearing project root.
$cached=Join-Path $temp 'dayz_baltic_12km_dev\tb'
New-Item -ItemType Directory -Path $cached | Out-Null
Copy-Item -LiteralPath "$project\build-temp\static_shape_v1\dayz_baltic_12km_dev\tb\narva_trial" -Destination $cached -Recurse
foreach($part in @('DZ','bin','core')){New-Item -ItemType Junction -Path (Join-Path $root $part) -Target (Join-Path 'P:\' $part) | Out-Null}
New-Item -ItemType Junction -Path (Join-Path $root 'baltic_water_shape_v3') -Target "$project\build-temp\water_shape_v3\baltic_water_shape_v3" | Out-Null
$log=Join-Path $out 'addonbuilder.log'
$previousErrorAction=$ErrorActionPreference
try {
    $ErrorActionPreference='Continue'
    & 'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe' $source $out '-prefix=dayz_baltic_12km_dev\tb\narva_trial' "-project=$root" "-temp=$temp" "-include=$project\packages\baltic-static-shape-probe-v2\tools\include.lst" '-binarizeFullLogs' > $log 2>&1
    $code=$LASTEXITCODE
} finally {$ErrorActionPreference=$previousErrorAction}
Get-Content -LiteralPath $log -Tail 6
if($code -ne 0){throw "AddonBuilder failed: $code"}
