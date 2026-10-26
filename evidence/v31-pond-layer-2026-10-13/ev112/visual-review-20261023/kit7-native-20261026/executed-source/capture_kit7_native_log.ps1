param([Parameter(Mandatory=$true)][int]$ServerProcessId,[Parameter(Mandatory=$true)][string]$ExpectedStartUtc,[Parameter(Mandatory=$true)][string]$SurveyId,[Parameter(Mandatory=$true)][int]$Count,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$log='C:/temp/DayZ_MCP_130_dev/_server/profiles-130/baltic_forest_boundary_v1.log'
$dest=Join-Path $OutputDirectory 'native.log'
if(Test-Path -LiteralPath $dest){throw 'Fresh native log output required'}
$start=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
$deadline=[DateTime]::UtcNow.AddSeconds(900)
while([DateTime]::UtcNow -lt $deadline){
 $p=Get-Process -Id $ServerProcessId -ErrorAction Stop
 if([Math]::Abs(($p.StartTime.ToUniversalTime()-$start).TotalMilliseconds) -gt 2){throw 'Process identity changed'}
 if(Test-Path -LiteralPath $log){
  $file=Get-Item -LiteralPath $log
  $head=@(Get-Content -LiteralPath $log -TotalCount 3)
  $tail=Get-Content -LiteralPath $log -Tail 1
  if($head.Count -eq 3 -and $head[0] -eq 'BALTIC_FOREST_BOUNDARY_V1;BalticTrial' -and $head[1] -eq ('SURVEY;'+$SurveyId) -and $head[2] -eq ('BEGIN;'+$Count) -and $file.LastWriteTimeUtc -ge $start -and $tail -eq ('END;'+$Count)){
   Copy-Item -LiteralPath $log -Destination $dest
   $receipt=[ordered]@{status='FRESH_LOG_CAPTURED_NOT_JUDGED';pid=$ServerProcessId;created_utc=$start.ToString('o');survey_id=$SurveyId;count=$Count;source=$log;last_write_utc=$file.LastWriteTimeUtc.ToString('o');sha256=(Get-FileHash -LiteralPath $dest).Hash.ToLowerInvariant()}
   [IO.File]::WriteAllText((Join-Path $OutputDirectory 'log-capture.json'),($receipt|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
   $receipt|ConvertTo-Json;exit 0
  }
  if($head.Count -ge 2 -and $head[1] -eq ('SURVEY;'+$SurveyId) -and $tail -like 'FAIL;*'){throw ('Native producer: '+$tail)}
 }
 Start-Sleep -Seconds 5
}
throw 'Native measurement deadline 900s'
