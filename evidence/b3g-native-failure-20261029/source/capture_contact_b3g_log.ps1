param(
 [Parameter(Mandatory=$true)][int]$ServerProcessId,
 [Parameter(Mandatory=$true)][string]$ExpectedStartUtc,
 [Parameter(Mandatory=$true)][string]$OutputDirectory,
 [Parameter(Mandatory=$true)][string]$DeadlineUtc
)
$ErrorActionPreference='Stop'
$hostRecord=Get-Content -LiteralPath (Join-Path $OutputDirectory 'host-identity.json') -Raw|ConvertFrom-Json
if($hostRecord.pid -ne $ServerProcessId){throw 'Host identity mismatch'}
$log=Join-Path $hostRecord.profiles 'baltic_contact_b3g.log'
$dest=Join-Path $OutputDirectory 'native.log'
if(Test-Path -LiteralPath $dest){throw 'Fresh capture required'}
$start=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
$deadline=[DateTime]::Parse($DeadlineUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
if($deadline -gt [DateTime]::UtcNow.AddSeconds(180)){throw 'Capture budget above180s'}
while([DateTime]::UtcNow -lt $deadline){
 $process=Get-Process -Id $ServerProcessId -ErrorAction Stop
 if([Math]::Abs(($process.StartTime.ToUniversalTime()-$start).TotalMilliseconds) -gt 1){throw 'Process identity changed'}
 if(Test-Path -LiteralPath $log){
  $file=Get-Item -LiteralPath $log
  $head=Get-Content -LiteralPath $log -TotalCount 1
  $tail=Get-Content -LiteralPath $log -Tail 1
  if($file.LastWriteTimeUtc -ge $start -and $head -eq 'BALTIC_CONTACT_B3G;BalticTrial' -and $tail -eq 'END;270'){
   Copy-Item -LiteralPath $log -Destination $dest
   $hash=(Get-FileHash -LiteralPath $dest).Hash.ToLowerInvariant()
   if((Get-FileHash -LiteralPath $log).Hash.ToLowerInvariant() -ne $hash){throw 'Capture changed while copying'}
   $count=@(Get-Content -LiteralPath $dest | Where-Object {$_ -like 'Q;*'}).Count
   if($count -ne 270){throw 'Capture Q count mismatch'}
   $receipt=[ordered]@{status='CAPTURED_NOT_JUDGED';pid=$ServerProcessId;created_utc=$start.ToString('o');count=$count;source=$log;last_write_utc=$file.LastWriteTimeUtc.ToString('o');sha256=$hash}
   [IO.File]::WriteAllText((Join-Path $OutputDirectory 'log-capture.json'),($receipt|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
   $receipt|ConvertTo-Json;exit 0
  }
  if($file.LastWriteTimeUtc -ge $start -and $tail -like 'FAIL;*'){throw ('Producer: '+$tail)}
 }
 Start-Sleep -Seconds 2
}
throw 'Measurement deadline180s from bridge readiness'
