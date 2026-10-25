"""Independent dense sections and protected-domain checks; not native acceptance."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from shapely.geometry import LineString, Point
from shapely import STRtree, points, distance
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2]


def audit(folder, heights=None, maximum_delta_m=1.35, maximum_geographic_distance_m=24.5, local_transition_v22=False, outline_v33_parent=False):
    manifest=json.loads((folder/'solve.json').read_text(encoding='utf-8'))
    parent_path=ROOT/('tests/regional_outline_smoothing_v33/reference.npz' if outline_v33_parent else 'tests/regional_foundation_combined_v10/reference.npz')
    if outline_v33_parent:
        assert hashlib.sha256(parent_path.read_bytes()).hexdigest()=='8e84d5ce38da8863116c52ecdf9953d5b201a097459513054eea8e0f0e14c45a'
        assert manifest.get('source_npz')=='tests/regional_outline_smoothing_v33/reference.npz'
    assert hashlib.sha256(parent_path.read_bytes()).hexdigest()==manifest['source_npz_sha256']
    parent=np.load(parent_path);base=parent['candidate']
    asc=next(folder.glob('*.asc'))
    with rasterio.open(asc) as ds:
        h=ds.read(1) if heights is None else heights
        format_ok=(ds.width==2048 and ds.height==2048 and ds.res==(6.,6.)
                   and tuple(ds.bounds)==(200000.,0.,212288.,12288.))
    changed=h!=base;wet=parent['wet']|parent['ocean'];wd=distance_transform_edt(~wet)*6
    declared=np.load(folder/'reference.npz')['pilot_support']
    corridor=[]
    for route in manifest['routes']:
        p=np.asarray(route['source_polyline']);station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        lo=route['solve_start_m'];hi=route['solve_end_m'];s=np.r_[lo,station[(station>lo)&(station<hi)],hi]
        corridor.append(LineString(np.column_stack([np.interp(s,station,p[:,i]) for i in [0,1]])))
    # Independent geometric envelope: 4m half-width, at most sqrt(2)*6m to
    # a native triangle vertex, plus the explicitly selected grading envelope.
    # V18/V20 use 24m transition and a separately specified 36.5m envelope.
    changed_r,changed_c=np.nonzero(changed)
    locations=points(np.column_stack([changed_c*6,12282-changed_r*6]))
    geometries=np.array(corridor,dtype=object);tree=STRtree(geometries)
    geographic_distances=distance(locations,geometries[tree.nearest(locations)]) if len(locations) else np.zeros(0)
    geographic_limits=np.full(len(locations),maximum_geographic_distance_m)
    if local_transition_v22:
        # Independent limits from plan V22, not copied from producer support.
        local=(changed_c*6>=4278)&(changed_c*6<=4572)&(12282-changed_r*6>=6876)&(12282-changed_r*6<=7008)
        geographic_limits[local]=60.5
    geometric_local=bool(np.all(geographic_distances<=geographic_limits))
    rr,cc=np.mgrid[:2048,:2048]
    allowed=(wd>30)&~parent['fairway_support']&(np.hypot(cc*6-2417.1428225906,12282-rr*6-6889.8850822322)>480)
    a=h[:-1,:-1];b=h[:-1,1:];c=h[1:,:-1];d=h[1:,1:]
    slope=np.degrees(np.arctan(np.maximum(np.hypot(b-a,d-b),np.hypot(d-c,c-a))/6))
    affected=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]
    checks=dict(format=format_ok,finite=bool(np.isfinite(h).all()),protected_exact=not bool(np.any(changed&~allowed)),delta_limit=bool(np.max(abs(h-base))<=maximum_delta_m+1e-5),dry_floor=bool(np.all(h[changed]>=np.minimum(base[changed],1.4)-1e-6)),affected_triangles=not bool(np.any(affected&(slope>35.01))))
    checks['island_minimum']=bool(np.all(h>=np.minimum(base,parent['island_minimum_conservative'])-1e-5))
    if outline_v33_parent:
        original=ROOT/'tests/regional_foundation_combined_v10/reference.npz'
        assert hashlib.sha256(original.read_bytes()).hexdigest()=='a43cb0f128c17318207a114f94f08801ff35a81af5d36a4b7e3427dd3d6aca2d'
        original_h=np.load(original)['candidate']
        checks['composed_delta_limit']=bool(np.all(abs(h[changed]-original_h[changed])<=6.+1e-5))
    checks.update(declared_support_exact=not bool(np.any(changed&~declared)),independent_geographic_support=geometric_local)
    reports=[];off=np.arange(-4,4.001,.25)
    for route in manifest['routes']:
        p=np.asarray(route['source_polyline']);station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        s=np.arange(.113,station[-1],.37)
        q=np.column_stack([np.interp(s,station,p[:,i]) for i in [0,1]])
        tangent=np.gradient(q,axis=0);normal=np.column_stack([-tangent[:,1],tangent[:,0]])/np.linalg.norm(tangent,axis=1)[:,None]
        sections=q[None,:,:]+off[:,None,None]*normal[None,:,:]
        values=[np.array([sample(z,v[:,0]+200000,v[:,1]) for v in sections]) for z in [base,h]]
        ri=np.clip(np.rint((12282-q[:,1])/6).astype(int),0,2047);ci=np.clip(np.rint(q[:,0]/6).astype(int),0,2047)
        eligible=(wd[ri,ci]>48)&(np.linalg.norm(q-[2417.1428225906,6889.8850822322],axis=1)>480)&(s>18)&(s<station[-1]-18)
        core=eligible&(s>=route['station_start_m'])&(s<=route['station_end_m'])
        if not core.any():
            reports.append(dict(chain=route['chain'],sections=0,pass_without_eligible_sections=True,**{'pass':True}));continue
        cross0,cross=[np.ptp(v,axis=0) for v in values];middle=len(off)//2
        grade=abs(np.diff(values[1][middle])/np.diff(s));pairs=core[1:]&core[:-1]
        along=[];chord_valid=core.copy()
        for delta in [-3,0,3]:
            pts=np.column_stack([np.interp(s+delta,station,p[:,i]) for i in [0,1]])
            along.append(sample(h,pts[:,0]+200000,pts[:,1]))
            rj=np.clip(np.rint((12282-pts[:,1])/6).astype(int),0,2047);cj=np.clip(np.rint(pts[:,0]/6).astype(int),0,2047)
            chord_valid&=(wd[rj,cj]>48)&(np.linalg.norm(pts-[2417.1428225906,6889.8850822322],axis=1)>480)&(s+delta>18)&(s+delta<station[-1]-18)
        chord=abs(along[1]-.5*(along[0]+along[2]))
        new_bad=eligible&(cross>.03)&(cross>cross0+.001)
        failed=np.flatnonzero(core&(cross>.03))
        record=dict(chain=route['chain'],sections=int(core.sum()),cross_failures=int(len(failed)),max_cross_m=float(cross[core].max()),grade_failures=int(np.sum(pairs&(grade>.065))),max_grade=float(grade[pairs].max()),chord_failures=int(np.sum(chord_valid&(chord>.03))),max_chord_m=float(chord[chord_valid].max()) if chord_valid.any() else 0.,new_or_worse_cross_outside_core=int(np.sum(new_bad&~core)),examples=[dict(station_m=float(s[i]),xz=q[i].tolist(),cross_m=float(cross[i]),baseline_m=float(cross0[i])) for i in failed[:8]])
        record['pass']=not any(record[k] for k in ['cross_failures','grade_failures','chord_failures','new_or_worse_cross_outside_core'])
        reports.append(record)
    checks['routes']=all(x['pass'] for x in reports)
    result=dict(status='PASS_OFFLINE_EDITABLE_DRY_NETWORK_GEOMETRY' if all(checks.values()) else 'FAIL_OFFLINE_NETWORK_GEOMETRY',checks=checks,changed_vertices=int(changed.sum()),max_delta_m=float(abs(h-base).max()),max_affected_triangle_degrees=float(slope[affected].max()) if affected.any() else 0.,station_step_m=.37,lateral_step_m=.25,routes=reports,asc_sha256=hashlib.sha256(asc.read_bytes()).hexdigest(),limits=['Dry road interiors only; wet crossings and junction aprons retain separate design/acceptance. Not native import or runtime.','No new/worse width failures permitted on other eligible portions of those chains.'])
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--folder',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);ap.add_argument('--max-delta-m',type=float,default=1.35);ap.add_argument('--max-geographic-distance-m',type=float,default=24.5);ap.add_argument('--local-transition-v22',action='store_true');ap.add_argument('--outline-v33-parent',action='store_true');args=ap.parse_args()
    assert 0<args.max_delta_m<=6.0
    if args.outline_v33_parent:
        assert args.max_geographic_distance_m==60.5 and args.max_delta_m==6. and not args.local_transition_v22
    else:assert 0<args.max_geographic_distance_m<=36.5
    assert not args.out.exists();result=audit(args.folder,maximum_delta_m=args.max_delta_m,maximum_geographic_distance_m=args.max_geographic_distance_m,local_transition_v22=args.local_transition_v22,outline_v33_parent=args.outline_v33_parent);result['maximum_delta_m']=args.max_delta_m;result['maximum_geographic_distance_m']=args.max_geographic_distance_m;result['local_transition_v22']=args.local_transition_v22;result['outline_v33_parent']=args.outline_v33_parent;args.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,indent=2));raise SystemExit(0 if result['status'].startswith('PASS_') else 1)

if __name__=='__main__':main()
