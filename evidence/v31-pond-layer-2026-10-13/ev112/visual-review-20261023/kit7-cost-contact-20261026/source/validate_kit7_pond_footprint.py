"""One isolated burial/footprint pass; rejects any unreviewed terrain change."""
from pathlib import Path
import subprocess,json,hashlib,sys,time,os,shutil
import numpy as np
R=Path(__file__).parent;K=R/'river-kit7-midpoint-a-20261026';F=R/'rectangle-pilot-f-merged';O=R/'river-kit7-merged-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
read=lambda p:json.loads(Path(p).read_text())
assert read(R/'kit7-midpoint-saved-review-20261026/receipt.json')['status']=='PASS_SAVED_KIT7_COLLISION'
assert sha(K/'terrain.npz')=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
assert sha(F/'terrain-buried.npz')=='caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc'
layers=read(R/'river-kit7-a-run-20261026/layers-and-cover-v2.json');assert all(layers['checks'].values())
assert layers['layers']['envelope.npy']['changed_cells']==36 and layers['layers']['cover.npy']['changed_cells']==0
for name in ['terrain.npz','cover.npy','envelope.npy']:assert sha(K/name)==sha(R/'river-kit7-a-on-f-20261026'/name)
paths=[Path(__file__),W/'plans/ev112-kit7-water-integration-20261026.md',W/'tools/water/bury_edges_v31.py',W/'tools/water/pond_footprint_v31.py',K/'terrain.npz',K/'cover.npy',K/'envelope.npy',F/'terrain-buried.npz',F/'bury-work/fp0/footprint.npz',F/'bury-work/fp0/footprint-report.json',R/'river-kit7-a-run-20261026/layers-and-cover-v2.json']
inputs={str(p):sha(p) for p in paths};O.mkdir(exist_ok=False)
(O/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
for name in ['cover.npy','envelope.npy']:shutil.copyfile(K/name,O/name)
args=[sys.executable,'-I',str(W/'tools/water/bury_edges_v31.py'),str(K/'terrain.npz'),str(F/'terrain-buried.npz'),str(O/'cover.npy'),str(O/'envelope.npy'),str(F/'bury-work/fp0/footprint-report.json'),str(O/'terrain-buried.npz'),str(O/'bury-work'),str(O/'bury-report.json')]
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
start=time.time();timeout=False
with (O/'stdout.log').open('wb') as out,(O/'stderr.log').open('wb') as err:
 try:q=subprocess.run(args,env=env,stdout=out,stderr=err,timeout=900,creationflags=0x08000000|0x00004000);code=q.returncode
 except subprocess.TimeoutExpired:timeout=True;code=None
same=all(sha(p)==h for p,h in inputs.items())
(O/'execution.json').write_text(json.dumps(dict(returncode=code,timeout=timeout,seconds=time.time()-start,inputs_unchanged=same,args=args),indent=2)+'\n')
assert code==0 and not timeout and same
bury=read(O/'bury-report.json');last=max((O/'bury-work').glob('fp[0-9]*'),key=lambda p:int(p.name[2:]))
old,new=np.load(F/'bury-work/fp0/footprint.npz'),np.load(last/'footprint.npz')
checks={k:bool(np.array_equal(old[k],new[k],equal_nan=True)) for k in ['plane','field','visible']}
checks.update(envelope_matches_reviewed_candidate=bool(np.array_equal(new['env_plane'],np.load(K/'envelope.npy'),equal_nan=True)),no_bury_changes=bury['changed_vs_input']==0,no_new_exposed=not bury['final_new_exposed'],terrain_byte_exact=sha(O/'terrain-buried.npz')==sha(K/'terrain.npz'),footprint_bound_to_exact_terrain=read(last/'footprint-report.json')['terrain_sha256']==sha(K/'terrain.npz'))
result=dict(status='POND_GEOMETRY_EXACT_KIT7_PENDING_INTEGRATION' if all(checks.values()) else 'FAIL',checks=checks,last_footprint=str(last/'footprint.npz'),footprint_sha256=sha(last/'footprint.npz'),terrain_sha256=sha(O/'terrain-buried.npz'),inputs_unchanged=same,limits=['Only pond geometry and unchanged buried terrain; no kit WRP/forest/native/visual acceptance.'])
(O/'merge-verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));raise SystemExit(0 if all(checks.values()) else 1)
