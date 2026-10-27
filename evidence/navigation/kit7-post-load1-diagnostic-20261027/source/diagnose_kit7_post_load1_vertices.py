"""Read only: compare archived empirical navigation vertices with packed surfaces."""
from pathlib import Path
import hashlib,json,sys,time,datetime
import numpy as np
from shapely.geometry import shape
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');A=W/'evidence/navigation/kit7-nav12-rejected-20261027/diagnostics';G=R/'kit7-packed-nav-discovery-20261026';O=R/'kit7-post-load1-vertex-surfaces-20261027'
O.mkdir(exist_ok=False)
start=datetime.datetime.now(datetime.timezone.utc);deadline=datetime.datetime.fromisoformat('2026-10-27T14:05:09+00:00');assert start<deadline
(O/'budget.json').write_text(json.dumps(dict(status='READ_ONLY_DISCOVERY_STARTED',phase_started_utc='2026-10-27T13:35:09+00:00',started_utc=start.isoformat(),deadline_utc=deadline.isoformat(),max_dayz_runs=0,max_generations=0),indent=2)+'\n')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/playtest'),'C:/temp/moto_lanes/review_g3/tools']
from prepare_visual_probe_v31 import height
from streambed_kit_v31 import tri_h
from attach_navmesh import read_pbo
from odol_reader import ODOL
import odol_reader
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
grid=read(A/'kit7-grid-vertex-diagnostic-20261027.json');recon=read(A/'kit7-nav12-height-reconstruction-20261027.json');native=read(A/'kit7-nav12-height-diagnostic-20261027.json');geo=read(G/'geometry.json')
pilot=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Nav12/Addons/baltic_stream_pilot.pbo');terrain=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz'
assert sha(pilot)=='3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6'
assert sha(terrain)=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40'
assert sha(G/'geometry.json')=='e3c902fd1561804b3b02b68ada18e64c26c3d697f79c9fce8bb0ad62e66d3c5e'
assert sha(Path(odol_reader.__file__))=='fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57'
# Verify archived inputs against their independently published manifest.
manifest=read(A.parent/'MANIFEST.json')
for p in [A/'kit7-grid-vertex-diagnostic-20261027.json',A/'kit7-nav12-height-reconstruction-20261027.json',A/'kit7-nav12-height-diagnostic-20261027.json']:
 assert sha(p)==manifest[p.relative_to(A.parent).as_posix()]['sha256']
H=np.load(terrain)['heights'];_,_,entries=read_pbo(pilot)
vertices={};points=set()
for nav in grid['navmeshes']:
 label=nav['label'];vertices[label]={}
 for tile in nav['tiles']:
  for v in tile['vertices']:
   x,y,z=map(float,v);points.add((x,z));vertices[label].setdefault((x,z),set()).add(y)
# Include every vertex of the six-waypoint reconstruction as well.
for tile in recon['tiles']:
 for poly in tile['polygons']:
  for x,y,z in poly['vertices']:points.add((x,z));vertices['12m'].setdefault((x,z),set()).add(y)
for s in native['samples']:points.add((s['nav'][0],s['nav'][2]))
for s in grid['points']:points.add((s['x'],s['z']))
points=sorted(points);meshes=[];model_inputs={}
for model,meta in geo['models'].items():
 bounds=shape(meta['dry']).union(shape(meta['water'])).bounds
 if not any(bounds[0]-1e-6<=x<=bounds[2]+1e-6 and bounds[1]-1e-6<=z<=bounds[3]+1e-6 for x,z in points):continue
 path=G/model.split('\\')[-1];assert path.read_bytes()==entries[path.name] and sha(path)==meta['odol_sha256']
 model_inputs[str(path)]=sha(path);od=ODOL.from_file(str(path),strict=True);assert not getattr(od,'lod_errors',{}) and all(l.lod_end_ok for l in od.lods)
 matrix=np.array(meta['pose']['matrix']);assert matrix[:9].tolist()==[1,0,0,0,1,0,0,0,1]
 for lod in od.lods:
  if not lod.faces:continue
  xyz=(np.array([(v.x,v.y,v.z) for v in lod.vertices])+matrix[9:]).astype(np.float32).astype(float)
  faces=np.array([f.vertex_indices for f in lod.faces]);assert faces.ndim==2 and faces.shape[1]==3 and faces.min()>=0 and faces.max()<len(xyz)
  triangles=xyz[faces];ab=triangles[:,1,:][:,[0,2]]-triangles[:,0,:][:,[0,2]];ac=triangles[:,2,:][:,[0,2]]-triangles[:,0,:][:,[0,2]]
  triangles=triangles[(ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0])!=0]
  if len(triangles):meshes.append((model,float(lod.resolution),triangles))
rows=[]
for x,z in points:
 assert datetime.datetime.now(datetime.timezone.utc)<deadline
 hits=[]
 for model,resolution,tris in meshes:
  y=height(tris,np.array([x,z]))
  if y is not None:
   assert np.isfinite(y);hits.append(dict(model=model,resolution=resolution,y=y))
 roads=[h['y'] for h in hits if abs(h['resolution']-3e15)/3e15<1e-6]
 road=max(roads) if roads else None
 rows.append(dict(x=x,z=z,terrain_y=float(tri_h(H,x,z)),roadway_y=road,lods=hits,nav_vertices={label:sorted(byxy.get((x,z),set())) for label,byxy in vertices.items()}))
lookup={(s['x'],s['z']):s for s in rows};controls=[]
# Six independent engine surface observations constrain the packed reader.
for s in native['samples']:
 row=lookup[(s['nav'][0],s['nav'][2])];assert row['roadway_y'] is not None
 residual=row['roadway_y']-s['engine_roadway'][1];assert abs(residual)<2e-5
 controls.append(dict(query=s['query'],index=s['index'],engine_roadway_residual_m=residual))
for s in grid['points']:
 row=lookup[(s['x'],s['z'])];assert abs(row['terrain_y']-s['terrain_y'])<1e-9
 for hit in s['model_lods']:
  exact=[h for h in row['lods'] if h['model']==hit['model'] and h['resolution']==hit['resolution']];assert len(exact)==1 and abs(exact[0]['y']-hit['y'])<1e-9
stats={}
for label in vertices:
 records=[]
 for row in rows:
  for y in row['nav_vertices'][label]:
   records.append(dict(x=row['x'],z=row['z'],nav_y=y,nav_minus_terrain_m=y-row['terrain_y'],nav_minus_roadway_m=None if row['roadway_y'] is None else y-row['roadway_y']))
 road=[p['nav_minus_roadway_m'] for p in records if p['nav_minus_roadway_m'] is not None]
 stats[label]=dict(vertices=len(records),with_roadway=len(road),without_roadway=len(records)-len(road),below_terrain=sum(p['nav_minus_terrain_m']<0 for p in records),roadway_delta_range_m=[min(road),max(road)] if road else None,roadway_abs_gt_0801=sum(abs(d)>.801 for d in road),records=records)
paths=[Path(__file__),W/'plans/ev112-kit7-post-load1-diagnostic-20261027.md',A/'kit7-grid-vertex-diagnostic-20261027.json',A/'kit7-nav12-height-reconstruction-20261027.json',A/'kit7-nav12-height-diagnostic-20261027.json',pilot,terrain,G/'geometry.json',Path(odol_reader.__file__),W/'tools/water/prepare_visual_probe_v31.py',W/'tools/water/streambed_kit_v31.py',W/'tools/playtest/attach_navmesh.py']
result=dict(status='INCONCLUSIVE_NO_VERIFIED_MECHANISM',stage='EXTENDED_ARCHIVED_LOCAL_VERTEX_SURFACE_DIAGNOSTIC',point_count=len(points),models=len(model_inputs),stats=stats,points=rows,native_surface_controls=controls,inputs={**model_inputs,**{str(p):sha(p) for p in paths}},limits=['No new NM payload decoder; only archived empirical local vertices, not full 8m/12m meshes.','12.5m vertex coverage remains unverified.','Native surface controls constrain six waypoints, not every new corner.','Roadway denotes the fluvial kit surface, not map roads.','Comparisons identify local discrepancies but do not isolate generator mechanism or RAM allocations.','No artifact changed, no native run, no tolerance change or global acceptance.'])
(O/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
(O/'completion.json').write_text(json.dumps(dict(returncode=0,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inputs_unchanged=all(sha(Path(p))==h for p,h in result['inputs'].items()),dayz_runs=0,generations=0),indent=2)+'\n')
print(json.dumps(dict(status=result['status'],points=len(points),models=len(model_inputs),stats={k:{a:b for a,b in v.items() if a!='records'} for k,v in stats.items()},native_controls=len(controls)),indent=2))
