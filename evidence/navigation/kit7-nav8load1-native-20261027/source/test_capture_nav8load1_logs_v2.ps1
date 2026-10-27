$ErrorActionPreference='Stop'
$root='E:/DayZ-Baltic-Build/shape-repair-20261025'
$scriptPath=Join-Path $root 'capture_kit7_nav8load1_logs.ps1'
$out=Join-Path $root 'kit7-nav8load1-consumer-20261027/capture-controls-v2'
if(Test-Path -LiteralPath $out){throw 'Fresh capture controls directory required'}
New-Item -ItemType Directory -Path $out | Out-Null
$parseTokens=$null;$parseErrors=$null
[void][System.Management.Automation.Language.Parser]::ParseFile($scriptPath,[ref]$parseTokens,[ref]$parseErrors)
if($parseErrors.Count){throw 'Current capture does not parse'}
[void][System.Management.Automation.Language.Parser]::ParseFile((Join-Path $root 'kit7-nav8load1-code-review-20261027/rejected-capture.ps1'),[ref]$parseTokens,[ref]$parseErrors)
if(-not $parseErrors.Count){throw 'Broken capture negative control unexpectedly parses'}
$brokenErrors=$parseErrors.Count
$cases=@();$identity=Get-Process -Id $PID
foreach($caseName in @('success','abort_end_zero','stale_config','stale_engine','wrong_creation','partial_config','existing_output')) {
 $folder=Join-Path $out $caseName
 New-Item -ItemType Directory -Path $folder | Out-Null
 $engine=Join-Path $folder 'engine.log';$config=Join-Path $folder 'config.log'
 [IO.File]::WriteAllText($engine,('HEADER'+[Environment]::NewLine+'END;607'+[Environment]::NewLine))
 [IO.File]::WriteAllText($config,('HEADER'+[Environment]::NewLine+'END;9'+[Environment]::NewLine))
 $stamp=$identity.StartTime.ToUniversalTime()
 if($caseName -eq 'abort_end_zero'){[IO.File]::WriteAllText($engine,('END;0'+[Environment]::NewLine))}
 if($caseName -eq 'stale_config'){(Get-Item -LiteralPath $config).LastWriteTimeUtc=$stamp.AddHours(-1)}
 if($caseName -eq 'stale_engine'){(Get-Item -LiteralPath $engine).LastWriteTimeUtc=$stamp.AddHours(-1)}
 if($caseName -eq 'wrong_creation'){$stamp=$stamp.AddHours(-1)}
 if($caseName -eq 'partial_config'){[IO.File]::WriteAllText($config,('HEADER'+[Environment]::NewLine+'C;partial'+[Environment]::NewLine))}
 if($caseName -eq 'existing_output'){[IO.File]::WriteAllText((Join-Path $folder 'runtime.log'),'preserve')}
 $ErrorActionPreference='Continue'
 & powershell -NoProfile -ExecutionPolicy Bypass -File $scriptPath -ServerProcessId $identity.Id -ExpectedStartUtc $stamp.ToString('o') -EngineLog $engine -ConfigEngineLog $config -OutputDirectory $folder 1> (Join-Path $folder 'stdout.log') 2> (Join-Path $folder 'stderr.log')
 $code=$LASTEXITCODE
 $ErrorActionPreference='Stop'
 $binding=Join-Path $folder 'log-binding.json'
 $positive=$caseName -in @('success','abort_end_zero')
 if($positive) {
  if($code -ne 0 -or -not(Test-Path -LiteralPath $binding)){throw "Expected complete capture: $caseName"}
  $row=Get-Content -LiteralPath $binding -Raw|ConvertFrom-Json
  if($row.pid -ne $identity.Id -or $row.sha256 -ne (Get-FileHash -LiteralPath $engine).Hash.ToLowerInvariant() -or $row.config_sha256 -ne (Get-FileHash -LiteralPath $config).Hash.ToLowerInvariant()){throw 'Captured binding mismatch'}
 } elseif($code -eq 0 -or (Test-Path -LiteralPath $binding)){throw "Invalid capture accepted: $caseName"}
 $cases+=[pscustomobject]@{name=$caseName;passed=$true;exit_code=$code;capture_only=$true}
}
$report=[ordered]@{status='PASS_REAL_POWERSHELL_CAPTURE_CONTROLS';capture_sha256=(Get-FileHash -LiteralPath $scriptPath).Hash.ToLowerInvariant();rejected_parser_errors=$brokenErrors;cases=$cases;limits='Synthetic logs on current owned PowerShell process; no DayZ acceptance.'}
[IO.File]::WriteAllText((Join-Path (Split-Path $out) 'capture-controls.json'),($report|ConvertTo-Json -Depth 6),[Text.UTF8Encoding]::new($false))
$report|ConvertTo-Json -Depth 6
