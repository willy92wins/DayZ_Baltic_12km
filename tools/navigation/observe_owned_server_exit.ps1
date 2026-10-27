param(
    [Parameter(Mandatory=$true)][int]$TargetProcessId,
    [Parameter(Mandatory=$true)][string]$ExpectedStartUtc,
    [Parameter(Mandatory=$true)][string]$ExpectedExecutable,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [ValidateRange(1,18300)][int]$MaxSeconds=7500,
    [ValidateRange(100,5000)][int]$IntervalMilliseconds=5000
)
# Read-only observer. The caller proves MCP ownership; this script never manages it.
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $OutputDirectory){throw 'Fresh observer directory required'}
[void][IO.Directory]::CreateDirectory($OutputDirectory)
$process=$null
$writer=$null
$terminal=[ordered]@{status='OBSERVER_ERROR';process_id=$TargetProcessId;start_utc=$null;exit_code=$null;observed_utc=$null;error=$null}
$scriptHash=$null
$timer=[Diagnostics.Stopwatch]::StartNew()
try {
    $scriptHash=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $process=Get-Process -Id $TargetProcessId -ErrorAction Stop
    $retainedHandle=$process.Handle
    $expected=[datetime]::Parse($ExpectedStartUtc).ToUniversalTime()
    $actual=$process.StartTime.ToUniversalTime()
    if([Math]::Abs(($actual-$expected).TotalMilliseconds) -gt 2){throw 'IDENTITY_MISMATCH'}
    $actualExecutable=$process.MainModule.FileName
    if(-not [StringComparer]::OrdinalIgnoreCase.Equals([IO.Path]::GetFullPath($ExpectedExecutable),[IO.Path]::GetFullPath($actualExecutable))){throw 'EXECUTABLE_MISMATCH'}
    if($retainedHandle -eq [IntPtr]::Zero){throw 'No retained process handle'}
    $terminal.start_utc=$actual.ToString('o')
    $begin=[ordered]@{status='ATTACHED';process_id=$TargetProcessId;start_utc=$actual.ToString('o');executable=$actualExecutable;executable_sha256=(Get-FileHash -LiteralPath $actualExecutable -Algorithm SHA256).Hash.ToLowerInvariant();observer_sha256=$scriptHash;utc=[DateTimeOffset]::UtcNow.ToString('o');local=[DateTimeOffset]::Now.ToString('o');time_zone=[TimeZoneInfo]::Local.Id;handle_retained=$true;mutation_attempted=$false;max_seconds=$MaxSeconds}
    $writer=[IO.StreamWriter]::new((Join-Path $OutputDirectory 'samples.jsonl'),$false,[Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $OutputDirectory 'attached.json'),($begin|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
    while($timer.Elapsed.TotalSeconds -lt $MaxSeconds) {
        if($process.HasExited){break}
        try {
            $process.Refresh()
            $sample=[ordered]@{utc=[DateTimeOffset]::UtcNow.ToString('o');elapsed_s=$timer.Elapsed.TotalSeconds;process_id=$TargetProcessId;start_utc=$actual.ToString('o');cpu_total_s=$process.TotalProcessorTime.TotalSeconds;working_set_bytes=$process.WorkingSet64;private_bytes=$process.PrivateMemorySize64;handles=$process.HandleCount;threads=$process.Threads.Count}
            $writer.WriteLine(($sample|ConvertTo-Json -Compress));$writer.Flush()
        } catch {if(-not $process.HasExited){throw}}
        $remaining=[int][Math]::Max(1,($MaxSeconds-$timer.Elapsed.TotalSeconds)*1000)
        if($process.WaitForExit([Math]::Min($IntervalMilliseconds,$remaining))){break}
    }
    if($process.HasExited) {
        $code=$process.ExitCode
        if($null -eq $code -or $code -isnot [int]){throw 'Exit code unavailable'}
        $terminal.status='EXIT_OBSERVED';$terminal.exit_code=$code
    } else {$terminal.status='OBSERVER_TIMEOUT'}
} catch {$terminal.error=$_.Exception.Message}
finally {
    $terminal.observed_utc=[DateTimeOffset]::UtcNow.ToString('o')
    $terminal['observer_sha256']=$scriptHash
    if($null -ne $writer){$writer.Dispose()}
    if($null -ne $process){$process.Dispose()}
    [IO.File]::WriteAllText((Join-Path $OutputDirectory 'terminal.json'),($terminal|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
}
$terminal|ConvertTo-Json -Compress
if($terminal.status -eq 'OBSERVER_ERROR'){exit 1}
if($terminal.status -eq 'OBSERVER_TIMEOUT'){exit 2}
