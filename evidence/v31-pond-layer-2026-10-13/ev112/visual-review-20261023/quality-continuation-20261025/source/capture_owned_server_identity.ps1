param(
 [Parameter(Mandatory=$true)][int]$ServerProcessId,
 [Parameter(Mandatory=$true)][string]$ExpectedStartUtc,
 [Parameter(Mandatory=$true)][string]$ExpectedMission,
 [Parameter(Mandatory=$true)][string]$RunId,
 [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $OutputPath){throw 'Fresh identity output required'}
$process=Get-Process -Id $ServerProcessId -ErrorAction Stop
$created=$process.StartTime.ToUniversalTime()
$expected=[DateTime]::Parse($ExpectedStartUtc,[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()
if([Math]::Abs(($created-$expected).TotalMilliseconds) -gt 2){throw 'Process creation identity changed'}
$info=Get-CimInstance Win32_Process -Filter ("ProcessId="+$ServerProcessId)
$options=[ordered]@{}
foreach($name in @('mod','mission','config','profiles','port')) {
 $pattern='(?i)"?[-]'+$name+'=(?:"([^"]*)"|([^"\s]*))'
 $found=[regex]::Matches($info.CommandLine,$pattern)
 if($found.Count -ne 1){throw ('Missing or repeated process option '+$name)}
 $options[$name]=$found[0].Groups[1].Value+$found[0].Groups[2].Value
}
if([IO.Path]::GetFullPath($options.mission) -ine [IO.Path]::GetFullPath($ExpectedMission)){throw 'Mission identity changed'}
if(-not(Test-Path -LiteralPath (Join-Path $options.mission 'init.c'))){throw 'Mission init.c missing'}
$hasServer=[regex]::IsMatch($info.CommandLine,'(?i)(?:^|\s)"?-server(?:"|\s|$)')
if(-not $hasServer){throw 'Process is not dedicated server'}
$mods=@($options.mod.Split(';') | Where-Object {$_})
$packageHashes=[ordered]@{}
foreach($mod in $mods) {
 $addon=Join-Path $mod 'Addons'
 $pbos=@(Get-ChildItem -LiteralPath $addon -File -Filter '*.pbo')
 if(-not $pbos.Count){throw 'Loaded mod has no PBO files'}
 foreach($pbo in $pbos){$packageHashes[$pbo.FullName]=(Get-FileHash -LiteralPath $pbo.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$sha=[Security.Cryptography.SHA256]::Create()
try{$commandHash=[BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($info.CommandLine))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
$result=[ordered]@{run_id=$RunId;pid=$ServerProcessId;created_utc=$created.ToString('o');mission=[IO.Path]::GetFileName($options.mission);mission_path=$options.mission;mission_sha256=(Get-FileHash -LiteralPath (Join-Path $options.mission 'init.c') -Algorithm SHA256).Hash.ToLowerInvariant();executable=$info.ExecutablePath;executable_file_sha256=(Get-FileHash -LiteralPath $info.ExecutablePath -Algorithm SHA256).Hash.ToLowerInvariant();host_raw_command_line_sha256=$commandHash;server_config=$options.config;server_config_sha256=(Get-FileHash -LiteralPath $options.config -Algorithm SHA256).Hash.ToLowerInvariant();profiles=$options.profiles;port=$options.port;mods=$mods;package_hashes=$packageHashes;navmesh_data_server=[regex]::IsMatch($info.CommandLine,'(?i)-startNavmeshDataServer(?:"|\s|$)');client_started=$false;limits=@('Process identity and loaded -mod directories inspected on host. Client absence must also be checked against MCP run manifest.','Bridge binding/version must be appended from actual MCP bridge_status, never inferred here.')}
[IO.File]::WriteAllText($OutputPath,($result|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
[pscustomobject]@{status='HOST_PROCESS_IDENTITY_CAPTURED';run_id=$RunId;process_id=$ServerProcessId;mission=$result.mission;package_count=$packageHashes.Count;host_raw_command_line_sha256=$commandHash}|ConvertTo-Json

