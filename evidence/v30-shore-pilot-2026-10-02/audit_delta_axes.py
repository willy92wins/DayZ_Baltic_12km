"""Read-only coverage gap audit: OSM axes of the two V3 navigable delta branches."""
from pathlib import Path
import json,sys
import numpy as np
import shapely
from shapely.geometry import shape,mapping
from shapely.ops import substring
R=Path('P:/DayZ_Baltic_12km_dev');E=Path(__file__).resolve().parent/'delta-audit'
sys.path.insert(0,str(R/'tools/water'));sys.path.insert(0,str(R/'tools/terrain'))
from water_common import read_shp
from v30_common import cell_planes
from audit_fairway_triangles_v30 import records,describe,controls,save,sha

def main():
 assert not E.exists();E.mkdir()
 terrain_path=Path('E:/DayZ-Baltic-Build/v30-fairway-candidate-bounded/terrain_v30.npz')
 t=np.load(terrain_path);h=t['heights'].astype(float);planes=cell_planes(t['cls'],t['level'].astype(float))
 design=R/'tests/water_v3/water_v3.geojson';features=json.loads(design.read_text())['features']
 branches=[f for f in features if f['properties']['class']=='delta_navigable'];assert len(branches)==2
 lines=read_shp('rivers',{'river','canal'});reports=[];exports=[]
 for f in branches:
  name=f['properties']['name'];water=shape(f['geometry'])
  selected=[(g,p) for g,p in lines if p['name']==name and g.intersects(water)]
  assert selected,name
  merged=shapely.line_merge(shapely.union_all([g for g,p in selected]))
  parts=list(merged.geoms) if hasattr(merged,'geoms') else [merged]
  for index,line in enumerate(parts):
   if line.length<=48:
    reports.append(dict(branch=name,part=index,excluded='Axis shorter than two 24 m endpoint margins',length_m=line.length));continue
   corridor=substring(line,24,line.length-24).buffer(12,cap_style='flat',join_style='round',quad_segs=32)
   rec=records(corridor,planes)
   report=dict(branch=name,part=index,length_m=line.length,osm_ids=[p['osm_id'] for g,p in selected],
               outside_branch_design_m2=float(corridor.difference(water).area),**describe(h,rec),controls=controls(h,rec))
   reports.append(report)
   exports.append(dict(type='Feature',properties=dict(branch=name,part=index,kind='axis'),geometry=mapping(line)))
   exports.append(dict(type='Feature',properties=dict(branch=name,part=index,kind='corridor24m'),geometry=mapping(corridor)))
 result=dict(status='FAIL' if any(r.get('failing_faces',0) for r in reports) else 'PASS_SCOPED_DELTA_AXES',
   inputs={str(p):sha(p) for p in [terrain_path,design,R/'source/vectors/rivers.shp',R/'source/vectors/rivers.dbf',Path(__file__)]},
   scope='Two navigable V3 delta branches; actual OSM centre lines merged by shared endpoints, 24 m useful width, min sea 0.5 m, depth 3 m with 1 cm tolerance.',
   exclusions=['24 m at branch endpoints; not mouth/confluence connectivity', 'Other delta branches intentionally not navigable in approved V3 design'],
   limitations=['Read-only diagnostic; does not invent a replacement route or alter geometry.', 'Axis corridor outside its approved polygon is separately reported, not clipped away.', 'No boat/collision/engine-wave acceptance.'],
   branches=reports)
 save(E/'audit.json',result);save(E/'axes-corridors.geojson',dict(type='FeatureCollection',features=exports))
 print(json.dumps({'status':result['status'],'branches':reports}))

if __name__=='__main__':main()
