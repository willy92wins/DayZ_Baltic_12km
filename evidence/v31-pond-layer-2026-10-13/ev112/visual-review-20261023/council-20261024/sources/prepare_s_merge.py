from pathlib import Path
import sys,subprocess,json,hashlib,numpy as np
R=Path(__file__).parent;B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
WT=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
src=R/'road-candidate-s3/terrain.npz';ref=B/'road-merged-20261024-h';out=R/'road-merged-s3';out.mkdir(exist_ok=False)
proof=json.loads((R/'road-candidate-s3/independent-mesh.json').read_text());assert proof['status']=='OFFLINE_MESH_PASS'
assert hashlib.sha256(src.read_bytes()).hexdigest() in proof['inputs'].values()
q=B/'visual-merged-20261024-b'
for name in ('cover.npy','envelope.npy'):
    assert (q/name).is_file();(out/name).write_bytes((q/name).read_bytes())
cmd=[sys.executable,'-I',str(WT/'tools/water/bury_edges_v31.py'),str(src),str(ref/'terrain-buried.npz'),str(out/'cover.npy'),str(out/'envelope.npy'),str(ref/'bury-work/fp0/footprint-report.json'),str(out/'terrain-buried.npz'),str(out/'bury-work'),str(out/'bury-report.json')]
subprocess.run(cmd,check=True)
bury=json.loads((out/'bury-report.json').read_text());assert bury['changed_vs_input']==0 and not bury['final_new_exposed']
assert np.array_equal(np.load(src)['heights'],np.load(out/'terrain-buried.npz')['heights'])
old,new=np.load(ref/'bury-work/fp0/footprint.npz'),np.load(out/'bury-work/fp0/footprint.npz')
assert old.files==new.files and all(np.array_equal(old[k],new[k],equal_nan=True) for k in old.files)
(out/'merge-verification.json').write_text(json.dumps(dict(status='WATER_FOOTPRINT_EXACT',bury_changes=0,arrays=old.files,terrain_sha256=hashlib.sha256((out/'terrain-buried.npz').read_bytes()).hexdigest(),sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (src,ref/'terrain-buried.npz',q/'cover.npy',q/'envelope.npy')}),indent=2))
print('WATER_FOOTPRINT_EXACT')
