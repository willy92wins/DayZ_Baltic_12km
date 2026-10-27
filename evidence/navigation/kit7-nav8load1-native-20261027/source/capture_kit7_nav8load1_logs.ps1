param([int]$ServerProcessId,[string]$ExpectedStartUtc,[string]$EngineLog,[string]$OutputDirectory,[string]$ConfigEngineLog)
$ErrorActionPreference='Stop'
$expected=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
$dest=Join-Path $OutputDirectory 'runtime.log'
$configDest=Join-Path $OutputDirectory 'config-runtime.log'
if((Test-Path -LiteralPath $dest) -or (Test-Path -LiteralPath $configDest)){throw 'Fresh output logs required'}
$deadline=[DateTime]::UtcNow.AddSeconds(900)
while([DateTime]::UtcNow -lt $deadline) {
 $p=Get-Process -Id $ServerProcessId -ErrorAction Stop
 if([Math]::Abs(($p.StartTime.ToUniversalTime()-$expected).TotalMilliseconds) -gt 2){throw 'Process identity changed'}
 if(Test-Path -LiteralPath $EngineLog) {
  $file=Get-Item -LiteralPath $EngineLog
  if($file.LastWriteTimeUtc -lt $expected){throw 'Stale engine log'}
  $rows=@(Get-Content -LiteralPath $EngineLog)
  if($rows.Count -gt 0 -and $rows[-1] -match '^END;[0-9]+$') {
   $configFile=Get-Item -LiteralPath $ConfigEngineLog
   if($configFile.LastWriteTimeUtc -lt $expected){throw 'Stale config capture'}
   $configRows=@(Get-Content -LiteralPath $ConfigEngineLog)
   if($configRows.Count -eq 0 -or $configRows[-1] -notmatch '^END;[0-9]+$'){throw 'Incomplete config capture'}
   Copy-Item -LiteralPath $EngineLog -Destination $dest
   Copy-Item -LiteralPath $ConfigEngineLog -Destination $configDest
   $binding=[ordered]@{pid=$ServerProcessId;created_utc=$expected.ToString('o');source=$EngineLog;source_last_write_utc=$file.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $dest).Hash.ToLowerInvariant();expected_end_count=607;config_source=$ConfigEngineLog;config_sha256=(Get-FileHash -LiteralPath $configDest).Hash.ToLowerInvariant();config_source_last_write_utc=$configFile.LastWriteTimeUtc.ToString('o')}
   [IO.File]::WriteAllText((Join-Path $OutputDirectory 'log-binding.json'),($binding|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
   Write-Output 'Captured bound graph/config logs; consumers must validate counts and contents.'
   exit 0
  }
 }
 Start-Sleep -Milliseconds 1000
}
throw 'Native log did not complete within 900 seconds'
