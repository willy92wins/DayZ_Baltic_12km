"""Independent retained-record, forest-ground and disjoint-domain verification."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct,sys
import numpy as np
from scipy.ndimage import binary_dilation
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
Q=Path('E:/DayZ-Baltic-Build/qc-council-20261024');B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sys.path[:0]=[str(W/'tools/navigation'),str(W/'tools/vegetation')]
from waterway_common import sample
from prune_visual_forest_v31 import prefix,objects
S=R/'stage-combined';rep=json.loads((S/'stage-report.json').read_text());delta=json.loads((S/'object-delta.json').read_text());shifts={q['id']:q for q in delta['shifts']};excluded={q['id']:q for q in delta['excluded_forest']}
models=json.loads(Path(rep['forest_reference']['path']).read_text())['models']
src=Q/'stage-s3/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';dst=S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
A=np.load(Q/'road-merged-s3/terrain-buried.npz');F=np.load(R/'terrain-free-final-merged/terrain-buried.npz');C=np.load(R/'river-131-compact-a/terrain.npz');H=np.load(R/'combined-merged/terrain-buried.npz')['heights']
free=F['heights']!=A['heights'];river=C['heights']!=A['heights']
assert not (binary_dilation(free,structure=np.ones((5,5),bool))&river).any(),'changed native faces/edge neighbourhoods overlap'
assert np.array_equal(H[free],F['heights'][free]) and np.array_equal(H[river],C['heights'][river]) and np.array_equal(H[~(free|river)],A['heights'][~(free|river)])
oldkit=Counter((r['model'].lower().replace('/','\\').lstrip('\\'),struct.pack('<12f',*r['matrix'])) for r in json.loads((B/'water-fix-b/kit/kit-records.json').read_text()) if r['site']=='131.0-0')
seen=set();dropped=[];retained=0;maxerror=0.;appended=[]
with src.open('rb') as f,dst.open('rb') as g:
    before=prefix(f);after=prefix(g);end=24+2048*2048*4
    assert before[:24]==after[:24] and before[end:]==after[end:] and np.array_equal(np.frombuffer(after,'<f4',2048*2048,24).reshape(2048,2048),H[::-1])
    iterator=objects(g)
    for ident,name,raw in objects(f):
        key=(name,raw[:48])
        if oldkit[key]:oldkit[key]-=1;dropped.append(ident);continue
        if ident in excluded:assert name in models;continue
        actual_id,actual_name,actual=next(iterator);assert (ident,name)==(actual_id,actual_name)
        if ident not in shifts:assert actual==raw
        else:
            assert raw[:40]+raw[44:]==actual[:40]+actual[44:] and name in models
            m=np.array(struct.unpack_from('<12f',raw));root=m[9:]-m[:9].reshape(3,3).T@models[name]['bc'];x=np.array([root[0]+200000]);z=np.array([root[2]])
            expected=m[10]+float(sample(H.astype(float),x,z)[0]-sample(A['heights'].astype(float),x,z)[0])
            value=struct.unpack_from('<f',actual,40)[0];error=abs(value-expected);maxerror=max(maxerror,error)
            assert error<=2*abs(float(np.spacing(np.float32(max(abs(value),abs(expected))))))+1e-7;seen.add(ident)
        retained+=1
    for ident,name,raw in iterator:appended.append((ident,name,raw[:48]))
assert not sum(oldkit.values()) and len(dropped)==74 and seen==set(shifts) and len(appended)==27
want=[r for r in json.loads((R/'combined-pilot/records.json').read_text()) if r['site']=='131.0-0']
assert [(n,m) for _,n,m in appended]==[(r['model'].lower(),struct.pack('<12f',*r['matrix'])) for r in want]
assert retained+27==rep['object_count'] and len(set(i for i,_,_ in appended))==27
out=dict(status='INDEPENDENT_SOURCE_COMPOSITION_PASS',retained_objects=retained,unchanged_objects=retained-len(seen),forest_y_verified=len(seen),old_kit_removed=len(dropped),forest_removed=len(excluded),new_pilot_records=27,maximum_ground_delta_error_m=maxerror,source_wrp_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),wrp_sha256=hashlib.sha256(dst.read_bytes()).hexdigest(),native_domains_separated_two_vertices=True,consumer_sha256=hashlib.sha256(Path(sample.__code__.co_filename).read_bytes()).hexdigest(),limits=['Delta byte parity and independent native ground only; existing boundary support and engine acceptance remain pending.'])
(S/'independent-verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
