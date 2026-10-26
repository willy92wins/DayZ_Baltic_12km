"""Read packed Roadway and current compiled poses; geometric discovery only."""
from pathlib import Path
import hashlib,json,sys,tempfile
import numpy as np
from shapely.geometry import Polygon,LineString,mapping
from shapely.ops import unary_union
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water'),str(W/'tools/playtest'),'C:/temp/moto_lanes/review_g3/tools']
from package_visual_forest_ev112 import compiled_arrays
from prune_visual_forest_v31 import prefix,objects
from attach_navmesh import read_pbo
from odol_reader import ODOL
from prepare_visual_probe_v31 import height
from streambed_kit_v31 import tri_h
import odol_reader
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
D=R/'kit7-packed-nav-discovery-20261026';D.mkdir(exist_ok=False)
P=R/'river-kit7-contact-only-20261026';mod=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap/Addons')
world=mod/'narva_trial.pbo';pilot=mod/'baltic_stream_pilot.pbo'
assert sha(world)=='10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc'
assert sha(pilot)=='3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6'
source=R/'stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
terrain=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
paths=[Path(__file__),world,pilot,source,terrain,P/'records.json',P/'author-report.json',P/'kit-7-surfaces.npz',Path(odol_reader.__file__),W/'tools/terrain/package_visual_forest_ev112.py',W/'tools/vegetation/prune_visual_forest_v31.py',W/'tools/playtest/attach_navmesh.py',W/'tools/water/prepare_visual_probe_v31.py',W/'tools/water/streambed_kit_v31.py']
inputs={str(p):sha(p) for p in paths}
with source.open('rb') as f:
    prefix(f);ident,name,raw=next(objects(f))
    anchor=dict(id=ident,name=name,matrix=np.frombuffer(raw,dtype='<f4',count=12))
_,_,worldentries=read_pbo(world)
wrp=worldentries['baltic_trial.wrp'];c,reader=compiled_arrays(wrp,anchor)
expected={p['model'].lower():p for p in read(P/'records.json')}
actual={}
for key,record in expected.items():
    mi=c['names'].index(key);ids=np.flatnonzero(c['mi']==mi);assert len(ids)==1
    ix=int(ids[0]);matrix=c['mat'][ix].astype(float).tolist();assert matrix==record['matrix']
    actual[key]=dict(id=int(c['ids'][ix]),model=key,matrix=matrix)
del c,worldentries
_,_,entries=read_pbo(pilot);meshes={};surfaces={};packed={}
for key,pose in actual.items():
    name=key.split('\\')[-1];blob=entries[name];path=D/name;path.write_bytes(blob)
    od=ODOL.from_file(str(path),strict=True)
    assert not getattr(od,'lod_errors',{}) and all(l.lod_end_ok for l in od.lods)
    lods=[l for l in od.lods if abs(l.resolution-3e15)/3e15<1e-4];assert len(lods)==1
    lod=lods[0];assert not lod.proxies and not lod.named_selections
    matrix=np.array(pose['matrix']);assert matrix[:9].tolist()==[1,0,0,0,1,0,0,0,1]
    xyz=(np.array([(v.x,v.y,v.z) for v in lod.vertices])+matrix[9:]).astype(np.float32).astype(float)
    groups={'dry':[],'water':[]};assigned=[];labels=[]
    for section in lod.sections:
        t=section.texture_index;assert 0<=t<len(lod.textures)
        label=lod.textures[t].lower();labels.append(label)
        if label.endswith('gravel_small_ext') or 'gravel_small_ext' in label:group='dry'
        elif label.endswith('water_ext') or 'water_ext' in label:group='water'
        else:raise ValueError(('Unknown Roadway surface',label))
        for index in section.get_face_indices(lod.faces):
            ids=lod.faces[index].vertex_indices;assert len(ids)==3 and len(set(ids))==3
            assert min(ids)>=0 and max(ids)<len(xyz)
            groups[group].append(xyz[ids]);assigned.append(index)
    assert sorted(assigned)==list(range(len(lod.faces)))
    groups={k:np.array(v) for k,v in groups.items()};assert all(len(v) for v in groups.values())
    foot={k:unary_union([Polygon(t[:,[0,2]]) for t in v]) for k,v in groups.items()}
    assert all(g.is_valid and g.area>0 for g in foot.values())
    dry=foot['dry'].difference(foot['water']);assert dry.is_valid
    surfaces[key]=groups;packed[key]=dict(pose=pose,odol_sha256=hashlib.sha256(blob).hexdigest(),labels=sorted(set(labels)),dry=mapping(dry),water=mapping(foot['water']))
    for kind,v in groups.items():meshes[name+'_'+kind]=v
H=np.load(terrain)['heights'];z=np.load(P/'kit-7-surfaces.npz');bed=z['bed'];axis=z['axis'];qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25])
instances=read(P/'author-report.json')['instances'];caps=[]
for end,j,inner,index in [('head',0,6,0),('tail',-1,-7,-1)]:
    tangent=axis[j]-axis[j+1 if j==0 else j-1];tangent=tangent/np.linalg.norm(tangent)
    model=instances[index]['model'];g=surfaces[model];dry=packed[model]['dry']
    for side,q in [('left',-6),('right',6)]:
        col=int(np.flatnonzero(qs==q)[0]);natural=bed[j,col,[0,2]]
        land=natural+10*tangent;inside=bed[inner,col,[0,2]]
        line=LineString([land,natural,inside]);profile=[]
        for dist in np.linspace(0,line.length,int(np.ceil(line.length/.25))+1):
            p=line.interpolate(dist);xz=np.array([p.x,p.y]);gy=float(tri_h(H,*xz));ry=height(g['dry'],xz);wy=height(g['water'],xz)
            profile.append(dict(x=float(xz[0]),z=float(xz[1]),ground=gy,road=ry,wet=wy is not None,y=max(gy,ry if ry is not None else gy)))
        pts=np.array([[p['x'],p['y'],p['z']] for p in profile]);slope=np.degrees(np.arctan(np.abs(np.diff(pts[:,1]))/np.linalg.norm(np.diff(pts[:,[0,2]],axis=0),axis=1)))
        assert not any(p['wet'] for p in profile)
        caps.append(dict(name=f'kit7_cap_{end}_{side}',start=(pts[0]+[0,.2,0]).tolist(),end=(pts[-1]+[0,.2,0]).tolist(),expect='path',side=side,kind='cap_to_land',models=[model],centerline=list(map(list,line.coords)),profile=profile,max_sample_slope_deg=float(slope.max()),land_endpoint_outside_model=height(g['dry'],land) is None))
np.savez_compressed(D/'roadway.npz',**meshes)
assert all(sha(p)==h for p,h in inputs.items())
report=dict(status='PACKED_ROADWAY_ROUTE_DISCOVERY_NOT_ACCEPTANCE',models=packed,cap_queries=caps,compiled_reader=reader,compiled_wrp_sha256=hashlib.sha256(wrp).hexdigest(),inputs=inputs,inputs_unchanged=True,limits=['Packed footprints and poses; graph/locomotion not tested.','Cap profiles sampled at25cm are screening, not continuous proof.'])
(D/'geometry.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(models=len(packed),caps=[{k:v for k,v in p.items() if k not in ('profile','centerline')} for p in caps]),indent=2))
