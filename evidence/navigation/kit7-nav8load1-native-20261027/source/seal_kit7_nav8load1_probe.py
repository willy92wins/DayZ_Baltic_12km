from pathlib import Path
import hashlib,json,sys,subprocess
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-nav8load1-consumer-20261027';V=R/'kit7-nav8load1-code-review-20261027'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
assert not (D/'frozen.json').exists()
review=read(V/'response.json');assert not review['is_error'] and not review.get('permission_denials') and 'claude-fable-5-1' in review['modelUsage']
assert read(V/'completion.json')['returncode']==0
adjudication=read(V/'adjudication.json');assert adjudication['status']=='ACCEPTED_AFTER_REVIEW'
assert set(read(V/'source-hashes.json'))<=set(adjudication['inputs'])
for p,h in adjudication['inputs'].items():assert sha(p)==h,p
parse_command="$tokens=$null;$errors=$null;[void][System.Management.Automation.Language.Parser]::ParseFile('E:/DayZ-Baltic-Build/shape-repair-20261025/capture_kit7_nav8load1_logs.ps1',[ref]$tokens,[ref]$errors);if($errors.Count){exit 1};Write-Output 'POWERSHELL_PARSE_PASS'"
p=subprocess.run(['powershell','-NoProfile','-Command',parse_command],capture_output=True)
(D/'capture-parse.log').write_bytes(p.stdout+p.stderr)
assert p.returncode==0 and b'POWERSHELL_PARSE_PASS' in p.stdout
cap=read(D/'capture-controls.json');assert cap['status']=='PASS_REAL_POWERSHELL_CAPTURE_CONTROLS' and cap['capture_sha256']==sha(R/'capture_kit7_nav8load1_logs.ps1') and len(cap['cases'])==7 and all(c['passed'] for c in cap['cases'])
prep=read(D/'runtime-preparation.json');mission=Path(prep['mission'])
assert (mission/'init.c').read_text()==(W/'missions/BalticKit7Nav8Load1.BalticTrial/init.c').read_text().replace('@PROBE_ID@',prep['probe_id'])
testdir=W/'tools/navigation'
command=[sys.executable,'-I','-c','import sys,unittest;sys.path.insert(0,'+repr(str(testdir))+');unittest.main(module="test_nav8_load1_config_ev112")']
p=subprocess.run(command,capture_output=True);(D/'consumer-controls.stdout.log').write_bytes(p.stdout);(D/'consumer-controls.stderr.log').write_bytes(p.stderr)
assert p.returncode==0 and b'Ran 8 tests' in p.stderr and b'OK' in p.stderr
coord=R/'orchestrate_kit7_nav8load1_probe.js'
for name in ('coordinator-controls.json','command-flow-controls.json'):
 report=read(D/name);assert report['coordinator_sha256']==sha(coord) and all(x['passed'] for x in report['cases'])
assert read(D/'script-validator.json')['status']=='PASS' and read(D/'script-validator.json')['info']['files_scanned']==1
assert sha(mission/'queries.csv')==sha(D/'queries.csv')
ref=read(D/'reference.json')
for p,h in ref['inputs'].items():assert sha(p)==h,p
stock=read(D/'vanilla-packages.json')
assert set(str(p.resolve()).casefold() for p in Path(stock['directory']).glob('*.pbo'))==set(str(Path(p).resolve()).casefold() for p in stock['packages'])
paths=list(map(Path,adjudication['inputs']))+[Path(__file__),V/'adjudication.json',V/'response.json',V/'completion.json',D/'runtime-preparation.json',D/'vanilla-packages.json',D/'script-validator.json',D/'consumer-controls.stderr.log',D/'coordinator-controls.json',D/'command-flow-controls.json',mission/'init.c',mission/'queries.csv',D/'queries.csv',D/'reference.json',D/'capture-controls.json',D/'capture-parse.log',D/'contract-parity.json',D/'deployment-parity.json',W/'tools/navigation/observe_owned_server_exit.ps1',R/'verify_c_orderly_close.py',R/'capture_owned_server_identity.ps1',R/'copy_owned_server_rpt.ps1',R/'record_nav_c_event.ps1']
inputs={**ref['inputs'],**{str(p):sha(p) for p in paths}}
assert read(D/'contract-parity.json')['status']=='EXACT_607_CONTRACT_AND_GRAPH_BODY_PRESERVED'
assert read(D/'deployment-parity.json')['status']=='EXACT_DEPLOYED_CONFIG_ONLY_DELTA'
write(D/'frozen.json',dict(**prep,inputs=inputs))
engine=Path('E:/SteamLibrary/steamapps/common/DayZ Exp/DayZDiag_x64.exe')
assert sha(engine)=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'
write(D/'deployment.json',dict(packages=prep['packages'],inputs={**stock['packages'],**prep['packages'],str(engine):sha(engine)}))
write(V/'accepted.json',dict(status='ACCEPTED_AFTER_REVIEW',inputs={str(D/'frozen.json'):sha(D/'frozen.json'),str(D/'deployment.json'):sha(D/'deployment.json'),**inputs}))
print(json.dumps(dict(status='SEALED_LOAD1_CONFIG_AND_NATIVE607',probe_id=prep['probe_id'],inputs=len(inputs),stock_packages=len(stock['packages']))))
