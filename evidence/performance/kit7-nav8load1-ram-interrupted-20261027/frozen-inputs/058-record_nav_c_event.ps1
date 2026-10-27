param([Parameter(Mandatory=$true)][string]$Directory,[Parameter(Mandatory=$true)][guid]$RunId,[Parameter(Mandatory=$true)][ValidateSet('LAUNCHED','ATTACHED','GENERATOR_STARTED','HEARTBEAT_OK','HEARTBEAT_ERROR','LEASE_RECOVERED','COORDINATION_LOST','SERVER_EXIT_OBSERVED','CLOSE_INTENT','GENERATOR_CANCEL_INTENT','CLOSED')][string]$Event)
$ErrorActionPreference='Stop'
$now=[DateTimeOffset]::UtcNow.ToString('o')
$record=[ordered]@{utc=$now;event=$Event;run_id=$RunId.ToString()}
$writer=[IO.StreamWriter]::new((Join-Path $Directory 'timeline.jsonl'),$true,[Text.UTF8Encoding]::new($false))
try {$writer.WriteLine(($record|ConvertTo-Json -Compress));$writer.Flush()} finally {$writer.Dispose()}
Write-Output $now
