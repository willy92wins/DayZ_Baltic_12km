param([int]$ServerProcessId,[string]$ExpectedStartUtc,[string]$EngineLog,[string]$OutputDirectory)
$ErrorActionPreference='Stop'
$expected=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
$dest=Join-Path $OutputDirectory 'runtime.log'
if(Test-Path -LiteralPath $dest){throw 'Fresh output log required'}
$deadline=$expected.AddSeconds(900)
while([DateTime]::UtcNow -lt $deadline) {
 $p=Get-Process -Id $ServerProcessId -ErrorAction Stop
 if([Math]::Abs(($p.StartTime.ToUniversalTime()-$expected).TotalMilliseconds) -gt 2){throw 'Process identity changed'}
 if(Test-Path -LiteralPath $EngineLog) {
  $file=Get-Item -LiteralPath $EngineLog
  if($file.LastWriteTimeUtc -ge $expected) {
   $last=Get-Content -LiteralPath $EngineLog -Tail 1
   if($last -like 'FAIL;*'){throw ('Native probe failed: '+$last)}
   if($last -eq 'END;269968') {
    $head=@(Get-Content -LiteralPath $EngineLog -TotalCount 3)
    if($head.Count -ne 3 -or $head[0] -ne 'BALTIC_FOREST_BOUNDARY_V1;BalticTrial' -or $head[1] -ne 'SURVEY;84936372-1378-44a6-823e-df7829724b7b' -or $head[2] -ne 'BEGIN;269968'){throw 'Unexpected native survey header'}
    Copy-Item -LiteralPath $EngineLog -Destination $dest
    $binding=[ordered]@{pid=$ServerProcessId;created_utc=$expected.ToString('o');source=$EngineLog;source_last_write_utc=$file.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $dest).Hash.ToLowerInvariant();expected_end_count=269968;survey_id='84936372-1378-44a6-823e-df7829724b7b'}
    [IO.File]::WriteAllText((Join-Path $OutputDirectory 'log-binding.json'),($binding|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
    Write-Output 'Captured fresh complete native 269968-point forest survey.'
    exit 0
   }
  }
 }
 Start-Sleep -Milliseconds 1000
}
throw 'Native forest log did not complete within 900 seconds of launch'
