"""Continue the independently reviewed context gate after config-only rejection."""
from pathlib import Path
import json,subprocess,sys,time,hashlib,os
R=Path(__file__).parent;O=R/'kit7-context-unit-20261026';C=R/'kit7-forest-context-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
frozen=read(R/'kit7-package-review-20261026/accepted.json')['inputs'];assert frozen and all(sha(p)==h for p,h in frozen.items());O.mkdir(exist_ok=False)
frozen[str(Path(__file__))]=sha(__file__);(O/'inputs.json').write_text(json.dumps(frozen,indent=2)+'\n')
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONIOENCODING='utf-8')
stages=[('context',[sys.executable,'-I',str(R/'prepare_kit7_forest_context.py'),str(B),str(C)],1800)]
stages += [(n,[sys.executable,'-I',str(W/'tools/vegetation/run_visual_forest_gate_v31.py'),str(C),n],900) for n in ['g2g3_map','g8_agreement','g7_map']]
for label,args,budget in stages:
 began=time.time();timeout=False
 with (O/(label+'.stdout.log')).open('wb') as out,(O/(label+'.stderr.log')).open('wb') as err:
  try:p=subprocess.run(args,cwd=W,env=env,stdout=out,stderr=err,timeout=budget,creationflags=0x08000000);rc=p.returncode
  except subprocess.TimeoutExpired:rc=None;timeout=True
 same=all(sha(p)==h for p,h in frozen.items());result=dict(label=label,args=args,returncode=rc,seconds=time.time()-began,timeout=timeout,inputs_unchanged=same)
 (O/(label+'.receipt.json')).write_text(json.dumps(result,indent=2)+'\n');print(label,rc,flush=True)
 if rc!=0 or timeout or not same:raise SystemExit(1)
a=read(C/'g2g3_map.json')['summary'];b=read(C/'g8_agreement.json')['summary'];c=read(C/'g7_map.json')['summary']
assert a['G2']['verdict']==a['G3']['verdict']=='PASS' and b['judged_forest_windows']>0 and b['failed_windows']==0 and c['judged_bogs']>0 and c['failed_bogs']==0
result=dict(status='PASS_CONTEXT_GATES_BOUNDARY_PENDING',G2=a['G2'],G3=a['G3'],G8=b,G7=c,boundary_support=read(C/'inputs.json')['boundary_support_status'],boundary_pending=read(C/'inputs.json')['boundary_support_pending'],inputs_unchanged=True,limits=['Raster density/context only; source boundary support3727 remains unknown. No compiled/native/visual acceptance.'])
(O/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
