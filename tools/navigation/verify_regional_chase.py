"""Check physical AI records against frozen targets and independent native heights."""
from pathlib import Path
import argparse, hashlib, json, math, re
import numpy as np
import rasterio
from waterway_common import sample

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def vec(text):
    m=re.fullmatch(r'<(-?\d+\.\d{6}),\s*(-?\d+\.\d{6}),\s*(-?\d+\.\d{6})>',text)
    if not m:raise ValueError('Malformed precise vector')
    out=np.array(list(map(float,m.groups())))
    if not np.isfinite(out).all():raise ValueError('Nonfinite vector')
    return out

def verify(ref,text,height):
    lines=text.splitlines(); rows=[]; anchors={}; parse=[]
    markers={'SETTLE_BEGIN','SETTLE','SPAWN','SAMPLE','NOISE','REACHED','TIMEOUT','FAILED_ACTOR','FAILED_SPAWN','INCONCLUSIVE_NAV_ANCHOR'}
    for line in lines[2:]:
        p=line.split(';')
        try:
            if p[0]=='A':
                if len(p)!=11 or p[3] not in markers:raise ValueError('Malformed/unknown actor row')
                r=dict(case=int(p[1]),t=float(p[2]),event=p[3],p=vec(p[4]),prey=vec(p[5]),goal=vec(p[6]),health=float(p[7]),mind=int(p[8]),ground=float(p[9]),road=float(p[10]))
                if not all(math.isfinite(r[k]) for k in ('t','health','ground','road')):raise ValueError('Nonfinite actor scalar')
                if rows and (r['case']<rows[-1]['case'] or r['t']<rows[-1]['t']):raise ValueError('Unordered actor log')
                rows.append(r)
            elif p[0]=='ANCHOR':
                if len(p)!=6:raise ValueError('Malformed anchor')
                ident=int(p[1])
                if ident in anchors:raise ValueError('Duplicate anchor')
                anchors[ident]=[vec(v) for v in p[2:]]
            elif p[0]=='END':
                if line!='END;ALL_CASES_COMPLETE' or line!=lines[-1]:raise ValueError('Incomplete terminal')
            else:raise ValueError('Unknown record')
        except (ValueError,IndexError) as exc:parse.append(str(exc))
    expected={c['case'] for c in ref['cases']}
    header=ref.get('log_header','BALTIC_REGIONAL_CHASE_V1')
    if header not in ('BALTIC_REGIONAL_CHASE_V1','BALTIC_REGIONAL_CHASE_V2','BALTIC_REGIONAL_CHASE_V3','BALTIC_V30_CONTINUITY_PHYSICAL_V1'):
        raise ValueError('Unknown regional chase header')
    global_checks=dict(header=lines[:2]==[header,'world=BalticTrial'],
                       end=bool(lines and lines[-1]=='END;ALL_CASES_COMPLETE' and lines.count('END;ALL_CASES_COMPLETE')==1),
                       exact_cases={r['case'] for r in rows}==expected,
                       no_parse_errors=not parse)
    reports=[];limits=ref['criteria'];bridge=ref['bridge']
    for case in ref['cases']:
        group=[r for r in rows if r['case']==case['case']]
        active=[r for r in group if r['event'] not in ('SETTLE_BEGIN','SETTLE')]
        terminal=[r['event'] for r in active if r['event'] not in ('SPAWN','SAMPLE','NOISE')]
        if len(active)<3 or active[0]['event']!='SPAWN':
            reports.append(dict(case=case['case'],name=case['name'],reverse=case['reverse'],status='FAIL_OR_INCONCLUSIVE',reason='Missing complete active sequence',terminal=terminal));continue
        pos=np.array([r['p'] for r in active]);t=np.array([r['t'] for r in active]);goal=np.array(case['goal']);spawn=np.array(case['start'])
        native=sample(height,pos[:,0]+200000,pos[:,2]);surface=native.copy()
        lateral=None
        if case['kind']=='bridge':
            delta=pos[:,[0,2]]-np.array(bridge['center_xz']);axis=np.array(bridge['axis_xz'])
            along=delta@axis;lateral=delta@np.array([-axis[1],axis[0]])
            on=(abs(along)<=bridge['half_length_m'])&(abs(lateral)<=bridge['max_lateral_m'])
            surface[on]=bridge['deck_y']
        physical=pos[:,1]-surface
        ground_error=abs(native-np.array([r['ground'] for r in active]))
        path=float(np.linalg.norm(np.diff(pos,axis=0),axis=1).sum());direct=float(np.linalg.norm(pos[0]-goal))
        prey_drift=max(float(np.linalg.norm(r['prey']-goal)) for r in active)
        settled=[r for r in group if r['event']=='SETTLE' and r['t']>=t[0]-5]
        mind=[r['mind'] for r in active if r['event']=='SAMPLE' and r['t']>=t[0]+1]
        anchor=anchors.get(case['case'])
        checks=dict(one_spawn=sum(r['event']=='SPAWN' for r in active)==1,
                    reached_terminal=terminal==['REACHED'],
                    frozen_goal=all(np.linalg.norm(r['goal']-goal)<=.000002 for r in group),
                    frozen_anchor=anchor is not None and np.linalg.norm(anchor[0]-spawn)<=.000002 and np.linalg.norm(anchor[1]-goal)<=.000002,
                    spawn_xz_error=np.linalg.norm(pos[0,[0,2]]-spawn[[0,2]])<=limits['maximum_spawn_error_m'],
                    continuous=np.all(np.diff(t)>=0) and np.max(np.diff(t))<=limits['maximum_sample_gap_s'],
                    enough_samples=sum(r['event']=='SAMPLE' for r in active)>=limits['minimum_active_samples'],
                    within_timeout=t[-1]-t[0]<=limits['stage_timeout_s'],
                    stable_target=prey_drift<=limits['maximum_prey_drift_m'],
                    stable_before_spawn=len(settled)>=limits['minimum_final_settle_samples'] and all(np.linalg.norm(r['prey']-goal)<=limits['maximum_prey_drift_m'] for r in settled),
                    healthy=all(r['health']>0 for r in active),
                    known_mind=bool(mind) and all(0<=m<=4 for m in mind),
                    reacted=any(1<=m<=4 for m in mind),
                    actual_goal_distance=np.linalg.norm(pos[-1]-goal)<=limits['goal_radius_m'],
                    bounded_path=path<=limits['path_length_factor']*direct,
                    physical_surface=np.all((physical>=limits['physical_y_min_m'])&(physical<=limits['physical_y_max_m'])),
                    terrain_consumer=ground_error.max()<=limits['maximum_ground_error_m'])
        if lateral is not None:checks['bridge_corridor']=max(abs(lateral))<=bridge['max_lateral_m']
        checks={k:bool(v) for k,v in checks.items()}
        reports.append(dict(case=case['case'],name=case['name'],reverse=case['reverse'],status='PASS' if all(checks.values()) else 'FAIL',checks=checks,
                            samples=len(active),terminal=terminal,duration_s=float(t[-1]-t[0]),maximum_gap_s=float(np.diff(t).max()),
                            path_length_m=path,initial_direct_m=direct,goal_distance_m=float(np.linalg.norm(pos[-1]-goal)),
                            physical_surface_difference_m=[float(physical.min()),float(physical.max())],
                            maximum_ground_error_m=float(ground_error.max()),prey_drift_m=prey_drift,
                            health_min=min(r['health'] for r in active),maximum_lateral_m=float(max(abs(lateral))) if lateral is not None else None))
    passed=all(global_checks.values()) and all(r['status']=='PASS' for r in reports)
    return dict(status='PASS_PHYSICAL_AI_SELECTED_REGIONAL_ROUTES' if passed else 'FAIL_OR_INCOMPLETE',
                global_checks=global_checks,parse_errors=parse,cases=reports,limits=ref['limits'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--log',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve prior evidence')
    ref=json.loads(a.reference.read_text());asc=Path(ref['terrain']);assert sha(asc)==ref['terrain_sha256']
    with rasterio.open(asc) as ds:h=ds.read(1)
    result=verify(ref,a.log.read_text(encoding='utf-8-sig'),h)
    result.update(reference_sha256=sha(a.reference),log_sha256=sha(a.log))
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS_') else 1)

if __name__=='__main__':main()
