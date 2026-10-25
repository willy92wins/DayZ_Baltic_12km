from pathlib import Path
import sys,json,hashlib
import numpy as np
import shapely
from shapely.geometry import shape,box
sys.path[:0]=['E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009','E:/DayZ-Baltic-Build/v30-native-contour-fit-20261009','E:/DayZ-Baltic-Build/v30-surface-crease-audit-20261009']
from verify_native_turns import geometry,line_stats
from check_shape_metric import actual_kinks
from audit_native_surface import hinges,incident_any
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build');SOURCE=R/'v30-native-hinge-finish-20261009/candidate/terrain.npz';PLANE=R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not (B/'authoring.json').exists()
 t=dict(np.load(SOURCE));h=t['heights'].astype(float);p=np.load(PLANE);fixed=np.load(R/'v30-native-terminal-finish-20261009/constraints.npz')['fixed']
 target=shape(json.loads((R/'v30-native-contour-fit-20261009/authoring.json').read_text())['target']);jobs=json.loads((R/'v30-rounded-terminal-footprint-20261009/discovery.json').read_text())['jobs'];job=next(q for q in jobs if q['features']==['stream_0207:0']);r0,c0,r1,c1=job['box_cells'];cx,cz=job['center'];level=3.425
 rr,cc=np.mgrid[r0+1:r1,c0+1:c1];rr,cc=rr.ravel(),cc.ravel();xy=np.c_[cc*6,12282-rr*6];distance=shapely.distance(shapely.points(xy),target.boundary);radial=np.linalg.norm(xy-[cx,cz],axis=1);inside=shapely.covers(target,shapely.points(xy));signed=np.where(inside,-distance,distance)
 keep=(radial<72)&(distance<30)&~fixed[rr,cc]&np.isin(t['cls'][rr,cc],[0,6]);rr,cc,distance,radial,signed=[a[keep] for a in (rr,cc,distance,radial,signed)]
 support=np.zeros(len(rr),bool)
 for dr,dc in ((0,0),(0,1),(1,0),(1,1)):support|=np.isfinite(p[rr-dr,cc-dc])
 border=np.minimum.reduce((rr-r0,r1-rr,cc-c0,c1-cc))*6
 blend=np.clip((30-distance)/12,0,1)*np.clip((72-radial)/12,0,1)*np.clip(border/12,0,1);blend=blend*blend*(3-2*blend);old=h[rr,cc]
 cells=[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(p[r,c])];field=np.repeat(p[:,:,None],4,axis=2);before=geometry(h,field,cells);history=[]
 def value(offset):
  new=old+blend*(level+.25*(signed-offset)-old);new=np.clip(new,np.maximum(old-1.5,1.),old+1.5);new[~support]=np.maximum(new[~support],level+.0001)
  v=h.copy();v[rr,cc]=new.astype(np.float32);geom=geometry(v,field,cells);history.append(dict(offset_m=float(offset),area_m2=float(geom.area)));return v,geom
 lo,hi=0.,3.;vl,gl=value(lo);vh,gh=value(hi);assert gl.area<=gh.area
 if not gl.area<=before.area<=gh.area:
  result=dict(status='INFEASIBLE_NATIVE_AREA_BRACKET_NO_CANDIDATE',source_area_m2=before.area,history=history);(B/'authoring.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));return
 for _ in range(32):
  offset=(lo+hi)/2;v,after=value(offset)
  assert gl.area-1e-7<=after.area<=gh.area+1e-7
  if abs(after.area-before.area)<1e-5:break
  if after.area<before.area:lo,gl=offset,after
  else:hi,gh=offset,after
 allowed=np.zeros(h.shape,bool);allowed[rr,cc]=True;out={k:a.copy() for k,a in t.items()};out['heights']=v.astype(np.float32);wet=v[rr,cc]<level;meta=float(np.nanmedian(t['level'][rr[t['cls'][rr,cc]==6],cc[t['cls'][rr,cc]==6]]));out['cls'][rr,cc]=np.where(wet,6,0);out['water'][rr,cc]=wet;out['level'][rr,cc]=np.where(wet,meta,np.nan)
 candidate=B/'candidate';candidate.mkdir(exist_ok=False);np.savez_compressed(candidate/'terrain.npz',**out);ids=np.flatnonzero(v!=h);np.savez_compressed(B/'delta.npz',ids=ids,before=h.ravel()[ids],after=v.ravel()[ids]);np.savez_compressed(B/'domain.npz',allowed=allowed,fixed=fixed,rr=rr,cc=cc,signed=signed,offset=offset)
 extent=box(c0*6,12282-r1*6,c1*6,12282-r0*6)
 def lines(poly):
  result=shapely.line_merge(poly.boundary.difference(extent.boundary.buffer(.001)));return [q for q in getattr(result,'geoms',[result]) if q.geom_type=='LineString' and q.length>24]
 a,b=actual_kinks(lines(before)),actual_kinks(lines(after));stats=[]
 for terrain in (h,v):
  values=np.concatenate([values[incident_any(allowed,kind)] for kind,values in hinges(terrain)]);stats.append(dict(rms=float(np.sqrt(np.mean(values**2))),over30=int((values>30).sum()),max=float(values.max())))
 def slopes(a):
  nw,ne,sw,se=a[:-1,:-1],a[:-1,1:],a[1:,:-1],a[1:,1:];return [np.degrees(np.arctan(np.hypot(ne-nw,se-ne)/6)),np.degrees(np.arctan(np.hypot(se-sw,sw-nw)/6))]
 core=(signed-offset)<=-3
 gates=dict(outside_exact=np.array_equal(v[~allowed],h[~allowed]),fixed_exact=np.array_equal(v[fixed],h[fixed]),max_delta=abs(v-h).max()<=1.500001,bed_floor=np.all(v[rr,cc]>=1),core_depth=np.all(level-v[rr[core],cc[core]]>=.30-1e-6),slopes=all(np.all(y<=np.maximum(x,35)+1e-4) for x,y in zip(slopes(h),slopes(v))),native_area=abs(after.area-before.area)<.001,displacement=shapely.hausdorff_distance(before.boundary,after.boundary)<=4.1,corner_max=b['corner_max_degrees']<=a['corner_max_degrees']+1e-6,angular_energy=b['one_metre_turn_square_mean']<=.9*a['one_metre_turn_square_mean'],native_rms=stats[1]['rms']<=stats[0]['rms']);gates={k:bool(v) for k,v in gates.items()}
 result=dict(status='SOURCE_CANDIDATE_REQUIRES_INDEPENDENT_CONSUMER' if all(gates.values()) else 'REJECTED_NATIVE_AREA_CONSTRAINED_PROFILE',source_sha256=sha(SOURCE),candidate_sha256=sha(candidate/'terrain.npz'),gates=gates,offset_m=offset,history=history,changed_vertices=len(ids),class_changes=int(np.count_nonzero(t['cls']!=out['cls'])),maximum_delta_m=float(abs(v-h).max()),before_area_m2=before.area,after_area_m2=after.area,hausdorff_m=float(shapely.hausdorff_distance(before.boundary,after.boundary)),actual_before=a,actual_after=b,legacy_before=line_stats(lines(before)),legacy_after=line_stats(lines(after)),native_hinges=stats,limits=['No game, model coverage, package or global acceptance.','Offset solves native area only; it was not selected by the angular or slope metrics.'])
 (B/'authoring.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='history'},indent=2))
if __name__=='__main__':main()
