from pathlib import Path
import sys,json
import numpy as np
import shapely
from shapely.geometry import shape,box
B=Path(__file__).parent
OLD=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009')
SOURCE=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')
sys.path.insert(0,str(OLD))
import terminal_pass as kernel
from discover_native_turns import sha
DESIGN=Path('E:/DayZ-Baltic-Build/v30-v11/design')

def main():
    assert not (B/'authoring.json').exists(),'One missing feature candidate only'
    assert sha(SOURCE)=='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6'
    data=dict(np.load(SOURCE));h=data['heights'];f=np.load(kernel.B12/'preserved-field.npy');p=np.load(kernel.B10/'frozen-field-reference/plane.npy');fixed=np.load(OLD/'constraints.npz')['fixed']
    features=json.loads((DESIGN/'water_v3.geojson').read_text())['features'];profiles=np.load(DESIGN/'profiles.npz')
    feats=[q for q in features if q['properties'].get('name')=='Volkhov'];assert len(feats)==1 and 'id' not in feats[0]['properties']
    cut=shape(feats[0]['geometry']).intersection(box(60,60,12222,12222).boundary);assert cut.geom_type=='LineString'
    center=cut.interpolate(.5,normalized=True);xmin,zmin,xmax,zmax=center.x-60,center.y-60,center.x+60,center.y+60
    r0=max(0,int((12282-zmax)//6));r1=min(2047,int(np.ceil((12282-zmin)/6)));c0=max(0,int(xmin//6));c1=min(2047,int(np.ceil(xmax/6)))
    job=dict(box_cells=[r0,c0,r1,c1],features=['Volkhov:polygon_east_cut'])
    old=json.loads((OLD/'discovery.json').read_text());assert all('Volkhov' not in str(q['features']) for q in old['jobs'])
    streams=json.loads((DESIGN/'streams_candidates.geojson').read_text())['features'];excluded=[]
    for name in ('stream_0452','stream_0456'):
        props=next(q['properties'] for q in streams if q['properties']['id']==name);assert props['tier_m']==1500 and not any(q['properties'].get('id')==name for q in features)
        previous=next(q for q in old['jobs'] if name+':-1' in q['features']);ra,ca,rb,cb=previous['box_cells']
        excluded.append(dict(id=name,properties=props,profile_samples=len(profiles[name]),in_built_design=False,finite_physical_water_cells_in_old_box=int(np.isfinite(p[ra:rb,ca:cb]).sum()),classification='EXCLUDED_TIER_1500_NOT_MISSING_CONTOUR'))
    discover=dict(status='MISSING_POLYGON_TERMINAL_DISCOVERY',source_sha256=sha(SOURCE),design_sha256=sha(DESIGN/'water_v3.geojson'),profiles_sha256=sha(DESIGN/'profiles.npz'),kernel_sha256=sha(OLD/'terminal_pass.py'),constraints_sha256=sha(OLD/'constraints.npz'),cut=list(cut.coords),cut_midpoint=[center.x,center.y],jobs=[job],candidate_boxes=1,excluded_streams=excluded)
    (B/'discovery.json').write_text(json.dumps(discover,indent=2)+'\n');np.savez_compressed(B/'constraints.npz',fixed=fixed)
    kernel.H=h.astype(float);kernel.F=f;kernel.P=p;kernel.FIXED=fixed
    report=kernel.solve_tile(job);(B/'tiles.jsonl').write_text(json.dumps(report)+'\n')
    candidate=h.copy()
    if report['status']=='INTEGRATE_SOURCE_ONLY':candidate.ravel()[report['ids']]=report['heights']
    target=B/'candidate';target.mkdir(exist_ok=False);np.savez_compressed(target/'terrain.npz',**(data|dict(heights=candidate)))
    ids=np.flatnonzero(candidate!=h);np.savez_compressed(B/'delta.npz',ids=ids,before=h.ravel()[ids],after=candidate.ravel()[ids])
    result=dict(status='POLYGON_TERMINAL_CANDIDATE_REQUIRES_GLOBAL_GATES' if len(ids) else 'NO_CANDIDATE_KEEP_EV25',source_sha256=sha(SOURCE),candidate_sha256=sha(target/'terrain.npz'),changed_vertices=len(ids),report={k:v for k,v in report.items() if k not in ['ids','heights']},excluded_streams=excluded)
    (B/'authoring.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
