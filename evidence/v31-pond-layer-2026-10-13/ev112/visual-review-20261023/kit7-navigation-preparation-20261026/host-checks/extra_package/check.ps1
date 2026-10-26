$ErrorActionPreference='Stop'
$h=Get-Content -LiteralPath 'E:/DayZ-Baltic-Build/shape-repair-20261025/nav-kit7-preparation-20261026/host-check-tests/extra_package/host-identity.json' -Raw|ConvertFrom-Json
$i=Get-Content -LiteralPath 'E:/DayZ-Baltic-Build/shape-repair-20261025/nav-kit7-preparation-20261026/host-check-tests/extra_package/launch-inputs.json' -Raw|ConvertFrom-Json
if(-not $h.navmesh_data_server -or $h.executable_file_sha256 -ne 'a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'){throw 'Wrong engine identity/mode'}
if(@($h.package_hashes.PSObject.Properties).Count -ne 4){throw 'Unexpected package set'}
$hh=@{};foreach($item in $h.package_hashes.PSObject.Properties){$key=[IO.Path]::GetFullPath($item.Name).ToLowerInvariant();if($hh.ContainsKey($key)){throw 'Duplicate host package path'};$hh[$key]=$item.Value}
foreach($v in $i.packages.PSObject.Properties){if($hh[[IO.Path]::GetFullPath($v.Name).ToLowerInvariant()] -ne $v.Value){throw 'Loaded stack mismatch'}}