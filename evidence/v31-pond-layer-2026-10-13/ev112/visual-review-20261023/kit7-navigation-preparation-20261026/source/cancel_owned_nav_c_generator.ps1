param([Parameter(Mandatory=$true)][guid]$RunId,[Parameter(Mandatory=$true)][string]$IdentityPath,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $OutputPath){throw 'Fresh cancellation receipt required'}
$i=Get-Content -LiteralPath $IdentityPath -Raw|ConvertFrom-Json
if($i.run_id -ne $RunId.ToString() -or -not $i.parent_has_run_and_output){throw 'Wrong generator ownership receipt'}
if($i.executable_sha256 -ne '66935ce864436892247cd520ea2205c179d661e6390478ec35a2c304aa2ecbb7'){throw 'Unrecognized generator'}
$process=Get-Process -Id $i.pid -ErrorAction SilentlyContinue
$state='ALREADY_GONE'
if($null -ne $process) {
    try {
        $handle=$process.Handle
        if([Math]::Abs(($process.StartTime.ToUniversalTime()-[DateTime]::Parse($i.created_utc).ToUniversalTime()).TotalMilliseconds) -gt 2){throw 'Generator PID reused'}
        if(-not [StringComparer]::OrdinalIgnoreCase.Equals($process.MainModule.FileName,$i.executable)){throw 'Wrong executable'}
        if((Get-FileHash -LiteralPath $i.executable).Hash.ToLowerInvariant() -ne $i.executable_sha256){throw 'Generator executable drift'}
        $c=Get-CimInstance Win32_Process -Filter "ProcessId=$($i.pid)"
        $hash=[Security.Cryptography.SHA256]::Create()
        try {$commandHash=([BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($c.CommandLine)))).Replace('-','').ToLowerInvariant()} finally {$hash.Dispose()}
        if($commandHash -ne $i.command_line_sha256){throw 'Generator command line drift'}
        $process.Kill()
        if(-not $process.WaitForExit(10000)){throw 'Own generator did not terminate'}
        $state='CANCELLED_EXACT_OWN_GENERATOR'
    } finally {$process.Dispose()}
}
$result=[ordered]@{status=$state;run_id=$RunId.ToString();pid=$i.pid;observed_utc=[DateTimeOffset]::UtcNow.ToString('o');dayz_process_touched=$false}
[IO.File]::WriteAllText($OutputPath,($result|ConvertTo-Json -Depth 3),[Text.UTF8Encoding]::new($false))
$result|ConvertTo-Json -Compress
