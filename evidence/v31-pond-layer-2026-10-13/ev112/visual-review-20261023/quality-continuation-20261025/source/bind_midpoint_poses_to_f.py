from pathlib import Path
import hashlib,json,sys
import numpy as np
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;O=R/'river-131-midpoint-b'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/terrain'))
from package_visual_forest_ev112 import source_arrays,compiled_arrays,read_pbo
import package_visual_forest_ev112 as reader
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
src=R/'stage-rectangle-f/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';pbo=Path('P:/Mods/@DayZ_Baltic_EV112_RectangleF/Addons/narva_trial.pbo')
assert sha(src)=='6e649b72bf4ec6789a83050f21b7e5597de417e14f251f854728eb20d8b84bd8' and sha(pbo)=='4e5f909d2a27e9322299d751d2d54d67f5cc06700499d0498e533b5e1674ef38'
assert not (O/'f-compiled-poses.json').exists() and not (O/'f-pose-binding.json').exists()
s=source_arrays(src,2578725);_,_,entries=read_pbo(pbo);wrp=entries['baltic_trial.wrp'];assert hashlib.sha256(wrp).hexdigest()=='0139cd1a7ce360436e474fa6448470dfe93bf34a21229b6cf44f4e839af54126'
anchor=dict(id=int(s['ids'][0]),name=s['names'][s['mi'][0]],matrix=s['mat'][0]);c,backend=compiled_arrays(wrp,anchor)
def pilot_rows(x):
    mi=[i for i,n in enumerate(x['names']) if n.startswith('baltic_stream_pilot\\')]
    ix=np.flatnonzero(np.isin(x['mi'],mi));rows={}
    for i in ix:
        name=x['names'][x['mi'][i]];assert name not in rows
        rows[name]=dict(model=name,id=int(x['ids'][i]),matrix=x['mat'][i].tolist())
    assert len(rows)==62;return rows
before,after=pilot_rows(s),pilot_rows(c);assert before==after
u={x['model']:x for x in json.loads((R/'collision-overlap-u2/records.json').read_text())}
for name,row in after.items():assert np.array_equal(np.float32(row['matrix']),np.float32(u[name]['matrix'])),name
b=json.loads((O/'records.json').read_text());assert len(b)==27
for row in b:assert np.array_equal(np.float32(row['matrix']),np.float32(after[row['model']]['matrix'])),row['model']
records=list(after.values());(O/'f-compiled-poses.json').write_text(json.dumps(records,indent=2)+'\n')
proof=dict(status='F_WRP_62_POSES_BOUND_B27_EXACT',objects=len(c['ids']),pilot_poses=62,candidate_poses_exact=27,
    sources={str(p):sha(p) for p in (src,pbo,O/'records.json',R/'collision-overlap-u2/records.json',Path(reader.__file__),Path(__file__))},
    compiled_wrp_sha256=hashlib.sha256(wrp).hexdigest(),records_sha256=sha(O/'f-compiled-poses.json'),reader=backend,
    limits=['OPRW object table discovery is heuristic; hashes, anchor and all62source pilot poses constrain it.','No native collision or actor acceptance.'])
(O/'f-pose-binding.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='sources'},indent=2))
