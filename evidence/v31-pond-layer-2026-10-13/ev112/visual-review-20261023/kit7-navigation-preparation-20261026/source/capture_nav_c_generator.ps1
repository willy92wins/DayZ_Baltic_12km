param([Parameter(Mandatory=$true)][guid]$RunId,[Parameter(Mandatory=$true)][string]$ServerStartUtc,[Parameter(Mandatory=$true)][string]$GenerationDirectory,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
if(Test-Path -LiteralPath $OutputPath){throw 'Fresh generator identity required'}
$exe='C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/NavMeshGenerator/NavMeshGenerator_x64.exe'
$expectedHash='66935ce864436892247cd520ea2205c179d661e6390478ec35a2c304aa2ecbb7'
$candidates=@()
foreach($candidate in @(Get-CimInstance Win32_Process -Filter "Name='NavMeshGenerator_x64.exe'")) {
    $parent=Get-CimInstance Win32_Process -Filter "ProcessId=$($candidate.ParentProcessId)"
    if($parent -and $parent.CommandLine -and $parent.CommandLine.Contains('generate_navmesh_console.py') -and $parent.CommandLine.Contains($RunId.ToString()) -and $parent.CommandLine.Replace('\','/').Contains($GenerationDirectory.Replace('\','/'))) {
        $candidates+=@{child=$candidate;parent=$parent}
    }
}
if($candidates.Count -ne 1){throw 'Exactly one generator child of this run required'}
$g=$candidates[0].child;$parent=$candidates[0].parent
if(-not [StringComparer]::OrdinalIgnoreCase.Equals([IO.Path]::GetFullPath($exe),[IO.Path]::GetFullPath($g.ExecutablePath))){throw 'Generator executable mismatch'}
if((Get-FileHash -LiteralPath $g.ExecutablePath).Hash.ToLowerInvariant() -ne $expectedHash){throw 'Generator bytes changed'}
if($g.CreationDate.ToUniversalTime() -lt [DateTime]::Parse($ServerStartUtc).ToUniversalTime()){throw 'Generator predates run'}
function TextHash([string]$text){$hash=[Security.Cryptography.SHA256]::Create();try {return ([BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($text)))).Replace('-','').ToLowerInvariant()} finally {$hash.Dispose()}}
$data=[ordered]@{run_id=$RunId.ToString();pid=$g.ProcessId;created_utc=$g.CreationDate.ToUniversalTime().ToString('o');executable=$g.ExecutablePath;executable_sha256=$expectedHash;command_line_sha256=(TextHash $g.CommandLine);parent_pid=$parent.ProcessId;parent_created_utc=$parent.CreationDate.ToUniversalTime().ToString('o');parent_command_line_sha256=(TextHash $parent.CommandLine);parent_has_run_and_output=$true;observed_utc=[DateTimeOffset]::UtcNow.ToString('o')}
[IO.File]::WriteAllText($OutputPath,($data|ConvertTo-Json -Depth 4),[Text.UTF8Encoding]::new($false))
$data|ConvertTo-Json -Compress
