from pathlib import Path
import json,hashlib,math
import numpy as np
from scipy.optimize import minimize_scalar
ROOT=Path(r'E:/DayZ-Baltic-Build'); EV=ROOT/'v30-narva-dry-bank-relief-20261010'
FOCUS=ROOT/'v30-bank-relief-review-20261010/luna-geometry/focus-anchors.json'; OUT=ROOT/'v30-mixed-bank-feasibility-20261010'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=EV/'candidate/terrain.npz'; K=EV/'constraints.npz'; P=EV/'candidate/plane.npy'; F=EV/'candidate/visible-field.npy'
expected={'candidate':'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c','constraints':'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c','plane':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0','visible':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c'}
for name,path in [('candidate',C),('constraints',K),('plane',P),('visible',F)]: assert sha(path)==expected[name]
with np.load(C,allow_pickle=False) as z:t={k:z[k] for k in z.files}
with np.load(K,allow_pickle=False) as z:cons={k:z[k] for k in z.files}
p=np.load(P);vis=np.load(F);anchors=json.loads(FOCUS.read_text())['focuses'];h=t['heights'].astype(float)
assert h.shape==(2048,2048) and p.shape==(2047,2047) and vis.shape==(2047,2047,4)

def tri_v(r,c,k):
 nw=(r,c);ne=(r,c+1);sw=(r+1,c);se=(r+1,c+1)
 return (nw,ne,se) if k==0 else (nw,se,sw)
def normal(H,tri):
 pts=np.array([[q[1]*6.,H[q],12282.-q[0]*6.] for q in tri]);n=np.cross(pts[1]-pts[0],pts[2]-pts[0]);n/=np.linalg.norm(n)
 return -n if n[1]<0 else n
def slope(H,tri):
 n=normal(H,tri);return math.degrees(math.atan2(math.hypot(n[0],n[2]),abs(n[1])))
def grad(H,tri):
 a,b,c=tri;mat=np.array([[6*(b[1]-a[1]),-6*(b[0]-a[0])],[6*(c[1]-a[1]),-6*(c[0]-a[0])]],float);rhs=np.array([H[b]-H[a],H[c]-H[a]],float);return np.linalg.solve(mat,rhs)
def patch_hinges(r,c):
 faces=[];edges={}
 for rr in range(r-2,r+2):
  for cc in range(c-2,c+2):
   for k in (0,1):
    f=tri_v(rr,cc,k);i=len(faces);faces.append(f)
    for j in range(3):edges.setdefault(tuple(sorted((f[j],f[(j+1)%3]))),[]).append(i)
 out=[]
 for edge,idxs in edges.items():
  if len(idxs)==2:out.append((edge,faces[idxs[0]],faces[idxs[1]]))
 assert len(out)==40
 return out
def hinge(H,pair):
 a,b=pair;n1,n2=normal(H,a),normal(H,b);return math.degrees(math.atan2(np.linalg.norm(np.cross(n1,n2)),float(n1@n2)))
def local_wet(H,r,c):
 out=[]
 for rr in range(r-1,r+1):
  for cc in range(c-1,c+1):
   corners={(rr,cc):0,(rr,cc+1):1,(rr+1,cc):2,(rr+1,cc+1):3}
   for k in (0,1):
    tri=tri_v(rr,cc,k);wet=False
    for vr,vc in tri:
     ki=corners[(vr,vc)];water=max(.85,float(p[rr,cc]) if np.isfinite(p[rr,cc]) else .85,float(vis[rr,cc,ki]) if np.isfinite(vis[rr,cc,ki]) else .85)
     if water>H[vr,vc]:wet=True
    out.append(wet)
 return out
def water_max_for_node(r,c):
 vals=[.85]
 for rr in range(r-1,r+1):
  for cc in range(c-1,c+1):
   ix={(rr,cc):0,(rr,cc+1):1,(rr+1,cc):2,(rr+1,cc+1):3}[(r,c)]
   if np.isfinite(p[rr,cc]):vals.append(float(p[rr,cc]))
   if np.isfinite(vis[rr,cc,ix]):vals.append(float(vis[rr,cc,ix]))
 return max(vals)
def slope_interval(H,h0,tri,node):
 g0=grad(H,tri);H1=H.copy();H1[node]=h0+1.;dg=grad(H1,tri)-g0;limit=max(35.,slope(H,tri));target=math.tan(math.radians(limit))
 a=float(dg@dg);b=float(2*g0@dg);c=float(g0@g0-target*target)
 if a<1e-24:return ((-math.inf,math.inf) if c<=1e-12 else (math.inf,-math.inf)),limit
 d=b*b-4*a*c
 if d<0:return ((-math.inf,math.inf) if c<=0 else (math.inf,-math.inf)),limit
 q=math.sqrt(max(0,d));return (h0+(-b-q)/(2*a),h0+(-b+q)/(2*a)),limit

results=[]
for anchor in anchors:
 x,z=int(anchor['x_m']),int(anchor['z_m']);r=math.floor((12282-z)/6);c=math.floor(x/6);node=(r,c)
 assert c*6==x and 12282-r*6==z
 h0=float(h[node]);support=bool(cons['wet_support'][node]);engineering=bool(cons['engineering_halo'][node]);fixed=bool(cons['fixed'][node]);allowed=bool(cons['allowed'][node])
 assert int(t['cls'][node])==0 and not support and not engineering
 watermax=water_max_for_node(r,c);floor=max(min(h0,1.8),watermax+1e-4);lo=max(h0-2.,floor);hi=h0+2.
 tris=[]
 for rr in range(r-1,r+1):
  for cc in range(c-1,c+1):
   for k in (0,1):
    tv=tri_v(rr,cc,k)
    if node in tv:tris.append((rr,cc,k,tv))
 assert len(tris)==6
 intervals=[];limits=[];angles0=[]
 for rr,cc,k,tv in tris:
  iv,lim=slope_interval(h,h0,tv,node);intervals.append(iv);limits.append(lim);angles0.append(slope(h,tv))
 slope_lo=max(v[0] for v in intervals);slope_hi=min(v[1] for v in intervals);feas_lo=max(lo,slope_lo);feas_hi=min(hi,slope_hi)
 patch=patch_hinges(r,c);base_angles=np.array([hinge(h,(a,b)) for _,a,b in patch]);wet0=local_wet(h,r,c)
 rec={'rank':anchor['rank'],'x_m':x,'z_m':z,'row':r,'col':c,'h_ev79_m':h0,'height_window_m':[h0-2,h0+2],
      'floor':{'min_h_1p8_m':min(h0,1.8),'max_incident_P_F_sea_m':watermax,'water_floor_plus_1e-4_m':watermax+1e-4,'effective_m':floor},
      'slope_interval_intersection_m':[slope_lo,slope_hi],'feasible_height_interval_m':[feas_lo,feas_hi] if feas_lo<=feas_hi else None,
      'wet_support_immutable':not support,'engineering_halo_immutable':not engineering,'fixed':fixed,'allowed_under_EV79_selection':allowed,
      'incident_slope_triangles':len(tris),'triangles':[], 'hinges_5x5':len(patch),
      'before':{'sum_squared_deg2':float(base_angles@base_angles),'max_deg':float(base_angles.max()),'count_over_30deg':int(np.count_nonzero(base_angles>30+1e-4)),'wet_faces':int(sum(wet0))}}
 for (rr,cc,k,tv),iv,lim,a0 in zip(tris,intervals,limits,angles0):rec['triangles'].append({'cell':[rr,cc],'tri':'NW-NE-SE' if k==0 else 'NW-SE-SW','slope_before_deg':a0,'limit_deg':lim,'height_interval_m':list(iv)})
 if feas_lo>feas_hi:
  rec.update({'status':'INFEASIBLE_SINGLE_VERTEX','blocker':'slope-bound intersection does not overlap ±2m and floor'});results.append(rec);continue
 def evalh(q):
  tmp=h.copy();tmp[node]=q;angs=np.array([hinge(tmp,(a,b)) for _,a,b in patch]);return float(angs@angs),angs,tmp
 if feas_hi-feas_lo<1e-10:best=(feas_lo+feas_hi)/2
 else:
  opt=minimize_scalar(lambda q:evalh(q)[0],bounds=(feas_lo,feas_hi),method='bounded',options={'xatol':1e-10,'maxiter':500})
  best=min((feas_lo,feas_hi,float(opt.x)),key=lambda q:evalh(q)[0])
 sum1,ang1,h1=evalh(best);wet1=local_wet(h1,r,c);slopes_after=[slope(h1,tv) for _,_,_,tv in tris];new30=int(np.count_nonzero((base_angles<=30+1e-4)&(ang1>30+1e-4)));max_ok=bool(ang1.max()<=base_angles.max()+1e-8);wet_ok=wet1==wet0;improved=sum1<float(base_angles@base_angles)-1e-8
 target_hinges=[]
 for oldhinge in anchor['hinges']:
  rr,cc=oldhinge['row'],oldhinge['col']
  if oldhinge['hinge']=='vertical':pair=(tri_v(rr,cc,0),tri_v(rr,cc+1,1))
  elif oldhinge['hinge']=='horizontal':pair=(tri_v(rr,cc,1),tri_v(rr+1,cc,0))
  else:pair=(tri_v(rr,cc,0),tri_v(rr,cc,1))
  target_hinges.append({'hinge':oldhinge['hinge'],'row':rr,'col':cc,'before_deg':hinge(h,pair),'after_deg':hinge(h1,pair)})
 rec.update({'status':'FEASIBLE_SINGLE_VERTEX','focus_hinges':target_hinges,'incident_slopes_after_deg':slopes_after,'h_opt_m':best,'delta_m':best-h0,'after':{'sum_squared_deg2':sum1,'reduction_deg2':float(base_angles@base_angles)-sum1,'reduction_percent':100*(float(base_angles@base_angles)-sum1)/(float(base_angles@base_angles)),'max_deg':float(ang1.max()),'count_over_30deg':int(np.count_nonzero(ang1>30+1e-4)),'new_over_30deg':new30,'wet_faces':int(sum(wet1))},
  'gates':{'height_window_floor':lo-1e-8<=best<=hi+1e-8 and best>=floor-1e-8,'all_incident_slopes':all(slope(h1,tv)<=lim+1e-7 for (_,_,_,tv),lim in zip(tris,limits)),'wet_faces_unchanged':wet_ok,'zero_new_over_30deg':new30==0,'local_max_not_worse':max_ok,'objective_improved':improved,'all_requested_conditions':bool(improved and wet_ok and new30==0 and max_ok)}})
 results.append(rec)
report={'status':'NUMERICAL_SINGLE_VERTEX_FEASIBILITY_DIAGNOSTIC','basis':'EV79 candidate only','inputs':{'candidate_sha256':sha(C),'constraints_sha256':sha(K),'plane_sha256':sha(P),'visible_sha256':sha(F),'focus_anchors_sha256':sha(FOCUS)},
 'method':{'variable':'one central dry vertex at a time','bounds':'h_EV79 ±2m and floor=max(min(h_EV79,1.8),max incident P/F/sea+1e-4)','slope_gate':'each of the six incident native triangles <= max(35deg, its EV79 slope)','local_objective':'sum of squared dihedral angles over all 40 shared edges of the 5x5-vertex patch','optimizer':'bounded 1D scalar minimization; endpoints checked','masks':'exact wet-support and 3x3 engineering halo checked immutable; every other height held fixed'},
 'focuses':results,'limits':['All three anchors are outside the EV79 allowed mask (Narva-only scope); this assesses numeric feasibility only, not EV79 edit authorization.','Diagnostic only; no NPZ or package produced.','Numerical one-dimensional optimization, not a formal proof for larger multi-vertex changes.','A single-node infeasibility does not authorize expanding the neighborhood.','No DayZ motor, render or visual acceptance.']}
(OUT/'single-node-feasibility.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'results':[{k:v for k,v in q.items() if k in ('rank','row','col','h_ev79_m','feasible_height_interval_m','h_opt_m','delta_m','status','before','after','gates')} for q in results]},indent=2))
