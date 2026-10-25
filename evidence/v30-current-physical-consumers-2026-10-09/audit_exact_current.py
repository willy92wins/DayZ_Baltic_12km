"""Independent coverage consumer adapted from the approved navigation contract."""
from pathlib import Path
import ast,hashlib,json,sys
import numpy as np
import shapely
from shapely.geometry import shape,box
B=Path(__file__).parent;W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-current-physical-consumers-2026-10-09'
sys.path.insert(0,str(W/'tools/terrain'));from v30_common import tri_sample
from audit_fairway_triangles_v30 import records
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=W/'evidence/v30-navigation-contract-2026-10-08/verify_contract.py';text=original.read_text();tree=ast.parse(text)
definition=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='corridor_faces');function=ast.get_source_segment(text,definition);exec(function)
source=Path('E:/DayZ-Baltic-Build/v30-native-terminal-finish-20261009/candidate/terrain.npz');h=np.load(source)['heights'].astype(float)
field=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy');plane=np.load(field)
reports=[];obstacle=False;missing=False
paths=[('main19',Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson'),.95),('delta4',W/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson',3.)]
for group,path,minimum in paths:
 features=[f for f in json.loads(path.read_text())['features'] if f['properties'].get('kind','corridor24m')=='corridor24m']
 assert len(features)==(19 if group=='main19' else 4)
 for f in features:
  geom=shape(f['geometry']);count=0;covered=0.;failed=0;worst=None;largest=0.;seen=set()
  for rr,cc,half,polys in corridor_faces(geom):
   xy,owner=shapely.get_coordinates(polys,return_index=True);surf=np.maximum(np.nan_to_num(plane[rr,cc],nan=-np.inf),.5)[owner]
   d=surf-tri_sample(h,xy[:,0],xy[:,1]);ids=((rr*2047+cc)*2+half).astype(int)
   assert not seen.intersection(ids.tolist());seen.update(ids.tolist());failed+=len(np.unique(owner[d<minimum-1e-9]));k=int(d.argmin())
   if worst is None or d[k]<worst['depth_m']:worst=dict(depth_m=float(d[k]),xz=xy[k].tolist())
   areas=shapely.area(polys);covered+=float(areas.sum());largest=max(largest,float(areas.max()));count+=len(polys)
   if not obstacle:
    j=int(d.argmax());r,c=int(rr[owner[j]]),int(cc[owner[j]]);mutant=h.copy();mutant[r:r+2,c:c+2]=surf[j]-.94;obstacle=bool(surf[j]-tri_sample(mutant,*xy[j])<.95)
  error=abs(covered-geom.area);assert error<1e-5 and count
  missing|=abs(covered-largest-geom.area)>1e-5
  raster=records(geom,plane)
  reports.append(dict(group=group,properties=f['properties'],minimum_required_m=minimum,faces=count,producer_raster_faces=raster['faces'],coverage_error_m2=error,failing_faces=failed,worst=worst))
prior=json.loads((E/'geometry-current.json').read_text())
gates=dict(main_19=sum(q['group']=='main19' for q in reports)==19,delta_4=sum(q['group']=='delta4' for q in reports)==4,all_depths=all(q['failing_faces']==0 for q in reports),all_areas_covered=all(q['coverage_error_m2']<1e-5 for q in reports),obstacle_094_rejected=obstacle,missing_face_rejected=missing,roads=prior['roads_status']=='PASS',no_new_low_exceptions=prior['new_bed_exceptions']==0,no_new_dry_flood=prior['new_dry_flood_vertices']==0)
result=dict(status='PASS_CURRENT_EXACT_GEOMETRY' if all(gates.values()) else 'FAIL_CURRENT_EXACT_GEOMETRY',gates=gates,corridors=reports,main_faces=sum(q['faces'] for q in reports if q['group']=='main19'),delta_faces=sum(q['faces'] for q in reports if q['group']=='delta4'),min_depth_m=min(q['worst']['depth_m'] for q in reports),source_sha256=sha(source),physical_field_sha256=sha(field),consumer_source_sha256=sha(original),exact_function_sha256=hashlib.sha256(function.encode()).hexdigest(),
 limits=['Earlier draft used producer raster enumeration and a mistaken total count of19 for19+4; all numeric depths passed, but the draft status remains FAIL as preserved.','This consumer enumerates triangles independently and proves polygon-area coverage.','Main and delta retain different minimum depths; runtime trips still cover selected sectors only.'])
(E/'geometry-current-exact.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='corridors'},indent=2));assert all(gates.values())
