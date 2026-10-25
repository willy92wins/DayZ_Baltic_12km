param(
    [Parameter(Mandatory=$true)][int]$ClientProcessId,
    [Parameter(Mandatory=$true)][datetime]$ExpectedStartUtc,
    [Parameter(Mandatory=$true)][string]$ExpectedImage,
    [Parameter(Mandatory=$true)][string]$Scenario,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [Parameter(Mandatory=$true)][string]$PresentMon
)
# Passive collector only. Launch/adopt DayZ through the session protocol first.
# No focus manipulation, game launch, settings changes or existing ETW takeover.
$ErrorActionPreference='Stop'
$exe=(Resolve-Path -LiteralPath $PresentMon).Path
if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'b2a706bc6ad475749e3b7e3409263aa1e6906d45bdcf993f6dbc0f660188f1af') {throw 'Unexpected PresentMon binary'}
$signature=Get-AuthenticodeSignature -LiteralPath $exe
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Intel Corporation') {throw 'PresentMon signature verification failed'}
$client=Get-Process -Id $ClientProcessId
$start=$client.StartTime.ToUniversalTime()
if ($start.Ticks -ne $ExpectedStartUtc.ToUniversalTime().Ticks) {throw 'Client PID generation mismatch'}
$expected=(Resolve-Path -LiteralPath $ExpectedImage).Path
if ($client.Path -ne $expected -or [IO.Path]::GetFileName($expected) -ne 'DayZDiag_x64.exe') {throw 'Unexpected client executable'}
$dest=[IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $dest) {throw 'Capture output must be fresh'}
if ($dest.Contains('"')) {throw 'Unsupported quote in output path'}
New-Item -ItemType Directory -Path $dest | Out-Null
$session='Baltic_EV112_'+[guid]::NewGuid().ToString('N')
$csv=Join-Path $dest 'frames.csv'
$argsList=@('--process_id',[string]$ClientProcessId,'--output_file',('"'+$csv+'"'),
    '--qpc_time_ms','--delay','30','--timed','120','--terminate_after_timed',
    '--terminate_on_proc_exit','--session_name',$session,'--no_track_input','--no_console_stats')
$meta=[ordered]@{schema='ev112-presentmon-capture-v1';status='CAPTURE_PENDING_CONTEXT_VALIDATION';
    scenario=$Scenario;client_pid=$ClientProcessId;client_start_utc=$start.ToString('o');client_image=$expected;
    client_sha256=(Get-FileHash -LiteralPath $expected -Algorithm SHA256).Hash.ToLowerInvariant();
    presentmon_sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant();
    session=$session;warmup_s=30;measurement_s=120;started_utc=[datetime]::UtcNow.ToString('o');
    arguments=$argsList;focus_pause_scene_settings_etw_loss_verified=$false}
$meta | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $dest 'capture.json') -Encoding utf8
$collector=$null;$samples=[Collections.Generic.List[object]]::new();$timer=[Diagnostics.Stopwatch]::StartNew()
try {
    $collector=Start-Process -FilePath $exe -ArgumentList $argsList -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $dest 'stdout.log') -RedirectStandardError (Join-Path $dest 'stderr.log')
    while (-not $collector.HasExited) {
        if ($timer.Elapsed.TotalSeconds -gt 175) {throw 'Collector exceeded bounded capture duration'}
        $current=Get-Process -Id $ClientProcessId
        if ($current.StartTime.ToUniversalTime().Ticks -ne $start.Ticks) {throw 'Client process changed during capture'}
        $samples.Add([ordered]@{elapsed_s=$timer.Elapsed.TotalSeconds;working_set_bytes=$current.WorkingSet64;private_bytes=$current.PrivateMemorySize64;cpu_total_s=$current.TotalProcessorTime.TotalSeconds})
        Start-Sleep -Milliseconds 1000
        $collector.Refresh()
    }
    $collector.WaitForExit();$meta['collector_exit_code']=$collector.ExitCode
    if ($collector.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $csv)) {throw 'PresentMon did not produce a successful capture'}
    $meta['status']='CAPTURED_NOT_BENCHMARK_ACCEPTANCE'
} catch {
    $meta['status']='CAPTURE_FAILED';$meta['error']=$_.Exception.Message
    throw
} finally {
    if ($null -ne $collector -and -not $collector.HasExited) {$collector.Kill();$collector.WaitForExit()}
    $meta['finished_utc']=[datetime]::UtcNow.ToString('o')
    $meta['host_elapsed_s']=$timer.Elapsed.TotalSeconds
    $meta | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $dest 'capture.json') -Encoding utf8
    $samples | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $dest 'host-memory-cpu.json') -Encoding utf8
}
