from pathlib import Path
import hashlib, json, sys, subprocess
import numpy as np

B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/terrain'))
import build_surface_v30 as surface
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
T=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')
P=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
assert sha(T)=='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6'
assert sha(P)=='d59dcdb908b4381a456629fb080a9769147b6fb1a3e321a6423bc931a0fb8803'
source=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/data/layers')
files=sorted(source.glob('s_*_lco.png'));assert len(files)==1024
fingerprints={p.name:sha(p) for p in files}
provenance=[]
for folder in ['v30-v12/surface','v30-v11/surface','v30-smoothing-pilot-20261007/surface-dry-18']:
 root=Path('E:/DayZ-Baltic-Build')/folder
 same=sum(sha(root/'layers'/name)==value for name,value in fingerprints.items())
 provenance.append(dict(root=str(root),exact_satellite_tiles=same,settings=json.loads((root/'surface.json').read_text())))
plane=surface.read_water_plane(P,sha(P));assert np.array_equal(plane,np.load(P),equal_nan=True)
controls=['valid_field_byte_identity']
def reject(name,path,digest):
 try:surface.read_water_plane(path,digest)
 except ValueError:controls.append(name)
 else:raise AssertionError(name)
reject('wrong_hash_rejected',P,'0'*64)
reject('missing_hash_rejected',P,None)
reject('missing_path_rejected',None,sha(P))
fixtures=B/'fixtures';fixtures.mkdir(exist_ok=False)
for name,a in [('wrong_shape',np.zeros((3,3))),('integer_type',np.zeros((2047,2047),np.int16)),('infinity',np.full((2047,2047),np.inf)),('all_missing',np.full((2047,2047),np.nan))]:
 path=fixtures/(name+'.npy');np.save(path,a);reject(name+'_rejected',path,sha(path))
run=subprocess.run([sys.executable,str(W/'tools/terrain/build_surface_v30.py'),str(T),str(B/'invalid-parent-output'),'--water-plane',str(P),'--water-plane-sha256','0'*64],capture_output=True,text=True,timeout=30)
assert run.returncode!=0 and not (B/'invalid-parent-output').exists()
controls.append('parent_rejects_before_pool_or_output')
report=dict(status='PASS_INPUT_CONTRACT',inputs={str(p):sha(p) for p in [T,P,W/'tools/terrain/build_surface_v30.py']},provenance=provenance,controls=controls,source_satellite_fingerprints=fingerprints)
(B/'inputs.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],provenance=[{'root':p['root'],'exact_satellite_tiles':p['exact_satellite_tiles']} for p in provenance],controls=controls)))
