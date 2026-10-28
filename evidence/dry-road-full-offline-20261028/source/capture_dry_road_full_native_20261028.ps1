param([Parameter(Mandatory=$true)][int]$ServerProcessId,[Parameter(Mandatory=$true)][string]$ExpectedStartUtc,[Parameter(Mandatory=$true)][string]$OutputDirectory,[Parameter(Mandatory=$true)][ValidateSet('calibration','probe')][string]$Mode)
$ErrorActionPreference='Stop'
$hostRecord=Get-Content -LiteralPath (Join-Path $OutputDirectory 'host-identity.json') -Raw|ConvertFrom-Json
if($hostRecord.pid -ne $ServerProcessId){throw 'Host identity mismatch'}
$name=if($Mode -eq 'calibration'){'baltic_collision_probe_v1.log'}else{'baltic_visual_probe_v1.log'}
$count=if($Mode -eq 'calibration'){289}else{2658}
$header=if($Mode -eq 'calibration'){'BALTIC_COLLISION_DIAGNOSTIC_V3'}else{'BALTIC_VISUAL_PROBE_V3;BalticTrial'}
$log=Join-Path $hostRecord.profiles $name
$dest=Join-Path $OutputDirectory 'native.log'
if(Test-Path -LiteralPath $dest){throw 'Fresh capture required'}
$start=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
$deadline=[DateTime]::UtcNow.AddSeconds(900)
while([DateTime]::UtcNow -lt $deadline){
 $process=Get-Process -Id $ServerProcessId -ErrorAction Stop
 if([Math]::Abs(($process.StartTime.ToUniversalTime()-$start).TotalMilliseconds) -gt 2){throw 'Process identity changed'}
 if(Test-Path -LiteralPath $log){
  $file=Get-Item -LiteralPath $log;$head=Get-Content -LiteralPath $log -TotalCount 1;$tail=Get-Content -LiteralPath $log -Tail 1
  if($file.LastWriteTimeUtc -ge $start -and $head -eq $header -and $tail -eq ('END;'+$count)){
   Copy-Item -LiteralPath $log -Destination $dest
   $receipt=[ordered]@{status='CAPTURED_NOT_JUDGED';pid=$ServerProcessId;created_utc=$start.ToString('o');count=$count;source=$log;last_write_utc=$file.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $dest).Hash.ToLowerInvariant()}
   [IO.File]::WriteAllText((Join-Path $OutputDirectory 'log-capture.json'),($receipt|ConvertTo-Json),[Text.UTF8Encoding]::new($false));$receipt|ConvertTo-Json;exit 0
  }
  if($file.LastWriteTimeUtc -ge $start -and $tail -like 'FAIL;*'){throw ('Producer: '+$tail)}
 }
 Start-Sleep -Seconds 5
}
throw 'Measurement deadline900s'
