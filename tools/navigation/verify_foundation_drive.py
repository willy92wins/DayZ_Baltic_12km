"""Independent physical driving checks against frozen terrain and route geometry."""
from pathlib import Path
import argparse,hashlib,json,math,re
import numpy as np
import rasterio
from shapely.geometry import LineString,Point
from scipy.spatial import cKDTree
from waterway_common import sample

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def verify_mission_identity(ref):
    identities={}
    for name,wanted in ref['mission'].items():
        path=Path(name)
        resolved=str(path.resolve()).lower()
        if resolved in identities and identities[resolved]!=wanted:
            raise ValueError('Conflicting mission aliases: '+name)
        identities[resolved]=wanted
        if sha(path)!=wanted:raise ValueError('Frozen mission changed: '+name)
    if not identities:raise ValueError('Missing frozen mission identity')
def vec(s):
    if not re.fullmatch(r'<-?\d+\.\d{6},\s*-?\d+\.\d{6},\s*-?\d+\.\d{6}>',s):raise ValueError('Precise vector required')
    return np.array([float(x) for x in s[1:-1].split(',')])
def boolean(s):
    if s not in ('true','false'):raise ValueError('Boolean required')
    return s=='true'
def streak(mask,t,max_dt):
    best=cur=0.
    for i in range(1,len(t)):
        cur=cur+t[i]-t[i-1] if mask[i] and mask[i-1] and 0<t[i]-t[i-1]<=max_dt else 0.
        best=max(best,cur)
    return float(best)
def surface(h,xy,bridge):
    y=sample(h,xy[:,0]+200000,xy[:,1])
    delta=xy-np.array(bridge['center_xz']);axis=np.array(bridge['axis_xz'])
    on=(abs(delta@axis)<=bridge['half_length_m'])&(abs(delta@np.array([-axis[1],axis[0]]))<=bridge['max_lateral_m'])
    y[on]=bridge['deck_y'];return y

def verify(ref,text,h):
    lines=text.splitlines();rows={};starts={};spawns={};ends={};arrived={};errors=[]
    sizes={'D':32,'CASE':3,'SPAWN':6,'ENGINE_REQUEST':4,'ARRIVED':4,'CASE_END':3,'END':2}
    for line in lines[2:]:
        p=line.split(';')
        try:
            if p[0] not in sizes or len(p)!=sizes[p[0]]:raise ValueError('Unknown/malformed record')
            if p[0]=='END':
                if line!=lines[-1] or p[1]!='ALL_CASES_COMPLETE':raise ValueError('Bad terminal')
                continue
            case=int(p[1])
            if p[0]=='D':
                d=dict(t=float(p[2]),p=vec(p[3]),orientation=vec(p[4]),v=vec(p[5]),health=float(p[6]),engine_health=float(p[7]),
                       engine=boolean(p[8]),rpm=float(p[9]),gear=int(p[10]),calls=int(p[11]),throttle=float(p[12]),steering=float(p[13]),brake=float(p[14]),
                       waypoint=int(p[15]),distance=float(p[16]),present=int(p[17]),up=float(p[18]),ground=float(p[19]),
                       contact=np.array([boolean(p[20+3*w]) for w in range(4)]),
                       wheel_pos=np.array([vec(p[21+3*w]) for w in range(4)]),
                       wheel_health=np.array([float(p[22+3*w]) for w in range(4)]))
                for value in d.values():
                    if not np.isfinite(value).all():raise ValueError('Nonfinite record')
                rows.setdefault(case,[]).append(d)
            elif p[0]=='CASE':starts[case]=starts.get(case,0)+1
            elif p[0]=='SPAWN':
                if case in spawns:raise ValueError('Duplicate spawn')
                spawns[case]=dict(p=vec(p[2]),orientation=vec(p[3]),health=float(p[4]),wheels=int(p[5]))
            elif p[0]=='CASE_END':ends.setdefault(case,[]).append(p[2])
            elif p[0]=='ARRIVED':arrived.setdefault(case,[]).append((float(p[2]),vec(p[3])))
        except (ValueError,IndexError) as exc:errors.append(str(exc))
    expected={c['case'] for c in ref['cases']};lim=ref['criteria'];bridge=ref['bridge'];reports=[]
    global_checks=dict(header=lines[:2]==['BALTIC_FOUNDATION_DRIVE_V1','EMPTY_VANILLA_SEDAN_NO_POSE_OR_VELOCITY_FORCING'],
                       end=bool(lines and lines[-1]=='END;ALL_CASES_COMPLETE' and lines.count('END;ALL_CASES_COMPLETE')==1),
                       cases=set(rows)==set(starts)==set(spawns)==set(ends)==expected,no_parse_errors=not errors)
    for c in ref['cases']:
        ident=c['case'];allrows=rows.get(ident,[]);active=[r for r in allrows if r['t']>=20]
        if len(active)<3 or ident not in spawns:
            reports.append(dict(case=ident,status='INCONCLUSIVE',reason='Incomplete motion sequence',end=ends.get(ident)));continue
        n=len(active);p=np.array([r['p'] for r in active]);v=np.array([r['v'] for r in active]);t=np.array([r['t'] for r in active]);dt=np.diff(t)
        route=np.array(c['route_xyz']);line=LineString(route[:,[0,2]])
        distance=np.array([line.distance(Point(x)) for x in p[:,[0,2]]]);steps=np.linalg.norm(np.diff(p,axis=0),axis=1)
        speed=np.linalg.norm(v[:,[0,2]],axis=1);native=sample(h,p[:,0]+200000,p[:,2])
        contact=np.array([r['contact'] for r in active]);wheels=np.array([r['wheel_pos'] for r in active]);wheelhealth=np.array([r['wheel_health'] for r in active])
        points=wheels[contact];contact_error=abs(points[:,1]-surface(h,points[:,[0,2]],bridge)) if len(points) else np.array([math.inf])
        no_contact=streak(contact.sum(axis=1)==0,t,lim['maximum_dt_s'])
        cruise=(speed>=lim['minimum_cruise_speed_m_s'])&np.array([r['engine'] and r['rpm']>800 and r['gear']>=2 for r in active])
        cruise_s=streak(cruise,t,lim['maximum_dt_s']);stop_s=streak(speed<=lim['maximum_stopped_speed_m_s'],t,lim['maximum_dt_s'])
        base=spawns[ident];endpoint=float(np.linalg.norm(p[-1,[0,2]]-route[-1,[0,2]]))
        checks=dict(one_case=starts.get(ident)==1,terminal=ends.get(ident)==['ARRIVED_AND_STOPPED'],one_arrival=len(arrived.get(ident,[]))==1,
                    clock=np.all(dt>0) and max(dt)<=lim['maximum_dt_s'],continuous_motion=max(steps)<=lim['maximum_step_m'],
                    spawn=np.linalg.norm(base['p'][[0,2]]-route[0,[0,2]])<=.02 and np.linalg.norm(p[0,[0,2]]-route[0,[0,2]])<=1,
                    endpoint=endpoint<=lim['maximum_endpoint_distance_m'],inside_corridor=max(distance)<=lim['maximum_axis_distance_m'],
                    all_waypoints=max(cKDTree(p[:,[0,2]]).query(route[:,[0,2]])[0])<=5,
                    body_healthy=min(r['health'] for r in allrows)>=base['health']-lim['maximum_health_loss'],
                    engine_healthy=min(r['engine_health'] for r in active)>=allrows[0]['engine_health']-lim['maximum_health_loss'],
                    wheels_present=base['wheels']==4 and all(r['present']==4 for r in allrows),
                    wheels_healthy=np.all(wheelhealth>0) and np.all(wheelhealth>=allrows[0]['wheel_health']-lim['maximum_health_loss']),
                    upright=min(r['up'] for r in active)>=lim['minimum_up_dot'],
                    ground=abs(native-np.array([r['ground'] for r in active])).max()<=lim['maximum_ground_error_m'],
                    contact_surface=contact_error.max()<=lim['maximum_contact_error_m'],
                    no_jump=no_contact<=lim['maximum_no_contact_s'],
                    callbacks=all(active[i]['calls']>=active[i-1]['calls'] for i in range(1,n)) and active[-1]['calls']-active[0]['calls']>100,
                    cruise=cruise_s>=lim['minimum_cruise_duration_s'],stopped=stop_s>=lim['minimum_stop_duration_s'] and speed[-1]<=lim['maximum_stopped_speed_m_s'],
                    logged_route=abs(distance-np.array([r['distance'] for r in active])).max()<=.05)
        checks={k:bool(v) for k,v in checks.items()}
        reports.append(dict(case=ident,name=c['name'],reverse=c['reverse'],status='PASS' if all(checks.values()) else 'FAIL',checks=checks,
                            samples=n,end=ends.get(ident),duration_s=float(t[-1]-t[0]),maximum_step_m=float(max(steps)),maximum_dt_s=float(max(dt)),
                            maximum_corridor_m=float(max(distance)),endpoint_distance_m=endpoint,maximum_contact_error_m=float(contact_error.max()),
                            maximum_ground_error_m=float(abs(native-np.array([r['ground'] for r in active])).max()),
                            contact_count_min=int(contact.sum(axis=1).min()),longest_no_contact_s=no_contact,cruise_duration_s=cruise_s,
                            stop_duration_s=stop_s,speed_m_s={'p50':float(np.median(speed)),'p95':float(np.quantile(speed,.95)),'max':float(max(speed))},
                            maximum_abs_vertical_speed_m_s=float(max(abs(v[:,1]))),health_min=min(r['health'] for r in allrows)))
    passed=all(global_checks.values()) and all(r['status']=='PASS' for r in reports)
    return dict(status='PASS_EMPTY_SEDAN_NARVA_GRADES_AND_BRIDGE' if passed else 'FAIL_OR_INCOMPLETE',global_checks=global_checks,parse_errors=errors,cases=reports,limits=ref['limits'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--log',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve evidence')
    ref=json.loads(a.reference.read_text());verify_mission_identity(ref)
    terrain=Path(ref['terrain']);assert sha(terrain)==ref['terrain_sha256']
    with rasterio.open(terrain) as ds:h=ds.read(1)
    r=verify(ref,a.log.read_text(encoding='utf-8-sig'),h);r.update(reference_sha256=sha(a.reference),log_sha256=sha(a.log))
    a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));raise SystemExit(0 if r['status'].startswith('PASS_') else 1)
