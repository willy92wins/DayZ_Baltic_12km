param(
    [string]$Python = 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe',
    [int]$Iterations = 10000,
    [double]$PerWorkerSeconds = 30.0,
    [long]$MemoryCapBytes = 268435456,
    [string]$RunTag = 'attempt-02'
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$worker = Join-Path $here 'telemetry_pointer_cache_probe.py'
$outDir = Join-Path (Join-Path $here 'telemetry-pointer-cache') $RunTag
if (!(Test-Path -LiteralPath $Python -PathType Leaf)) { throw "GIS Python missing: $Python" }
if (!(Test-Path -LiteralPath $worker -PathType Leaf)) { throw "Probe script missing: $worker" }
if (!(Test-Path -LiteralPath $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$results = @()
foreach ($mode in @('original','cached')) {
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $Python
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.Arguments = '"' + $worker + '" --worker ' + $mode + ' --iterations ' + [string]$Iterations + ' --hold-seconds 1'
    $clock = [System.Diagnostics.Stopwatch]::StartNew()
    $proc = [System.Diagnostics.Process]::Start($psi)
    # The GIS Python entrypoint may launch the interpreter child; identify the
    # measured worker from its flushed first event instead of assuming proc.Id.
    $firstLine = $proc.StandardOutput.ReadLine()
    if ([string]::IsNullOrWhiteSpace($firstLine)) { throw "worker emitted no start record: $mode" }
    $startEvent = $firstLine | ConvertFrom-Json
    if ($startEvent.event -ne 'started' -or $startEvent.mode -ne $mode) { throw "invalid worker start record: $firstLine" }
    $workerPid = [int]$startEvent.pid
    $samples = [System.Collections.Generic.List[object]]::new()
    $peakWs = 0L; $peakPrivate = 0L; $baseWs = $null; $basePrivate = $null
    $timedOut = $false; $memoryExceeded = $false
    while ($true) {
        try {
            $p = Get-Process -Id $workerPid -ErrorAction Stop
        } catch { break }
        try {
            $ws = [long]$p.WorkingSet64; $priv = [long]$p.PrivateMemorySize64
            if ($null -eq $baseWs) { $baseWs = $ws; $basePrivate = $priv }
            if ($ws -gt $peakWs) { $peakWs = $ws }
            if ($priv -gt $peakPrivate) { $peakPrivate = $priv }
            if (($samples.Count -eq 0) -or ($clock.ElapsedMilliseconds - $samples[$samples.Count-1].elapsed_ms -ge 250)) {
                $samples.Add([pscustomobject]@{elapsed_ms=$clock.ElapsedMilliseconds;working_set_bytes=$ws;private_bytes=$priv})
            }
            if ($ws -gt $MemoryCapBytes -or $priv -gt $MemoryCapBytes) { $memoryExceeded = $true; $proc.Kill(); break }
        } catch { throw }
        if ($clock.Elapsed.TotalSeconds -gt $PerWorkerSeconds) { $timedOut = $true; $proc.Kill(); break }
        Start-Sleep -Milliseconds 20
    }
    $proc.WaitForExit()
    $stdout = $firstLine + "`n" + $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $clock.Stop()
    $workerLines = @($stdout -split "`r?`n" | Where-Object { $_.Trim() })
    $workerEvents = @()
    foreach ($line in $workerLines) { try { $workerEvents += ($line | ConvertFrom-Json) } catch { } }
    $item = [pscustomobject]@{
        mode=$mode; pid=$workerPid; launcher_pid=$proc.Id; exit_code=$proc.ExitCode; timed_out=$timedOut; memory_exceeded=$memoryExceeded
        wall_seconds=$clock.Elapsed.TotalSeconds; iterations=$Iterations
        external_reader='PowerShell Get-Process WorkingSet64 and PrivateMemorySize64, sampled every 20ms'
        baseline_working_set_bytes=$baseWs; sampled_peak_working_set_bytes=$peakWs
        baseline_private_bytes=$basePrivate; sampled_peak_private_bytes=$peakPrivate
        cap_bytes=$MemoryCapBytes; samples=$samples; worker_events=$workerEvents
        stdout=$stdout; stderr=$stderr
    }
    $json = $item | ConvertTo-Json -Depth 8
    [IO.File]::WriteAllText((Join-Path $outDir "$mode.json"),$json,[Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $outDir "$mode.stdout.txt"),$stdout,[Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $outDir "$mode.stderr.txt"),$stderr,[Text.UTF8Encoding]::new($false))
    $results += $item
    if ($timedOut -or $memoryExceeded -or $proc.ExitCode -ne 0) { break }
}
$summary = [pscustomobject]@{
    schema='telemetry-pointer-cache-isolation.v1'; iterations=$Iterations
    per_worker_seconds=$PerWorkerSeconds; memory_cap_bytes=$MemoryCapBytes
    solver_path='E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\global-operator-prototype\admm-quantized-pilot\solve.py'
    solver_sha256=(Get-FileHash -LiteralPath 'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\global-operator-prototype\admm-quantized-pilot\solve.py' -Algorithm SHA256).Hash.ToLower()
    probe_path=$worker; probe_sha256=(Get-FileHash -LiteralPath $worker -Algorithm SHA256).Hash.ToLower()
    runs=$results
    interpretation='The worker executes the frozen helper AST in a fresh GIS Python process; cached differs only by lifting Counters to module scope. External PowerShell sampling is independent of ctypes._pointer_type_cache.'
}
$summaryPath = Join-Path $outDir 'summary.json'
[IO.File]::WriteAllText($summaryPath,($summary | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$summary | Select-Object schema,iterations,solver_sha256,probe_sha256,@{n='runs';e={$_.runs | Select-Object mode,pid,exit_code,timed_out,memory_exceeded,wall_seconds,baseline_working_set_bytes,sampled_peak_working_set_bytes,baseline_private_bytes,sampled_peak_private_bytes,@{n='pointer_cache_delta';e={($_.worker_events | Where-Object event -eq 'finished' | Select-Object -First 1).pointer_cache_delta}}}} | ConvertTo-Json -Depth 7
if ($results.Count -ne 2 -or @($results | Where-Object { $_.exit_code -ne 0 -or $_.timed_out -or $_.memory_exceeded }).Count -gt 0) { exit 1 }
