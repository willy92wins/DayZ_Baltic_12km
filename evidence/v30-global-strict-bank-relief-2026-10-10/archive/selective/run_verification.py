"""Single frozen EV87-S full consumer run, preserving result and execution receipt."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
D=Path(__file__).resolve().parent;EV=D.parent;ROOT=EV.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={D/'verify_selective.py':'224ff346f237f066a3b244a9bc6920c0c4a35c246f96202978f466b2197fcc25',
D/'candidate-terrain.npz':'8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b',
D/'integration-receipt.json':'0f97b30f4bba7df93a593f1adf2b3ef040719bf4f96380e8d0d049f1f5c38a52',
D/'fixtures-report.json':'a4597b244b1a87a0179be6b9ba457c9dbfee974560f0bfe14ee588ac21fa72c3',
D/'preflight-report.json':'8c37709c6710b420c3dc75d7612c5e975604c1f82d0452e27c3e2681b4471b57',
EV/'review-independent/incremental-conflict-inventory.json':'7fc8d2f77e8fd79ce49897a253ae8ed60944e5218b80260f7ed4a1a312e64d16'}
for p,s in pins.items():assert sha(p)==s,('Pinned input changed',p)
assert json.loads((D/'fixtures-report.json').read_text())['status']=='PASS_EV87_S_FIXTURES'
assert json.loads((D/'preflight-report.json').read_text())['status']=='PASS_EV87_S_PREFLIGHT'
report=D/'selective-review.json';receipt=D/'execution-receipt.json';log=D/'full-run.log'
assert not report.exists() and not receipt.exists() and not (D/'_consumer-scratch').exists()
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010';S=ROOT/'v30-narva-dry-bank-relief-20261010'
args={'receipt':D/'integration-receipt.json','candidate':D/'candidate-terrain.npz',
'source-b':B/'candidate/terrain.npz','source-ev79':S/'candidate/terrain.npz',
'source-constraints':S/'constraints.npz','prior-constraints':ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz',
'plane':S/'candidate/plane.npy','visible-field':S/'candidate/visible-field.npy',
'wrp':B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp',
'deploy':B/'deploy.json','bounds':ROOT/'v30-low-water-components-20261009/compiled-instance-bounds.json',
'models':ROOT/'v30-native-terminal-finish-20261009/package/water/temp/baltic_water_v30',
'workspace':Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290'),
'report':report,'scratch':D/'_consumer-scratch'}
cmd=[sys.executable,str(D/'verify_selective.py')]
for key,value in args.items():cmd.extend(['--'+key,str(value)])
start=time.monotonic();out={'status':'RUNNING','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'command':cmd,'pins':{str(p):s for p,s in pins.items()},'timeout_seconds':900}
receipt.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'RUNNING','started_utc':out['started_utc'],'report':str(report)}),flush=True)
try:
 with log.open('w',encoding='utf-8') as stream:
  proc=subprocess.run(cmd,env={**os.environ,'OPENBLAS_NUM_THREADS':'1','PYTHONUTF8':'1','PYTHONDONTWRITEBYTECODE':'1'},
      stdout=stream,stderr=subprocess.STDOUT,timeout=900)
 out['child_exit_code']=proc.returncode
 data=json.loads(report.read_text(encoding='utf-8')) if report.exists() else {}
 out['report_status']=data.get('status');out['report_sha256']=sha(report) if report.exists() else None
 out['pins_unchanged']=all(sha(p)==s for p,s in pins.items())
 out['status']='PASS_EXECUTION' if proc.returncode==0 and data.get('status')=='PASS_INCREMENTAL_NONREGRESSION' and out['pins_unchanged'] else 'FAIL_EXECUTION'
except Exception as exc:
 out.update(status='ERROR_EXECUTION',error=repr(exc))
finally:
 out['seconds']=time.monotonic()-start;out['log_sha256']=sha(log)
 receipt.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:out[k] for k in ('status','report_status','report_sha256','seconds') if k in out}),flush=True)
sys.exit(0 if out['status']=='PASS_EXECUTION' else 1)
