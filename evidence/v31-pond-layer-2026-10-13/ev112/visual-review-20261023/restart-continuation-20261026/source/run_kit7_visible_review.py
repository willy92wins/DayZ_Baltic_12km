from pathlib import Path
import subprocess,json,hashlib,sys,time,os
R=Path(__file__).parent;C=R/'river-kit7-a-on-f-20261026';O=R/'river-kit7-visible-run-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
assert not O.exists() and not (C/'visible-relief-review.json').exists();O.mkdir()
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
inputs=json.loads((R/'river-kit7-saved-review-run-20261026/inputs.json').read_text());inputs[str(W/'tools/terrain/review_visible_pilot_relief_v31.py')]=sha(W/'tools/terrain/review_visible_pilot_relief_v31.py')
assert inputs=={p:sha(p) for p in inputs}
args=[sys.executable,'-I',str(W/'tools/terrain/review_visible_pilot_relief_v31.py'),str(C),str(B),'--base-terrain',str(R/'rectangle-pilot-f-merged/terrain-buried.npz'),'--expected-base-sha256','caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc']
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');start=time.time();timeout=False
with (O/'stdout.log').open('wb') as out,(O/'stderr.log').open('wb') as err:
 try:q=subprocess.run(args,cwd=W,env=env,stdout=out,stderr=err,timeout=600,creationflags=0x08000000|0x00004000);code=q.returncode
 except subprocess.TimeoutExpired:code=None;timeout=True
same=inputs=={p:sha(p) for p in inputs};data=dict(returncode=code,timeout=timeout,seconds=time.time()-start,inputs_unchanged=same,inputs=inputs,limits='Saved MLOD and sampled visibility only. No engine, continuous occlusion or aesthetic acceptance.')
(O/'receipt.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps({k:v for k,v in data.items() if k!='inputs'},indent=2));assert same
raise SystemExit(2 if timeout else code)
