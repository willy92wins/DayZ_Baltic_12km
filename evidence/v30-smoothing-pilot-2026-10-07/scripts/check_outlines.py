"""Independent geometry check against frozen unsmoothed design; no writes to inputs."""
from pathlib import Path
import sys,json,numpy as np,shapely
from shapely.geometry import shape
W=Path(__file__).resolve().parents[3]
B=Path('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007')
SRC=Path('E:/DayZ-Baltic-Build/v30-redesign/design')
CONTOUR=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson')

def rings(g):
 return [r for p in getattr(g,'geoms',[g]) if p.geom_type=='Polygon' for r in [p.exterior,*p.interiors]]

def directed(a,b):
 points=np.concatenate([shapely.get_coordinates(shapely.segmentize(r,1.0)) for r in rings(a)])
 seg=[]
 for r in rings(b):
  p=np.asarray(r.coords); seg.append(np.stack([p[:-1],p[1:]],axis=1))
 tree=shapely.STRtree(shapely.linestrings(np.concatenate(seg)))
 _,d=tree.query_nearest(shapely.points(points),return_distance=True,all_matches=False)
 return float(d.max())

def main():
 source=[*json.loads((SRC/'water_v3.geojson').read_text(encoding='utf-8'))['features'],*json.loads(CONTOUR.read_text(encoding='utf-8'))['features']]
 streams=[f for f in json.loads((SRC/'streams_candidates.geojson').read_text(encoding='utf-8'))['features'] if f['properties'].get('tier_m',0)>=2500]
 source += streams
 gs=[shape(f['geometry']) for f in source]
 drawn=[not f['properties'].get('body','').startswith('river_contour') for f in source]
 tree=shapely.STRtree(gs)
 pairs=[]
 for i,g in enumerate(gs):
  for j in tree.query(g.buffer(0.05)):
   if j>i and drawn[i] and drawn[j] and g.distance(gs[j])<=0.05: pairs.append((i,int(j),g.distance(gs[j])))
 reports={}
 for label,folder in ([(sys.argv[1],B/('design-'+sys.argv[1]))] if len(sys.argv)>1 else [('12',Path('E:/DayZ-Baltic-Build/v30-v11/design')),('18',B/'design-18'),('24',B/'design-24')]):
  fs=[*json.loads((folder/'water_v3.geojson').read_text(encoding='utf-8'))['features'],*json.loads((folder/'contour_lakes.geojson').read_text(encoding='utf-8'))['features']]
  fs += streams
  assert len(fs)==len(source)
  out=[shape(f['geometry']) for f in fs]
  details=[]; forb=[]
  for i,(f,g,h) in enumerate(zip(source,gs,out)):
   assert f['properties']==fs[i]['properties']
   cls=f['properties'].get('class',f['properties'].get('body',''))
   allowed=cls in ('river','pond') or cls.startswith('lake')
   if not g.equals(h) and not allowed: forb.append(i)
   if not allowed or g.equals(h): continue
   d=max(directed(g,h),directed(h,g))
   details.append({'index':i,'kind':cls,'sampled_final_hausdorff_m':d,'area_change_pct':100*(h.area/g.area-1),'valid':bool(h.is_valid),'continuous_4m':bool(g.boundary.buffer(4.0,quad_segs=64).covers(h.boundary) and h.boundary.buffer(4.0,quad_segs=64).covers(g.boundary)),'holes_before':sum(len(p.interiors) for p in getattr(g,'geoms',[g])),'holes_after':sum(len(p.interiors) for p in getattr(h,'geoms',[h]))})
  gaps=[{'i':i,'j':j,'before':d,'after':float(out[i].distance(out[j]))} for i,j,d in pairs if out[i].distance(out[j])>d+0.05]
  violations=[x for x in details if x['sampled_final_hausdorff_m']>4.00001 or abs(x['area_change_pct'])>2.0 or not x['valid'] or not x['continuous_4m'] or x['holes_before']!=x['holes_after']]
  reports[label]={'features_measured':len(details),'forbidden_changes':forb,'max_final_sampled_shift_m':max(x['sampled_final_hausdorff_m'] for x in details),'over_4m':sum(x['sampled_final_hausdorff_m']>4.00001 for x in details),'area_over_2pct':sum(abs(x['area_change_pct'])>2 for x in details),'topology_changes':sum(x['holes_before']!=x['holes_after'] for x in details),'contact_gaps':gaps,'violations':violations,'details':details,'status':'FAIL' if violations or forb or gaps else 'PASS_VECTOR_GEOMETRY_ONLY'}
  print(label,{k:v for k,v in reports[label].items() if k not in ('details','violations','contact_gaps')},flush=True)
 (B/('outline-independent-'+sys.argv[1]+'.json') if len(sys.argv)>1 else B/'outline-independent.json').write_text(json.dumps({'sampling_m':1.0,'hausdorff_sampling_upper_error_m':0.5,'frozen_reference':str(SRC),'variants':reports},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__': main()
