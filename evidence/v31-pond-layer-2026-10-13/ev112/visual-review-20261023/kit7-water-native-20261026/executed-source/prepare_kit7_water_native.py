"""Prepare immutable kit7 water/regression and calibration missions; no lifecycle."""
from pathlib import Path
from collections import Counter
import hashlib,json,shutil,sys
import numpy as np
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');O=R/'kit7-water-native-20261026'
sys.path.insert(0,str(W/'tools/water'));from prepare_visual_probe_v31 import height,triangles
from streambed_kit_v31 import tri_h
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
dep=read(R/'kit7-native-20261026/deployment.json');native=read(R/'kit7-native-20261026/result.json');assert native['status']=='NATIVE_HEIGHT_AND_BOUNDARY_SAMPLES_PASS'
discovery=read(R/'kit7-water-controls-discovery-20261026.json');regression=read(R/'kit7-regression-discovery-20261026.json')
for key in ('dry_conflicts','wet_missing','ground_expectation_drift','bed_expectation_drift','water_level_drift','models_without_wet_query'):assert not discovery[key],key
assert discovery['inputs_unchanged'] and discovery['kit_models']==139 and discovery['joints']==138 and discovery['joint_coordinate_max_m']<1e-6
assert regression['inherited_points']==4749 and regression['changed_ground']==regression['within_new_geometry']==0
oldpath=R/'runtime-rectangle-f/points.json';newpath=R/'probe-kit7-prepared-20261026/points.json';old=read(oldpath);new=read(newpath)
assert len(old['points'])==4749 and len(new['points'])==2050 and not new['diagnostics']
inputs={}
for mapping in (dep['inputs'],discovery['inputs'],regression['inputs'],old['inputs'],old['inherited_inputs'],new['inputs']):
 for p,h in mapping.items():assert sha(Path(p))==h,p;inputs[p]=h
points=[dict(p,original_id=p['id'],origin_set=label) for label,group in [('F',old['points']),('kit7',new['points'])] for p in group]
for i,p in enumerate(points):p['id']=i
M=R/'river-kit7-merged-byteexact-20261026';P=R/'river-kit7-midpoint-a-20261026';H=np.load(M/'terrain-buried.npz')['heights'];z=np.load(P/'kit-7-surfaces.npz');bed=triangles(z['bed']);water=triangles(z['water'])
contactpath=P/'compiled-contact-review.json';contact=read(contactpath);assert contact['status']=='PACKED_KIT7_COLLISION_AT_DERIVED_POSES_PASS' and all(contact['contact']['checks'].values())
for label,record in contact['contact']['extrema'].items():
 q=np.round(record['xz'],6);by=height(bed,q);wy=height(water,q);ground=float(tri_h(H,q[0],q[1]));assert by is not None
 points.append(dict(id=len(points),kind='kit7_contact_'+label,site='kit-7',x=float(q[0]),z=float(q[1]),ground=ground,bed=by,water_ext=None if wy is None else wy-.25,expect='dry' if wy is None else 'wet',collision_pilot=by>ground+.03,origin_set='contact_certificate'))
assert len(points)==6801
missionroot=Path('C:/temp/DayZ_MCP_130_dev/mpmissions');missions={k:missionroot/n for k,n in [('full','BalticKit7Water.BalticTrial'),('calibration','BalticKit7Calibration.BalticTrial')]}
producers={'full':W/'missions/BalticVisualProbeV1.BalticTrial/init.c','calibration':W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/runtime-rv-contact-20261025/probe/calibration/init.c'}
assert 'BALTIC_COLLISION_DIAGNOSTIC_V3' in producers['calibration'].read_text()
assert not O.exists() and all(not p.exists() for p in missions.values())
O.mkdir()
for k,p in missions.items():p.mkdir();shutil.copyfile(producers[k],p/'init.c');assert sha(p/'init.c')==sha(producers[k]);inputs[str(p/'init.c')]=sha(p/'init.c');inputs[str(producers[k])]=sha(producers[k])
csv=''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in points);(missions['full']/'points.csv').write_text(csv,encoding='ascii',newline='\n')
for p in [Path(__file__),oldpath,newpath,contactpath,R/'kit7-water-controls-discovery-20261026.json',R/'kit7-regression-discovery-20261026.json',R/'kit7-native-20261026/result.json',missions['full']/'points.csv',W/'tools/water/prepare_visual_probe_v31.py',W/'tools/water/streambed_kit_v31.py',W/'tools/water/eval_visual_probe_v31.py',W/'plans/ev112-kit7-water-native-unit-20261026.md']:inputs[str(p)]=sha(p)
doc=dict(schema='ev112-visual-probe-v1',points=points,counts=dict(Counter(p['kind'] for p in points)),inputs=inputs,scope='4749 F exact expectations +2050 kit7 +2 contact certificate witnesses; no client, navigation, performance or global acceptance.')
(O/'points.json').write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8')
inputs[str(O/'points.json')]=sha(O/'points.json')
receipt=dict(status='PREPARED_PENDING_INDEPENDENT_REVIEW',deployed=dep['deployed'],inputs=inputs,missions={k:str(v) for k,v in missions.items()},producers={k:sha(v) for k,v in producers.items()},counts=dict(total=6801,inherited_F=4749,new_kit7=2050,contact_witnesses=2),mod=dep['mod'],navmesh_data_server=True,navigation_accepted=False,client_started=False)
(O/'deployment.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('inputs','deployed')},indent=2))
