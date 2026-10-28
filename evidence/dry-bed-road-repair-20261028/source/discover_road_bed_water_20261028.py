"""Bounded read-only discriminator: actual water projection at existing road/bed conflict."""
import os,time
START=time.monotonic()
for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np
import shapely
from shapely import Polygon
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'road-bed-water-discovery-20261028';O.mkdir(exist_ok=False)
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
q=W/'tools/quality';e=module('exposure',q/'pilot_visible_exposure_ev112.py');g=e.g
s=module('inventory',q/'deployed_surface_inventory_ev112.py');meter=module('meter',q/'water_constraint_diagnostic_ev112.py')
meter.STARTED=START;meter.MAX_SECONDS=180;stop=meter.bounded(O);pins={}
def pin(p,expected=None):
 d=meter.sha(p)
 if expected is not None:g.require(d==expected,'changed:'+str(p))
 pins[str(p)]=d;return p
def nz(p):
 with np.load(p,allow_pickle=False) as f:return {k:f[k] for k in f.files}
def save(name,obj):meter.dump(O/name,obj)
try:
 save('scope.json',dict(hypothesis='The existing pilot bed/road conflict may be outside all actual water footprints; test projection independently of water height before repair choice.',budget=dict(seconds=180,bytes=2*1024**3),mutations='New evidence only. No terrain, bed, water, protection or deployed file changes.',verdict='Diagnostic only; any unknown water contact blocks a dry-repair claim.'))
 for p in (Path(__file__),q/'pilot_visible_exposure_ev112.py',q/'pilot_surface_refinement_ev112.py',q/'deployed_surface_inventory_ev112.py'):pin(p)
 aman=json.loads(pin(W/'evidence/deployed-surface-prototypes-20261028/artifact-hashes.json').read_bytes());a=R/'deployed-surface-prototypes-20261028'
 for rel,d in aman.items():pin(R/rel,d['sha256'])
 z=nz(a/'surface-prototypes.npz');v,m=z['vertices'],z['meta'];i=nz(a/'instances.npz');cat={x['index']:x for x in json.loads((a/'model-catalog.json').read_bytes())}
 mods=json.loads(pin(R/'pilot-visible-surface-extraction-20261028/models.json').read_bytes())
 target=next(x for x in mods if x['model']=='baltic_stream_pilot/cs_kit_118_0000.p3d')
 z=nz(pin(R/'pilot-visible-surface-extraction-20261028'/target['file'],target['sha256']));bed=z['bed'][:,:3]
 h=nz(pin(R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz',e.H_SHA))['heights']
 f=nz(pin(R/'river-kit7-merged-byteexact-20261026/bury-work/fp0/footprint.npz',e.FP_SHA));wp,wf=f['plane'],f['field']
 road=nz(pin(W.parents[2]/'tests/regional_foundation_roads_v6/reference.npz',e.ROAD_SHA));xy,edges=road['xy'],road['edges'];e.road_guard(xy,edges)
 footprint=shapely.union_all([Polygon(t[:,(0,2)]) for t in bed]);lo=np.array(footprint.bounds[:2]);hi=np.array(footprint.bounds[2:]);near=[];rids=[]
 for ri,(n1,n2,_) in enumerate(edges):
  ab=xy[[int(n1),int(n2)]]
  if np.any(ab.max(0)+4<lo) or np.any(ab.min(0)-4>hi):continue
  p=e.rect(*ab)
  if p.intersects(footprint):near.append(p);rids.append(ri)
 roadpoly=shapely.union_all(near);source_conflict=footprint.intersection(roadpoly)
 expos=[];nominal_wet=[];parts=0
 for tri in bed:
  if not Polygon(tri[:,(0,2)]).intersects(roadpoly):continue
  for p in g.refine(tri,h,wp,wf):
   parts+=1;reg=g.sign_regions(p,'terrain');poly=e.polygon(reg['above_polygon']).intersection(roadpoly)
   if poly.is_empty:continue
   expos.append(poly)
   # Native nominal water presence is H<=W, not B<=W.
   delta=g.evaluate(p['terrain_plane'],p['polygon'])-g.evaluate(p['water_coeff'],p['polygon'])
   nominal=e.polygon(g.clip(p['polygon'],delta,False))
   nominal_wet.append(poly.intersection(nominal))
 exposed=shapely.union_all(expos);native_wet=shapely.union_all(nominal_wet)
 water_ids=np.flatnonzero(np.isin(m['kind'],[1,2]));groups={}
 for mid in np.unique(m['model'][water_ids]):groups[int(mid)]=water_ids[m['model'][water_ids]==mid]
 bounds={}
 for mid,fs in groups.items():
  verts=v[fs][np.arange(4)[None,:]<m['vertices'][fs,None]];mn,mx=verts.min(0),verts.max(0)
  bounds[mid]=np.array([[x,y,z] for x in (mn[0],mx[0]) for y in (mn[1],mx[1]) for z in (mn[2],mx[2])])
 contacts=[];near_water=[];refs=[];wgeom=[];unknown=[];instances_with_water=0;candidate_instances=0
 for ii,(mid,pose) in enumerate(zip(i['model_index'],i['matrix'])):
  if int(mid) not in groups:continue
  instances_with_water+=1;b=s.transform(bounds[int(mid)],pose)[:,(0,2)]
  if np.any(b.max(0)<lo) or np.any(b.min(0)>hi):continue
  candidate_instances+=1;fs=groups[int(mid)];world=s.transform(v[fs],pose)
  for fi,verts in zip(fs,world):
   n=int(m['vertices'][fi]);shape=Polygon(verts[:n][:,(0,2)]).convex_hull
   if not shape.intersects(footprint):continue
   flags=int(m['flags'][fi]);inter=shape.intersection(exposed)
   # Convex hull conservatively retains ambiguous faces; do not call them dry.
   ref=dict(instance=int(i['ids'][ii]),prototype=int(fi),model=cat[int(mid)]['name'],flags=flags,projected_conflict_area=float(inter.area),distance_to_conflict=float(shape.distance(exposed)))
   contacts.append(ref);near_water.append(verts);refs.append([int(i['ids'][ii]),int(fi),n,flags]);wgeom.append(shape)
   if flags and shape.intersects(exposed):unknown.append(ref)
 waterunion=shapely.union_all(wgeom)
 np.savez_compressed(O/'near-water.npz',vertices=np.asarray(near_water),refs=np.asarray(refs,dtype=np.int64))
 save('geometry.json',dict(footprint=shapely.to_geojson(footprint),road=shapely.to_geojson(roadpoly),exposed_conflict=shapely.to_geojson(exposed),native_nominal_wet_conflict=shapely.to_geojson(native_wet),actual_water=shapely.to_geojson(waterunion)))
 save('water-contacts.json',contacts);save('inputs.json',pins)
 result=dict(status='READ_ONLY_DISCRIMINATOR_COMPLETE',target=target['model'],all_instances=len(i['ids']),instances_with_water=instances_with_water,broadphase_instances=candidate_instances,near_water_faces=len(contacts),source_conflict_area=float(source_conflict.area),exposed_conflict_area=float(exposed.area),actual_water_projection_overlap=float(exposed.intersection(waterunion).area),distance_to_nearest_actual_water=float(exposed.distance(waterunion)),unknown_contacts=unknown,native_nominal_wet_overlap=float(native_wet.area),road_edges=rids,native_parts=parts,measurement=meter.memory(),limitations=['Coverage of sealed A inventory; conditional proxies stay unknown. Native nominal water is not runtime wave envelope. Target selected from already complete201 census; no new global acceptance.'])
 for p,d in pins.items():g.require(meter.sha(p)==d,'changed_after:'+p)
 save('report.json',result);print(json.dumps(result))
except Exception as ex:
 save('failure.json',dict(type=type(ex).__name__,error=str(ex),measurement=meter.memory()));raise
finally:stop.set()
