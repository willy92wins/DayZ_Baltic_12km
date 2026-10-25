from __future__ import annotations
import hashlib, json, math
from pathlib import Path
import numpy as np

ROOT=Path(r'E:/DayZ-Baltic-Build')
EV82=ROOT/'v30-mixed-bank-incremental-fixed-20261010'
EV79=ROOT/'v30-narva-dry-bank-relief-20261010'
OUT=ROOT/'v30-global-strict-bank-relief-20261010/residual-review'
N0=(840,370)
SEA=.85
TRIS=((0,1,3),(0,2,3))
OFF=((0,0),(0,1),(1,0),(1,1))
EXPECTED={
 'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 'EV79':'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
 'P':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
 'F':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
 'constraints':'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
}
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def unique(points,tol=1e-8):
 out=[]
 for p in points:
  if not any(np.linalg.norm(p-q)<=tol for q in out):out.append(p)
 return out
def contour_segments(h,levels,kind,cell_r,cell_c):
 # corners NW,NE,SW,SE and the verified NW-SE terrain diagonal.
 xy=np.array([[cell_c*6,12282-cell_r*6],[(cell_c+1)*6,12282-cell_r*6],
              [cell_c*6,12282-(cell_r+1)*6],[(cell_c+1)*6,12282-(cell_r+1)*6]],float)
 segs=[]
 for tri_id,tri in enumerate(TRIS):
  inds=list(tri); pts=[]
  for a,b in ((inds[0],inds[1]),(inds[1],inds[2]),(inds[2],inds[0])):
   da=float(h[a]-levels[a]); db=float(h[b]-levels[b])
   if da==0: pts.append(xy[a])
   if (da<0<db) or (db<0<da): pts.append(xy[a]+(xy[b]-xy[a])*(da/(da-db)))
   if db==0: pts.append(xy[b])
  pts=unique(pts)
  if len(pts)>=2:
   # Keep farthest pair for vertex-on-edge degeneracies.
   pair=max(((a,b) for i,a in enumerate(pts) for b in pts[i+1:]),key=lambda ab:np.linalg.norm(ab[0]-ab[1]))
   if np.linalg.norm(pair[0]-pair[1])>1e-9:
    segs.append({'kind':kind,'cell':[cell_r,cell_c],'triangle':tri_id,'a':pair[0],'b':pair[1],
                 'levels':levels,'tri':inds})
 return segs
def closest(seg,pt):
 a,b=seg['a'],seg['b'];v=b-a; t=float(np.clip(np.dot(pt-a,v)/np.dot(v,v),0,1));q=a+t*v
 if seg['kind'] in ('P','SEA'): level=float(seg['levels'][0])
 else:
  # Interpolate the same triangular F field at the projected point using barycentric coordinates.
  r,c=seg['cell']; tri=seg['tri'];
  xy=np.array([[c*6,12282-r*6],[(c+1)*6,12282-r*6],[c*6,12282-(r+1)*6],[(c+1)*6,12282-(r+1)*6]],float)[tri]
  mat=np.column_stack((xy[1]-xy[0],xy[2]-xy[0])); uv=np.linalg.solve(mat,q-xy[0]); weights=np.array([1-uv.sum(),uv[0],uv[1]])
  level=float(np.dot(weights,np.array(seg['levels'])[tri]))
 return q,float(np.linalg.norm(pt-q)),level
def boundary_height(x,z,h):
 # Bilinear interpolation on one outer edge of the two-node collar.
 rlo,rhi,clo,chi=832,848,362,378
 eps=1e-6
 if abs(x-clo*6)<eps or abs(x-chi*6)<eps:
  c=clo if abs(x-clo*6)<eps else chi
  rf=(12282-z)/6; r0=max(rlo,min(rhi-1,int(math.floor(rf))));t=rf-r0
  return float((1-t)*h[r0,c]+t*h[r0+1,c])
 if abs(z-(12282-rlo*6))<eps or abs(z-(12282-rhi*6))<eps:
  r=rlo if abs(z-(12282-rlo*6))<eps else rhi
  cf=x/6;c0=max(clo,min(chi-1,int(math.floor(cf))));t=cf-c0
  return float((1-t)*h[r,c0]+t*h[r,c0+1])
 raise ValueError('ray did not intersect exact outer collar edge')
def ray_to_collar(q,pt,h):
 v=pt-q; d=float(np.linalg.norm(v))
 if d<1e-9:return None
 u=v/d;xlo,xhi=362*6,378*6;zlo,zhi=12282-848*6,12282-832*6
 hits=[]
 for bound,origin,du in ((xlo,q[0],u[0]),(xhi,q[0],u[0]),(zlo,q[1],u[1]),(zhi,q[1],u[1])):
  if abs(du)<1e-12:continue
  s=(bound-origin)/du
  if s>d+1e-8:
   x=q[0]+s*u[0];z=q[1]+s*u[1]
   if xlo-1e-6<=x<=xhi+1e-6 and zlo-1e-6<=z<=zhi+1e-6:hits.append((float(s),np.array([x,z])))
 if not hits:return None
 s,p=max(hits,key=lambda x:x[0]) # continue through the full window to the outer collar edge
 return {'D_m':float(s),'xy':p,'height_m':boundary_height(float(p[0]),float(p[1]),h)}
def main():
 bp=EV82/'candidate/terrain.npz'; ep=EV79/'candidate/terrain.npz'; pp=EV79/'candidate/plane.npy'; fp=EV79/'candidate/visible-field.npy'; cp=EV79/'constraints.npz'; priorp=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
 paths={'B':bp,'EV79':ep,'P':pp,'F':fp,'constraints':cp}
 for k,p in paths.items():assert sha(p)==EXPECTED[k],(k,sha(p))
 with np.load(bp,allow_pickle=False) as z: h=z['heights'].astype(np.float64); cls=z['cls']; reserve=z['reserve'].astype(bool); platform=z['platform'].astype(bool)
 with np.load(ep,allow_pickle=False) as z: e=z['heights'].astype(np.float64)
 P=np.load(pp,mmap_mode='r');F=np.load(fp,mmap_mode='r')
 with np.load(cp,allow_pickle=False) as z: other=z['other_fixed'].astype(bool);eng=z['engineering_halo'].astype(bool);support=z['wet_support'].astype(bool)
 with np.load(priorp,allow_pickle=False) as z: large=z['large_lake_banks'].astype(bool)
 r0,c0=N0;win=(r0-8,r0+9,c0-8,c0+9);core=(r0-6,r0+7,c0-6,c0+7)
 protected=other|eng|large|reserve|platform
 # Per-corner incident level bound, used only to count eligible dry vertices and reproduce EV79 floor.
 level=np.full((2048,2048),SEA,dtype=np.float64)
 for cr in range(r0-9,r0+9):
  for cc in range(c0-9,c0+9):
   pl=float(P[cr,cc]); ff=np.asarray(F[cr,cc],dtype=np.float64)
   vals=[SEA]
   if np.isfinite(pl):vals.append(pl)
   for k,(dr,dc) in enumerate(((0,0),(0,1),(1,0),(1,1))):
    fv=float(ff[k]); valsk=vals+[fv] if np.isfinite(fv) else vals
    rr,cc2=cr+dr,cc+dc;level[rr,cc2]=max(level[rr,cc2],max(valsk))
 # Build actual B face contours separately per source surface and SEA. Only nearby cells matter.
 segs=[]
 for cr in range(r0-9,r0+9):
  for cc in range(c0-9,c0+9):
   hs=np.array([h[cr,cc],h[cr,cc+1],h[cr+1,cc],h[cr+1,cc+1]],float)
   pl=float(P[cr,cc])
   if math.isfinite(pl):segs+=contour_segments(hs,np.full(4,pl),'P',cr,cc)
   ff=np.asarray(F[cr,cc],dtype=float)
   if np.isfinite(ff).all():segs+=contour_segments(hs,ff,'F',cr,cc)
   segs+=contour_segments(hs,np.full(4,SEA),'SEA',cr,cc)
 # Only core vertices that are class0, not protected and dry at every incident water sample.
 rlo,rhi,clo,chi=core
 free=[]
 for r in range(rlo,rhi):
  for c in range(clo,chi):
   if cls[r,c]!=0 or protected[r,c] or h[r,c]<=level[r,c]:continue
   free.append((r,c))
 records=[]; counts={'free':len(free),'no_nearest_segment':0,'ray_missing_or_ambiguous':0,'targets_below_lower':0,'targets_above_B':0}
 under_clamp=np.zeros((13,13),bool); clamped=np.full((13,13),np.nan,dtype=np.float32); bb=h[rlo:rhi,clo:chi]
 for r,c in free:
  pt=np.array([c*6,12282-r*6],float)
  candidates=[]
  for s in segs:
   q,d,lev=closest(s,pt)
   candidates.append((d,s['kind'],q,lev,s))
  candidates.sort(key=lambda x:x[0])
  if not candidates:
   counts['no_nearest_segment']+=1;continue
  d0=candidates[0][0]
  nearest=[x for x in candidates if x[0]<=d0+1e-6]
  # Collapse coincident triangle segments into geometric projections, but preserve P/F identity.
  projections=[]
  for d,k,q,lev,s in nearest:
   hit=next((x for x in projections if x['kind']==k and np.linalg.norm(x['q']-q)<=1e-4 and abs(x['level']-lev)<=1e-6),None)
   if hit is None:projections.append({'kind':k,'q':q,'level':lev,'d':d,'cell':s['cell'],'tri':s['triangle']})
  per_kind={}
  for k in ('P','F','SEA'):
   options=[x for x in candidates if x[1]==k]
   if options:
    x=options[0];per_kind[k]={'distance_m':x[0],'projection_xz_m':[float(x[2][0]),float(x[2][1])],'level_m':x[3],'cell':x[4]['cell'],'triangle':x[4]['triangle']}
  chosen=projections[0]
  ray=ray_to_collar(chosen['q'],pt,h)
  if ray is None:
   counts['ray_missing_or_ambiguous']+=1;continue
  D=ray['D_m'];t=min(1.,max(0.,d0/D));sval=6*t**5-15*t**4+10*t**3
  target=chosen['level']+(ray['height_m']-chosen['level'])*sval
  lower=max(float(e[r,c])-2.,min(float(e[r,c]),1.8),min(float(e[r,c]),float(level[r,c])+1e-4))
  upper=min(float(e[r,c])+2.,float(h[r,c]))
  if target<lower:counts['targets_below_lower']+=1;under_clamp[r-rlo,c-clo]=True
  if target>upper:counts['targets_above_B']+=1
  clamped[r-rlo,c-clo]=np.float32(min(upper,max(lower,target)))
  pf=[per_kind[k] for k in ('P','F') if k in per_kind]
  conflict=False
  if len(pf)==2:
   conflict=(math.dist(pf[0]['projection_xz_m'],pf[1]['projection_xz_m'])>1e-3 or abs(pf[0]['level_m']-pf[1]['level_m'])>1e-3)
  records.append({'row':r,'col':c,'x_m':c*6,'z_m':12282-r*6,'B_m':float(h[r,c]),'lower_m':lower,'upper_m':upper,
    'nearest_distance_m':d0,'nearest_tied_unique_projections':len(projections),'nearest_projection_types':[x['kind'] for x in projections],
    'P_nearest':per_kind.get('P'),'F_nearest':per_kind.get('F'),'SEA_nearest':per_kind.get('SEA'),'P_F_conflict':conflict,
    'chosen_projection':{'kind':chosen['kind'],'xz_m':[float(chosen['q'][0]),float(chosen['q'][1])],'level_m':chosen['level']},
    'ray_to_outer_collar_D_m':D,'collar_height_m':ray['height_m'],'t':t,'smoothstep':sval,'target_m':target,
    'target_below_lower':target<lower,'clamped_float32_m':float(clamped[r-rlo,c-clo])})
 # New 2x2 exact plateaus after lower/upper clamp, compared with B float32 in matching squares.
 squares=[]
 for rr in range(12):
  for cc in range(12):
   vals=clamped[rr:rr+2,cc:cc+2]
   if np.isfinite(vals).all() and np.all(vals==vals.flat[0]):
    old=bb[rr:rr+2,cc:cc+2].astype(np.float32)
    if not np.all(old==old.flat[0]):squares.append({'rows':[rlo+rr,rlo+rr+1],'cols':[clo+cc,clo+cc+1],'clamp_m':float(vals.flat[0]),'B_values_m':old.tolist()})
 # Compact distribution summaries and connected components of newly clamped floor values.
 def qstats(values):
  a=np.asarray(values,dtype=float)
  return {'count':int(len(a)),'min':float(a.min()),'median':float(np.median(a)),'p90':float(np.quantile(a,.9)),'p95':float(np.quantile(a,.95)),'max':float(a.max())}
 sep_pf=[]; level_pf=[]; dist_pf=[]
 for x in records:
  p0=x.get('P_nearest');f0=x.get('F_nearest')
  if p0 and f0:
   sep_pf.append(math.dist(p0['projection_xz_m'],f0['projection_xz_m']))
   level_pf.append(abs(p0['level_m']-f0['level_m']))
   dist_pf.append(abs(p0['distance_m']-f0['distance_m']))
 floor_value=float(np.float32(1.8)); floor_mask=np.zeros((13,13),bool)
 for x in records:
  if x['clamped_float32_m']==floor_value:floor_mask[x['row']-rlo,x['col']-clo]=True
 comps=[]; seen=set(map(tuple,np.argwhere(floor_mask)))
 while seen:
  todo=[seen.pop()]; comp=[]
  while todo:
   rr,cc=todo.pop();comp.append((rr,cc))
   for n in ((rr+1,cc),(rr-1,cc),(rr,cc+1),(rr,cc-1)):
    if n in seen:seen.remove(n);todo.append(n)
  comps.append(comp)
 components=[{'nodes':int(len(x)),'bounds_rc':[int(rlo+min(a for a,b in x)),int(rlo+max(a for a,b in x)),int(clo+min(b for a,b in x)),int(clo+max(b for a,b in x))]} for x in sorted(comps,key=len,reverse=True)]
 # Hash inputs again to bind report and avoid a stale read.
 for k,p in paths.items():assert sha(p)==EXPECTED[k],('input changed',k)
 out={'status':'READ_ONLY_PROFILE_TARGET_DIAGNOSTIC','inputs_sha256':EXPECTED,'window':{'outer_rc':[832,849,362,379],'core_rc':[834,847,364,377]},
  'counts':counts,'P_F_nearest_projection_conflicts':sum(bool(x['P_F_conflict']) for x in records),
  'diagnostic_projection_thresholds':{'P_F_conflict_distance_or_level_gt_m':1e-3,'projection_dedup_distance_m':1e-4,'projection_dedup_level_m':1e-6,'nearest_tie_distance_delta_m':1e-6},
  'P_F_separation_m':qstats(sep_pf),'P_F_level_difference_m':qstats(level_pf),'P_F_nearest_distance_difference_m':qstats(dist_pf),
  'nearest_distance_m':qstats([x['nearest_distance_m'] for x in records]),'ray_D_m':qstats([x['ray_to_outer_collar_D_m'] for x in records]),
  'profile_t':qstats([x['t'] for x in records]),'profile_target_m':qstats([x['target_m'] for x in records]),
  'unique_projection_count_histogram':{str(n):sum(x['nearest_tied_unique_projections']==n for x in records) for n in sorted(set(x['nearest_tied_unique_projections'] for x in records))},
  'floor_1_8_float32_nodes':int(floor_mask.sum()),'floor_1_8_float32_connected_components_4way':components,
  'new_exact_flat_2x2_after_lower_or_upper_clamp':squares,'records':records,
  'limitations':['Nearest contour is measured from local B triangles; the surface fit itself has not been run.','The 2x2 equality test detects only exact float32 plateaus, not all visually flat terraces.','Free and contour counts are local diagnostics, not water/exposure acceptance.']}
 outp=OUT/'profile-target-diagnostic.json';outp.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf-8')
 print(json.dumps({'output':str(outp),'counts':counts,'projection_conflicts':out['P_F_nearest_projection_conflicts'],'tied_hist':out['unique_projection_count_histogram'],'new_flat_2x2':len(squares),'examples':records[:3]},indent=2))
if __name__=='__main__':main()
