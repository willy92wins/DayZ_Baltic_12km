"""Frozen Luga boundary stations; inspect the visible native-triangle waterline.
Missing crossings are not filled or connected across gaps for curvature metrics.
"""
from pathlib import Path
import sys,json,numpy as np,shapely
from shapely.geometry import shape
from scipy.ndimage import gaussian_filter1d
W=Path(__file__).resolve().parents[3];sys.path[:0]=[str(W/'tools/water'),str(W/'tools/terrain')]
from audit_waterline_v30 import measure
from v30_common import grid_xz
B=Path('E:/DayZ-Baltic-Build/v30-smoothing-pilot-20261007')
SOURCE=Path('E:/DayZ-Baltic-Build/v30-v12/inland/terrain_inland.npz')

def stats(P,RID,off,keep):
 good=keep&np.isfinite(off)
 zig=[]; turns=[]; triples=0
 for r in np.unique(RID):
  ix=np.flatnonzero(RID==r);n=len(ix)
  if n<30:continue
  o=off[ix];ok=good[ix]
  # Do not join the two sides of a missing/excluded run. A 25-point complete
  # window allows a 12m residual at 2m station spacing; no synthetic zeros.
  for i in range(12,n-12):
   if not ok[i-12:i+13].all():continue
   d=np.arange(-12,13);weight=np.exp(-.5*(d/6.)**2);weight/=weight.sum()
   zig.append(o[i]-float(np.dot(weight,o[i-12:i+13])))
  v=P[ix]+NORMAL[ix]*np.nan_to_num(o)[:,None]
  valid=ok[3:-3]&ok[:-6]&ok[6:]
  aa=v[3:-3]-v[:-6];bb=v[6:]-v[3:-3]
  norm=np.linalg.norm(aa,axis=1)*np.linalg.norm(bb,axis=1)
  angle=np.degrees(np.arccos(np.clip((aa*bb).sum(1)/np.maximum(norm,1e-12),-1,1)))
  turns.extend(angle[valid].tolist());triples+=int(valid.sum())
 z=np.asarray(zig);t=np.asarray(turns)
 return {'stations':int(keep.sum()),'crossings':int(good.sum()),'missing':int((keep&~np.isfinite(off)).sum()),'offset_p90_m':float(np.percentile(np.abs(off[good]),90)),'zigzag_rms_m':float(np.sqrt(np.mean(z*z))) if len(z) else None,'zigzag_stations':len(z),'turn_gt30_share':float(np.mean(t>30)) if len(t) else None,'valid_turn_triples':triples}

def main():
 global NORMAL
 f=json.loads(Path('E:/DayZ-Baltic-Build/v30-redesign/design/water_v3.geojson').read_text(encoding='utf-8'))['features']
 g=next(shape(x['geometry']) for x in f if x['properties'].get('id')=='Luga_0')
 others=shapely.union_all([shape(x['geometry']) for x in f if x['properties'].get('id')!='Luga_0'])
 ps=[];ns=[];rs=[]
 for poly in getattr(g,'geoms',[g]):
  for ring in [poly.exterior,*poly.interiors]:
   n=int(ring.length//2);p=np.array([ring.interpolate(v).coords[0] for v in np.arange(n)*2.])
   if n<4:continue
   tangent=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0);tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-12)
   normal=np.column_stack([tangent[:,1],-tangent[:,0]])
   inside=shapely.contains(poly,shapely.points(p+normal));normal[inside]*=-1
   rs.append(np.full(n,len(rs)));ps.append(p);ns.append(normal)
 P=np.vstack(ps);NORMAL=np.vstack(ns);RID=np.concatenate(rs);kind=np.full(len(P),'river')
 keep=(P[:,0]>66)&(P[:,0]<12216)&(P[:,1]>66)&(P[:,1]<12216)&(np.hypot(P[:,0]-2417.1428,P[:,1]-6889.885)>620)&(shapely.distance(shapely.points(P),others)>18)
 with np.load(SOURCE) as f:base=dict(f)
 with np.load(B/'luga-frozen-masks.npz') as f:fixed=f['frozen'];allowed=f['allowed'];corridor=f['corridor']
 c=np.clip(np.rint(P[:,0]/6).astype(int),0,2047);r=np.clip(np.rint((12282-P[:,1])/6).astype(int),0,2047)
 keep &= ~fixed[r,c]
 scopes={'all':keep,'west':keep&(P[:,0]<5000),'central':keep&(P[:,0]>=5000)&(P[:,0]<8000),'east':keep&(P[:,0]>=8000)}
 results={}; offs={}
 for label,path in [('12',SOURCE),('18',B/'luga-18/terrain_inland.npz'),('24',B/'luga-24/terrain_inland.npz')]+([('18-vector',B/'luga-18-vector/terrain_inland.npz')] if (B/'luga-18-vector/terrain_inland.npz').exists() else []):
  _,off=measure(str(path),P,NORMAL,kind,RID,np.ones(len(P),bool));offs[label]=off
  with np.load(path) as f:u=dict(f)
  results[label]={'by_sector':{k:stats(P,RID,off,m) for k,m in scopes.items()},'corridor_exact':bool(np.array_equal(base['heights'][corridor],u['heights'][corridor])),'outside_allowed_exact':bool(np.array_equal(base['heights'][~allowed],u['heights'][~allowed])),'metadata_exact':all(np.array_equal(v,u[k],equal_nan=True) for k,v in base.items() if k!='heights')}
  if label!='12':
   gates={}
   for k,v in results[label]['by_sector'].items():
    old=results['12']['by_sector'][k]
    gates[k+'_missing']=v['missing']<=old['missing'];gates[k+'_offset']=v['offset_p90_m']<=old['offset_p90_m'];gates[k+'_zigzag']=v['zigzag_rms_m']<old['zigzag_rms_m']
   gates.update({k:results[label][k] for k in ('corridor_exact','outside_allowed_exact','metadata_exact')})
   results[label]['gates']=gates;results[label]['status']='PASS_OFFLINE_SHORE_ONLY' if all(gates.values()) else 'FAIL'
  print(label,results[label],flush=True)
 np.savez_compressed(B/'luga-waterline-stations.npz',points=P,normal=NORMAL,ring_id=RID,keep=keep,**{'offset_'+k:v for k,v in offs.items()})
 (B/'luga-independent.json').write_text(json.dumps({'source_outline':'v30-redesign/design/water_v3.geojson::Luga_0','step_m':2,'probe_ds_m':.25,'search_m':8,'excluded_stations':int((~keep).sum()),'variants':results},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
