"""EV87 one-pass global strict-bank relief author. Offline only."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, multiprocessing as mp, os, queue, sys, time, traceback
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.optimize import linprog, minimize

ROOT=Path(r'E:/DayZ-Baltic-Build')
OUT=ROOT/'v30-global-strict-bank-relief-20261010'
EV79=ROOT/'v30-narva-dry-bank-relief-20261010'
B=ROOT/'v30-mixed-bank-incremental-fixed-20261010'
PRIOR=ROOT/'v30-remaining-exact-dry-support-20261009/constraints.npz'
REVIEW=OUT/'review-independent/verify_ev87.py'
EVAL=ROOT/'v30-coupled-shore-pilot-20261010/performance/ev85_vectorized.py'
REPAIR=ROOT/'v30-coupled-shore-pilot-20261010/repair_quantized.py'
N=2048; CELL=6.0; SEA=.85; TOL=1e-4; MAXITER=150; PATCH_TIMEOUT=5.0; DEADLINE=1800.0
EXPECTED={'B':'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
 'EV79':'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c',
 'P':'768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
 'F':'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
 'EV79_CONSTRAINTS':'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
 'PRIOR_CONSTRAINTS':'18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
 'WRP':'3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6'}
OFF=((0,0),(0,1),(1,0),(1,1)); TRIS=((0,1,3),(0,2,3))

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
 return h.hexdigest()
def canonical_sha(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')).hexdigest()
def load_npz(p):
 with np.load(p,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def write_json(path,x): Path(path).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

def hinge_vertices(kind,r,c):
 if kind in ('diag','diagonal'):return ((r,c),(r,c+1),(r+1,c),(r+1,c+1))
 if kind=='vertical':return ((r,c),(r,c+1),(r+1,c+1),(r+1,c+2))
 return ((r,c),(r+1,c),(r+1,c+1),(r+2,c+1))
def edge_vertex_slices(mask,kind):
 if kind=='diag':return (mask[:-1,:-1],mask[:-1,1:],mask[1:,:-1],mask[1:,1:])
 if kind=='vertical':return (mask[:-1,:-2],mask[:-1,1:-1],mask[1:,1:-1],mask[1:,2:])
 return (mask[:-2,:-1],mask[1:-1,:-1],mask[1:-1,1:],mask[2:,1:])
def edge_angles(h):
 nw,ne,sw,se=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:];one=np.ones_like(nw)
 ea=np.stack((6*one,ne-nw,np.zeros_like(nw)),axis=-1);dg=np.stack((6*one,se-nw,-6*one),axis=-1);eb=np.stack((np.zeros_like(nw),sw-nw,-6*one),axis=-1)
 a=np.cross(ea,dg);b=np.cross(dg,eb);a/=np.linalg.norm(a,axis=-1)[...,None];b/=np.linalg.norm(b,axis=-1)[...,None]
 return {'diag':np.degrees(np.arctan2(np.linalg.norm(np.cross(a,b),axis=-1),np.einsum('...i,...i->...',a,b))),
 'vertical':np.degrees(np.arctan2(np.linalg.norm(np.cross(a[:,:-1],b[:,1:]),axis=-1),np.einsum('...i,...i->...',a[:,:-1],b[:,1:]))),
 'horizontal':np.degrees(np.arctan2(np.linalg.norm(np.cross(b[:-1,:],a[1:,:]),axis=-1),np.einsum('...i,...i->...',b[:-1,:],a[1:,:])))}
def node_stats(angles):
 vmax=np.full((N,N),-np.inf);hot=np.zeros((N,N),bool)
 for k,a in angles.items():
  for d in edge_vertex_slices(vmax,k):np.maximum(d,a,out=d)
  for d in edge_vertex_slices(hot,k):d|=a>30.0001
 return vmax,hot
def prominent(h):
 o=np.zeros(h.shape,bool);o[:,1:-1]=(h[:,1:-1]>h[:,:-2]+.1)&(h[:,1:-1]>h[:,2:]+.1);o[1:-1,:]|=(h[1:-1,:]>h[:-2,:]+.1)&(h[1:-1,:]>h[2:,:]+.1);return o
def selector(h,eligible,angles):
 vmax,hot=node_stats(angles); coords=np.argwhere(eligible&hot&prominent(h));
 if not len(coords):return [],[],[]
 idx=np.lexsort((coords[:,1],coords[:,0],-vmax[coords[:,0],coords[:,1]]));bucket=defaultdict(list);selected=[];excluded=[]
 for i in idx:
  r,c=map(int,coords[i])
  if min(r,c)<4 or r>=N-4 or c>=N-4:excluded.append({'coordinates':[r,c],'reason':'boundary_window_not_full'});continue
  blockers=[]
  for br in range((r-10)//11,(r+10)//11+1):
   for bc in range((c-10)//11,(c+10)//11+1):
    for rr,cc in bucket.get((br,bc),[]):
     if max(abs(r-rr),abs(c-cc))<11:blockers.append((rr,cc))
  if blockers:excluded.append({'coordinates':[r,c],'reason':'chebyshev_overlap','blocked_by':list(min(blockers))});continue
  selected.append({'queue_id':len(selected),'coordinates':[r,c],'center':[r,c], 'max_incident_angle_deg':float(vmax[r,c]),
   'window7':[r-3,c-3,r+4,c+4],'window9':[r-4,c-4,r+5,c+5]})
  bucket[(r//11,c//11)].append((r,c))
 seed_rows=[{'seed_id':i,'coordinates':[int(r),int(c)],'center':[int(r),int(c)],'max_incident_angle_deg':float(vmax[r,c]),
  'axial_prominence_m':float(max(h[r,c]-max(h[r,c-1],h[r,c+1]),h[r,c]-max(h[r-1,c],h[r+1,c]))),'eligible':True} for i,(r,c) in enumerate(coords[idx])]
 ids={tuple(s['coordinates']):s['seed_id'] for s in seed_rows}
 for q in selected:q['seed_id']=ids[tuple(q['coordinates'])]
 for q in excluded:q['seed_id']=ids[tuple(q['coordinates'])]
 return seed_rows,selected,excluded

def population_masks(base,cons):
 cls=base['cls']; dry=(cls==0)&~cons['wet_support'].astype(bool)&~base['reserve'].astype(bool)&~base['platform'].astype(bool)
 bank=dry&(distance_transform_edt(~np.isin(cls,(3,5,6)),sampling=CELL)<=96.+1e-9)
 return {'bank':bank,'interior':dry&~bank}
def stat_threshold(vals):
 a=np.asarray(vals,dtype=np.float64);n=a.size;pos=(n-1)*.99;k0=math.floor(pos);k1=math.ceil(pos);part=np.partition(a,(k0,k1));return (float(part[k0]),float(part[k1]),int(n),float(pos-k0))
def optimizer_constraints(order_ineq,order_eq,hinge_ineq,slope_ineq,energy_ineq,focus_index,has_order_eq):
 constraints=[{'type':'ineq','fun':order_ineq},{'type':'ineq','fun':hinge_ineq},{'type':'ineq','fun':slope_ineq},{'type':'ineq','fun':energy_ineq},
              {'type':'ineq','fun':lambda x:-.2-float(x[focus_index])}]
 if has_order_eq:constraints.append({'type':'eq','fun':order_eq})
 return constraints
def solver_wiring_fixture():
 # Exercise the same constraint factory used by patch_task, including tied B edges and focus descent.
 eq=lambda x:np.asarray([x[1]-x[0]])
 cs=optimizer_constraints(lambda x:np.asarray([x[0]-x[1]+1.]),eq,lambda x:np.asarray([.5-x[0]]),
                          lambda x:np.asarray([1.]),lambda x:np.asarray([1.]),0,True)
 res=minimize(lambda x:float(x@x),np.asarray([-.2,-.2]),method='SLSQP',bounds=[(-1.,0.),(-1.,0.)],constraints=cs,
              options={'maxiter':10,'ftol':1e-12,'disp':False})
 assert np.isfinite(res.x).all() and abs(res.x[0]-res.x[1])<1e-10 and res.x[0]<=-.2+1e-10
 assert min(float(np.min(np.asarray(c['fun'](res.x)))) for c in cs if c['type']=='ineq')>=-1e-9
 return {'same_constraint_factory_as_patch_task':True,'scipy_status':int(res.status),'finite_solution':True,'tie_and_focus_pass':True}
def pop_data(base,cons,angles):
 masks=population_masks(base,cons);out={}
 for name,mask in masks.items():
  out[name]={'masks':{},'parts':[]}
  for kind,a in angles.items():
   slices=edge_vertex_slices(mask,kind);allm=np.logical_and.reduce(slices);v=a[allm]
   out[name]['masks'][kind]=allm;out[name]['parts'].append(v)
  joined=np.concatenate(out[name]['parts'])
  out[name]['threshold']=stat_threshold(joined);out[name]['count30']=int(np.count_nonzero(joined>30.));out[name]['population']=int(joined.size)
  del out[name]['parts']
 return masks,out

def physical_inputs():
 paths={'B':B/'candidate/terrain.npz','EV79':EV79/'candidate/terrain.npz','P':EV79/'candidate/plane.npy','F':EV79/'candidate/visible-field.npy',
 'EV79_CONSTRAINTS':EV79/'constraints.npz','PRIOR_CONSTRAINTS':PRIOR,'WRP':B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'}
 got={k:sha(v) for k,v in paths.items()}
 for k in EXPECTED:
  if got[k]!=EXPECTED[k]:raise RuntimeError(f'input identity mismatch {k}: {got[k]} != {EXPECTED[k]}')
 return paths,got

def local_caps(base,descs,slopefaces,angles_all,author,block=None):
 old=author.eval_hinges(base,descs); caps=[]
 if block is None:
  block={}
  for k,a in angles_all.items():
   nr,nc=a.shape
   for r0 in range(0,nr,64):
    for c0 in range(0,nc,64):block[(k,r0//64,c0//64)]=float(np.max(a[r0:r0+64,c0:c0+64],initial=0.))
 for i,d in enumerate(descs):
  k,r,c=d;k='diag' if k=='diagonal' else k;cap=block[(k,r//64,c//64)]+TOL
  if old[i]<=30.+TOL:cap=min(cap,30.+TOL)
  caps.append(cap)
 sf0=author.slope_values(base,slopefaces);scaps=np.maximum(35.,sf0)
 return old,np.asarray(caps),sf0,scaps

def cell_f_partial(f,r,c):
 n=int(np.count_nonzero(np.isfinite(f[r,c])));return 0<n<4
def crossing_lower(h,p,f,variables,ev79,upper,lower):
 """One-variable crossing records; returns tightened scalar lower bounds or rejection reason."""
 result=lower.copy(); vars_set=set(variables); cells=set()
 for r,c in variables:
  for dr in (-1,0):
   for dc in (-1,0):
    rr,cc=r+dr,c+dc
    if 0<=rr<N-1 and 0<=cc<N-1:cells.add((rr,cc))
 for r,c in cells:
  if cell_f_partial(f,r,c):return None,'partial_F_triangle_incident'
  hs=(float(h[r,c]),float(h[r,c+1]),float(h[r+1,c]),float(h[r+1,c+1]))
  levels=[]
  if np.isfinite(p[r,c]):levels.append(('P',(float(p[r,c]),)*4,((0,1,3),(0,2,3))))
  levels.append(('SEA',(SEA,)*4,((0,1,3),(0,2,3))))
  fv=tuple(float(x) for x in f[r,c])
  if np.isfinite(fv).all():levels.append(('F',fv,((0,1,3),(0,2,3))))
  for name,lev,tris in levels:
   for tri in tris:
    for i,j in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
     a=(r+OFF[i][0],c+OFF[i][1]);b=(r+OFF[j][0],c+OFF[j][1]);va=a in vars_set;vb=b in vars_set
     d0=hs[i]-lev[i];d1=hs[j]-lev[j]
     if (d0>0)==(d1>0):continue
     if va and vb:return None,'two_mutable_crossing_endpoints'
     if not(va or vb):continue
     v=a if va else b;fixed=b if va else a;iv=i if va else j;jf=j if va else i
     dv=hs[iv]-lev[iv];df=hs[jf]-lev[jf]
     if dv<=0 or df>=0:return None,'crossing_endpoint_not_dry_variable_wet_fixed'
     length=CELL if (a[0]==b[0] or a[1]==b[1]) else CELL*math.sqrt(2)
     t0=dv/(dv-df);tmin=t0-1./length
     if tmin>0:
      hmin=lev[iv]+(-df)*tmin/(1.-tmin)
      result[v]=max(result[v],hmin)
      if result[v]>upper[v]+1e-10:return None,'crossing_bound_empty'
 return result,None

def crossing_displacement(h0,h1,p,f,variables):
 """Recheck every original local P/F/SEA edge crossing after float32 midpoint."""
 vset=set(variables);cells=cells_for_nodes(variables);worst=0.;count=0
 for r,c in cells:
  hs0=(float(h0[r,c]),float(h0[r,c+1]),float(h0[r+1,c]),float(h0[r+1,c+1]))
  hs1=(float(h1[r,c]),float(h1[r,c+1]),float(h1[r+1,c]),float(h1[r+1,c+1]))
  fields=[]
  if np.isfinite(p[r,c]):fields.append(('P',(float(p[r,c]),)*4,((0,1,3),(0,2,3))))
  fields.append(('SEA',(SEA,)*4,((0,1,3),(0,2,3))))
  fv=tuple(float(x) for x in f[r,c])
  if np.isfinite(fv).all():fields.append(('F',fv,((0,1,3),(0,2,3))))
  for name,lev,tris in fields:
   for tri in tris:
    for i,j in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
     a=(r+OFF[i][0],c+OFF[i][1]);b=(r+OFF[j][0],c+OFF[j][1])
     d0=hs0[i]-lev[i];d1=hs0[j]-lev[j];n0=hs1[i]-lev[i];n1=hs1[j]-lev[j]
     if (d0>0)==(d1>0):continue
     count+=1
     if (n0>0)==(n1>0):return math.inf,count
     t0=d0/(d0-d1);t1=n0/(n0-n1)
     length=CELL if (a[0]==b[0] or a[1]==b[1]) else CELL*math.sqrt(2)
     worst=max(worst,abs(t1-t0)*length)
 return worst,count

def crossing_displacement_overlay(h,p,f,variables,overrides):
 vset=set(variables);cells=cells_for_nodes(variables);worst=0.;count=0
 get=lambda r,c:float(overrides.get((r,c),h[r,c]))
 for r,c in cells:
  vs=((r,c),(r,c+1),(r+1,c),(r+1,c+1));hs0=tuple(float(h[v]) for v in vs);hs1=tuple(get(*v) for v in vs)
  fields=[]
  if np.isfinite(p[r,c]):fields.append((tuple([float(p[r,c])]*4),((0,1,3),(0,2,3))))
  fields.append((tuple([SEA]*4),((0,1,3),(0,2,3))))
  fv=tuple(float(x) for x in f[r,c])
  if np.isfinite(fv).all():fields.append((fv,((0,1,3),(0,2,3))))
  for lev,tris in fields:
   for tri in tris:
    for i,j in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):
     d0=hs0[i]-lev[i];d1=hs0[j]-lev[j]
     if (d0>0)==(d1>0):continue
     count+=1;n0=hs1[i]-lev[i];n1=hs1[j]-lev[j]
     if (n0>0)==(n1>0):return math.inf,count
     t0=d0/(d0-d1);t1=n0/(n0-n1)
     a,b=vs[i],vs[j];length=CELL if (a[0]==b[0] or a[1]==b[1]) else CELL*math.sqrt(2)
     worst=max(worst,abs(t1-t0)*length)
 return worst,count

def patch_task(q,eligible,h,ev79,p,f,angles_all,pop_stats,author,repair,evaluator_mod,block):
 center=tuple(q['center']);r,c=center
 vars=[(rr,cc) for rr in range(r-2,r+3) for cc in range(c-2,c+3) if eligible[rr,cc]]
 if not vars:return {'state':'rejected_lp','reason':'no_mutable_nodes','mutable_nodes':[]}
 # Exactly all nodes in the 7x7 footprint participate in repair; ring and ineligible nodes are point-fixed.
 nodes={(rr,cc) for rr in range(r-3,r+4) for cc in range(c-3,c+4)}
 vset=set(vars); edges=sorted(author.order_edges(vset)); idx={v:i for i,v in enumerate(vars)}
 if any(u not in nodes or v not in nodes for u,v in edges):raise RuntimeError('variable order edge escapes repair window7')
 desc=sorted(set().union(*(author.vertex_hinges(v) for v in vars)))
 sf=author.slope_faces_for_vertices(vset)
 old,caps,slope0,scaps=local_caps(h,desc,sf,angles_all,author,block)
 # Full touched hinge coverage must be contained in this 9x9 window.
 for kind,rr,cc in desc:
  for vr,vc in hinge_vertices(kind,rr,cc):
   if abs(vr-r)>4 or abs(vc-c)>4:raise RuntimeError('affected hinge escapes evaluation window')
 lo={};hi={}
 for v in vars:
  lo[v]=max(float(ev79[v])-2.,min(float(ev79[v]),1.8),min(float(ev79[v]),float(ev79_level[v])+1e-4))
  hi[v]=min(float(h[v]),float(ev79[v])+2.)
  if lo[v]>hi[v]+1e-10:return {'state':'rejected_gate','reason':'empty_physical_bounds','mutable_nodes':[list(v) for v in vars]}
 tightened,why=crossing_lower(h,p,f,vars,ev79,hi,lo)
 if why:return {'state':'rejected_gate','reason':why,'mutable_nodes':[list(v) for v in vars]}
 lo=tightened
 bounds=[(lo[v]-float(h[v]),hi[v]-float(h[v])) for v in vars]
 if any(a>b+1e-10 for a,b in bounds):return {'state':'rejected_gate','reason':'empty_crossing_interval','mutable_nodes':[list(v) for v in vars]}
 # Reject any partial finite F cell in the evaluation support, even if no scalar crossing was found.
 for rr,cc in cells_for_nodes(vars):
  if cell_f_partial(f,rr,cc):return {'state':'rejected_gate','reason':'partial_F_triangle_incident','mutable_nodes':[list(v) for v in vars]}
 # LP: weak source ordering, exact B ties, and focus descent >=0.2.
 aub=[];bub=[];aeq=[];beq=[]
 for u,v in edges:
  du=np.zeros(len(vars));dv=np.zeros(len(vars));
  if u in idx:du[idx[u]]=1
  if v in idx:dv[idx[v]]=1
  gap=float(h[u])-float(h[v])
  if gap>0:aub.append(du-dv);bub.append(gap)
  elif gap<0:aub.append(dv-du);bub.append(-gap)
  else:aeq.append(du-dv);beq.append(0.)
 focus=center;fc=idx.get(focus)
 if fc is None:return {'state':'rejected_lp','reason':'focus_not_mutable','mutable_nodes':[list(v) for v in vars]}
 row=np.zeros(len(vars));row[fc]=1.;aub.append(row);bub.append(-.2)
 res=linprog(np.ones(len(vars)),A_ub=np.asarray(aub),b_ub=np.asarray(bub),A_eq=np.asarray(aeq) if aeq else None,b_eq=np.asarray(beq) if beq else None,bounds=bounds,method='highs')
 if not res.success:return {'state':'rejected_lp','reason':f'linprog:{res.status}:{res.message}','mutable_nodes':[list(v) for v in vars]}
 x0=np.asarray(res.x,dtype=np.float64)
 evaluator=evaluator_mod.PatchEvaluator(h,vars,desc,sf,edges)
 base_state=evaluator.evaluate(np.zeros(len(vars))); E0=base_state['angles']; Efocus=np.asarray([desc.index(d) for d in sorted(author.vertex_hinges(focus))],dtype=np.int64)
 focus_energy=float(E0[Efocus]@E0[Efocus])
 # Per-patch local p99/order-stat and exact >30 guards; maps are fixed from B.
 domain_records=[]
 for domain in ('bank','interior'):
  q0,q1,_,_=pop_stats[domain]['threshold'];ids=[]
  for i,d in enumerate(desc):
   kind,rr,cc=d;kind='diag' if kind=='diagonal' else kind
   if pop_stats[domain]['masks'][kind][rr,cc]:ids.append(i)
  if ids:domain_records.append((domain,np.asarray(ids,dtype=np.int64),q0,q1,pop_stats[domain]['count30']))
 # Constraints only continuous gates; p99/count/extrema are exact post-solve gates.
 def calc(x):return evaluator.evaluate(x)
 def order_ineq(x):return calc(x)['order_ineq']
 def order_eq(x):return calc(x)['order_eq']
 def hinge_ineq(x):return caps-calc(x)['angles']
 def slope_ineq(x):return scaps-calc(x)['slopes']
 def energy_ineq(x):
  a=calc(x)['angles'][Efocus];return .99*focus_energy-float(a@a)
 constraints=optimizer_constraints(order_ineq,order_eq,hinge_ineq,slope_ineq,energy_ineq,fc,bool(np.asarray(base_state['order_eq']).size))
 def obj(x):a=calc(x)['angles'];return float(a@a)
 sr=minimize(obj,x0,method='SLSQP',bounds=bounds,constraints=constraints,options={'maxiter':MAXITER,'ftol':1e-10,'disp':False})
 if not np.isfinite(sr.x).all():return {'state':'rejected_solver','reason':'nonfinite_solver_output','mutable_nodes':[list(v) for v in vars]}
 # Quantize R and project exactly once with EV85-R generic isotonic correction.
 R={v:np.float32(float(h[v])+float(sr.x[i])) for i,v in enumerate(vars)}
 repair_nodes={v:float(h[v]) for v in nodes};diagnostic={v:np.float32(h[v]) for v in nodes};intervals={v:(float(h[v]),float(h[v])) for v in nodes}
 for v in vars:
  repair_nodes[v]=float(h[v]);diagnostic[v]=R[v];intervals[v]=(lo[v],hi[v])
 try: projected,meta=repair.project(repair_nodes,diagnostic,intervals,edges,set(vars),limit=1e-4)
 except Exception as e:return {'state':'rejected_gate','reason':'quantized_projection:'+str(e),'mutable_nodes':[list(v) for v in vars],'solver':{'success':bool(sr.success),'status':int(sr.status),'message':str(sr.message),'iterations':int(sr.nit)}}
 Rv=np.asarray([projected[v] for v in vars],dtype='<f4'); # canonical vector
 mid=np.asarray([(float(h[v])+(float(projected[v])-float(h[v]))*.5) for v in vars],dtype=np.float32)
 # Test projected direction and exact final midpoint against local physical/order/angle/slope gates.
 states=[]
 for arr in (Rv,mid):states.append(evaluator.evaluate((arr.astype(np.float64)-np.asarray([h[v] for v in vars],dtype=np.float64))))
 xR=Rv.astype(np.float64)-np.asarray([h[v] for v in vars],dtype=np.float64); xM=mid.astype(np.float64)-np.asarray([h[v] for v in vars],dtype=np.float64)
 final=states[1]; ang=final['angles'];sl=final['slopes'];oldangles=E0
 reason=[]
 if float(xM[fc])>-.1:reason.append('focus_descent_lt_0.1')
 if np.any(mid.astype(np.float64)<np.asarray([lo[v] for v in vars])) or np.any(mid.astype(np.float64)>np.asarray([hi[v] for v in vars])):reason.append('physical_bounds')
 # Strict signs and at least half B difference; equality edges remain tied.
 max_ord=0.;half_bad=0
 for u,v in edges:
  before=float(h[u])-float(h[v]);after=(float(mid[idx[u]]) if u in idx else float(h[u]))-(float(mid[idx[v]]) if v in idx else float(h[v]))
  if before==0:
   if after!=0:half_bad+=1
  elif math.copysign(1.,before)!=math.copysign(1.,after):half_bad+=1
  raw_u=float(h[u])+(float(projected[u])-float(h[u]))*.5 if u in vset else float(h[u])
  raw_v=float(h[v])+(float(projected[v])-float(h[v]))*.5 if v in vset else float(h[v])
  err=abs(float(np.float32(raw_u))-raw_u)+abs(float(np.float32(raw_v))-raw_v)
  if before and abs(after)<.5*abs(before)-err-1e-12:half_bad+=1
  max_ord=max(max_ord,max(0.,.5*abs(before)-abs(after)) if before else abs(after))
 if half_bad:reason.append(f'order_half_slope:{half_bad}')
 if np.max(ang-caps,initial=-np.inf)>1e-8:reason.append('hinge_caps')
 if np.max(sl-scaps,initial=-np.inf)>1e-8:reason.append('slope_caps')
 # Candidate values are spliced only for the current patch; no full-map copy.
 h1_local_patch={(v):float(mid[i]) for i,v in enumerate(vars)}
 # Crossing recheck uses an overlay accessor to preserve the full B array untouched.
 cross_max,cross_count=crossing_displacement_overlay(h,p,f,vars,h1_local_patch)
 if cross_max>1.0+1e-8:reason.append('crossing_displacement_gt_1m')
 if float(ang@ang)>=float(oldangles@oldangles)-1e-10:reason.append('union_energy_not_decreased')
 if float(ang[Efocus]@ang[Efocus])>0.99*focus_energy+1e-8:reason.append('focus_energy')
 # Global p99 composition and local >30 counts are exact post-solve comparisons.
 p99counts={}
 for domain,ids,q0,q1,total30 in domain_records:
  before=E0[ids];after=ang[ids]
  b0=int(np.count_nonzero(before<=q0));b1=int(np.count_nonzero(before<=q1));a0=int(np.count_nonzero(after<=q0));a1=int(np.count_nonzero(after<=q1))
  old_over=int(np.count_nonzero(before>30.));new_over=int(np.count_nonzero(after>30.))
  p99counts[domain]={'q0_before':b0,'q0_after':a0,'q1_before':b1,'q1_after':a1,'over30_before':old_over,'over30_after':new_over}
  if a0<b0 or a1<b1 or new_over>old_over:reason.append('p99_or_over30:'+domain)
 # No new weak axial extrema within the 7x7 core evaluated at interior nodes.
 local_h=np.asarray([[h[rr,cc] for cc in range(c-3,c+4)] for rr in range(r-3,r+4)],dtype=np.float64)
 final_h=local_h.copy()
 for v,z in zip(vars,mid):final_h[v[0]-(r-3),v[1]-(c-3)]=z
 def extrema(a):
  e=set()
  for rr in range(1,6):
   for cc in range(1,6):
    z=a[rr,cc]
    for axis,u,w in (('ew',a[rr,cc-1],a[rr,cc+1]),('ns',a[rr-1,cc],a[rr+1,cc])):
     if z>=u and z>=w and (z>u or z>w):e.add((rr,cc,axis,'max'))
     if z<=u and z<=w and (z<u or z<w):e.add((rr,cc,axis,'min'))
  return e
 if extrema(final_h)-extrema(local_h):reason.append('new_weak_extrema')
 # Per-patch direction and worker metrics.
 return {'state':'rejected_gate' if reason else 'accepted','reason':';'.join(reason) if reason else None,
  'mutable_nodes':[list(v) for v in vars],'direction_values':Rv,'direction_sha256':hashlib.sha256(Rv.tobytes()).hexdigest(),
  'solver':{'success':bool(sr.success),'status':int(sr.status),'message':str(sr.message),'iterations':int(sr.nit),'objective_initial':float(obj(np.zeros(len(vars)))),'objective_final':float(obj(xR))},
  'projection':meta,'focus_delta_R':float(Rv[fc])-float(h[focus]),'focus_delta_mid':float(mid[fc])-float(h[focus]),'p99_counts':p99counts,
  'crossing_max_displacement_m':cross_max,'crossing_records':cross_count,
  'max_half_order_deficit_m':max_ord,'changed_nodes':int(np.count_nonzero(mid!=np.asarray([h[v] for v in vars],dtype=np.float32)))}

def cells_for_nodes(nodes):
 cells=set()
 for r,c in nodes:
  for dr in (-1,0):
   for dc in (-1,0):
    rr,cc=r+dr,c+dc
    if 0<=rr<N-1 and 0<=cc<N-1:cells.add((rr,cc))
 return cells

def worker_main(conn):
 try:
  b=load_npz(B/'candidate/terrain.npz');ev=load_npz(EV79/'candidate/terrain.npz');h=b['heights'].astype(np.float64)
  cons=load_npz(EV79/'constraints.npz');prior=load_npz(PRIOR)
  p=np.load(EV79/'candidate/plane.npy',allow_pickle=False).astype(np.float64);f=np.load(EV79/'candidate/visible-field.npy',allow_pickle=False).astype(np.float64)
  level=load_module('ev87_cons_worker',REVIEW).vertex_levels(p,f)
  global ev79_level;ev79_level=level
  eligible=(b['cls']==0)&~cons['other_fixed'].astype(bool)&~cons['engineering_halo'].astype(bool)&~prior['large_lake_banks'].astype(bool)&(h>level)
  angles=edge_angles(h);_,pop_stats=pop_data(b,cons,angles)
  block={}
  for k,a in angles.items():
   for r0 in range(0,a.shape[0],64):
    for c0 in range(0,a.shape[1],64):block[(k,r0//64,c0//64)]=float(np.max(a[r0:r0+64,c0:c0+64],initial=0.))
  mod=load_module('ev85_author_worker',ROOT/'v30-coupled-shore-pilot-20261010/author_ev85.py')
  rep=load_module('ev85_repair_worker',REPAIR)
  evaluator_mod=load_module('ev85_eval_worker',EVAL)
  conn.send({'event':'ready','pid':os.getpid()})
  while True:
   task=conn.recv()
   if task is None:break
   task_started=time.monotonic()
   try:
    result=patch_task(task['queue'],eligible,h,ev['heights'],p,f,angles,pop_stats,mod,rep,evaluator_mod,block)
   except BaseException as e:result={'state':'rejected_solver','reason':f'worker_exception:{type(e).__name__}:{e}','traceback':traceback.format_exc(),'mutable_nodes':[]}
   result['elapsed_ms']=round((time.monotonic()-task_started)*1000,3)
   conn.send({'queue_id':task['queue']['queue_id'],'result':result})
 except BaseException as e:
  try:conn.send({'event':'worker_error','error':repr(e),'traceback':traceback.format_exc()})
  except Exception:pass
 finally:
  try:conn.close()
  except Exception:pass

def start_worker(ctx):
 parent,child=ctx.Pipe();proc=ctx.Process(target=worker_main,args=(child,),daemon=True);proc.start();child.close()
 if not parent.poll(120):proc.terminate();proc.join();raise TimeoutError('worker initialization timeout')
 msg=parent.recv()
 if msg.get('event')!='ready':proc.terminate();proc.join();raise RuntimeError('worker startup failed '+repr(msg))
 return {'proc':proc,'conn':parent,'busy':None,'started':time.monotonic()}

def fixture_timeout_worker(conn,delay):
 try:
  conn.send({'event':'ready'});task=conn.recv();time.sleep(delay);conn.send({'qid':task['qid'],'value':task['value']})
 except (EOFError,BrokenPipeError):pass
 finally:conn.close()

def timeout_scheduler_fixture(ctx):
 def launch(delay):
  parent,child=ctx.Pipe();proc=ctx.Process(target=fixture_timeout_worker,args=(child,delay));proc.start();child.close()
  if not parent.poll(5) or parent.recv().get('event')!='ready':proc.terminate();proc.join();raise AssertionError('fixture worker handshake failed')
  return proc,parent
 slow,sc=launch(6.0);quick,qc=launch(.02);baseline={'height':17.0};dispatch=time.monotonic()
 sc.send({'qid':0,'value':'discard'});qc.send({'qid':1,'value':'quick'})
 got=None
 while time.monotonic()-dispatch<4.0:
  if qc.poll(.02):got=qc.recv();break
 assert got=={'qid':1,'value':'quick'} and not sc.poll(0)
 while time.monotonic()-dispatch<5.05:time.sleep(.01)
 assert not sc.poll(0);slow.terminate();slow.join(2);assert not slow.is_alive() and baseline['height']==17.0
 sc.close();qc.close();quick.join(2)
 replacement,rc=launch(.01);rc.send({'qid':2,'value':'next'});assert rc.poll(2) and rc.recv()=={'qid':2,'value':'next'}
 replacement.join(2);rc.close()
 return {'quick_completed_before_deadline':True,'slow_killed_at_parent_dispatch_deadline':True,'timed_out_patch_base_unchanged':True,'replacement_processed_next_patch':True}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args()
 run_started=time.monotonic()
 OUT.mkdir(parents=True,exist_ok=True)
 paths,ids=physical_inputs();review=load_module('ev87_consumer_lib',REVIEW)
 review_status=review.verify_controls();
 if not review_status:raise RuntimeError('consumer fixture function unavailable')
 author=load_module('ev85_author_main',ROOT/'v30-coupled-shore-pilot-20261010/author_ev85.py')
 b=load_npz(paths['B']);ev79=load_npz(paths['EV79']);cons=load_npz(paths['EV79_CONSTRAINTS']);prior=load_npz(paths['PRIOR_CONSTRAINTS'])
 h=b['heights'].astype(np.float64);o=ev79['heights'].astype(np.float64);p=np.load(paths['P'],allow_pickle=False).astype(np.float64);f=np.load(paths['F'],allow_pickle=False).astype(np.float64)
 level=review.vertex_levels(p,f);global ev79_level;ev79_level=level
 eligible=(b['cls']==0)&~cons['other_fixed'].astype(bool)&~cons['engineering_halo'].astype(bool)&~prior['large_lake_banks'].astype(bool)&(h>level)
 angles=edge_angles(h); seeds,selected,excluded=selector(h,eligible,angles)
 seed_by={tuple(s['coordinates']):s for s in seeds}
 for q in selected:q['seed_id']=seed_by[tuple(q['center'])]['seed_id']
 for q in excluded:q['seed_id']=seed_by[tuple(q['coordinates'])]['seed_id']
 # Structural preflight: exact 9x9 evaluation domains and every variable-touched hinge once.
 affected=[];covered={};coverage_errors=[]
 for q in selected:
  r,c=q['center']; vv=[(rr,cc) for rr in range(r-2,r+3) for cc in range(c-2,c+3) if eligible[rr,cc]]
  ds=sorted(set().union(*(author.vertex_hinges(v) for v in vv))) if vv else []
  for d in ds:
   kind,rr,cc=d
   if any(abs(vr-r)>4 or abs(vc-c)>4 for vr,vc in hinge_vertices(kind,rr,cc)):coverage_errors.append((q['queue_id'],d))
   covered[d]=covered.get(d,0)+1
   affected.append(d)
 if coverage_errors:raise RuntimeError(f'hinge escapes window9: {coverage_errors[:3]}')
 if any(n!=1 for n in covered.values()):raise RuntimeError('affected hinge sets overlap')
 # Exact p99 source domains and local-count thresholds are frozen from B.
 masks,pop_stats=pop_data(b,cons,angles)
 # Fixture: isolated disjoint count composition + deliberately bad negative.
 q0,q1,n,frac=stat_threshold(np.arange(100,dtype=np.float64)); assert q0==98 and q1==99 and n==100 and abs(frac-.01)<1e-12
 pos=np.arange(100,dtype=np.float64); pos[-1]=pos[-2]
 neg=np.arange(100,dtype=np.float64); neg[-2:]=101
 assert all(np.count_nonzero(pos[:50]<=q)>=np.count_nonzero(np.arange(100)[:50]<=q) and np.count_nonzero(pos[50:]<=q)>=np.count_nonzero(np.arange(100)[50:]<=q) for q in (q0,q1))
 assert not all(np.count_nonzero(neg[:50]<=q)>=np.count_nonzero(np.arange(100)[:50]<=q) and np.count_nonzero(neg[50:]<=q)>=np.count_nonzero(np.arange(100)[50:]<=q) for q in (q0,q1))
 # F corner independently controls eligibility when P is NaN; partial F is conservatively rejected.
 p_fixture=float('nan');f_fixture=np.asarray([1.25,np.nan,np.nan,np.nan]);
 level_corner=max(SEA,f_fixture[0] if math.isfinite(float(f_fixture[0])) else SEA,p_fixture if math.isfinite(p_fixture) else SEA)
 assert level_corner==1.25 and 1.1<=level_corner
 assert cell_f_partial(f_fixture.reshape(1,1,4),0,0)
 assert not cell_f_partial(np.full((1,1,4),np.nan),0,0) and not cell_f_partial(np.ones((1,1,4)),0,0)
 # Exercise the parent scheduler, peer completion, timeout kill, and replacement.
 ctx=mp.get_context('spawn');timeout_fixture=timeout_scheduler_fixture(ctx)
 preflight={'status':'PASS_EV87_PREFLIGHT','inputs':ids,'input_paths':{k:str(v) for k,v in paths.items()},
  'selector':{'eligible_vertices':int(eligible.sum()),'seed_count':len(seeds),'selected_count':len(selected),'excluded_count':len(excluded),'affected_hinges':len(covered),'windows9_disjoint':True,'affected_hinges_exactly_once':True},
   'p99_domains':{d:{'n':x['population'],'threshold_q0':x['threshold'][0],'threshold_q1':x['threshold'][1],'fraction':x['threshold'][3],'p99':x['threshold'][0]+x['threshold'][3]*(x['threshold'][1]-x['threshold'][0]),'count30_B':x['count30']} for d,x in pop_stats.items()},
 'fixtures':{'solver_wiring':solver_wiring_fixture(),'p99_order_stats_positive_negative':True,'F_while_P_nan':True,'partial_F_reject':True,**timeout_fixture},
  'consumer_script_sha256':sha(REVIEW),'selector_digest':canonical_sha({'seeds':seeds,'selected':selected,'excluded':excluded}),
  'walltime_deadline_s':DEADLINE,'per_patch_timeout_s':PATCH_TIMEOUT,'maxiter':MAXITER}
 write_json(OUT/'preflight.json',preflight)
 # Publish full queue before solving so the consumer/reviewer can independently check selection.
 header={'event':'header','source_B_sha256':ids['B'],'source_EV79_sha256':ids['EV79'],'source_constraints_sha256':ids['EV79_CONSTRAINTS'],
  'prior_constraints_sha256':ids['PRIOR_CONSTRAINTS'],'P_sha256':ids['P'],'F_sha256':ids['F'],'WRP_sha256':ids['WRP'],
  'seeds':seeds,'selected':selected,'excluded':excluded,'inventory_sha256':preflight['selector_digest'],'queue_sha256':canonical_sha(selected),
  'queue_count':len(selected),'complete_inventory':True,'windows':'half-open [r0,c0,r1,c1]'}
 ledger=OUT/'queue-ledger.jsonl';ledger.write_text(json.dumps(header,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
 write_json(OUT/'progress.json',{'status':'RUNNING','processed':0,'total':len(selected),'accepted':0,'rejected':0,'timeout':0,'selector_digest':preflight['selector_digest']})
 print(json.dumps({'event':'preflight','queue':len(selected),'seeds':len(seeds),'eligible':int(eligible.sum()),'affected_hinges':len(covered),'preflight':str(OUT/'preflight.json')}),flush=True)
 if not args.execute:return
 # Precompute B/source levels and work items; queue remains deterministic.
 work=selected
 # Dispatch in deterministic order, integrate in order. Parent enforces hard timeout.
 ctx=mp.get_context('spawn'); workers=[]; start=run_started; accepted=0; rejected=0; timedout=0; patches=[]; cursor=0; next_integrate=0; pending={}; completed={}; directions={}; candidate=h.astype(np.float32,copy=True); queue_status={}
 try:
  workers=[start_worker(ctx) for _ in range(2)]
  # To bound transport/memory, one task per worker and only two outstanding.
  while next_integrate<len(work):
   if time.monotonic()-start>=DEADLINE:break
   for w in workers:
    if w.get('needs_restart') and all((x is w) or x.get('busy') is None for x in workers):
     wi=workers.index(w);workers[wi]=start_worker(ctx);w=workers[wi]
    if w.get('proc') is not None and not w.get('needs_restart') and w['busy'] is None and cursor<len(work):
     q=selected[cursor];task={'queue':q}
     w['conn'].send(task);w['busy']=cursor;w['dispatch_time']=time.monotonic();pending[cursor]=w;cursor+=1
   # Observe both workers so each 5s deadline is enforced independently by the parent.
   for wi,w in enumerate(list(workers)):
    if w['busy'] is None:continue
    qi=w['busy'];elapsed=time.monotonic()-w['dispatch_time']
    if w['conn'].poll(0):
     msg=w['conn'].recv();result=msg.get('result',{'state':'rejected_solver','reason':msg.get('error','malformed_worker_result'),'mutable_nodes':[]})
     if float(result.get('elapsed_ms',elapsed*1000))>PATCH_TIMEOUT*1000:
      result={'state':'timeout','reason':'parent_enforced_5s_timeout','worker_status':'terminated_after_late_result','elapsed_ms':float(result.get('elapsed_ms')),'mutable_nodes':[]}
      timedout+=1;w['proc'].terminate();w['proc'].join(2)
      try:w['conn'].close()
      except Exception:pass
      workers[wi]={'proc':None,'conn':None,'busy':None,'needs_restart':True}
     completed[qi]=result;w['busy']=None
    elif elapsed>PATCH_TIMEOUT:
     w['proc'].terminate();w['proc'].join(2);timedout+=1
     completed[qi]={'state':'timeout','reason':'parent_enforced_5s_timeout','worker_status':'terminated','elapsed_ms':round(elapsed*1000,3),'mutable_nodes':[]}
     try:w['conn'].close()
     except Exception:pass
     workers[wi]={'proc':None,'conn':None,'busy':None,'needs_restart':True}
   if next_integrate not in completed:
    time.sleep(.01);continue
   qi=next_integrate;result=completed.pop(qi);pending.pop(qi,None);q=selected[qi];state=result.get('state')
   if str(result.get('reason','')).startswith('worker_exception:'):
    failed={'event':'final','status':'FAILED_IMPLEMENTATION','remaining_count':len(selected)-next_integrate,'processed_count':next_integrate,
     'accepted_count':accepted,'rejected_count':rejected,'timeout_count':timedout,'queue_sha256':header['queue_sha256'],
     'inventory_sha256':header['inventory_sha256'],'failure_queue_id':qi,'failure_reason':result['reason']}
    with ledger.open('a',encoding='utf-8') as f_ledger:f_ledger.write(json.dumps(failed,ensure_ascii=False,allow_nan=False)+'\n');f_ledger.flush();os.fsync(f_ledger.fileno())
    write_json(OUT/'progress.json',{'status':'FAILED_IMPLEMENTATION','processed':next_integrate,'total':len(selected),'queue_id':qi,'reason':result['reason']})
    raise RuntimeError(f'worker implementation exception at queue {qi}: {result["reason"]}')
   rr,cc=q['center'];expected_nodes=[[vr,vc] for vr in range(rr-2,rr+3) for vc in range(cc-2,cc+3) if eligible[vr,vc]]
   if result.get('mutable_nodes') not in (None,[],expected_nodes) and result.get('mutable_nodes')!=expected_nodes:raise RuntimeError(f'worker variable inventory mismatch queue {qi}')
   ev={'event':'patch','queue_id':qi,'seed_id':q['seed_id'],'center':q['center'],'window7':q['window7'],'window9':q['window9'],
       'mutable_nodes':expected_nodes,'state':state,'elapsed_ms':result.get('elapsed_ms'),'worker_status':result.get('worker_status','completed')}
   if state=='accepted':
    key=f'q{qi:06d}';vec=np.asarray(result.pop('direction_values'),dtype='<f4');ev.update(direction_key=key,direction_sha256=hashlib.sha256(vec.tobytes()).hexdigest())
    directions[key]=vec; indexnodes=ev['mutable_nodes'];
    # Candidate is exact one-shot midpoint from B and projected R; rejected patches remain B.
    for v,z in zip((tuple(x) for x in indexnodes),vec):candidate[v]=np.float32(float(h[v])+(float(z)-float(h[v]))*.5)
    accepted+=1
   else:
    ev['reason']=str(result.get('reason') or 'unspecified_rejection');rejected+=1
   for k in ('solver','projection','focus_delta_R','focus_delta_mid','p99_counts','max_half_order_deficit_m','changed_nodes','traceback'):
    if k in result:ev[k]=result[k]
   line=json.dumps(ev,ensure_ascii=False,allow_nan=False); 
   with ledger.open('a',encoding='utf-8') as f_ledger:f_ledger.write(line+'\n');f_ledger.flush();os.fsync(f_ledger.fileno())
   patches.append(ev);next_integrate+=1
   if next_integrate%25==0:
    write_json(OUT/'progress.json',{'status':'RUNNING','processed':next_integrate,'total':len(selected),'accepted':accepted,'rejected':rejected,'timeout':timedout,'elapsed_s':round(time.monotonic()-start,2),'queue_sha256':header['queue_sha256']})
    print(json.dumps({'event':'progress','processed':next_integrate,'total':len(selected),'accepted':accepted,'rejected':rejected,'timeout':timedout,'elapsed_s':round(time.monotonic()-start,2)}),flush=True)
  complete=(next_integrate==len(work) and time.monotonic()-start<DEADLINE)
  for w in workers:
   if w.get('proc') is None:continue
   try:w['conn'].send(None)
   except Exception:pass
   w['proc'].join(1)
   if w['proc'].is_alive():w['proc'].terminate();w['proc'].join(2)
   try:w['conn'].close()
   except Exception:pass
  direction_index={'queue_id_to_direction':{str(int(k[1:])):{'key':k,'nodes':patches[int(k[1:])]['mutable_nodes'],'sha256':hashlib.sha256(v.tobytes()).hexdigest()} for k,v in directions.items()}}
  final={'event':'final','status':'COMPLETE' if complete else 'INCOMPLETE','remaining_count':len(selected)-next_integrate,'processed_count':next_integrate,
   'accepted_count':accepted,'rejected_count':rejected,'timeout_count':timedout,'candidate_sha256':None,'directions_sha256':None,
   'queue_sha256':header['queue_sha256'],'inventory_sha256':header['inventory_sha256']}
  if complete:
   # Emit only complete candidate/sidecar names. Preserve B metadata byte values.
   arrays=dict(b);arrays['heights']=candidate
   candpath=OUT/'candidate-terrain.npz';np.savez_compressed(candpath,**arrays)
   dirpath=OUT/'directions.npz';np.savez_compressed(dirpath,**directions)
   idxpath=OUT/'direction-index.json';write_json(idxpath,direction_index)
   final['candidate_sha256']=sha(candpath);final['directions_sha256']=sha(dirpath);final['direction_index_sha256']=sha(idxpath)
   final['ledger_before_final_sha256']=sha(ledger)
  with ledger.open('a',encoding='utf-8') as f_ledger:f_ledger.write(json.dumps(final,ensure_ascii=False,allow_nan=False)+'\n');f_ledger.flush();os.fsync(f_ledger.fileno())
  write_json(OUT/'progress.json',{'status':final['status'],'processed':next_integrate,'total':len(selected),'accepted':accepted,'rejected':rejected,'timeout':timedout,'elapsed_s':round(time.monotonic()-start,2)})
  print(json.dumps(final),flush=True)
 except BaseException:
  for w in workers:
   if w.get('proc') is None:continue
   try:w['proc'].terminate();w['proc'].join(2)
   except Exception:pass
  raise

if __name__=='__main__':main()
