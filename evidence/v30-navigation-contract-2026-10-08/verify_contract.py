"""Read-only consumer: independent box enumeration of all corridor/native faces."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import shapely
from shapely.geometry import shape,box,LineString,Point
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/terrain'))
from v30_common import cell_planes,tri_sample
from verify_roads_v30 import evaluate
SOURCE=Path('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/wave-banks-r1/terrain_wave_banks.npz')
CANDIDATE=Path('E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz')
CORRIDORS=Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(CORRIDORS)=='28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343'
a,b=np.load(SOURCE),np.load(CANDIDATE);old,new=a['heights'].astype(float),b['heights'].astype(float)
decision=json.loads((OUT/'decision.json').read_text());minimum=decision['nominal_corridor_min_depth_m']
assert minimum==.95
planes=cell_planes(a['cls'],a['level'],sea_cut=.51)

def corridor_faces(geom):
    """No rasterize/records reuse: walk intersecting 64-cell boxes then triangles."""
    x0,z0,x1,z1=geom.bounds
    c0=max(0,int(np.floor(x0/6)));c1=min(2047,int(np.ceil(x1/6)))
    r0=max(0,int(np.floor((12282-z1)/6)));r1=min(2047,int(np.ceil((12282-z0)/6)))
    for r in range(r0,r1,64):
      for c in range(c0,c1,64):
        re,ce=min(r+64,r1),min(c+64,c1)
        if not geom.intersects(box(c*6,12282-re*6,ce*6,12282-r*6)):continue
        rr,cc=np.mgrid[r:re,c:ce];rr,cc=rr.ravel(),cc.ravel()
        for half,(dr,dc) in enumerate(((0,1),(1,0))):
          vertices=np.stack([np.column_stack((cc*6,12282-rr*6)),
                             np.column_stack(((cc+dc)*6,12282-(rr+dr)*6)),
                             np.column_stack(((cc+1)*6,12282-(rr+1)*6))],axis=1)
          clipped=shapely.intersection(shapely.polygons(vertices),geom)
          keep=shapely.area(clipped)>1e-9
          if np.any(keep):yield rr[keep],cc[keep],half,clipped[keep]

reports=[];rejected_obstacle=False;rejected_missing_face=False
features=json.loads(CORRIDORS.read_text())['features'];assert len(features)==19
for feature in features:
    geom=shape(feature['geometry']);count=0;covered=0.;seen=set();worst=None;failed=set();old_failed=set()
    removed_area=None
    for rr,cc,half,polys in corridor_faces(geom):
        coords,owner=shapely.get_coordinates(polys,return_index=True)
        surface=np.maximum(np.nan_to_num(planes[rr,cc],nan=-np.inf),.5)[owner]
        d=surface-tri_sample(new,coords[:,0],coords[:,1])
        d0=surface-tri_sample(old,coords[:,0],coords[:,1])
        ident=((rr*2047+cc)*2+half).astype(int)
        assert not seen.intersection(ident.tolist());seen.update(ident.tolist())
        failed.update(ident[owner[d<minimum-1e-9]].tolist())
        old_failed.update(ident[owner[d0<.99]].tolist())
        k=int(np.argmin(d))
        if worst is None or d[k]<worst['depth_m']:
            worst=dict(depth_m=float(d[k]),xz=coords[k].tolist(),cell=[int(rr[owner[k]]),int(cc[owner[k]])])
        area=shapely.area(polys);covered+=float(area.sum());count+=len(polys)
        if removed_area is None:removed_area=float(area.max())
        if not rejected_obstacle:
            q=int(np.argmax(d));r,c=int(rr[owner[q]]),int(cc[owner[q]])
            bad=new.copy();bad[r:r+2,c:c+2]=surface[q]-.94
            rejected_obstacle=bool(surface[q]-tri_sample(bad,*coords[q])<minimum)
    area_error=abs(covered-geom.area)
    assert count and area_error<1e-5,(feature['properties']['river'],area_error)
    rejected_missing_face |= bool(abs((covered-removed_area)-geom.area)>1e-5)
    reports.append(dict(river=feature['properties']['river'],faces=count,area_m2=geom.area,
                        coverage_error_m2=area_error,failing_faces=len(failed),old_failures_at_0_99=len(old_failed),worst=worst))
changed=old!=new;r,c=np.indices(new.shape)
narva=np.hypot(c*6-2417.1428225906,12282-r*6-6889.8850822322)<=620
high=(b['cls']==3)&(b['level']>=2)&~narva
checks=dict(nonempty_19_corridors=len(reports)==19,depth_0_95=all(p['failing_faces']==0 for p in reports),
            metadata_exact=all(np.array_equal(a[k],b[k],equal_nan=True) for k in a.files if k!='heights'),
            high_bed_floor=bool(np.all(new[high]>=1)),baseline_floor_rejected=bool(np.any(old[high]<1)),
            only_2_isolated_high_beds=int(changed.sum())==2 and bool(np.all(high[changed])),
            no_lowering=bool(np.all(new>=old)),dry_ground_exact=bool(np.array_equal(old[a['cls']==0],new[a['cls']==0])),
            roads_and_platform_vertices_exact=not bool(np.any(changed&(a['reserve']|a['platform']))),
            narva_exact=bool(np.array_equal(old[narva],new[narva])),
            obstacle_0_94_rejected=rejected_obstacle,missing_face_rejected=rejected_missing_face)
steep=[]
for dr,dc in ((0,1),(1,0)):
    def slope(h):
        mid=h[dr:dr+2047,dc:dc+2047]
        return np.degrees(np.arctan(np.hypot(mid-h[:-1,:-1],h[1:,1:]-mid)/6))
    before,after=slope(old),slope(new)
    land=a['cls']==0;touch=land[:-1,:-1]|land[dr:dr+2047,dc:dc+2047]|land[1:,1:]
    steep.extend(dict(row=int(r),col=int(c),before=float(before[r,c]),after=float(after[r,c]))
                 for r,c in zip(*np.nonzero(touch&(after>35.01)&(after>before+1e-6))))
checks['mixed_steep_faces_not_worsened']=not steep
roads=evaluate(new,a['water'].astype(bool));checks['roads_pass']=roads['status']=='PASS'
route_reports=[];vertices=[Point(c*6,12282-r*6) for r,c in zip(*np.nonzero(changed))]
for kind,ref in [('car',ROOT/'evidence/v30-bug-recheck-2026-10-08/drive-reference.json'),
                 ('boat',ROOT/'evidence/v30-bounded-integration-2026-10-08/boat-reference.json')]:
    for case in json.loads(ref.read_text())['cases']:
        raw=np.asarray(case['route_xyz'] if kind=='car' else case['waypoints_xz'])
        line=LineString(raw[:,[0,2]] if kind=='car' else raw)
        route_reports.append(dict(kind=kind,case=case['case'],distance_m=min(p.distance(line) for p in vertices)))
checks['previous_vehicle_routes_outside_25m']=all(q['distance_m']>25 for q in route_reports)
ref=json.loads((ROOT/'evidence/v30-continuation-2026-10-08/controls-reference.json').read_text())
coords=np.asarray([[p['x'],p['z']] for p in ref['points']])
checks['18_water_observers_exact']=bool(np.array_equal(tri_sample(old,*coords.T),tri_sample(new,*coords.T)))
floor=dict(high_vertices=int(high.sum()),old_below_1=int((old[high]<1).sum()),new_below_1=int((new[high]<1).sum()))
result=dict(status='PASS_OFFLINE_NAVIGATION_CONTRACT' if all(checks.values()) else 'FAIL',checks=checks,
 inputs={str(p):sha(p) for p in [SOURCE,CANDIDATE,CORRIDORS,OUT/'decision.json',Path(__file__)]},
 minimum_depth_m=min(p['worst']['depth_m'] for p in reports),native_faces=sum(p['faces'] for p in reports),
 corridors=reports,floor=floor,steep_faces=steep,roads=roads,routes=route_reports,
 limits=['24 m corridor polygons retain their frozen endpoint and Narva exclusions.',
         'Independent face enumeration, shared native sampler and water-plane rule.',
         'Nominal geometry only; water response after raising two beds requires engine replay.'])
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('status','checks','minimum_depth_m','native_faces','floor','steep_faces')},indent=1))
assert result['status']=='PASS_OFFLINE_NAVIGATION_CONTRACT'
