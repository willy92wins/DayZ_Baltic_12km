"""Compare native anomaly points with the exact deployed ODOL models and authored poses."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union

W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09'
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
B8=Path('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008')
B9=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
F=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water'),str(W/'tools/playtest'),str(W/'tools/navigation')]
from wrp0wzd import read
from attach_navmesh import read_pbo
from engine_water_model import ODOL
from water_mesh import py3d
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
deployed=Path('P:/Mods/@DayZ_Baltic_ValleySmoothC1R3P/Addons')
assert sha(deployed/'baltic_water_v30.pbo')=='542bd4e85e9f82d9ef373386371168c9b489c0794e3f4bd4773709c680c4b068'
assert sha(deployed/'narva_trial.pbo')=='75adb673ed23ab5b656a162063d6a89cbb2e0a0d99aba82263bf2a54a31e8623'
_,props,packed=read_pbo(deployed/'baltic_water_v30.pbo')
worldpath=B9/'world-c1r3p/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
assert sha(worldpath)=='96c15a5bc7f3fb6adb8e626136c9c2bdebb079c7e44be01f1e4f922d16f1d6fd'
world=read(worldpath)
old=json.loads((F/'water/pieces.json').read_text())
author=json.loads((W/'evidence/v30-curved-channel-pilot-2026-10-08/flat-water-authoring.json').read_text())
poses=[p for p in old['poses'] if p not in author['removed_poses']]+author['new_poses']
objects=[o for o in world['objects'] if o['name'].startswith('baltic_water_v30')]
assert [o['name'] for o in objects]==[p['model'] for p in poses]
tree=cKDTree(np.array([p['origin'] for p in poses])[:,[0,2]])
cache={};instance_cache={}
def mesh(name):
    if name in cache:return cache[name]
    nativepath=B8/'stitched-water/water/temp/baltic_water_v30'/name
    assert nativepath.read_bytes()==packed[name],name
    obj=ODOL.from_file(str(nativepath));vcenter=obj.model_info.bounding_center
    center=np.array([vcenter.x,vcenter.y,vcenter.z])
    model={}
    source=B8/'stitched-water/compile/source/baltic_water_v30'/name
    if not source.exists():source=F/'water/source/baltic_water_v30'/name
    with source.open('rb') as stream:mlod=py3d.P3D(stream)
    for label,res in [('roadway',3e15),('visible',1)]:
        lod=min(obj.lods,key=lambda l:abs(l.resolution-res));assert abs(lod.resolution-res)/max(1,res)<1e-6
        v=np.array([(p.x,p.y,p.z) for p in lod.vertices]);faces=[list(f.vertex_indices) for f in lod.faces]
        ml=min(mlod.lods,key=lambda l:abs(l.resolution-res))
        mv=np.array([p.coords for p in ml.points]);mf=[[q.point_index for q in face.vertices] for face in ml.faces]
        model[label]=(v,faces,mv,mf)
    model.update(center=center,sha=sha(nativepath),source_sha=sha(source))
    cache[name]=model;return model
def instance(i):
    if i in instance_cache:return instance_cache[i]
    pose,obj=poses[i],objects[i];name=pose['model'].split('\\')[-1];mdl=mesh(name)
    mat=np.array(obj['matrix']);rot=mat[:9].reshape(3,3);pos=mat[9:]
    assert np.max(np.abs(rot-np.eye(3)))<1e-6
    offset=pos-np.array(pose['origin'])-mdl['center']@rot
    out=dict(index=i,id=obj['id'],model=name,origin=pose['origin'],center=mdl['center'].tolist(),matrix=obj['matrix'],placement_error=offset.tolist(),sha256=mdl['sha'],source_sha256=mdl['source_sha'])
    for label in ['roadway','visible']:
        v,f,mv,mf=mdl[label];wv=v@rot+pos;sv=mv+np.array(pose['origin'])
        polys=[Polygon(wv[q][:,[0,2]]) for q in f]
        geom=unary_union(polys);sg=unary_union([Polygon(sv[q][:,[0,2]]) for q in mf])
        out[label]=dict(vertices=wv,faces=f,polys=polys,geometry=geom,source_geometry=sg,
            source_footprint_difference_m2=geom.symmetric_difference(sg).area)
    instance_cache[i]=out;return out
points=json.loads((E/'native-anomaly-classification.json').read_text())['points']
points.append(dict(x=2718.4852495913565,z=6812.812873578129,ground=1.520454,plane=.707429,reason='USER_CALIBRATED_DRY_VISUAL_RESIDUAL'))
results=[]
for pt in points:
    x,z=float(pt['x']),float(pt['z']);point=Point(x,z);hits=[];near=[]
    for i in tree.query_ball_point([x,z],72):
        ins=instance(i);road=ins['roadway'];distance=road['geometry'].distance(point)
        if distance>6:continue
        hit={k:ins[k] for k in ['id','model','origin','placement_error']}
        hit['distance_m']=distance
        hit['source_covers']=road['source_geometry'].buffer(1e-6).covers(point)
        for label in ['roadway','visible']:
            m=ins[label];levels=[]
            for f,poly in zip(m['faces'],m['polys']):
                if not poly.buffer(1e-6).covers(point):continue
                a,b,c=m['vertices'][f[:3]];n=np.cross(b-a,c-a)
                if abs(n[1])>1e-10:levels.append(float(a[1]-(n[0]*(x-a[0])+n[2]*(z-a[2]))/n[1]))
            hit[label+'_levels']=sorted(set(round(q,7) for q in levels))
        (hits if hit['roadway_levels'] else near).append(hit)
    predicted=max([y for a in hits for y in a['roadway_levels']],default=None)
    measured=float(pt['plane']);ground=float(pt['ground'])
    classification='compiled_pond_matches_runtime' if predicted is not None and abs(predicted-measured)<.002 else ('compiled_pond_absent' if predicted is None else 'compiled_pond_runtime_mismatch')
    results.append(dict(point=pt,compiled_max_level=predicted,compiled_depth=None if predicted is None else predicted-ground,
        comparison=classification,hits=hits,near=near))
metadata=[]
for ins in instance_cache.values():
    row={k:v for k,v in ins.items() if k not in ('roadway','visible')}
    row['roadway_source_footprint_difference_m2']=ins['roadway']['source_footprint_difference_m2']
    row['visible_source_footprint_difference_m2']=ins['visible']['source_footprint_difference_m2']
    metadata.append(row)
report=dict(status='COMPILED_POINT_COMPARISON_NOT_GLOBAL_RENDER_CERTIFICATION',points=results,instances=metadata,
    counts=dict(Counter(r['comparison'] for r in results)),models=len(cache),instance_count=len(instance_cache),
    maximum_placement_error_m=max(np.max(np.abs(q['placement_error'])) for q in metadata),
    world_sha256=sha(worldpath),water_sha256=sha(deployed/'baltic_water_v30.pbo'),
    limitations=['Water ODOL bytes compared directly to deployed archive. WRP placement uses hashed source of deployed build; native raster readback independently matched all heights.',
    'XZ geometry and interpolated visual heights do not model pond/sea shader displacement or image artifacts.',
    'Coverage sampled only at native anomalies and calibrated reported point; no global continuous-area verdict.'])
(E/'compiled-water-point-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('points','instances')},indent=2))
for row in results:
    if row['point']['reason'] in ('runtime_water_missing_below_frozen_plane','USER_CALIBRATED_DRY_VISUAL_RESIDUAL'):
        print(json.dumps(row))
