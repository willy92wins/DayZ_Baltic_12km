param([string]$Path)
$ErrorActionPreference='Stop'
$stream=[IO.File]::Open($Path,[IO.FileMode]::Create,[IO.FileAccess]::Write,[IO.FileShare]::None)
try {
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes("BALTIC_SYNTHETIC_CAPTURE_SMOKE`ncolumns;smoke`n")
    $stream.Write($bytes,0,$bytes.Length);$stream.Flush()
    Start-Sleep -Seconds 2
} finally {$stream.Dispose()}
Start-Sleep -Seconds 2
[IO.File]::AppendAllText($Path,"END;120;150`n",[Text.UTF8Encoding]::new($false))
Start-Sleep -Seconds 5
