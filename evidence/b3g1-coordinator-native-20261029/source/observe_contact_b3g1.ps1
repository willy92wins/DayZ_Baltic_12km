param([Parameter(Mandatory=$true)][string]$Directory,[Parameter(Mandatory=$true)][string]$ReadyUtc)
$ErrorActionPreference='Stop'
$env:PSModulePath=(Join-Path $PSHOME 'Modules')+';'+$env:PSModulePath
$hostRecord=Get-Content -LiteralPath (Join-Path $Directory 'host-identity.json') -Raw | ConvertFrom-Json
$ready=[DateTimeOffset]::Parse($ReadyUtc).UtcDateTime
$deadline=$ready.AddSeconds(180)
$created=[DateTimeOffset]::Parse($hostRecord.created_utc).UtcDateTime
$process=Get-Process -Id $hostRecord.pid -ErrorAction Stop
if([Math]::Abs(($process.StartTime.ToUniversalTime()-$created).TotalMilliseconds) -gt 1){throw 'Process identity changed'}
if([DateTime]::UtcNow -gt $deadline){throw 'Capture deadline exceeded'}
$logs=@(Get-ChildItem -LiteralPath $hostRecord.profiles -File -Filter 'script_*.log' | Where-Object {$_.CreationTimeUtc -ge $created -and $_.LastWriteTimeUtc -ge $created})
if($logs.Count -ne 1){throw 'Unique fresh script log missing'}
$scriptFile=$logs[0]
if($scriptFile.Length -gt 20971520){throw 'Script log size budget'}
$scriptRaw=[IO.File]::ReadAllBytes($scriptFile.FullName)
$scriptText=[Text.Encoding]::UTF8.GetString($scriptRaw)
$sha=[Security.Cryptography.SHA256]::Create()
function HashBytes([byte[]]$Data){return [BitConverter]::ToString($sha.ComputeHash($Data)).Replace('-','').ToLowerInvariant()}
function SaveJson($Name,$Value){[IO.File]::WriteAllText((Join-Path $Directory $Name),($Value|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))}
try {
 $scriptSha=HashBytes $scriptRaw
 $checked=[DateTime]::UtcNow
 $startMatch=[regex]::Match($scriptText,'started at .*\((\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) UTC\)')
 if(-not $startMatch.Success){throw 'Script header UTC missing'}
 $logStart=[DateTime]::SpecifyKind([DateTime]::ParseExact($startMatch.Groups[1].Value,'yyyy-MM-dd HH:mm:ss',[Globalization.CultureInfo]::InvariantCulture),[DateTimeKind]::Utc)
 if($logStart -lt $created.AddSeconds(-1) -or $logStart -gt $checked){throw 'Script header not fresh'}
 if($scriptText -match 'SCRIPT\s*\(E\)|Can.t compile mission init script'){
  [IO.File]::WriteAllBytes((Join-Path $Directory 'script-failure.log'),$scriptRaw)
  SaveJson 'script-failure.json' ([ordered]@{status='NATIVE_SCRIPT_ERROR';run_id=$hostRecord.run_id;pid=$hostRecord.pid;source=$scriptFile.FullName;sha256=$scriptSha;checked_utc=$checked.ToString('o')})
  throw 'NATIVE_SCRIPT_ERROR (fresh run log archived)'
 }
 $startPath=Join-Path $Directory 'capture-start.json'
 if(-not(Test-Path -LiteralPath $startPath)){
  [IO.File]::WriteAllBytes((Join-Path $Directory 'script-before.log'),$scriptRaw)
  $start=[ordered]@{basis='HOST_UTC_FIRST_SERVER_BOUND_VERSION_OK_FRESH';run_id=$hostRecord.run_id;pid=$hostRecord.pid;ready_utc=$ready.ToString('o');capture_started_utc=[DateTime]::UtcNow.ToString('o');capture_deadline_utc=$deadline.ToString('o');script_log_checked_utc=$checked.ToString('o');script_log_sha256=$scriptSha;mission_error_before_capture=$false;script_source=$scriptFile.FullName;script_created_utc=$scriptFile.CreationTimeUtc.ToString('o');script_last_write_utc=$scriptFile.LastWriteTimeUtc.ToString('o')}
  SaveJson 'capture-start.json' $start
 }
 $native=Join-Path $hostRecord.profiles 'baltic_contact_b3g.log'
 if(-not(Test-Path -LiteralPath $native)){[pscustomobject]@{status='PENDING_NATIVE_LOG'}|ConvertTo-Json;exit 0}
 $info=Get-Item -LiteralPath $native
 if($info.LastWriteTimeUtc -lt $created -or $info.Length -gt 20971520){throw 'Native log stale or too large'}
 $raw=[IO.File]::ReadAllBytes($native);$lines=[Text.Encoding]::UTF8.GetString($raw).TrimEnd("`r","`n").Split("`n")
 if($lines[0].TrimEnd("`r") -ne 'BALTIC_CONTACT_B3G;BalticTrial'){throw 'Native header mismatch'}
 if($lines[-1] -like 'FAIL;*'){throw ('Producer failed: '+$lines[-1])}
 if($lines[-1].TrimEnd("`r") -ne 'END;270'){[pscustomobject]@{status='PENDING_SAMPLES';lines=$lines.Count}|ConvertTo-Json;exit 0}
 $count=@($lines|Where-Object{$_ -like 'Q;*'}).Count
 if($count -ne 270){throw 'Native Q count mismatch'}
 # Re-read after capture-start, even if END was already present at first observation.
 $scriptFile=Get-Item -LiteralPath $scriptFile.FullName
 if($scriptFile.Length -gt 20971520){throw 'Script log size budget'}
 $scriptRaw=[IO.File]::ReadAllBytes($scriptFile.FullName)
 $scriptText=[Text.Encoding]::UTF8.GetString($scriptRaw)
 $scriptSha=HashBytes $scriptRaw
 $checked=[DateTime]::UtcNow
 if($scriptText -match 'SCRIPT\s*\(E\)|Can.t compile mission init script'){
  [IO.File]::WriteAllBytes((Join-Path $Directory 'script-failure.log'),$scriptRaw)
  SaveJson 'script-failure.json' ([ordered]@{status='NATIVE_SCRIPT_ERROR';run_id=$hostRecord.run_id;pid=$hostRecord.pid;source=$scriptFile.FullName;sha256=$scriptSha;checked_utc=$checked.ToString('o')})
  throw 'NATIVE_SCRIPT_ERROR (fresh run log archived)'
 }
 $dest=Join-Path $Directory 'native.log'
 if(Test-Path -LiteralPath $dest){throw 'Capture already consumed'}
 [IO.File]::WriteAllBytes($dest,$raw)
 $hash=HashBytes $raw
 if((Get-FileHash -LiteralPath $native).Hash.ToLowerInvariant() -ne $hash){throw 'Native changed during copy'}
 [IO.File]::WriteAllBytes((Join-Path $Directory 'script-at-capture.log'),$scriptRaw)
 $ended=[DateTime]::UtcNow
 if($ended -gt $deadline){throw 'Capture ended after deadline'}
 $window=Get-Content -LiteralPath $startPath -Raw|ConvertFrom-Json
 $window|Add-Member -NotePropertyName capture_ended_utc -NotePropertyValue $ended.ToString('o')
 SaveJson 'capture-window.json' $window
 SaveJson 'script-at-capture.json' ([ordered]@{source=$scriptFile.FullName;sha256=$scriptSha;checked_utc=$checked.ToString('o');last_write_utc=$scriptFile.LastWriteTimeUtc.ToString('o')})
 SaveJson 'log-capture.json' ([ordered]@{status='CAPTURED_NOT_JUDGED';pid=$hostRecord.pid;created_utc=$hostRecord.created_utc;count=$count;source=$native;last_write_utc=$info.LastWriteTimeUtc.ToString('o');sha256=$hash;captured_utc=$ended.ToString('o')})
 [pscustomobject]@{status='CAPTURED_NOT_JUDGED';count=$count;sha256=$hash}|ConvertTo-Json
} finally {$sha.Dispose()}
