param([Parameter(Mandatory=$true)][string]$RunName,[Parameter(Mandatory=$true)][string]$ExpectedSha)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OPENBLAS_NUM_THREADS='1'
$taskRoot=$PSScriptRoot
$taskScript=Join-Path $taskRoot 'selector.py'
if($RunName -notmatch '^run-[0-9]+$'){throw 'Invalid run name'}
$taskOut=Join-Path $taskRoot $RunName
if(Test-Path -LiteralPath $taskOut){throw 'Output already exists'}
if((Get-FileHash -LiteralPath $taskScript -Algorithm SHA256).Hash.ToLower() -ne $ExpectedSha){throw 'Selector source drift'}
[ordered]@{source=$taskScript;source_sha256=$ExpectedSha;started_utc=[DateTime]::UtcNow.ToString('o');output=$taskOut;policy='One execution; no solver or automatic retries'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot ($RunName+'.launch.json')) -Encoding utf8
$taskWatch=[Diagnostics.Stopwatch]::StartNew()
& 'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe' $taskScript --execute --pool 'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/crest-extension/quarantine-pool-v3/compound-pool.json' --output-dir $taskOut --progress-jsonl (Join-Path $taskOut 'progress.jsonl') *> (Join-Path $taskRoot ($RunName+'.console.log'))
$taskExit=$LASTEXITCODE
$taskFinalHash=(Get-FileHash -LiteralPath $taskScript -Algorithm SHA256).Hash.ToLower()
[ordered]@{exit_code=$taskExit;source_sha256=$taskFinalHash;source_unchanged=($taskFinalHash -eq $ExpectedSha);wall_seconds=$taskWatch.Elapsed.TotalSeconds;ended_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskRoot ($RunName+'.completion.json')) -Encoding utf8
Get-Content -LiteralPath (Join-Path $taskRoot ($RunName+'.console.log')) -Tail 2
exit $taskExit
