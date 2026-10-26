$ErrorActionPreference='Stop'
$output='E:/DayZ-Baltic-Build/shape-repair-20261025/c-nav-exit-diagnostic-20261026/windows-events.json'
if(Test-Path -LiteralPath $output){throw 'Fresh diagnostic output required'}
$from=[DateTimeOffset]::Parse('2026-10-26T11:57:00Z')
$until=[DateTimeOffset]::Parse('2026-10-26T11:59:00Z')
$channels=@()
foreach($channel in @('Application','System','Microsoft-Windows-TaskScheduler/Operational','Microsoft-Windows-Sysmon/Operational','Security')) {
    $row=[ordered]@{channel=$channel;enabled=$null;events=@();error_id=$null}
    try {
        $meta=Get-WinEvent -ListLog $channel -ErrorAction Stop
        $row.enabled=$meta.IsEnabled
        $filter=@{LogName=$channel;StartTime=$from.LocalDateTime;EndTime=$until.LocalDateTime}
        if($channel -eq 'Security'){$filter.Id=4689}
        $events=@(Get-WinEvent -FilterHashtable $filter -ErrorAction Stop)
        $row.events=@($events | ForEach-Object {[ordered]@{utc=$_.TimeCreated.ToUniversalTime().ToString('o');id=$_.Id;provider=$_.ProviderName;level=$_.LevelDisplayName}})
    } catch {$row.error_id=$_.FullyQualifiedErrorId}
    $channels+=$row
}
$report=[ordered]@{from_utc=$from.UtcDateTime.ToString('o');until_utc=$until.UtcDateTime.ToString('o');channels=$channels;limits='Read-only metadata; absent events or disabled/unavailable channels do not establish the shutdown cause.'}
[IO.File]::WriteAllText($output,($report|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
$report|ConvertTo-Json -Depth 8
