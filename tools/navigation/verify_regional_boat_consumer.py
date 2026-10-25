"""Consumer checks on actual boat motion; mission markers alone never pass."""
from pathlib import Path
import argparse,hashlib,json,re
import numpy as np
import rasterio
from scipy.spatial import cKDTree
from shapely.geometry import LineString,Point
from waterway_common import sample

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def verify(reference,lines,h):
    criteria=reference['criteria'];rows={};ended={};started={};arrivals={};errors=[]
    version=reference.get('log_version',1)
    if version not in (1,2):raise ValueError('Unsupported boat log version')
    for line in lines:
        fields=line.split(';')
        try:
            if fields[0]=='B':
                if len(fields)!=(23 if version==2 else 22):raise ValueError('bad B schema')
                if fields[9] not in ('true','false'):raise ValueError('bad engine bool')
                case=int(fields[1]);values=[float(v) if i!=9 else float(v=='true') for i,v in enumerate(fields[2:22],2)]
                if not np.isfinite(values).all():raise ValueError('nonfinite sample')
                if version==2:
                    match=re.fullmatch(r'<(-?\d+\.\d{6}),\s*(-?\d+\.\d{6}),\s*(-?\d+\.\d{6})>',fields[22])
                    if not match:raise ValueError('bad precise vector')
                    precise=list(map(float,match.groups()))
                    if not np.isfinite(precise).all():raise ValueError('nonfinite precise vector')
                    # Six significant digits are the old scalar serialization.
                    # This is a schema consistency check, not a geometric tolerance.
                    for i,value in zip((1,2,3),precise):
                        scalar=values[i]
                        half_unit=.5*10**(np.floor(np.log10(abs(scalar)))-5) if scalar else 0.
                        if abs(value-scalar)>half_unit+.0000005+1e-9:raise ValueError('vector/scalar mismatch')
                        values[i]=value
                rows.setdefault(case,[]).append(values)
            elif fields[0]=='CASE':
                case=int(fields[1]);started[case]=started.get(case,0)+1
            elif fields[0]=='CASE_END':
                case=int(fields[1]);ended.setdefault(case,[]).append(fields[2])
            elif fields[0]=='ARRIVED':
                arrivals.setdefault(int(fields[1]),[]).append(float(fields[2]))
        except (ValueError,IndexError) as exc:errors.append(str(exc))
    expected_ids={c['case'] for c in reference['cases']}
    global_checks={'header':bool(lines and lines[0]==f'BALTIC_REGIONAL_BOAT_V{version}'),'all_cases_complete':bool(lines and lines[-1]=='END;ALL_CASES_COMPLETE'),'exact_cases':set(rows)==set(started)==set(ended)==expected_ids,'no_parse_errors':not errors}
    reports=[]
    for case in reference['cases']:
        ident=case['case'];raw=rows.get(ident,[])
        if len(raw)<3:
            reports.append({'case':ident,'status':'FAIL','reason':'missing motion samples','samples':len(raw)});continue
        n=np.asarray(raw);t=n[:,0];pos=n[:,[1,3]];dt=np.diff(t);steps=np.linalg.norm(np.diff(pos,axis=0),axis=1)
        waypoints=np.asarray(case['waypoints_xz']);line=LineString(waypoints)
        distances=np.array([line.distance(Point(p)) for p in pos])
        waypoint_errors=cKDTree(pos).query(waypoints)[0]
        expected_ground=sample(h,pos[:,0]+200000,pos[:,1]);ground_error=np.abs(expected_ground-n[:,17])
        # n indexes are raw B field indexes minus2.
        powered=(n[:,7]==1)&(n[:,8]!=n[:,9])&(n[:,10]>800)&(abs(n[:,11])>.01)&(n[:,5]>.5)
        longest=streak=0.
        for i in range(1,len(n)):
            streak=streak+dt[i-1] if powered[i] and powered[i-1] and 0<dt[i-1]<=criteria['max_sample_dt_s'] else 0.
            longest=max(longest,streak)
        checks={
            'one_start_and_finish':started.get(ident)==1 and ended.get(ident)==['ARRIVED_AND_STOPPED'],
            'one_arrival':len(arrivals.get(ident,[]))==1,
            'monotone_continuous_clock':bool(np.all(dt>0) and np.max(dt)<=criteria['max_sample_dt_s']),
            'continuous_motion':bool(np.max(steps)<=criteria['max_step_m']),
            'no_health_loss':bool(n[:,6].min()>=n[0,6]-criteria['max_health_loss']),
            'inside_corridor':bool(distances.max()<=criteria['max_axis_distance_m']),
            'all_intermediate_points_visited':bool(waypoint_errors.max()<=criteria['max_waypoint_distance_m']),
            'start_and_endpoint':bool(np.linalg.norm(pos[0]-waypoints[0])<=1 and np.linalg.norm(pos[-1]-waypoints[-1])<=criteria['max_endpoint_distance_m']),
            'engine_ground_matches_source':bool(np.max(ground_error)<=criteria['max_ground_error_m']),
            'input_callbacks':bool(np.all(np.diff(n[:,12])>=0) and n[-1,12]-n[0,12]>100),
            'sustained_powered_motion':bool(longest>=criteria['min_powered_motion_s']),
            'engine_route_distance_agrees':bool(np.max(abs(distances-n[:,16]))<=.15),
            'targets_in_order':bool(np.all(np.diff(n[:,15])>=0) and np.all(np.diff(n[:,15])<=2)),
        }
        reports.append(dict(case=ident,river=case['river'],reverse=case['reverse'],status='PASS' if all(checks.values()) else 'FAIL',checks=checks,end_reason=ended.get(ident),samples=len(n),max_dt_s=float(dt.max()),max_step_m=float(steps.max()),max_corridor_distance_m=float(distances.max()),max_waypoint_distance_m=float(waypoint_errors.max()),end_distance_m=float(np.linalg.norm(pos[-1]-waypoints[-1])),max_ground_error_m=float(ground_error.max()),health_first_min_last=[float(n[0,6]),float(n[:,6].min()),float(n[-1,6])],longest_powered_motion_s=longest))
    passed=all(global_checks.values()) and all(c['status']=='PASS' for c in reports)
    return dict(status='PASS_EMPTY_BOAT_SELECTED_REGIONAL_SECTORS_BOTH_DIRECTIONS' if passed else 'FAIL_OR_INCOMPLETE',global_checks=global_checks,parse_errors=errors,cases=reports,limits=reference['limits'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--log',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve prior report')
    ref=json.loads(a.reference.read_text());terrain=Path(ref['terrain']);assert sha(terrain)==ref['terrain_sha256']
    with rasterio.open(terrain) as ds:h=ds.read(1)
    report=verify(ref,a.log.read_text(encoding='utf-8-sig').splitlines(),h)
    report.update(reference_sha256=sha(a.reference),log_sha256=sha(a.log),terrain_sha256=sha(terrain))
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['status'].startswith('PASS_') else 1)

if __name__=='__main__':main()
