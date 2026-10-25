"""Diagnostic only: compare shoreline feasibility under frozen vs product constraints."""
from pathlib import Path
import json,time,sys
import numpy as np
from scipy import sparse,ndimage
from scipy.optimize import lsq_linear
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
scope={};code=(B/'correct_shore.py').read_text()
exec(code[:code.index('lo=h-2.')],scope)
for k in ('W','E','t','h','ha','fixed','core','edge','water','pmin','pmax','wet','dry','ew','el','et','lv','x','z','lines_for'):
 globals()[k]=scope[k]
groove=np.load(W.parents[2]/'tests/terrain_v30/water_v30.npz')['groove']
n=2048;ends=np.unique(np.r_[ew,el]);local=np.zeros(h.size,bool);local[ends]=True
local=local.reshape(h.shape)&~fixed
report={}
measure={}
measure_code=(B/'measure_waterline.py').read_text()
exec(measure_code[:measure_code.index('label=sys.argv')],measure)
for policy in ('unchanged_bed','peripheral_margin','channel_depth_bound','bank_depth_bound'):
 lo=h-2.;hi=h+2.
 lo[wet]=np.maximum(lo[wet],np.minimum(h[wet],1.))
 hi[wet]=h[wet]
 if policy!='unchanged_bed':
  cap=np.fmin(np.fmin(pmin-.101,water-.101),t['level']-.101)
  free=wet&~groove if policy=='peripheral_margin' else wet
  if policy=='channel_depth_bound':cap=np.where(groove,np.fmin(cap,t['level']-.3001),cap)
  hi[free]=np.maximum(h[free],np.minimum(h[free]+6.,cap[free]))
 floor=np.fmax(1.4,np.fmax(pmax+.0501,water+.0501))
 lo[dry]=np.maximum(lo[dry],np.minimum(h[dry],floor[dry]))
 lo[fixed]=h[fixed];hi[fixed]=h[fixed]
 active=local&(hi-lo>1e-6);ids=np.flatnonzero(active)
 lookup=np.full(h.size,-1,int);lookup[ids]=np.arange(len(ids))
 rows=[];cols=[];vals=[];rhs=[]
 def add(indices,coeff,value):
  row=len(rhs)
  for i,c in zip(indices,coeff):
   col=lookup[i]
   if col<0:value-=c*h.ravel()[i]
   else:rows.append(row);cols.append(col);vals.append(c)
  rhs.append(value)
 for a,b,tau,y in zip(ew,el,et,lv):add([a,b],[1-tau,tau],y)
 A=sparse.csr_matrix((vals,(rows,cols)),shape=(len(rhs),len(ids)))
 fit=lsq_linear(A,np.array(rhs),bounds=(lo.ravel()[ids],hi.ravel()[ids]),tol=1e-9,lsmr_tol=1e-9,max_iter=120)
 got=h.copy();got.ravel()[ids]=fit.x
 residual=(1-et)*got.ravel()[ew]+et*got.ravel()[el]-lv
 midpoint=np.c_[(x.ravel()[ew]+x.ravel()[el])/2,(z.ravel()[ew]+z.ravel()[el])/2]
 group={}
 for name,ax in scope.get('axes',json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())).items():
  rc=np.array(ax['removed_cells']);r,c=rc.T
  m=(midpoint[:,0]>=c.min()*6)&(midpoint[:,0]<=(c.max()+1)*6)&(midpoint[:,1]>=12282-(r.max()+1)*6)&(midpoint[:,1]<=12282-r.min()*6)
  group[name]=dict(n=int(m.sum()),residual_median_p95=np.percentile(np.abs(residual[m]),[50,95]).tolist(),over_005=int((np.abs(residual[m])>.05).sum()),native_line=measure['stats'](lines_for(got,ax['removed_cells'])))
 largest=[]
 for j in np.argsort(np.abs(residual))[-8:]:
  a,b=ew[j],el[j]
  largest.append(dict(x=float(midpoint[j,0]),z=float(midpoint[j,1]),tau=float(et[j]),water=float(lv[j]),residual=float(residual[j]),wet_before=float(h.ravel()[a]),dry_before=float(h.ravel()[b]),wet_after=float(got.ravel()[a]),dry_after=float(got.ravel()[b]),wet_bounds=[float(lo.ravel()[a]),float(hi.ravel()[a])],dry_bounds=[float(lo.ravel()[b]),float(hi.ravel()[b])],groove=bool(groove.ravel()[a]),fixed_wet=bool(fixed.ravel()[a]),fixed_dry=bool(fixed.ravel()[b])))
 report[policy]=dict(success=bool(fit.success),iterations=fit.nit,variables=len(ids),cost=fit.cost,groups=group,wet_raise_vertices=int((got[wet]>h[wet]+1e-6).sum()),wet_max_raise=float((got[wet]-h[wet]).max()),fixed_changed=int(((got!=h)&fixed).sum()),largest=largest)
print(json.dumps(report,indent=2))
(E/'shore-feasibility-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n')
