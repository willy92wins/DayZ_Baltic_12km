"""Independent no-infected human controller consumer; never approves AI navigation."""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np
import rasterio
from waterway_common import sample
from verify_regional_chase import vec
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def verify(ref,server,client,height):
    rows=[];anchors={};errors=[];lines=server.splitlines();clines=client.splitlines();inputs=[]
    for line in lines[2:]:
        p=line.split(';')
        try:
            if p[0]=='CASE':
                assert len(p)==5 and int(p[1]) not in anchors
                anchors[int(p[1])]=[vec(v) for v in p[2:]]
            elif p[0]=='P':
                assert len(p)==18 and p[3] in ('SETTLE_BEGIN','SAMPLE','MOVE_BEGIN','REACHED','BAD_PREY','UNSTABLE_PREY','CORRIDOR','WALK_TIMEOUT')
                assert p[17] in ('true','false') and int(p[9]) in (0,1,2)
                row=dict(case=int(p[1]),t=float(p[2]),event=p[3],actor=vec(p[4]),pos=vec(p[5]),actor_health=float(p[6]),health=float(p[7]),mind=int(p[8]),ground=vec(p[12]),road=float(p[13]),goal=vec(p[14]),unconscious=p[17]=='true')
                assert all(math.isfinite(row[k]) for k in ('t','actor_health','health','road'))
                assert not rows or (row['case']>=rows[-1]['case'] and row['t']>=rows[-1]['t'])
                rows.append(row)
            elif p[0]=='END':assert line==lines[-1]
            else:raise ValueError('Unknown server record')
        except (ValueError,AssertionError,IndexError):errors.append('Invalid server record')
    for line in clines[1:]:
        p=line.split(';')
        try:
            if p[0]=='C':
                assert len(p)==9
                row=dict(t=float(p[1]),command=int(p[2]),pos=vec(p[3]),goal=vec(p[4]),requested=float(p[5]),angle=float(p[6]),actual=float(p[7]),direction=vec(p[8]))
                assert all(math.isfinite(row[k]) for k in ('t','requested','angle','actual'))
                assert row['command'] in (0,1,2) and row['requested'] in (0,1) and -180<=row['angle']<=180 and 0<=row['actual']<=3
                assert not inputs or row['t']>inputs[-1]['t'];inputs.append(row)
            elif p[0]=='END':assert len(p)==3 and p[1]=='MISSION_FINISH' and line==clines[-1]
            else:raise ValueError('Unknown client record')
        except (ValueError,AssertionError,IndexError):errors.append('Invalid client record')
    expected={c['case'] for c in ref['cases']};limit=ref['criteria'];bridge=ref['bridge']
    global_checks=dict(server_header=lines[:2]==['BALTIC_BRIDGE_HUMAN_CONTROL_V1','world=BalticTrial'],client_header=bool(clines and clines[0]=='BALTIC_BRIDGE_HUMAN_CONTROL_CLIENT_V1'),
        server_end=bool(lines and lines[-1]=='END;ALL_CASES_COMPLETE' and sum(x.startswith('END;') for x in lines)==1),client_end=bool(clines and clines[-1].startswith('END;MISSION_FINISH;') and sum(x.startswith('END;') for x in clines)==1),
        exact_cases=set(anchors)==expected and {x['case'] for x in rows}==expected,no_parse_errors=not errors,
        no_actor_records=bool(rows) and all(np.linalg.norm(x['actor'])==0 and x['actor_health']==0 and x['mind']==-1 for x in rows))
    reports=[]
    for c in ref['cases']:
        group=[x for x in rows if x['case']==c['case']];moves=[i for i,x in enumerate(group) if x['event']=='MOVE_BEGIN']
        if len(moves)!=1 or len(group)-moves[0]<3:reports.append(dict(case=c['case'],status='FAIL',reason='Missing movement sequence'));continue
        active=group[moves[0]:];settle=group[:moves[0]];t=np.array([x['t'] for x in active]);pos=np.array([x['pos'] for x in active]);start=np.array(c['prey_start']);goal=np.array(c['goal']);terrain=sample(height,pos[:,0]+200000,pos[:,2]);floor=terrain.copy()
        axis=goal[[0,2]]-start[[0,2]];length=np.linalg.norm(axis);axis/=length;normal=np.array([-axis[1],axis[0]])
        lat=(pos[:,[0,2]]-start[[0,2]])@normal;permitted=np.full(len(pos),limit['maximum_lateral_m'],dtype=float)
        if c['kind']=='bridge':
            rel=pos[:,[0,2]]-np.array(bridge['center_xz']);along=rel@np.array(bridge['axis_xz']);cross=rel@np.array([-bridge['axis_xz'][1],bridge['axis_xz'][0]])
            on=(abs(along)<=bridge['half_length_m'])&(abs(cross)<=bridge['max_lateral_m']);floor[on]=bridge['deck_y'];permitted[abs(along)<=bridge['half_length_m']]=limit['maximum_bridge_lateral_m']
        ground=np.array([x['ground'] for x in active]);gap=pos[:,1]-floor;dt=np.diff(t);step=np.linalg.norm(np.diff(pos[:,[0,2]],axis=0),axis=1)
        speed=np.divide(step,dt,out=np.full_like(step,np.inf),where=dt>0);speed[(dt==0)&(step<=.002)]=0;peak=float(max(speed));progress=float((pos[-1,[0,2]]-start[[0,2]])@axis)
        ci=[x for x in inputs if x['command']==c['case']+1]
        checks=dict(anchor=c['case'] in anchors and all(np.linalg.norm(a-b)<=.000002 for a,b in zip(anchors[c['case']],[np.array(c['start']),start,goal])),
            settled=bool(settle and t[0]-settle[0]['t']>=limit['settlement_s'] and len([x for x in settle if x['t']>=t[0]-5])>=20 and all(np.linalg.norm(x['pos']-start)<=limit['settlement_drift_m'] for x in settle if x['t']>=t[0]-5)),
            terminal=[x['event'] for x in active if x['event'] not in ('MOVE_BEGIN','SAMPLE')]==['REACHED'],
            frozen_goal=all(np.linalg.norm(x['goal']-goal)<=.000002 for x in group),continuous=bool(min(dt)>=0 and max(dt)<=limit['maximum_gap_s']),
            health=all(x['health']>0 and not x['unconscious'] for x in active),contact=bool(np.all((gap>=limit['physical_y_min_m'])&(gap<=limit['physical_y_max_m']))),
            terrain=bool(max(abs(ground[:,1]-terrain))<=limit['maximum_ground_error_m'] and max(np.linalg.norm(ground[:,[0,2]]-pos[:,[0,2]],axis=1))<=.000002),
            corridor=bool(np.all(abs(lat)<=permitted)),bounded_speed=math.isfinite(peak) and peak<=limit['maximum_prey_step_speed_mps'],
            arrived=np.linalg.norm(pos[-1]-goal)<=limit['prey_goal_radius_m'],complete_distance=progress>=length-limit['prey_goal_radius_m'],
            bounded_time=t[-1]-t[0]<=c['timeout_s'],bounded_path=float(np.linalg.norm(np.diff(pos,axis=0),axis=1).sum())<=limit['path_length_factor']*np.linalg.norm(goal-start),
            native_input=len(ci)>=3 and sum(x['requested']==1 and x['actual']>.1 for x in ci)>=3 and all(np.linalg.norm(x['goal']-goal)<=.000002 for x in ci))
        checks={k:bool(v) for k,v in checks.items()}
        reports.append(dict(case=c['case'],status='PASS' if all(checks.values()) else 'FAIL',checks=checks,samples=len(active),duration_s=float(t[-1]-t[0]),progress_m=progress,maximum_speed_mps=peak if math.isfinite(peak) else None,maximum_lateral_m=float(max(abs(lat))),strict_lane_4m=bool(max(abs(lat))<=4),maximum_gap_s=float(max(dt)),floor_error_range_m=[float(min(gap)),float(max(gap))]))
    passed=all(global_checks.values()) and all(x['status']=='PASS' for x in reports)
    return dict(status='PASS_HUMAN_CONTROL_WITHOUT_INFECTED' if passed else 'FAIL_OR_INCOMPLETE_HUMAN_CONTROL',global_checks=global_checks,errors=errors,cases=reports,limits=ref['limits'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
    ref=json.loads(a.reference.read_text(encoding='utf-8'));terrain=Path(ref['terrain']);assert sha(terrain)==ref['terrain_sha256']
    with rasterio.open(terrain) as ds:height=ds.read(1)
    sp=a.folder/'engine.log';cp=a.folder/'client-input.log';result=verify(ref,sp.read_text(encoding='utf-8-sig'),cp.read_text(encoding='utf-8-sig'),height)
    result['source_sha256']={str(p):sha(p) for p in (a.reference,sp,cp)};a.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['status'].startswith('PASS_') else 1)
