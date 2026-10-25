from pathlib import Path
import json,csv,hashlib
import numpy as np
from scipy.ndimage import distance_transform_edt,label,median_filter
O=Path(r'E:/DayZ-Baltic-Build/v30-bank-relief-review-20261010/luna-geometry'); R=Path(r'E:/DayZ-Baltic-Build'); C=R/'v30-remaining-exact-dry-support-20261009/candidate'
T=dict(np.load(C/'terrain.npz'));h=T['heights'].astype(np.float64);cls=T['cls'];p=np.load(C/'plane.npy');f=np.load(C/'visible-field.npy');con=np.load(R/'v30-remaining-exact-dry-support-20261009/constraints.npz')
nom=np.fmax(p,.85);vis=np.where(np.isfinite(p)[:,:,None],f,.85);corner=((0,0),(0,1),(1,0),(1,1)); tri=((0,1,3),(0,2,3)); face=[];support=np.zeros(h.shape,bool)
for ids in tri:
 w=np.zeros(p.shape,bool)
 for j in ids:
  dr,dc=corner[j];hv=h[dr:dr+p.shape[0],dc:dc+p.shape[1]];w|=(nom>hv)|(vis[:,:,j]>hv)
 face.append(w)
 for j in ids:
  dr,dc=corner[j];support[dr:dr+p.shape[0],dc:dc+p.shape[1]]|=w
assert np.array_equal(support,con['water_support'].astype(bool))
flow=np.isin(cls,[3,5,6]);belt=distance_transform_edt(~flow,sampling=6)<=96
base=belt&(cls==0)&~support&~T['water'].astype(bool)&~T['beach'].astype(bool)&~T['reserve'].astype(bool)&~T['platform'].astype(bool);fixed=con['fixed'].astype(bool)
# 8-connected watercourse labels are geographic sector buckets, not flow-physics claims.
flowids,n=label(flow,structure=np.ones((3,3),np.uint8));near=distance_transform_edt(~flow,return_distances=False,return_indices=True)
# Existing crease formulas from audit_native_surface.py, shared/native face normals.
nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:];one=np.ones_like(nw)
a=np.stack((-(ne-nw)/6,one,(se-ne)/6),-1);a/=np.linalg.norm(a,axis=-1)[...,None]
b=np.stack((-(se-sw)/6,one,(sw-nw)/6),-1);b/=np.linalg.norm(b,axis=-1)[...,None]
def angle(a,b):return np.degrees(np.arctan2(np.linalg.norm(np.cross(a,b),axis=-1),np.einsum('ijk,ijk->ij',a,b)))
hinges=[('diagonal',angle(a,b)),('vertical',angle(a[:,:-1],b[:,1:])),('horizontal',angle(b[:-1],a[1:]))]
def any4(m,k):
 if k=='diagonal':return m[:-1,:-1]|m[:-1,1:]|m[1:,:-1]|m[1:,1:]
 if k=='vertical':return m[:-1,:-2]|m[:-1,1:-1]|m[1:,1:-1]|m[1:,2:]
 return m[:-2,:-1]|m[1:-1,:-1]|m[1:-1,1:]|m[2:,1:]
def all4(m,k):
 if k=='diagonal':return m[:-1,:-1]&m[:-1,1:]&m[1:,:-1]&m[1:,1:]
 if k=='vertical':return m[:-1,:-2]&m[:-1,1:-1]&m[1:,1:-1]&m[1:,2:]
 return m[:-2,:-1]&m[1:-1,:-1]&m[1:-1,1:]&m[2:,1:]
def vs(k,r,c):
 if k=='diagonal':return [(r,c),(r,c+1),(r+1,c),(r+1,c+1)]
 if k=='vertical':return [(r,c),(r,c+1),(r+1,c+1),(r+1,c+2)]
 return [(r,c),(r+1,c),(r+1,c+1),(r+2,c+1)]
def xy(k,r,c):
 if k=='diagonal':return (c+.5)*6,12282-(r+.5)*6
 if k=='vertical':return (c+1)*6,12282-(r+.5)*6
 return (c+.5)*6,12282-(r+1)*6
med=median_filter(h,size=5,mode='nearest');records=[]
for k,ang in hinges:
 valid=(ang>30)&any4(base,k)&~all4(base,k)
 for r,c in zip(*np.nonzero(valid)):
  r=int(r);c=int(c);v=vs(k,r,c);x,z=xy(k,r,c)
  if k=='diagonal': w1,w2=bool(face[0][r,c]),bool(face[1][r,c])
  elif k=='vertical':w1,w2=bool(face[0][r,c]),bool(face[1][r,c+1])
  else:w1,w2=bool(face[1][r,c]),bool(face[0][r+1,c])
  flowverts=[(y,xx) for y,xx in v if flow[y,xx]]
  if flowverts:
   ids=[int(flowids[y,xx]) for y,xx in flowverts];comp=int(np.bincount(ids).argmax());dist=0.;codes=','.join(map(str,sorted({int(cls[y,xx]) for y,xx in flowverts})))
  else:
   qr=int(np.clip(round((12282-z)/6),0,2047));qc=int(np.clip(round(x/6),0,2047));fr,fc=near[:,qr,qc];comp=int(flowids[fr,fc]);dist=float(np.hypot(fr-qr,fc-qc)*6);codes=''
  dryfree=[(y,xx) for y,xx in v if base[y,xx] and not fixed[y,xx]]
  dryall=[(y,xx) for y,xx in v if cls[y,xx]==0]
  dry_support=[(y,xx) for y,xx in v if cls[y,xx]==0 and support[y,xx]]
  prom=[float(h[y,xx]-med[y,xx]) for y,xx in v if cls[y,xx]==0 and not support[y,xx]]
  records.append(dict(kind=k,row=r,col=c,x_m=x,z_m=z,angle_deg=float(ang[r,c]),face_state='wet-dry' if w1!=w2 else ('wet-wet' if w1 else 'dry-dry'),face_wet=[w1,w2],bank_vertices=sum(bool(base[y,xx]) for y,xx in v),dry_class0_vertices=len(dryall),wet_support_vertices=sum(bool(support[y,xx]) for y,xx in v),dry_class0_wet_support_vertices=len(dry_support),fixed_vertices=sum(bool(fixed[y,xx]) for y,xx in v),eligible_dry_vertices_not_fixed=len(dryfree),hard_engineering_vertices=sum(bool(T['reserve'][y,xx] or T['platform'][y,xx]) for y,xx in v),water_beach_vertices=sum(bool(T['water'][y,xx] or T['beach'][y,xx]) for y,xx in v),flow_component=comp,flow_distance_m=dist,adjacent_flow_codes=codes,dry_vertex_prominence_vs_5x5_median_m=max(prom,key=abs) if prom else None,vertices_rc=[list(q) for q in v]))
assert len(records)==4768,len(records)
# label metadata by spatial extents and class mix only. Flow component is 8-neighbor cls3/5/6.
by={}
for q in records:
 g=by.setdefault(str(q['flow_component']),dict(hinges=0,wet_dry=0,wet_wet=0,dry_dry=0,max_angle_deg=0.,max_prominence_abs_m=0.,bbox=[1e9,1e9,-1e9,-1e9],mean_nearest_distance_m=0.,shoreline_with_dryfree=0))
 g['hinges']+=1;g[q['face_state'].replace('-','_')]+=1;g['max_angle_deg']=max(g['max_angle_deg'],q['angle_deg']);g['max_prominence_abs_m']=max(g['max_prominence_abs_m'],abs(q['dry_vertex_prominence_vs_5x5_median_m'] or 0.))
 g['bbox']=[min(g['bbox'][0],q['x_m']),min(g['bbox'][1],q['z_m']),max(g['bbox'][2],q['x_m']),max(g['bbox'][3],q['z_m'])];g['mean_nearest_distance_m']+=q['flow_distance_m']
 if q['face_state']=='wet-dry' and q['eligible_dry_vertices_not_fixed']>0:g['shoreline_with_dryfree']+=1
for k,g in by.items():g['mean_nearest_distance_m']/=g['hinges'];g['component_vertex_count']=int((flowids==int(k)).sum());g['component_class_codes']=','.join(map(str,sorted({int(x) for x in np.unique(cls[flowids==int(k)])})))
from collections import Counter
states=Counter(q['face_state'] for q in records)
summary={'candidate_hinges':len(records),'face_states':dict(states),'by_flow_component':sorted([dict(component=int(k),**v) for k,v in by.items()],key=lambda a:(-a['hinges'],a['component'])),'per_face_state':{},'all_high_creases_gt30_touching_base':len(records),'source':{'terrain_sha256':hashlib.sha256((C/'terrain.npz').read_bytes()).hexdigest(),'plane_sha256':hashlib.sha256((C/'plane.npy').read_bytes()).hexdigest(),'visible_field_sha256':hashlib.sha256((C/'visible-field.npy').read_bytes()).hexdigest(),'constraints_sha256':hashlib.sha256((R/'v30-remaining-exact-dry-support-20261009/constraints.npz').read_bytes()).hexdigest()},'method':{'domain':'>30 degree native shared hinges; at least one unique vertex in class0 96m band outside exact wet support, water/beach, reserve/platform; exclude 4/4 base-dry hinges','shoreline':'XOR of actual wet status on two incident source triangles using nominal=max(P,0.85) and visible F per exact EV71 consumer','dry_support':'vertices class0 and marked by exact wet support; support is preserved, dry side is potentially editable only when base eligible and no current fixed mask','flow_grouping':'8-connected raster components in combined cls {3,5,6}; spatial sector grouping only, not flow-physics proof','prominence':'max signed dry non-support vertex height minus 5x5 terrain median; a screening metric, not a visual pyramid verdict'}}
for state in ('wet-dry','wet-wet','dry-dry'):
 rs=[q for q in records if q['face_state']==state]
 summary['per_face_state'][state]={'hinges':len(rs),'dry_support_vertices_total':sum(q['dry_class0_wet_support_vertices'] for q in rs),'direct_wet_support_vertices_total':sum(q['wet_support_vertices'] for q in rs),'eligible_dry_vertices_not_fixed_total':sum(q['eligible_dry_vertices_not_fixed'] for q in rs),'engineering_vertex_hits':sum(q['hard_engineering_vertices'] for q in rs),'water_beach_vertex_hits':sum(q['water_beach_vertices'] for q in rs),'component_count':len({q['flow_component'] for q in rs}),'component_top':Counter(q['flow_component'] for q in rs).most_common(12)}
# Three focus anchors require true wet-dry hinge, >=2 available dry non-support vertices, no direct engineering hits,
# and nontrivial relief. Rank high prominence first then angle; spatially separate components / >=300m.
candidates=[q for q in records if q['face_state']=='wet-dry' and q['eligible_dry_vertices_not_fixed']>=2 and q['hard_engineering_vertices']==0 and q['water_beach_vertices']==0 and q['dry_vertex_prominence_vs_5x5_median_m'] is not None]
candidates.sort(key=lambda q:(abs(q['dry_vertex_prominence_vs_5x5_median_m']),q['angle_deg']),reverse=True)
focus=[]
for q in candidates:
 if all(q['flow_component']!=v['flow_component'] and np.hypot(q['x_m']-v['x_m'],q['z_m']-v['z_m'])>=300 for v in focus):
  focus.append(q)
 if len(focus)==3:break
summary['focus_selection_rule']='3 spatially separated (>=300m) true wet/dry folds, distinct 8-connected flow components, at least 2 base-eligible dry nonsupport vertices not currently fixed, no reserve/platform/water/beach vertices; ranked by absolute dry nonsupport vertex prominence vs 5x5 median then angle. These are diagnostic candidates only.'
summary['focus_candidates_found']=len(focus)
summary['focuses']=focus
(O/'non4of4-fold-classification.json').write_text(json.dumps({'summary':summary,'records':records},indent=2)+'\n')
with (O/'non4of4-folds.csv').open('w',newline='',encoding='utf-8') as fp:
 w=csv.DictWriter(fp,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
print(json.dumps({'total':len(records),'face_states':summary['face_states'],'by_flow_component':summary['by_flow_component'][:20],'per_face_state':summary['per_face_state'],'focus_candidates_found':len(focus),'focuses':focus},indent=2))

