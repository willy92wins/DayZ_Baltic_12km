"""Challenge the inherited six-metre turn gate with exact known geometry."""
from pathlib import Path
import sys,json
import numpy as np
import shapely
from shapely.geometry import LineString,box
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path(__file__).parent
sys.path.insert(0,'E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009')
from verify_native_turns import geometry,line_stats

def actual_kinks(lines):
 turns=[];energy=0.;length=sum(q.length for q in lines)
 for line in lines:
  xy=np.array(line.coords);ds=np.linalg.norm(np.diff(xy,axis=0),axis=1);xy=xy[np.r_[True,ds>1e-7]]
  if len(xy)<3:continue
  a=xy[1:-1]-xy[:-2];b=xy[2:]-xy[1:-1]
  angles=np.arctan2(abs(a[:,0]*b[:,1]-a[:,1]*b[:,0]),np.sum(a*b,axis=1));turns.extend(np.degrees(angles).tolist());energy+=np.sum(angles*angles)
 samples=[]
 for phase in (0,.25,.5,.75):
  total=0
  for line in lines:
   xy=np.array([line.interpolate(d).coords[0] for d in np.arange(phase,line.length,1.)]);a=np.diff(xy,axis=0)
   if len(a)<2:continue
   angle=np.arctan2(abs(a[:-1,0]*a[1:,1]-a[:-1,1]*a[1:,0]),np.sum(a[:-1]*a[1:],axis=1));total+=np.sum(angle*angle)
  samples.append(total)
 return dict(corner_count=len(turns),corner_max_degrees=float(max(turns,default=0)),corner_turn_square_sum=float(energy),corner_turn_square_per_m=float(energy/length),one_metre_turn_square_mean=float(np.mean(samples)),one_metre_phases=samples)

def main():
 theta=np.linspace(-np.pi/2,np.pi/2,301)
 square=LineString([(0,-5),(20,-5),(20,5),(0,5)])
 roundcap=LineString(np.vstack(([0,-5],np.c_[15+5*np.cos(theta),5*np.sin(theta)],[0,5])))
 control={name:dict(legacy=line_stats([line]),actual=actual_kinks([line])) for name,line in [('square',square),('round',roundcap)]}
 a,b=control['square']['legacy'],control['round']['legacy']
 control['legacy_accepts_round_cap']=b['p90_degrees']<=.9*a['p90_degrees'] and b['over30_share']<=a['over30_share'] and b['max_degrees']<=a['max_degrees']
 h=np.load('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')['heights'].astype(float);v=np.load(B/'candidate/terrain.npz')['heights'].astype(float);p=np.load('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy');f=np.repeat(p[:,:,None],4,axis=2)
 r0,c0,r1,c1=589,2027,610,2047;cells=[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(p[r,c])];extent=box(c0*6,12282-r1*6,c1*6,12282-r0*6)
 fig,axes=plt.subplots(1,2,figsize=(13,6),layout='constrained');actual={}
 for name,t,color in [('source',h,'#3473c7'),('candidate',v,'#d14124')]:
  poly=geometry(t,f,cells);lines=shapely.line_merge(poly.boundary.difference(extent.boundary.buffer(.001)));lines=[q for q in getattr(lines,'geoms',[lines]) if q.geom_type=='LineString' and q.length>24]
  actual[name]=actual_kinks(lines)
  for i,line in enumerate(lines):axes[1].plot(*np.array(line.coords).T,color=color,label=name if i==0 else None)
 for name,line in [('square',square),('round',roundcap)]:axes[0].plot(*np.array(line.coords).T,label=name)
 for ax in axes:ax.set_aspect('equal');ax.legend();ax.grid(alpha=.2)
 axes[0].set_title('Known geometry: sharp and rounded cap');axes[1].set_title('Nazia: actual native triangles')
 fig.savefig(B/'metric-discriminator.png',dpi=140)
 report=dict(status='METRIC_DIAGNOSTIC_NOT_CANDIDATE_ACCEPTANCE',controls=control,native_candidate=actual,limits=['Raw corners and one-metre samples are diagnostics, not retroactively substituted acceptance gates.','The inherited six-metre statistic measures curvature as well as angularity.'])
 (B/'metric-discriminator.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
