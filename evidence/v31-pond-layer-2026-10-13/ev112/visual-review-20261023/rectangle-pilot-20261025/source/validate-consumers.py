from pathlib import Path
import hashlib,json,shutil,subprocess,sys
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
base=R/'guarded-relief-batch-e-merged';source=R/'rectangle-pilot-f';out=R/'rectangle-pilot-f-merged';out.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((source/'report.json').read_text())['status']=='OFFLINE_CANDIDATE_PASS_PENDING_CONSUMERS'
for name in ('cover.npy','envelope.npy'):shutil.copyfile(base/name,out/name)
cmd=[sys.executable,'-I',str(W/'tools/water/bury_edges_v31.py'),str(source/'terrain.npz'),str(base/'terrain-buried.npz'),str(out/'cover.npy'),str(out/'envelope.npy'),str(base/'bury-work/fp0/footprint-report.json'),str(out/'terrain-buried.npz'),str(out/'bury-work'),str(out/'bury-report.json')]
with (out/'bury.log').open('w') as f:subprocess.run(cmd,cwd=W,check=True,stdout=f,stderr=subprocess.STDOUT)
assert np.array_equal(np.load(source/'terrain.npz')['heights'],np.load(out/'terrain-buried.npz')['heights']);bury=json.loads((out/'bury-report.json').read_text());assert bury['changed_vs_input']==0 and not bury['final_new_exposed']
old,new=np.load(base/'bury-work/fp0/footprint.npz'),np.load(out/'bury-work/fp0/footprint.npz')
assert old.files==new.files and all(np.array_equal(old[k],new[k],equal_nan=True) for k in old.files)
(out/'merge-verification.json').write_text(json.dumps(dict(status='WATER_FOOTPRINT_EXACT',bury_changes=0,terrain_sha256=sha(out/'terrain-buried.npz'),source_sha256=sha(source/'terrain.npz')),indent=2)+'\n')
cmd=[sys.executable,'-I',str(W/'tools/terrain/review_visual_roads_ev112.py'),str(B),str(R/'rectangle-pilot-f-roads'),'--terrain',str(out/'terrain-buried.npz'),'--expected-terrain-sha256',sha(out/'terrain-buried.npz')]
with (R/'rectangle-pilot-f-roads.log').open('w') as f:subprocess.run(cmd,cwd=W,check=True,stdout=f,stderr=subprocess.STDOUT)
print('Water footprint exact; road consumer finished successfully')
