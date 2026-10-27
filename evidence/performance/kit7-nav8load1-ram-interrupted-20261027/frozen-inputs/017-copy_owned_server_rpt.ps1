param([Parameter(Mandatory=$true)][string]$ExpectedStartUtc,[Parameter(Mandatory=$true)][string]$ExpectedMission,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$ExpectedMission=[IO.Path]::GetFullPath($ExpectedMission).Replace('/','\')
$start=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
$matches=@()
foreach($file in (Get-ChildItem -LiteralPath 'C:/temp/DayZ_MCP_130_dev/_server/profiles-130' -Filter '*.RPT' -File | Where-Object {$_.CreationTimeUtc -ge $start.AddSeconds(-1)})) {
    $head=(Get-Content -LiteralPath $file.FullName -TotalCount 80) -join "`n"
    if($head.IndexOf($ExpectedMission,[StringComparison]::OrdinalIgnoreCase) -ge 0){$matches+=$file}
}
if($matches.Count -ne 1){throw 'Unique RPT with expected mission and fresh creation timestamp required'}
$dest=Join-Path $OutputDirectory 'server.RPT'
if(Test-Path -LiteralPath $dest){throw 'Fresh RPT output required'}
Copy-Item -LiteralPath $matches[0].FullName -Destination $dest
$receipt=[ordered]@{source=$matches[0].FullName;source_creation_utc=$matches[0].CreationTimeUtc.ToString('o');process_creation_utc=$start.ToString('o');mission=$ExpectedMission;mission_match_in_header=$true;sha256=(Get-FileHash -LiteralPath $dest).Hash.ToLowerInvariant();note='RPT timestamp can fall in the next second after process creation; selected by unique mission in header and file creation, not exact filename time.'}
[IO.File]::WriteAllText((Join-Path $OutputDirectory 'rpt-binding.json'),($receipt|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
Write-Output 'RPT copied with mission and creation-time binding.'
