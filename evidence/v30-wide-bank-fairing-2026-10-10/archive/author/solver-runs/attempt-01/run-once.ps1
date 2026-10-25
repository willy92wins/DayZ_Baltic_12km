$ErrorActionPreference='Stop'
$w='E:\DayZ-Baltic-Build\v30-wide-bank-fairing-pilot-20261010'
$run="$w\author\solver-runs\attempt-01"
$python='C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe'
$script="$w\author\author_ev88q.py"
$candidate="$w\candidate-terrain.npz"
$authoring="$w\authoring.json"
$marker="$run\solver-attempt.started.json"
if(Test-Path -LiteralPath $marker){throw 'create-only marker exists; refusing repeat'}
if((Test-Path -LiteralPath $candidate) -or (Test-Path -LiteralPath $authoring)){throw 'candidate/receipt exists; refusing overwrite'}
$expected=Get-Content -LiteralPath "$run\pins.json" -Raw | ConvertFrom-Json
$verified=[ordered]@{}
foreach($prop in $expected.PSObject.Properties){$rel=$prop.Name; $path=Join-Path $w $rel; $actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant(); if($actual -ne $prop.Value){throw "pin mismatch $rel $actual != $($prop.Value)"}; $verified[$rel]=$actual}
$pre=Get-Content -LiteralPath "$w\author\preflight\preflight.json" -Raw | ConvertFrom-Json
if($pre.status -ne 'PREFLIGHT_READY_SOLVER_NOT_RUN' -or $pre.solver_invoked -ne $false){throw 'preflight not READY or solver already invoked'}
if($pre.plan_sha256 -ne $verified['plan.md']){throw 'preflight plan hash differs from pinned plan'}
$running=Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?\.exe$' -and $_.CommandLine -like '*author_ev88q.py*' -and $_.CommandLine -like '*--solve*' }
if($running){throw 'solver process already exists'}
$stamp=[DateTime]::UtcNow.ToString('o')
$fs=[System.IO.File]::Open($marker,[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
try{$bytes=[System.Text.Encoding]::UTF8.GetBytes((([ordered]@{status='ATTEMPT_STARTED_ONCE';started_utc=$stamp;pinned_sha256=$verified}|ConvertTo-Json -Depth 5)+"`n"));$fs.Write($bytes,0,$bytes.Length);$fs.Flush($true)}finally{$fs.Dispose()}
$started=[DateTime]::UtcNow.ToString('o')
& $python $script --solve 1> "$run\stdout.log" 2> "$run\stderr.log"
$exit=$LASTEXITCODE
$ended=[DateTime]::UtcNow.ToString('o')
$out=[ordered]@{status=if($exit -eq 0){'PROCESS_EXIT_0'}else{'PROCESS_NONZERO'};started_utc=$started;ended_utc=$ended;exit_code=$exit;pinned_sha256=$verified;stdout_path="$run\stdout.log";stderr_path="$run\stderr.log";candidate_exists=(Test-Path -LiteralPath $candidate);authoring_exists=(Test-Path -LiteralPath $authoring)}
$out | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$run\execution-receipt.json" -Encoding utf8
if($exit -ne 0){exit $exit}
