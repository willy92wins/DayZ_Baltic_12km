param(
    [Parameter(Mandatory=$true)][int]$ServerProcessId,
    [Parameter(Mandatory=$true)][string]$ExpectedStartUtc,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [Parameter(Mandatory=$true)][string]$EngineLogPath,
    [ValidateRange(10,600)][int]$MaxSeconds=600
)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $OutputPath){throw 'Fresh host capture required'}
$expected=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
$timer=[Diagnostics.Stopwatch]::StartNew()
$writer=[IO.StreamWriter]::new($OutputPath,$false,[Text.UTF8Encoding]::new($false))
$count=0
$ended=$false
try {
    while($timer.Elapsed.TotalSeconds -lt $MaxSeconds) {
        $process=Get-Process -Id $ServerProcessId -ErrorAction Stop
        $actualStart=$process.StartTime.ToUniversalTime()
        if([Math]::Abs(($actualStart-$expected).TotalMilliseconds) -gt 2){throw 'Process identity changed'}
        $process.Refresh()
        $last=''
        $readUnavailable=$false
        if(Test-Path -LiteralPath $EngineLogPath) {
            $stream=$null
            try {
                $stream=[IO.File]::Open($EngineLogPath,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
                $size=$stream.Length
                $tail=[int][Math]::Min(8192,$size)
                [void]$stream.Seek($size-$tail,[IO.SeekOrigin]::Begin)
                $buffer=[byte[]]::new($tail)
                $read=$stream.Read($buffer,0,$tail)
                $text=[Text.Encoding]::UTF8.GetString($buffer,0,$read)
                $newline=$text.LastIndexOf("`n")
                if($newline -ge 0){$last=[string]($text.Substring(0,$newline).TrimEnd("`r","`n").Split("`n")[-1].TrimEnd("`r"))}
            } catch [IO.IOException] {
                # The engine can briefly hold an exclusive writer; preserve the
                # host sample with no marker. Coverage is judged by the reader.
                $last=''
                $readUnavailable=$true
            } finally {if($null -ne $stream){$stream.Dispose()}}
        }
        $row=[ordered]@{sample=$count;utc=[DateTime]::UtcNow.ToString('o');elapsed_s=$timer.Elapsed.TotalSeconds;process_id=$ServerProcessId;start_utc=$actualStart.ToString('o');cpu_total_s=$process.TotalProcessorTime.TotalSeconds;working_set_bytes=$process.WorkingSet64;private_bytes=$process.PrivateMemorySize64;engine_last_line=$last;engine_read_unavailable=$readUnavailable}
        $writer.WriteLine(($row|ConvertTo-Json -Compress));$writer.Flush();$count++
        if($last -match '^END;120;[0-9.eE+-]+$'){$ended=$true;break}
        Start-Sleep -Milliseconds 500
    }
} finally {$writer.Dispose()}
if(-not $ended){throw 'Engine END120 not observed before bounded timeout'}
Write-Output "Captured $count samples through END120; consumer validation still required."
