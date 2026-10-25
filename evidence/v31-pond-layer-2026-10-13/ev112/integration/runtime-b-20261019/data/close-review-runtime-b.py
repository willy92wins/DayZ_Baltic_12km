"""Record the executor's explicit response to the actual independent R2 review."""
from pathlib import Path
import hashlib,json,subprocess,datetime
O=Path(__file__).parent;W=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
target=O/'build-review-closure-runtime-b.json';assert not target.exists()
response=read(O/'review-runtime-b-r2-response.json')
assert response['verdict'] in ('SOUND','SOUND-with-fixes') and response['critical_major_open']==0
raw=O/'review-runtime-b-r2.json';r=read(raw);run=read(O/'review-runtime-b-r2-run.json')
assert not r.get('is_error',True) and run['rc']==0 and response['raw_review_sha256']==sha(raw)
assert response['verdict'] in r['result']
dep=read(O/'deploy-runtime-b.json');binding=read(O/'review-runtime-b-r2-binding.json')
assert binding['deploy_sha256']==sha(O/'deploy-runtime-b.json')
assert all(binding[k]==dep[k] for k in ('world_sha256','water_sha256','terrain_sha256','footprint_sha256','compiled_wrp_sha256','forest_records_sha256'))
assert all(sha(p)==h for p,h in dep['evidence'].items())
for name,key in [('narva_trial.pbo','world_sha256'),('baltic_water_v30.pbo','water_sha256')]:assert sha(Path(dep['mod'])/'Addons'/name)==dep[key]
source=W/'tools/terrain/apply_engine_water_margins_v31.py';rel=source.relative_to(W).as_posix()
commit=subprocess.check_output(['git','log','-1','--format=%H','--',rel],cwd=W,text=True).strip();assert commit
blob=subprocess.check_output(['git','show',commit+':'+rel],cwd=W)
assert hashlib.sha256(blob.replace(b'\r\n',b'\n')).hexdigest()==hashlib.sha256(source.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
files=['review-runtime-b-r2.json','review-runtime-b-r2-run.json','review-runtime-b-r2-binding.json','review-runtime-b-r2-prompt.md','review-runtime-b-r2-response.json','deploy-runtime-b.json','capture-runtime-probe-runtime-b.py','capture-runtime-b-temporal.py','evaluate-runtime-probe-runtime-b.py','evaluate-water-temporal-runtime-b.py','prepare-runtime-b-followup.py','water-fix-b/terrain-closure.json']
evidence={str(O/p):sha(O/p) for p in files};evidence[str(source)]=sha(source)
result=dict(verdict=response['verdict'],critical_major_open=0,review_round=2,maximum_rounds=2,time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),raw_review=str(raw),raw_review_sha256=sha(raw),source_commit=commit,source_sha256=sha(source),deploy_sha256=sha(O/'deploy-runtime-b.json'),world_sha256=dep['world_sha256'],water_sha256=dep['water_sha256'],terrain_sha256=dep['terrain_sha256'],minor_responses=response['responses'],ready_for_server_probe=True,server_probe='NOT_RUN_ON_THIS_PACKAGE',personal_view='PREPARED_NOT_ACCEPTED',evidence=evidence,limits=response['limits'])
target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('verdict','critical_major_open','source_commit','ready_for_server_probe')}))
