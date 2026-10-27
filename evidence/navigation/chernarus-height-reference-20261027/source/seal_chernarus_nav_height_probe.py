from pathlib import Path
import hashlib,json,sys,subprocess
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'chernarus-nav-height-reference-20261027';V=R/'chernarus-nav-height-code-review-20261027'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
assert not (D/'frozen.json').exists()
review=read(V/'response.json');assert not review['is_error'] and not review.get('permission_denials') and 'claude-fable-5-1' in review['modelUsage']
assert read(V/'completion.json')['returncode']==0
adjudication=read(V/'adjudication.json');assert adjudication['status']=='ACCEPTED_AFTER_REVIEW'
for p,h in adjudication['inputs'].items():assert sha(p)==h,p
prep=read(D/'runtime-preparation.json');mission=Path(prep['mission'])
assert (mission/'init.c').read_text()==(W/'missions/BalticChernarusNavHeightRef.ChernarusPlus/init.c').read_text().replace('@PROBE_ID@',prep['probe_id'])
assert sha(mission/'anchors.csv')==sha(D/'anchors.csv')
testdir=W/'tools/navigation'
command=[sys.executable,'-I','-c','import sys,unittest;sys.path.insert(0,'+repr(str(testdir))+');unittest.main(module="test_chernarus_nav_height_reference")']
p=subprocess.run(command,capture_output=True);(D/'consumer-controls.stdout.log').write_bytes(p.stdout);(D/'consumer-controls.stderr.log').write_bytes(p.stderr)
assert p.returncode==0 and b'Ran 18 tests' in p.stderr and b'OK' in p.stderr
coord=R/'orchestrate_chernarus_nav_height_probe.js'
for name in ('coordinator-controls.json','command-flow-controls.json'):
 report=read(D/name);assert report['coordinator_sha256']==sha(coord) and all(x['passed'] for x in report['cases'])
assert read(D/'script-validator.json')['status']=='PASS' and read(D/'script-validator.json')['info']['files_scanned']==1
stock=read(D/'vanilla-packages.json')
assert set(str(p.resolve()).casefold() for p in Path(stock['directory']).glob('*.pbo'))==set(str(Path(p).resolve()).casefold() for p in stock['packages'])
paths=list(map(Path,adjudication['inputs']))+[Path(__file__),V/'adjudication.json',V/'response.json',V/'completion.json',D/'runtime-preparation.json',D/'anchors.json',D/'anchors.csv',D/'extent-check.json',D/'vanilla-packages.json',D/'script-validator.json',D/'consumer-controls.stderr.log',D/'coordinator-controls.json',D/'command-flow-controls.json',mission/'init.c',mission/'anchors.csv',W/'tools/navigation/observe_owned_server_exit.ps1',R/'verify_c_orderly_close.py',R/'capture_owned_server_identity.ps1',R/'copy_owned_server_rpt.ps1',R/'record_nav_c_event.ps1',W/'tools/navigation/verify_kit7_nav_ev112.py']
inputs={str(p):sha(p) for p in paths}
write(D/'frozen.json',dict(**prep,inputs=inputs))
write(D/'deployment.json',dict(packages=prep['packages'],inputs={**stock['packages'],**prep['packages']}))
write(V/'accepted.json',dict(status='ACCEPTED_AFTER_REVIEW',inputs={str(D/'frozen.json'):sha(D/'frozen.json'),str(D/'deployment.json'):sha(D/'deployment.json'),**inputs}))
print(json.dumps(dict(status='SEALED_REFERENCE_ONLY',probe_id=prep['probe_id'],inputs=len(inputs),stock_packages=len(stock['packages']))))
