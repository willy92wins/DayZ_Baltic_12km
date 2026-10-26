"""Bounded independent saved-geometry audit; no candidate mutation or deployment."""
from pathlib import Path
import subprocess,hashlib,json,sys,time,os,datetime
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
C=R/'river-kit7-a-on-f-20261026';O=R/'river-kit7-saved-review-20261026';L=R/'river-kit7-saved-review-run-20261026'
assert not O.exists() and not L.exists();L.mkdir()
source=W/'tools/water/review_continuous_stream_pilot_v31.py'
base=R/'rectangle-pilot-f-merged/terrain-buried.npz';fp=R/'rectangle-pilot-f-merged/bury-work/fp0/footprint.npz'
sha=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
paths=[source,C/'author-report.json',C/'terrain.npz',C/'kit-7-surfaces.npz',base,fp]+sorted((C/'source').rglob('*.p3d'))
inputs={str(p):sha(p) for p in paths}
assert inputs[str(base)]=='caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc'
assert inputs[str(fp)]=='95f7a26304e88c726679ec69ef076bb149ec1f1f8bdf4a6cd1e83e40f3b6be83'
args=[sys.executable,'-I',str(source),str(C),str(B),'--output',str(O),'--base-terrain',str(base),'--base-footprint',str(fp),'--expected-base-sha256',inputs[str(base)],'--expected-footprint-sha256',inputs[str(fp)]]
(L/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
start=time.time();timed_out=False
with (L/'stdout.log').open('wb') as out,(L/'stderr.log').open('wb') as err:
 try:q=subprocess.run(args,cwd=W,env=env,stdout=out,stderr=err,timeout=600,creationflags=0x08000000|0x00004000);code=q.returncode
 except subprocess.TimeoutExpired:code=None;timed_out=True
same=inputs=={str(p):sha(p) for p in paths}
receipt=dict(args=args,returncode=code,timeout=timed_out,seconds=time.time()-start,inputs_unchanged=same,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),limits='Saved MLOD only; T bound, full footprint/forest/build/native and visual acceptance remain separate.')
(L/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));assert same
raise SystemExit(2 if timed_out else code)
