param([Parameter(Mandatory=$true)][int]$ServerProcessId,[Parameter(Mandatory=$true)][string]$ExpectedStartUtc,[Parameter(Mandatory=$true)][ValidateSet('full','calibration')][string]$Kind,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$logName=if($Kind -eq 'full'){'baltic_visual_probe_v1.log'}else{'baltic_collision_probe_v1.log'}
$header=if($Kind -eq 'full'){'BALTIC_VISUAL_PROBE_V3;BalticTrial'}else{'BALTIC_COLLISION_DIAGNOSTIC_V3'}
$count=if($Kind -eq 'full'){6801}else{289}
$budget=if($Kind -eq 'full'){1200}else{180}
$log=Join-Path 'C:/temp/DayZ_MCP_130_dev/_server/profiles-130' $logName
$dest=Join-Path $OutputDirectory 'native.log'
if(Test-Path -LiteralPath $dest){throw 'Fresh output required'}
$start=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
$deadline=[DateTime]::UtcNow.AddSeconds($budget)
while([DateTime]::UtcNow -lt $deadline){
 $p=Get-Process -Id $ServerProcessId -ErrorAction Stop
 if([Math]::Abs(($p.StartTime.ToUniversalTime()-$start).TotalMilliseconds) -gt 2){throw 'Process identity changed'}
 if(Test-Path -LiteralPath $log){
  $f=Get-Item -LiteralPath $log;$head=Get-Content -LiteralPath $log -TotalCount 1;$tail=Get-Content -LiteralPath $log -Tail 1
  if($f.LastWriteTimeUtc -ge $start -and $head -eq $header -and $tail -eq ('END;'+$count)){
   Copy-Item -LiteralPath $log -Destination $dest
   $receipt=[ordered]@{status='CAPTURED_NOT_JUDGED';pid=$ServerProcessId;created_utc=$start.ToString('o');kind=$Kind;count=$count;source=$log;last_write_utc=$f.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $dest).Hash.ToLowerInvariant();limits=@('Producer V3 has no UUID; fresh post-launch modification, run/PID/mission binding and immutable CSV are required together.')}
   [IO.File]::WriteAllText((Join-Path $OutputDirectory 'log-capture.json'),($receipt|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
   $receipt|ConvertTo-Json;exit 0
  }
  if($f.LastWriteTimeUtc -ge $start -and $head -eq $header -and $tail -like 'FAIL;*'){throw ('Producer: '+$tail)}
 }
 Start-Sleep -Seconds 5
}
throw ('Measurement deadline '+$budget+'s')
