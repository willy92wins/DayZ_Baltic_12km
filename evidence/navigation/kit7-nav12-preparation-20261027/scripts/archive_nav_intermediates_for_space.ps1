$ErrorActionPreference='Stop'
$modsDiskRoot=[IO.Path]::GetFullPath('C:/Program Files (x86)/Steam/steamapps/common/DayZ/!Workshop')
$archiveRoot=[IO.Path]::GetFullPath('E:/DayZ-Baltic-Build/shape-repair-20261025/archived-mods-nav12-space-20261027')
if (Test-Path -LiteralPath $archiveRoot) { throw 'Fresh archive required' }
if (-not $archiveRoot.StartsWith('E:\DayZ-Baltic-Build\shape-repair-20261025\')) { throw 'Archive escaped task root' }
$names=@('@DayZ_Baltic_EV112_Kit7Nav8Input','@DayZ_Baltic_EV112_Kit7NavV9')
$worldHashes=@{
 '@DayZ_Baltic_EV112_Kit7Nav8Input'='9fbc7608dc407b8b90c7809071aa01f4c27082e6943b293d58d09cb4fd451b49'
 '@DayZ_Baltic_EV112_Kit7NavV9'='a2919a80ae6da6fc90e75b0ac55d1e9dd4ba4a39f6700b9fec237c7e7683b16c'
}
$files=@('narva_trial.pbo','baltic_stream_pilot.pbo','baltic_water_v30.pbo')
$records=@()
foreach ($name in $names) {
 $source=[IO.Path]::GetFullPath((Join-Path $modsDiskRoot $name))
 $destination=[IO.Path]::GetFullPath((Join-Path $archiveRoot $name))
 if ([IO.Path]::GetDirectoryName($source) -ne $modsDiskRoot -or [IO.Path]::GetDirectoryName($destination) -ne $archiveRoot) { throw 'Archive path mismatch' }
 $items=@(Get-ChildItem -LiteralPath $source -Recurse -Force)
 if ((Get-Item -LiteralPath $source).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Source is a link' }
 if (@($items | Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count) { throw 'Linked archive member' }
 $actual=@($items | Where-Object {-not $_.PSIsContainer})
 if ($actual.Count -ne 3 -or @($actual | Where-Object {$_.DirectoryName -ne (Join-Path $source 'Addons') -or $_.Name -notin $files}).Count) { throw 'Unexpected source inventory' }
 foreach ($file in $files) {
  $p=Join-Path (Join-Path $source 'Addons') $file
  $expected=switch ($file) {'narva_trial.pbo' {$worldHashes[$name]} 'baltic_stream_pilot.pbo' {'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6'} 'baltic_water_v30.pbo' {'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'}}
  if ((Get-FileHash -LiteralPath $p).Hash.ToLowerInvariant() -ne $expected) { throw 'Source no longer matches our intermediate' }
  $records+=[pscustomobject]@{source=$p;destination=(Join-Path (Join-Path $destination 'Addons') $file);sha256=$expected;bytes=(Get-Item -LiteralPath $p).Length}
 }
}
New-Item -ItemType Directory -Path $archiveRoot | Out-Null
[IO.File]::WriteAllText((Join-Path $archiveRoot 'archive-plan.json'),($records|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
$partial=Join-Path $modsDiskRoot '@DayZ_Baltic_EV112_Kit7Nav12Input/Addons/narva_trial.pbo'
$complete='E:/DayZ-Baltic-Build/shape-repair-20261025/package-kit7-nav12-input-20261027/Addons/narva_trial.pbo'
if ([IO.Path]::GetFullPath($partial) -ne ($modsDiskRoot+'\@DayZ_Baltic_EV112_Kit7Nav12Input\Addons\narva_trial.pbo')) { throw 'Partial path mismatch' }
if ((Get-FileHash -LiteralPath $complete).Hash.ToLowerInvariant() -ne 'ed1acb1d993a705996edad1bc3008f14e0b904483ad207d5b903a4d2aee35287') { throw 'Complete source changed' }
$partialItem=Get-Item -LiteralPath $partial
if ($partialItem.Length -ne 804257792 -or $partialItem.CreationTimeUtc.ToString('o') -ne '2026-10-27T06:55:42.4802772Z') { throw 'Partial copy changed; preserve it' }
[IO.File]::WriteAllText((Join-Path $archiveRoot 'partial-copy.json'),([pscustomobject]@{source=$complete;complete_sha256='ed1acb1d993a705996edad1bc3008f14e0b904483ad207d5b903a4d2aee35287';partial=$partial;partial_bytes=$partialItem.Length;reason='Own deployment copy interrupted by ENOSPC'}|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
Remove-Item -LiteralPath $partial
foreach ($name in $names) {
 $source=[IO.Path]::GetFullPath((Join-Path $modsDiskRoot $name))
 $destination=[IO.Path]::GetFullPath((Join-Path $archiveRoot $name))
 if ([IO.Path]::GetDirectoryName($source) -ne $modsDiskRoot -or [IO.Path]::GetDirectoryName($destination) -ne $archiveRoot) { throw 'Archive path changed' }
 Copy-Item -LiteralPath $source -Destination $destination -Recurse
 $owned=@($records | Where-Object {$_.source.StartsWith($source+'\')})
 foreach ($record in $owned) {
  if ((Get-FileHash -LiteralPath $record.destination).Hash.ToLowerInvariant() -ne $record.sha256 -or (Get-Item -LiteralPath $record.destination).Length -ne $record.bytes) { throw 'Archive verification failed; preserve originals' }
 }
 foreach ($record in $owned) {
  if ((Get-FileHash -LiteralPath $record.source).Hash.ToLowerInvariant() -ne $record.sha256) { throw 'Original changed before removal; preserve it' }
  Remove-Item -LiteralPath $record.source
 }
 foreach ($empty in @((Join-Path $source 'Addons'),$source)) {
  if (@(Get-ChildItem -LiteralPath $empty -Force).Count -ne 0) { throw 'Unexpected new file; preserve directory' }
  Remove-Item -LiteralPath $empty
 }
}
$receipt=[pscustomobject]@{status='ARCHIVED_VERIFIED_OWN_INTERMEDIATES';files=$records.Count;bytes_archived=($records|Measure-Object bytes -Sum).Sum;partial_bytes_removed=$partialItem.Length;c_free_bytes=(Get-PSDrive C).Free;restore='Copy the named archived mod directory back to P:/Mods only when needed; verify every file against archive-plan.json before use.'}
[IO.File]::WriteAllText((Join-Path $archiveRoot 'archive-complete.json'),($receipt|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
$receipt|ConvertTo-Json
