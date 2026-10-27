param([int]$ServerProcessId,[string]$ExpectedStartUtc,[string]$EngineLog,[string]$OutputDirectory)
$ErrorActionPreference='Stop'
$expected=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
$dest=Join-Path $OutputDirectory 'runtime.log'
if(Test-Path -LiteralPath $dest){throw 'Fresh output log required'}
$deadline=[DateTime]::UtcNow.AddSeconds(300)
while([DateTime]::UtcNow -lt $deadline) {
 $p=Get-Process -Id $ServerProcessId -ErrorAction Stop
 if([Math]::Abs(($p.StartTime.ToUniversalTime()-$expected).TotalMilliseconds) -gt 2){throw 'Process identity changed'}
 if(Test-Path -LiteralPath $EngineLog) {
  $file=Get-Item -LiteralPath $EngineLog
  if($file.LastWriteTimeUtc -lt $expected){throw 'Stale engine log'}
  $rows=Get-Content -LiteralPath $EngineLog
  if($rows[-1] -match '^END;[0-9]+$') {
   Copy-Item -LiteralPath $EngineLog -Destination $dest
   $binding=[ordered]@{pid=$ServerProcessId;created_utc=$expected.ToString('o');source=$EngineLog;source_last_write_utc=$file.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $dest).Hash.ToLowerInvariant();expected_end_count=49}
   [IO.File]::WriteAllText((Join-Path $OutputDirectory 'log-binding.json'),($binding|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
   Write-Output 'Captured fresh complete native 49-query log.'
   exit 0
  }
 }
 Start-Sleep -Milliseconds 1000
}
throw 'Native log did not complete within 300 seconds'
