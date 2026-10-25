# Read-only foreground sampling from before launch until this client exits.
# No screenshots, input, window movement or foreground changes.
param([Parameter(Mandatory=$true)][string]$Out, [int]$Seconds=1500)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $Out){throw 'Fresh log required'}
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class BalticFocus {
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
}
"@
'utc,client_pid,window_exists,foreground_is_client,minimized' | Set-Content -LiteralPath $Out -Encoding ASCII
$end=(Get-Date).AddSeconds($Seconds)
$seen=$null
while((Get-Date) -lt $end){
    # Dedicated server and client share the same image. The sealed launcher's
    # observed client has -connect=127.0.0.1, whereas its server has -server.
    $clientRecords=@(Get-CimInstance Win32_Process -Filter "Name='DayZDiag_x64.exe'" |
        Where-Object { $_.CommandLine -match '(?i)(?:^|\s)-connect=127\.0\.0\.1(?:\s|$)' })
    $clients=@($clientRecords | ForEach-Object { Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue })
    if($seen){$clients=@($clients | Where-Object Id -eq $seen)}
    if($seen -and $clients.Count -eq 0){break}
    if($clients.Count -gt 1){throw 'Ambiguous client; observer stopped'}
    $clientId=0; $hasWindow=$false; $focused=$false; $minimized=$false
    if($clients.Count -eq 1){
        $clientId=$clients[0].Id; $seen=$clientId
        $window=$clients[0].MainWindowHandle
        $hasWindow=$window -ne [IntPtr]::Zero
        if($hasWindow){
            $focused=[BalticFocus]::GetForegroundWindow() -eq $window
            $minimized=[BalticFocus]::IsIconic($window)
        }
    }
    '{0},{1},{2},{3},{4}' -f [DateTime]::UtcNow.ToString('o'),$clientId,$hasWindow,$focused,$minimized | Add-Content -LiteralPath $Out -Encoding ASCII
    Start-Sleep -Milliseconds 1000
}
