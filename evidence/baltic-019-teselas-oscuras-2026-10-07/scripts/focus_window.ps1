# Gives a window the foreground (DayZ for the BALTIC-019 focus test) and records the previous foreground window, or
# restores a recorded window. Uses AttachThreadInput to the current foreground thread so SetForegroundWindow is
# honoured; no keystrokes are sent.
param([int]$ClientPid = 0, [string]$State, [switch]$Restore)
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class FW {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool attach);
  [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
}
"@
function Set-Front([IntPtr]$target) {
  $fg = [FW]::GetForegroundWindow()
  $p = 0
  $fgThread = [FW]::GetWindowThreadProcessId($fg, [ref]$p)
  $me = [FW]::GetCurrentThreadId()
  $attached = $false
  if ($fgThread -ne 0 -and $fgThread -ne $me) { $attached = [FW]::AttachThreadInput($me, $fgThread, $true) }
  [void][FW]::BringWindowToTop($target)
  $ok = [FW]::SetForegroundWindow($target)
  if ($attached) { [void][FW]::AttachThreadInput($me, $fgThread, $false) }
  Start-Sleep -Milliseconds 400
  return @($ok, ([FW]::GetForegroundWindow() -eq $target))
}
if ($Restore) {
  $prev = [IntPtr][Int64](Get-Content $State)
  if (-not [FW]::IsWindow($prev)) { "previous window gone: $prev"; exit 1 }
  $r = Set-Front $prev
  "{0:HH:mm:ss} restore set={1} foreground_is_previous={2}" -f (Get-Date), $r[0], $r[1]
} else {
  $dz = (Get-Process -Id $ClientPid).MainWindowHandle
  $prev = [FW]::GetForegroundWindow()
  $pp = 0
  [void][FW]::GetWindowThreadProcessId($prev, [ref]$pp)
  [string][Int64]$prev | Out-File -FilePath $State -Encoding ascii
  $r = Set-Front $dz
  "{0:HH:mm:ss} focus set={1} foreground_is_dayz={2} previous={3} ({4})" -f (Get-Date), $r[0], $r[1], $prev, (Get-Process -Id $pp -ErrorAction SilentlyContinue).ProcessName
}
