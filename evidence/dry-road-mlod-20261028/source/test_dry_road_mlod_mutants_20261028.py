"""One bounded run: original positive plus byte mutants of the saved real MLOD."""
import os,time
START=time.monotonic()
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/quality'))
import verify_dry_road_mlod_ev112 as c
import water_constraint_diagnostic_ev112 as meter
O=R/'dry-road-mlod-mutants-20261028';O.mkdir(exist_ok=False)
meter.STARTED=START;meter.MAX_SECONDS=300;stop=meter.bounded(O)
def put(blob,offset,value):struct.pack_into('<f',blob,offset,float(value))
def main():
    source=R/'pilot-kit7-fc-20261026/source/baltic_stream_pilot/cs_kit_118_0000.p3d'
    target=R/'dry-road-mlod-candidate-r2-20261028/source/baltic_stream_pilot/cs_kit_118_0000.p3d'
    receipt=json.loads((R/'dry-road-mlod-consumer-20261028/report.json').read_bytes())
    assert receipt['status']=='MLOD_OFFLINE_VERIFIED'
    old=np.load(R/'pilot-visible-surface-extraction-20261028/models/cs_kit_118_0000.npz')['source_grid']
    grid=np.load(R/'dry-bed-road-candidate-20261028/kit-118-candidate.npz')['grid'][:len(old)]
    origin=np.array([8262.,7.,8934.]);initial={str(p):c.sha(p) for p in (source,target,Path(c.__file__),Path(__file__))}
    assert initial[str(source)]=='bbf4d5e40dfcb3bf5216981f10cbf21db681d403ea51c4e20676956289207c5a'
    assert initial[str(target)]=='d13069d5ec2816cdacc90891a83e5f92f517c4c33703380d534d3f7538baddef'
    positive=c.check_saved(source,source,old,origin)
    header,lods,blobs=c.load(target);raw=target.read_bytes();count=old.size//3
    base=[len(header)]
    for b in blobs[:-1]:base.append(base[-1]+len(b))
    visual=lods[0];geo=lods[1]
    face_start=base[0]+28+16*len(visual.points)+12*len(visual.facenormals)
    assert struct.unpack_from('<I',raw,face_start)[0]==3
    cases=[]
    def case(name,offset,delta,reason):
        blob=bytearray(raw);put(blob,offset,struct.unpack_from('<f',blob,offset)[0]+delta)
        cases.append((name,blob,{reason}))
    case('water_y',base[0]+28+16*count+4,.125,'unauthorized_bytes_lod_0')
    case('bed_x',base[0]+28+16*100,.125,'unauthorized_bytes_lod_0')
    case('uv',face_start+4+8,.125,'unauthorized_bytes_lod_0')
    blob=bytearray(raw);normal_start=base[0]+28+16*len(visual.points)
    for axis in range(3):put(blob,normal_start+4*axis,-struct.unpack_from('<f',blob,normal_start+4*axis)[0])
    cases.append(('turned_normal',blob,{'wrong_bed_normal'}))
    coords=np.array([p.coords for p in geo.points]);index={id(p):i for i,p in enumerate(geo.points)}
    y_by_xz={tuple(p[[0,2]]):p[1] for p in grid.reshape(-1,3)-origin}
    safe=[]
    for selection in geo.selections.values():
        ids=[index[id(p)] for p in selection.points]
        tops=[i for i in ids if coords[i,1]==y_by_xz[tuple(coords[i,[0,2]])]]
        assert len(tops)==3
        if all(coords[:,1].min()<coords[i,1]<coords[:,1].max()-.05 for i in tops):safe.append(tops)
    assert len(safe)>=760
    blob=bytearray(raw)
    for i in safe[0]:put(blob,base[1]+28+16*i+4,coords[i,1]+.05)
    cases.append(('roof_plus_5cm',blob,{'prism_volume_changed','geometry_not_saved_visual_prism'}))
    blob=bytearray(raw)
    for tops in safe[:760]:
        for i in tops:put(blob,base[1]+28+16*i+4,coords[i,1]-180/512)
    cases.append(('half_roofs_collapsed',blob,{'open_or_wrong_winding_component'}))
    outcomes=[]
    for name,blob,expected in cases:
        path=O/(name+'.p3d');path.write_bytes(blob);t=time.monotonic()
        try:c.check_saved(source,path,grid,origin)
        except ValueError as exc:
            reason=str(exc);assert reason in expected,(name,reason,expected)
            result=dict(case=name,status='REJECTED_BY_SEMANTIC_CONSUMER',reason=reason,seconds=time.monotonic()-t,sha256=c.sha(path))
            outcomes.append(result);meter.dump(O/(name+'.json'),result);print(json.dumps(result),flush=True)
        else:raise AssertionError('MUTANT_PASSED:'+name)
    assert all(c.sha(p)==h for p,h in initial.items())
    result=dict(status='SIX_REAL_MLOD_MUTANTS_REJECTED',positive_original=positive,positive_candidate_receipt_sha256=c.sha(R/'dry-road-mlod-consumer-20261028/report.json'),mutants=outcomes,inputs=initial,measurement=meter.memory(),limits='Offline saved MLOD; no engine or visual acceptance.')
    meter.dump(O/'report.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('positive_original','inputs')}))
try:main()
except Exception as e:meter.dump(O/'failure.json',dict(type=type(e).__name__,error=str(e),measurement=meter.memory()));raise
finally:stop.set()
