# Focus probe for BALTIC-019: once per -Every seconds, saves a PrintWindow (PW_RENDERFULLCONTENT) frame of the DayZ
# client window at half size and logs whether DayZ holds the foreground. Stops at -Seconds, or 30 s after the first
# focus period that lasted at least 10 s ends. Read-only towards the game: no input is sent, no window is moved.
param([int]$ClientPid, [string]$OutDir, [int]$Seconds = 300, [double]$Every = 1.0)
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class PWP {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
}
"@
[void][PWP]::SetProcessDPIAware()
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$dz = (Get-Process -Id $ClientPid).MainWindowHandle
$log = Join-Path $OutDir 'log.csv'
"time,focused,file" | Out-File -FilePath $log -Encoding ascii
$start = Get-Date
$focusStart = $null
$doneAt = $null
while (((Get-Date) - $start).TotalSeconds -lt $Seconds) {
  $t = Get-Date
  $focused = ([PWP]::GetForegroundWindow() -eq $dz)
  if ($focused -and -not $focusStart) { $focusStart = $t }
  if (-not $focused -and $focusStart) {
    if (($t - $focusStart).TotalSeconds -ge 10 -and -not $doneAt) { $doneAt = $t.AddSeconds(30) }
    $focusStart = $null
  }
  $r = New-Object PWP+RECT
  [void][PWP]::GetWindowRect($dz, [ref]$r)
  $w = $r.R - $r.L; $h = $r.B - $r.T
  $name = '{0:HHmmss_fff}_{1}.jpg' -f $t, $(if ($focused) { 'F' } else { 'U' })
  try {
    $bmp = New-Object System.Drawing.Bitmap $w, $h
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    [void][PWP]::PrintWindow($dz, $hdc, 2)
    $g.ReleaseHdc($hdc)
    $half = New-Object System.Drawing.Bitmap $bmp, ([int]($w / 2)), ([int]($h / 2))
    $half.Save((Join-Path $OutDir $name), [System.Drawing.Imaging.ImageFormat]::Jpeg)
    $half.Dispose(); $g.Dispose(); $bmp.Dispose()
  } catch { $name = 'capture_failed' }
  "{0:HH:mm:ss.fff},{1},{2}" -f $t, $focused, $name | Out-File -FilePath $log -Append -Encoding ascii
  if ($doneAt -and (Get-Date) -ge $doneAt) { break }
  $sleep = $Every - ((Get-Date) - $t).TotalSeconds
  if ($sleep -gt 0) { Start-Sleep -Milliseconds ([int]($sleep * 1000)) }
}
"done {0:HH:mm:ss}" -f (Get-Date) | Out-File -FilePath $log -Append -Encoding ascii
