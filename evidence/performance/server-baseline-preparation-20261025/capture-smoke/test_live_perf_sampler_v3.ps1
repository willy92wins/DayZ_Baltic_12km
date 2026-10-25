$ErrorActionPreference='Stop'
$root='E:/DayZ-Baltic-Build/shape-repair-20261025/server-baseline-capture-smoke-v3'
if(Test-Path -LiteralPath $root){throw 'Fresh smoke output required'}
New-Item -ItemType Directory -Path $root | Out-Null
$log=Join-Path $root 'synthetic-engine.log'
$child=Start-Process -FilePath powershell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','E:/DayZ-Baltic-Build/shape-repair-20261025/perf_sampler_exclusive_writer.ps1','-Path',$log) -WindowStyle Hidden -PassThru
try {
    $start=$child.StartTime.ToUniversalTime()
    $capture='C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c/tools/performance/capture_server_baseline_ev112.ps1'
    $negative=$false
    try {& $capture -ServerProcessId $child.Id -ExpectedStartUtc $start.AddDays(1).ToString('o') -OutputPath (Join-Path $root 'wrong-identity.jsonl') -EngineLogPath $log -MaxSeconds 15}
    catch {if($_.Exception.Message -like '*Process identity changed*'){$negative=$true}else{throw}}
    if(-not $negative){throw 'Wrong process identity was accepted'}
    & $capture -ServerProcessId $child.Id -ExpectedStartUtc $start.ToString('o') -OutputPath (Join-Path $root 'captured.jsonl') -EngineLogPath $log -MaxSeconds 15
    $rows=@(Get-Content -LiteralPath (Join-Path $root 'captured.jsonl') | ForEach-Object {$_|ConvertFrom-Json})
    if($rows.Count -lt 3 -or $rows[-1].engine_last_line -ne 'END;120;150'){throw 'Capture did not reach expected marker'}
    if(@($rows | Where-Object {$_.process_id -ne $child.Id -or $_.private_bytes -le 0}).Count){throw 'Bad live process counters'}
    if(@($rows | Where-Object {$_.engine_read_unavailable -eq $true}).Count -lt 1){throw 'Exclusive writer branch not exercised'}
    $result=[ordered]@{status='PASS_LIVE_SAMPLER_SMOKE_ONLY';wrong_identity_rejected=$negative;samples=$rows.Count;process_id=$child.Id;start_utc=$start.ToString('o');limits=@('Synthetic child PowerShell writer. This is not a DayZ performance run.','Only process identity, live counters, bounded tail reading and END stop are exercised.')}
    [IO.File]::WriteAllText((Join-Path $root 'result.json'),($result|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
    $result|ConvertTo-Json -Depth 4
    [void]$child.WaitForExit(15000)
} finally {if(-not $child.HasExited){$child.Kill();$child.WaitForExit()};$child.Dispose()}
