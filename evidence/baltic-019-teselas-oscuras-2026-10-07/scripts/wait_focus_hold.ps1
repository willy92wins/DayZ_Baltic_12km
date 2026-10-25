# Waits until a window has held the foreground continuously for -Hold seconds (or -Timeout passes), sampling every
# 250 ms, and prints the timeline of foreground changes with the owning process. Read-only.
param([int]$ClientPid, [int]$Hold = 15, [int]$Timeout = 180)
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class FG4 {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
}
"@
$dz = (Get-Process -Id $ClientPid).MainWindowHandle
$start = Get-Date
$since = $null
$last = ''
$cpu0 = $null
while (((Get-Date) - $start).TotalSeconds -lt $Timeout) {
  $fg = [FG4]::GetForegroundWindow()
  $p = 0
  [void][FG4]::GetWindowThreadProcessId($fg, [ref]$p)
  $name = if ($fg -eq $dz) { 'DayZ' } else { (Get-Process -Id $p -ErrorAction SilentlyContinue).ProcessName }
  if ($name -ne $last) { "{0:HH:mm:ss.f} foreground -> {1}" -f (Get-Date), $name; $last = $name }
  if ($fg -eq $dz) {
    if (-not $since) { $since = Get-Date; $cpu0 = (Get-Process -Id $ClientPid).CPU }
    if (((Get-Date) - $since).TotalSeconds -ge $Hold) {
      "{0:HH:mm:ss.f} DayZ held the foreground {1} s; client cpu in that time {2:N2} s" -f (Get-Date), $Hold, ((Get-Process -Id $ClientPid).CPU - $cpu0)
      exit 0
    }
  } else { $since = $null }
  Start-Sleep -Milliseconds 250
}
"{0:HH:mm:ss} timeout: DayZ never held the foreground {1} s" -f (Get-Date), $Hold
exit 1
