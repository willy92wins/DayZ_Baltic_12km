# Logs, every few seconds, how much of the DayZ client window is visible (25 sample points, top-level window under each
# point) and how much CPU the client process used since the previous sample. Read-only: no window is moved or focused.
param([int]$ClientPid, [string]$Out, [int]$Seconds = 900, [int]$Every = 5)
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class W3 {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(POINT p);
  [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr h, uint f);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
}
"@
$proc = Get-Process -Id $ClientPid
$dz = $proc.MainWindowHandle
$prev = $proc.CPU
$inv = [System.Globalization.CultureInfo]::InvariantCulture
"time,visible_points_of_25,iconic,foreground_is_dayz,client_cpu_pct_of_one_core,window_rect_l;t;r;b" | Out-File -FilePath $Out -Encoding utf8
$end = (Get-Date).AddSeconds($Seconds)
while ((Get-Date) -lt $end) {
  Start-Sleep -Seconds $Every
  try { $proc = Get-Process -Id $ClientPid -ErrorAction Stop } catch { "{0:HH:mm:ss},client_gone" -f (Get-Date) | Out-File -FilePath $Out -Append -Encoding utf8; break }
  $c = $proc.CPU
  $r = New-Object W3+RECT; [void][W3]::GetWindowRect($dz, [ref]$r)
  $v = 0
  foreach ($fx in 0.1,0.3,0.5,0.7,0.9) { foreach ($fy in 0.1,0.3,0.5,0.7,0.9) {
    $pt = New-Object W3+POINT; $pt.X = [int]($r.L + $fx*($r.R-$r.L)); $pt.Y = [int]($r.T + $fy*($r.B-$r.T))
    if ([W3]::GetAncestor([W3]::WindowFromPoint($pt), 2) -eq $dz) { $v++ } } }
  [string]::Format($inv, "{0:HH:mm:ss},{1},{2},{3},{4:0.0},{5};{6};{7};{8}", (Get-Date), $v, [W3]::IsIconic($dz), ([W3]::GetForegroundWindow() -eq $dz), (100*($c-$prev)/$Every), $r.L, $r.T, $r.R, $r.B) | Out-File -FilePath $Out -Append -Encoding utf8
  $prev = $c
}
