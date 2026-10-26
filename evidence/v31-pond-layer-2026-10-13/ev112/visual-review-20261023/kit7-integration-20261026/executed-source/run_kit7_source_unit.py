"""Bounded one-shot source writer, independent reader and full forest consumer."""
from pathlib import Path
import subprocess,json,time,sys,os,hashlib
R=Path(__file__).parent;O=R/'kit7-source-unit-20261026';O.mkdir(exist_ok=False)
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018');S=R/'stage-kit7-fc-20261026'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
gate=read(R/'kit7-stage-review-20261026/accepted.json');assert all(sha(p)==h for p,h in gate['inputs'].items())
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
stages=[('compose',[sys.executable,'-I',str(R/'stage_kit7_fc.py')],900),('readback',[sys.executable,'-I',str(R/'verify_kit7_fc_stage.py')],900),('forest',[sys.executable,'-I',str(W/'tools/vegetation/review_visual_forest_support_v31.py'),str(B),str(S),str(R/'pilot-kit7-fc-20261026'),str(R/'river-kit7-merged-byteexact-20261026')],1800)]
for label,args,limit in stages:
 began=time.time();timeout=False
 with (O/(label+'.stdout.log')).open('wb') as out,(O/(label+'.stderr.log')).open('wb') as err:
  try:q=subprocess.run(args,cwd=W,env=env,stdout=out,stderr=err,timeout=limit,creationflags=0x08000000);rc=q.returncode
  except subprocess.TimeoutExpired:rc=None;timeout=True
 result=dict(label=label,args=args,returncode=rc,timeout=timeout,seconds=time.time()-began)
 (O/(label+'.receipt.json')).write_text(json.dumps(result,indent=2)+'\n');print(label,rc,flush=True)
 if rc!=0 or timeout:
  if label=='forest' and rc==1 and (S/'forest-support-review-full.json').exists():
   d=read(S/'forest-support-review-full.json');result['forest_status']=d['status'];result['counts']=d['counts'];result['boundary_count']=d['boundary_pending']['count']
  (O/'stopped.json').write_text(json.dumps(result,indent=2)+'\n');raise SystemExit(1)
print('SOURCE_AND_FULL_FOREST_DONE',flush=True)
