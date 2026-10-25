param([int]$ServerProcessId,[string]$ExpectedStartUtc,[string]$EngineLog,[string]$OutputDirectory,[int]$ExpectedCount)
$ErrorActionPreference='Stop'
if($ExpectedCount -notin @(187)){throw 'Unexpected point count'}
$expected=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
$dest=Join-Path $OutputDirectory 'runtime.log'
if(Test-Path -LiteralPath $dest){throw 'Fresh output log required'}
$deadline=$expected.AddSeconds(900)
while([DateTime]::UtcNow -lt $deadline){
 $p=Get-Process -Id $ServerProcessId -ErrorAction Stop
 if([Math]::Abs(($p.StartTime.ToUniversalTime()-$expected).TotalMilliseconds) -gt 2){throw 'Process identity changed'}
 if(Test-Path -LiteralPath $EngineLog){
  $file=Get-Item -LiteralPath $EngineLog
  if($file.LastWriteTimeUtc -ge $expected){
   $last=Get-Content -LiteralPath $EngineLog -Tail 1
   if($last -like 'FAIL;*'){throw ('Probe failed: '+$last)}
   if($last -eq ('END;'+$ExpectedCount)){
    $head=@(Get-Content -LiteralPath $EngineLog -TotalCount 2)
    if($head.Count -ne 2 -or $head[0] -ne 'BALTIC_VISUAL_PROBE_V3;BalticTrial' -or $head[1] -ne ('BEGIN;'+$ExpectedCount)){throw 'Unexpected header'}
    Copy-Item -LiteralPath $EngineLog -Destination $dest
    if((Get-FileHash -LiteralPath $dest).Hash -ne (Get-FileHash -LiteralPath $EngineLog).Hash){throw 'Log changed during copy'}
    $binding=[ordered]@{pid=$ServerProcessId;created_utc=$expected.ToString('o');source=$EngineLog;source_last_write_utc=$file.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $dest).Hash.ToLowerInvariant();expected_end_count=$ExpectedCount}
    [IO.File]::WriteAllText((Join-Path $OutputDirectory 'log-binding.json'),($binding|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
    Write-Output ('Captured '+$ExpectedCount+' points');exit 0
   }
  }
 }
 Start-Sleep -Milliseconds 1000
}
throw 'Probe did not complete within 900s'
