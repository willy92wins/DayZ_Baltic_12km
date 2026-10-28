"""Materialize only the selected input contract. No deployment or DayZ lifecycle."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).resolve().parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'water-query-b1-offline-20261028';O.mkdir(exist_ok=False)
sys.path.insert(0,str(W/'tools/quality'))
import water_query_diag_b1_ev112 as d
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
start=time.monotonic()
selected=R/'dry-road-native-discriminators-a-20261028/selected-points.json'
original=R/'dry-road-full-native-20261028/probe/result.json'
assert sha(selected)=='14be579b0fd5a83f821422818b227a6100f0d224af999c352c68ed9b282e30c9'
assert sha(original)=='e717a124c38ff61b4af932793541ab78b7dfb703aea946d497c246b59ee33390'
paths=[selected,original,W/'plans/ev112-water-query-discriminator-b1-20261028.md',W/'tools/quality/water_query_diag_b1_ev112.py',W/'tools/quality/test_water_query_diag_b1_ev112.py',W/'missions/BalticWaterQueryB1.BalticTrial/init.c',Path(__file__)]
pins={str(p):sha(p) for p in paths}
points=d.source_points(json.loads(selected.read_bytes()),json.loads(original.read_bytes()))
csv=d.csv_for(points);d.check_csv(csv,points)
(O/'points.csv').write_bytes(csv.encode('utf-8'))
(O/'points.json').write_text(json.dumps(points,indent=2)+'\n',encoding='utf-8')
# Child tests have a bounded timeout. Capture actual interpreter/tree and output.
command=[sys.executable,'-I',str(W/'tools/quality/test_water_query_diag_b1_ev112.py')]
test=subprocess.run(command,cwd=W,capture_output=True,text=True,timeout=120,creationflags=0x08000000)
(O/'tests.log').write_text(test.stdout+test.stderr,encoding='utf-8')
assert test.returncode==0 and 'Ran 22 tests' in test.stderr
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
bootstrap="import runpy,sys;sys.path.insert(0,"+repr(str(validator.parent))+");sys.argv=["+repr(str(validator))+","+repr(str(W/'missions/BalticWaterQueryB1.BalticTrial'))+"];runpy.run_path(sys.argv[0],run_name='__main__')"
lint=subprocess.run([sys.executable,'-I','-c',bootstrap],cwd=W,capture_output=True,text=True,timeout=120,creationflags=0x08000000)
(O/'lint.json').write_text(lint.stdout,encoding='utf-8');(O/'lint-stderr.txt').write_text(lint.stderr,encoding='utf-8')
l=json.loads(lint.stdout);assert lint.returncode==0 and l['status']=='PASS' and l['info']['files_scanned']==1 and not l['errors'] and not l['warnings']
assert all(sha(p)==h for p,h in pins.items())
assert time.monotonic()-start<120
result=dict(status='OFFLINE_CONTRACT_ONLY_NOT_READY_FOR_DAYZ',points=len(points),rounds=3,native_rows_expected=345,tests=22,lint_files=1,seconds=time.monotonic()-start,interpreter=sys.executable,worktree=str(W),inputs=pins,csv_sha256=sha(O/'points.csv'),points_sha256=sha(O/'points.json'),limits=['No engine compilation or native B1 measurements.','No deployment, lifecycle binder or admission gate prepared.','Source2658 remains FAIL; product and collision B2 remain unresolved.'])
(O/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))
