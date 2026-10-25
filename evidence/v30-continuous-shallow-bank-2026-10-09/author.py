from pathlib import Path
import sys,json,hashlib
import numpy as np
import shapely
from shapely.geometry import shape,box
sys.path[:0]=['E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009','E:/DayZ-Baltic-Build/v30-native-contour-fit-20261009','E:/DayZ-Baltic-Build/v30-surface-crease-audit-20261009']
from verify_native_turns import geometry,line_stats
from check_shape_metric import actual_kinks
from audit_native_surface import hinges,incident_any
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build')
SOURCE=R/'v30-native-hinge-finish-20261009/candidate/terrain.npz';PLANE=R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy';FIELD=R/'v30-frozen-water-stitch-20261009/preserved-field.npy'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 assert not (B/'authoring.json').exists(),'one continuous-shallow-profile candidate'
 t=dict(np.load(SOURCE));h=t['heights'].astype(float);p=np.load(PLANE);f=np.load(FIELD);fixed=np.load(R/'v30-native-terminal-finish-20261009/constraints.npz')['fixed']
 target=shape(json.loads((R/'v30-native-contour-fit-20261009/authoring.json').read_text())['target'])
 jobs=json.loads((R/'v30-rounded-terminal-footprint-20261009/discovery.json').read_text())['jobs'];job=next(q for q in jobs if q['features']==['stream_0207:0']);r0,c0,r1,c1=job['box_cells'];cx,cz=job['center'];level=3.425
 rr,cc=np.mgrid[r0+1:r1,c0+1:c1];rr,cc=rr.ravel(),cc.ravel();xy=np.c_[cc*6,12282-rr*6];distance=shapely.distance(shapely.points(xy),target.boundary);radial=np.linalg.norm(xy-[cx,cz],axis=1);inside=shapely.covers(target,shapely.points(xy));signed=np.where(inside,-distance,distance)
 keep=(radial<72)&(distance<30)&~fixed[rr,cc]&np.isin(t['cls'][rr,cc],[0,6]);rr,cc,xy,distance,radial,inside,signed=[a[keep] for a in (rr,cc,xy,distance,radial,inside,signed)]
 support=np.zeros(len(rr),bool)
 for dr,dc in ((0,0),(0,1),(1,0),(1,1)):support|=np.isfinite(p[rr-dr,cc-dc])
 assert np.all(~inside|support)
 blend=np.clip((30-distance)/12,0,1)*np.clip((72-radial)/12,0,1);blend=blend*blend*(3-2*blend)
 proposed=level+.25*signed;old=h[rr,cc];new=old+blend*(proposed-old);new=np.clip(new,np.maximum(old-1.5,1.),old+1.5)
 # Keep the intended side of the shore after blending; no artificial 30cm jump at the water edge.
 new=np.where(inside,np.minimum(new,level-.0001),np.maximum(new,level+.0001))
 v=h.copy();v[rr,cc]=new.astype(np.float32);out={key:value.copy() for key,value in t.items()};out['heights']=v.astype(np.float32)
 meta=float(np.nanmedian(t['level'][rr[t['cls'][rr,cc]==6],cc[t['cls'][rr,cc]==6]]));out['cls'][rr,cc]=np.where(inside,6,0);out['water'][rr,cc]=inside;out['level'][rr,cc]=np.where(inside,meta,np.nan)
 allowed=np.zeros(h.shape,bool);allowed[rr,cc]=True;changed=np.flatnonzero(v!=h);candidate=B/'candidate'
 if candidate.exists():
  retained=dict(np.load(candidate/'terrain.npz'));assert set(retained)==set(out) and all(np.array_equal(retained[k],out[k],equal_nan=True) for k in out),'JSON-only repair must reproduce every retained candidate array'
 else:
  candidate.mkdir(exist_ok=False);np.savez_compressed(candidate/'terrain.npz',**out);np.savez_compressed(B/'delta.npz',ids=changed,before=h.ravel()[changed],after=v.ravel()[changed]);np.savez_compressed(B/'domain.npz',allowed=allowed,fixed=fixed,rr=rr,cc=cc,signed_distance=signed)
 cells=[(r,c) for r in range(r0,r1) for c in range(c0,c1) if np.isfinite(p[r,c])];fields=np.repeat(p[:,:,None],4,axis=2);before=geometry(h,fields,cells);after=geometry(v,fields,cells);extent=box(c0*6,12282-r1*6,c1*6,12282-r0*6)
 def lines(poly):
  line=shapely.line_merge(poly.boundary.difference(extent.boundary.buffer(.001)));return [q for q in getattr(line,'geoms',[line]) if q.geom_type=='LineString' and q.length>24]
 actual_before,actual_after=actual_kinks(lines(before)),actual_kinks(lines(after));normals=[]
 for terrain in (h,v):
  parts=[values[incident_any(allowed,kind)] for kind,values in hinges(terrain)];values=np.concatenate(parts);normals.append(dict(rms=float(np.sqrt(np.mean(values**2))),over30=int((values>30).sum()),max=float(values.max())))
 def slopes(a):
  nw,ne,sw,se=a[:-1,:-1],a[:-1,1:],a[1:,:-1],a[1:,1:];return [np.degrees(np.arctan(np.hypot(ne-nw,se-ne)/6)),np.degrees(np.arctan(np.hypot(se-sw,sw-nw)/6))]
 gates=dict(outside_exact=bool(np.array_equal(v[~allowed],h[~allowed])),fixed_exact=bool(np.array_equal(v[fixed],h[fixed])),delta=float(abs(v-h).max())<=1.500001,bed_floor=bool(np.all(v[rr,cc]>=1.)),core_depth=bool(np.all(level-v[rr[inside&(distance>=3)],cc[inside&(distance>=3)]]>=.30-1e-6)),slopes=all(np.all(b<=np.maximum(a,35)+1e-4) for a,b in zip(slopes(h),slopes(v))),area_retained=after.area>=.9*before.area,displacement=shapely.hausdorff_distance(before.boundary,after.boundary)<=4.1,corner_max=actual_after['corner_max_degrees']<=actual_before['corner_max_degrees']+1e-6,angular_energy=actual_after['one_metre_turn_square_mean']<=.9*actual_before['one_metre_turn_square_mean'],native_rms=normals[1]['rms']<=normals[0]['rms'])
 gates={key:bool(value) for key,value in gates.items()}
 report=dict(status='SOURCE_CANDIDATE_REQUIRES_INDEPENDENT_CONSUMER' if all(gates.values()) else 'REJECTED_CONTINUOUS_SHALLOW_PROFILE',gates=gates,source_sha256=sha(SOURCE),candidate_sha256=sha(candidate/'terrain.npz'),target_source_sha256=sha(R/'v30-native-contour-fit-20261009/authoring.json'),changed_vertices=len(changed),class_changes=int(np.count_nonzero(out['cls']!=t['cls'])),maximum_delta_m=float(abs(v-h).max()),area_before_m2=before.area,area_after_m2=after.area,new_water_m2=after.difference(before).area,lost_water_m2=before.difference(after).area,hausdorff_m=float(shapely.hausdorff_distance(before.boundary,after.boundary)),actual_before=actual_before,actual_after=actual_after,legacy_before=line_stats(lines(before)),legacy_after=line_stats(lines(after)),native_hinges=normals,limits=['No model coverage, package or native game test yet.','One local pilot, no global smoothing or base acceptance.'])
 (B/'authoring.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
