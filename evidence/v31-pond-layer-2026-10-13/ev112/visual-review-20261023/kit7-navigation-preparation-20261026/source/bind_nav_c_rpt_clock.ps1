param([Parameter(Mandatory=$true)][string]$ExpectedStartUtc,[Parameter(Mandatory=$true)][string]$ExpectedMission,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $OutputPath){throw 'Fresh clock binding required'}
$start=[DateTime]::Parse($ExpectedStartUtc).ToUniversalTime()
$mission=[IO.Path]::GetFullPath($ExpectedMission)
$matches=@()
foreach($file in @(Get-ChildItem -LiteralPath 'C:/temp/DayZ_MCP_130_dev/_server/profiles-130' -Filter '*.RPT' -File | Where-Object {$_.CreationTimeUtc -ge $start.AddSeconds(-1)})) {
    $head=(Get-Content -LiteralPath $file.FullName -TotalCount 80) -join "`n"
    if($head.IndexOf($mission,[StringComparison]::OrdinalIgnoreCase) -ge 0){$matches+=@{file=$file;head=$head}}
}
if($matches.Count -ne 1){throw 'Unique RPT mission binding required'}
$match=[regex]::Match($matches[0].head,'Current time:\s+(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})')
if(-not $match.Success){throw 'RPT wall clock header absent'}
$localHeader=[DateTime]::ParseExact($match.Groups[1].Value,'yyyy/MM/dd HH:mm:ss',[Globalization.CultureInfo]::InvariantCulture)
$zone=[TimeZoneInfo]::Local
if($zone.IsAmbiguousTime($localHeader) -or $zone.IsInvalidTime($localHeader)){throw 'RPT local clock ambiguous'}
$utcHeader=[TimeZoneInfo]::ConvertTimeToUtc($localHeader,$zone)
$delta=($utcHeader-$start).TotalSeconds
if($delta -lt -2 -or $delta -gt 180){throw 'RPT and process clocks inconsistent'}
$report=[ordered]@{status='RPT_LOCAL_CLOCK_BOUND';observed_utc=[DateTimeOffset]::UtcNow.ToString('o');process_created_utc=$start.ToString('o');rpt_path=$matches[0].file.FullName;rpt_creation_utc=$matches[0].file.CreationTimeUtc.ToString('o');rpt_header_local=$match.Groups[1].Value;rpt_header_utc=$utcHeader.ToString('o');time_zone=$zone.Id;utc_offset_seconds=$zone.GetUtcOffset($localHeader).TotalSeconds;header_after_process_seconds=$delta;limits='RPT timestamps use this local offset. Generator progress has observation UTC only; ordering inside the 5-second observation interval is not asserted.'}
[IO.File]::WriteAllText($OutputPath,($report|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
$report|ConvertTo-Json -Compress
