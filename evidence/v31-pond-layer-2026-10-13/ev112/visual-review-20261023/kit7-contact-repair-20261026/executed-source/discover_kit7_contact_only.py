from pathlib import Path
import hashlib,json,sys
import numpy as np
from shapely.geometry import MultiPoint,Polygon
import shapely
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');sys.path.insert(0,str(W/'tools/water'))
from review_compact_collision_v31 import load,vertices
from overlap_stream_collision_v31 import expanded_component,selected_components
A=R/'river-kit7-midpoint-a-20261026';targets=json.loads((R/'kit7-native-contact-diagnosis-20261026/targets.json').read_text());rows=[]
for i in json.loads((A/'author-report.json').read_text())['instances']:
 name=i['model'].split('\\')[-1]
 if name not in targets:continue
 _,lods,_=load(A/'source/baltic_stream_pilot'/name);g=lods[1];old=np.array([p.coords for p in g.points]);chosen=selected_components(g,targets[name],i['origin'],minimal_bbox_anchors=True)
 chosen={n:why for n,why in chosen.items() if 'contact_footprint' in why};assert chosen
 allxyz=[];over=[];excess=[]
 t=vertices(lods[0],[f for f in lods[0].faces if 'water_streambed.rvmat' not in f.material]);allowed=shapely.union_all([Polygon(a[:,[0,2]]) for a in t]).buffer(.0100001)
 for n,s in g.selections.items():
  xyz=np.array([p.coords for p in s.points])
  if n in chosen:
   part=expanded_component(xyz);xyz=part['points']
   if len(xyz)>72 or len(part['faces'])>140:over.append(n)
   extra=MultiPoint(xyz[:,[0,2]]).convex_hull.difference(allowed).area
   if extra>1e-8:excess.append(dict(component=n,area=extra))
  allxyz.extend(xyz)
 new=np.array(allxyz)
 rows.append(dict(model=name,chosen=chosen,bbox_exact=bool(np.array_equal(old.min(0),new.min(0)) and np.array_equal(old.max(0),new.max(0))),delta_min=(new.min(0)-old.min(0)).tolist(),delta_max=(new.max(0)-old.max(0)).tolist(),over_caps=over,horizontal_excess=excess))
report=dict(status='DISCOVERY_CONTACT_ONLY',rows=rows,all_bbox_exact=all(r['bbox_exact'] for r in rows),horizontal_excess_models=sum(bool(r['horizontal_excess']) for r in rows),oversized=sum(len(r['over_caps']) for r in rows))
(R/'kit7-contact-only-discovery.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

