"""Freeze all local corridor contracts and inherited45 before any native query."""
from pathlib import Path
import hashlib,json,sys,uuid
import numpy as np
from shapely.geometry import LineString,shape,mapping,GeometryCollection
from shapely.ops import unary_union
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/terrain')]
from prepare_visual_probe_v31 import height
from v30_common import tri_sample
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
D=R/'kit7-nav-consumer-20261026';D.mkdir(exist_ok=False)
oldpath=R/'patch-nav-f45/reference.json';old=read(oldpath);proppath=R/'kit7-nav-route-discovery-20261026/proposals.json';proposed=read(proppath)
gpath=R/'kit7-packed-nav-discovery-20261026/geometry.json';g=read(gpath)
terrain=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz';h=np.load(terrain)['heights'];oldh=np.load(old['terrain'])['heights']
profiles={p['name']:p['profile'] for p in proposed['screen']};models=g['models']
PolygonEmpty=GeometryCollection()
dry={k:shape(v['dry']) for k,v in models.items()};wet=unary_union([shape(v['water']) for v in models.values()]);full=unary_union(list(dry.values())+[wet])
mesh=np.load(R/'kit7-packed-nav-discovery-20261026/roadway.npz');allroof=np.concatenate([mesh[k] for k in mesh.files if k.endswith('_dry')])
queries=json.loads(json.dumps(old['queries']));updates=[]
for q in queries:
    for end in ('start','end'):
        p=q[end];ground=float(tri_sample(h,p[0],p[2]));previous=float(tri_sample(oldh,p[0],p[2]))
        if abs(ground-previous)<1e-9:continue
        assert q['name']=='changed_bank_13'
        roof=height(allroof,np.array(p)[[0,2]]);before=p[1];p[1]=max(ground,ground if roof is None else roof)+.1
        updates.append(dict(name=q['name'],endpoint=end,old_y=before,new_y=p[1],terrain=ground,packed_dry_roadway=roof))
assert len(updates)==2
cases=[]
for q0 in proposed['queries']+g['cap_queries']:
    q={k:v for k,v in q0.items() if k not in ('profile','max_sample_slope_deg','land_endpoint_outside_model')}
    line=LineString(q.get('centerline') or [[p['x'],p['z']] for p in profiles[q['name']]])
    corridor=line.buffer(2.1)
    allowed=[k for k,geom in dry.items() if corridor.intersects(geom)]
    required=q.pop('models');assert set(required)<=set(allowed)
    base=unary_union([dry[k] for k in allowed]);exterior=corridor.difference(full) if q['kind']=='cap_to_land' else PolygonEmpty
    permit=base.union(exterior)
    water_area=corridor.intersection(wet).area;outside_area=corridor.difference(permit.buffer(.01)).area
    coverage={k:line.intersection(dry[k]).length for k in required}
    assert water_area<1e-8 and outside_area<1e-8 and all(v>=.5 for v in coverage.values()),q['name']
    assert q['kind']!='cap_to_land' or line.intersection(exterior).length>=.5
    q.update(required_models=required,allowed_models=allowed,centerline=list(map(list,line.coords)))
    queries.append(q)
    cases.append(dict(name=q['name'],corridor=mapping(corridor),exterior=mapping(exterior),water_area=water_area,outside_area=outside_area,required_coverage_m=coverage,allowed_models=allowed))
assert len(queries)==607 and len(set(q['name'] for q in queries))==607
probe=str(uuid.uuid4());inputs={str(p):sha(p) for p in [Path(__file__),oldpath,proppath,gpath,terrain,Path(old['terrain']),R/'kit7-packed-nav-discovery-20261026/roadway.npz',W/'plans/ev112-kit7-navigation-consumer-20261026.md',W/'tools/water/prepare_visual_probe_v31.py',W/'tools/terrain/v30_common.py']}
ref=dict(status='FROZEN_GEOMETRIC_CONTRACT_PENDING_CODE_REVIEW',probe_id=probe,header='BALTIC_KIT7_NAV_V1;BalticTrial;'+probe,log_name='baltic_kit7_nav_'+probe+'.log',terrain=str(terrain),terrain_sha256=sha(terrain),queries=queries,local_query_names=[q['name'] for q in queries[45:]],f_local_query_names=old['local_query_names'],previous_reference=str(oldpath),previous_reference_sha256=sha(oldpath),endpoint_updates=updates,max_waypoint_surface_error_m=old['max_waypoint_surface_error_m'],geometry=str(gpath),geometry_sha256=sha(gpath),corridors=cases,inputs=inputs,limits=['Native graph only; no locomotion, boats, visual, FPS or global acceptance.','Continuous XZ coverage, but waypoint-only native heights.','Existing terrain/surface/endpoint tolerances retained.'])
(D/'reference.json').write_text(json.dumps(ref,indent=2)+'\n')
(D/'queries.csv').write_text(''.join(q['name']+';'+';'.join(' '.join(f'{v:.8f}' for v in q[k]) for k in ('start','end'))+'\n' for q in queries),encoding='ascii')
(D/'freeze-summary.json').write_text(json.dumps(dict(queries=607,local=562,models=139,seams=138,endpoint_updates=updates,water_area_max=max(c['water_area'] for c in cases),outside_area_max=max(c['outside_area'] for c in cases),extra_allowed_models=[dict(name=q['name'],allowed=q['allowed_models'],required=q['required_models']) for q in queries[45:] if set(q['allowed_models'])!=set(q['required_models'])],reference_sha256=sha(D/'reference.json'),queries_sha256=sha(D/'queries.csv')),indent=2)+'\n')
print(json.dumps(dict(queries=len(queries),probe_id=probe,water_area_max=max(c['water_area'] for c in cases),outside_area_max=max(c['outside_area'] for c in cases))))
