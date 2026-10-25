param(
    [Parameter(Mandatory=$true)][int]$ServerProcessId,
    [Parameter(Mandatory=$true)][string]$ExpectedStartUtc,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [int]$Samples = 170,
    [string]$EngineLogPath = ''
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $OutputPath) { throw 'Fresh measurement output required' }
$expected = [DateTime]::Parse($ExpectedStartUtc).ToUniversalTime()
$timer = [Diagnostics.Stopwatch]::StartNew()
$writer = [IO.StreamWriter]::new($OutputPath, $false, [Text.UTF8Encoding]::new($false))
try {
    for ($sample = 0; $sample -lt $Samples; $sample++) {
        $observed = Get-Process -Id $ServerProcessId -ErrorAction Stop
        $actualStart = $observed.StartTime.ToUniversalTime()
        if ([Math]::Abs(($actualStart - $expected).TotalMilliseconds) -gt 2) { throw 'Process identity changed' }
        $observed.Refresh()
        $row = [ordered]@{
            sample = $sample; utc = [DateTime]::UtcNow.ToString('o'); elapsed_s = $timer.Elapsed.TotalSeconds
            process_id = $ServerProcessId; start_utc = $actualStart.ToString('o')
            cpu_total_s = $observed.TotalProcessorTime.TotalSeconds
            working_set_bytes = $observed.WorkingSet64; private_bytes = $observed.PrivateMemorySize64
            threads = $observed.Threads.Count; handles = $observed.HandleCount
        }
        if ($EngineLogPath -and (Test-Path -LiteralPath $EngineLogPath)) {
            # Freeze a bounded byte snapshot. Get-Content -Tail can observe appended
            # lines while reading; the phase marker must remain one complete string.
            $logStream = [IO.File]::Open($EngineLogPath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
            try {
                $snapshotLength = $logStream.Length
                $tailLength = [int][Math]::Min(8192, $snapshotLength)
                [void]$logStream.Seek($snapshotLength - $tailLength, [IO.SeekOrigin]::Begin)
                $tailBytes = [byte[]]::new($tailLength)
                $tailRead = $logStream.Read($tailBytes, 0, $tailLength)
                $tailText = [Text.Encoding]::UTF8.GetString($tailBytes, 0, $tailRead)
                $lastNewline = $tailText.LastIndexOf("`n")
                if ($lastNewline -ge 0) {
                    $completeLines = $tailText.Substring(0, $lastNewline).TrimEnd("`r", "`n").Split("`n")
                    $row['engine_last_line'] = [string]$completeLines[-1].TrimEnd("`r")
                }
                else { $row['engine_last_line'] = '' }
            }
            finally { $logStream.Dispose() }
        }
        $writer.WriteLine(($row | ConvertTo-Json -Compress))
        $writer.Flush()
        if ($sample -lt $Samples - 1) { Start-Sleep -Milliseconds 1000 }
    }
} finally { $writer.Dispose() }
Write-Output "Recorded $Samples read-only process samples: $OutputPath"
