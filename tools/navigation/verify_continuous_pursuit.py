"""Check native pursuit against frozen geometry and independent actor/target traces."""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np
import rasterio
from waterway_common import sample
from verify_regional_chase import vec

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def verify(ref,server,client,height):
    lines=server.splitlines();records=[];anchors={};errors=[]
    events={'SETTLE_BEGIN','SAMPLE','SPAWN','NOISE','MOVE_BEGIN','REACHED',
            'BAD_PREY','UNSTABLE_PREY','SPAWN_FAILED','ACTOR_DEAD','CORRIDOR','ACQUISITION_TIMEOUT','WALK_TIMEOUT'}
    for line in lines[2:]:
        cells=line.split(';')
        try:
            if cells[0]=='CASE':
                ident=int(cells[1]);assert len(cells)==5 and ident not in anchors
                anchors[ident]=[vec(v) for v in cells[2:]]
            elif cells[0]=='P':
                if len(cells)!=18 or cells[3] not in events or cells[17] not in ('true','false'):raise ValueError('Bad server row')
                row=dict(case=int(cells[1]),t=float(cells[2]),event=cells[3],actor=vec(cells[4]),prey=vec(cells[5]),
                    ah=float(cells[6]),ph=float(cells[7]),mind=int(cells[8]),command=int(cells[9]),aground=vec(cells[10]),
                    aroad=float(cells[11]),pground=vec(cells[12]),proad=float(cells[13]),goal=vec(cells[14]),
                    direction=vec(cells[15]),heading=float(cells[16]),unconscious=cells[17]=='true')
                if not all(math.isfinite(row[k]) for k in ('t','ah','ph','aroad','proad','heading')):raise ValueError('Nonfinite server scalar')
                if records and (row['case']<records[-1]['case'] or row['t']<records[-1]['t']):raise ValueError('Unordered server records')
                records.append(row)
            elif cells[0]=='END':
                if line!=lines[-1]:raise ValueError('Nonterminal END')
            else:raise ValueError('Unknown server record')
        except (ValueError,IndexError,AssertionError) as error:errors.append(str(error) or 'Invalid CASE')
    clines=client.splitlines();crows=[]
    for line in clines[1:]:
        cells=line.split(';')
        try:
            if cells[0]=='C':
                if len(cells)!=9:raise ValueError('Bad client row')
                row=dict(t=float(cells[1]),command=int(cells[2]),pos=vec(cells[3]),goal=vec(cells[4]),
                    requested_speed=float(cells[5]),angle=float(cells[6]),actual_speed=float(cells[7]),local_direction=vec(cells[8]))
                if not all(math.isfinite(row[k]) for k in ('t','requested_speed','angle','actual_speed')):raise ValueError('Nonfinite client scalar')
                if not 0<=row['command']<=3 or row['requested_speed'] not in (0,1) or not -180<=row['angle']<=180 or not 0<=row['actual_speed']<=3:raise ValueError('Invalid client input')
                if crows and row['t']<=crows[-1]['t']:raise ValueError('Unordered client records')
                crows.append(row)
            elif cells[0]=='END':
                if len(cells)!=3 or cells[1]!='MISSION_FINISH' or line!=clines[-1]:raise ValueError('Incomplete client terminal')
            else:raise ValueError('Unknown client record')
        except (ValueError,IndexError) as error:errors.append(str(error))
    expected={c['case'] for c in ref['cases']};limits=ref['criteria'];bridge=ref['bridge']
    global_checks=dict(server_header=lines[:2]==['BALTIC_CONTINUOUS_PURSUIT_V1','world=BalticTrial'],
        server_end=bool(lines and lines[-1]=='END;ALL_CASES_COMPLETE' and sum(l.startswith('END;') for l in lines)==1),
        client_header=bool(clines and clines[0]=='BALTIC_CONTINUOUS_PURSUIT_CLIENT_V1'),
        client_end=bool(clines and clines[-1].startswith('END;MISSION_FINISH;') and sum(l.startswith('END;') for l in clines)==1),
        exact_cases={r['case'] for r in records}==expected and set(anchors)==expected,no_parse_errors=not errors)
    reports=[]
    def physical(rows,key,kind):
        pos=np.array([r[key] for r in rows]);ground=sample(height,pos[:,0]+200000,pos[:,2]);floor=ground.copy()
        if kind=='bridge':
            d=pos[:,[0,2]]-np.array(bridge['center_xz']);along=d@np.array(bridge['axis_xz'])
            lateral=d@np.array([-bridge['axis_xz'][1],bridge['axis_xz'][0]])
            on=(abs(along)<=bridge['half_length_m'])&(abs(lateral)<=bridge['max_lateral_m'])
            floor[on]=bridge['deck_y']
        reported=np.array([r['aground' if key=='actor' else 'pground'] for r in rows])
        error=float(abs(reported[:,1]-ground).max());xy_error=float(np.linalg.norm(reported[:,[0,2]]-pos[:,[0,2]],axis=1).max())
        gap=pos[:,1]-floor
        return dict(contact=bool(np.all((gap>=limits['physical_y_min_m'])&(gap<=limits['physical_y_max_m']))),
            terrain=error<=limits['maximum_ground_error_m'] and xy_error<=.000002,
            min_y=float(gap.min()),max_y=float(gap.max()),maximum_ground_error_m=error),pos
    for case in ref['cases']:
        group=[r for r in records if r['case']==case['case']]
        spawns=[i for i,r in enumerate(group) if r['event']=='SPAWN']
        if len(spawns)!=1 or len(group)-spawns[0]<3:
            reports.append(dict(case=case['case'],status='FAIL',reason='Missing active sequence'));continue
        active=group[spawns[0]:];settle=group[:spawns[0]];moves=[r for r in active if r['event']=='MOVE_BEGIN']
        terminal=[r['event'] for r in active if r['event'] not in ('SPAWN','SAMPLE','NOISE','MOVE_BEGIN')]
        times=np.array([r['t'] for r in active]);start=np.array(case['start']);prey_start=np.array(case['prey_start']);goal=np.array(case['goal'])
        aphys,apos=physical(active,'actor',case['kind']);pphys,ppos=physical(active,'prey',case['kind'])
        axis=goal[[0,2]]-start[[0,2]];length=np.linalg.norm(axis);axis/=length;normal=np.array([-axis[1],axis[0]])
        def trace(pos,maximum_speed):
            dt=np.diff(times);step=np.linalg.norm(np.diff(pos[:,[0,2]],axis=0),axis=1)
            speed=np.divide(step,dt,out=np.full_like(step,np.inf),where=dt>0)
            speed[(dt==0)&(step<=.002)]=0
            lateral=(pos[:,[0,2]]-start[[0,2]])@normal
            peak=float(np.max(speed));finite=math.isfinite(peak)
            return dict(bounded_speed=finite and peak<=maximum_speed,maximum_speed_mps=peak if finite else None,
                corridor=bool(max(abs(lateral))<=limits['maximum_lateral_m']),maximum_lateral_m=float(max(abs(lateral))),
                path_length_m=float(np.linalg.norm(np.diff(pos,axis=0),axis=1).sum()),progress_m=float((pos[-1,[0,2]]-start[[0,2]])@axis))
        atrace=trace(apos,limits['maximum_actor_step_speed_mps']);ptrace=trace(ppos,limits['maximum_prey_step_speed_mps'])
        inputs=[r for r in crows if r['command']==case['case']+1]
        known_mind=[r['mind'] for r in active if r['t']>=times[0]+1]
        checks=dict(one_spawn=True,one_move_begin=len(moves)==1,terminal=terminal==['REACHED'],
            anchor=case['case'] in anchors and all(np.linalg.norm(a-b)<=.000002 for a,b in zip(anchors[case['case']],[start,prey_start,goal])),
            frozen_goal=all(np.linalg.norm(r['goal']-goal)<=.000002 for r in group),
            settlement=bool(settle and times[0]-settle[0]['t']>=limits['settlement_s'] and len([r for r in settle if r['t']>=times[0]-5])>=20 and all(np.linalg.norm(r['prey']-prey_start)<=limits['settlement_drift_m'] for r in settle if r['t']>=times[0]-5)),
            spawn_xz=float(np.linalg.norm(apos[0,[0,2]]-start[[0,2]]))<=limits['spawn_xz_error_m'],
            continuous=bool(np.all(np.diff(times)>=0) and max(np.diff(times))<=limits['maximum_gap_s']),
            actor_health=all(r['ah']>0 for r in active),prey_conscious_healthy=all(r['ph']>0 and not r['unconscious'] for r in active),
            known_mind=bool(known_mind) and all(0<=v<=4 for v in known_mind),
            acquired=bool(moves and moves[0]['mind']>=3 and moves[0]['t']-times[0]<=limits['acquisition_timeout_s']),
            within_timeout=bool(moves and times[-1]-moves[0]['t']<=case['timeout_s']),
            actual_actor_goal=np.linalg.norm(apos[-1]-goal)<=limits['actor_goal_radius_m'],
            actual_prey_goal=np.linalg.norm(ppos[-1]-goal)<=limits['prey_goal_radius_m'],
            actor_contact=aphys['contact'],prey_contact=pphys['contact'],actor_terrain=aphys['terrain'],prey_terrain=pphys['terrain'],
            actor_corridor=atrace['corridor'],prey_corridor=ptrace['corridor'],actor_no_teleport=atrace['bounded_speed'],prey_no_teleport=ptrace['bounded_speed'],
            actor_complete_distance=atrace['progress_m']>=length-limits['actor_goal_radius_m'],
            bounded_path=atrace['path_length_m']<=limits['path_length_factor']*np.linalg.norm(goal-start),
            actual_client_input=len(inputs)>=3 and sum(r['requested_speed']==1 and r['actual_speed']>.1 for r in inputs)>=3 and all(np.linalg.norm(r['goal']-goal)<=.000002 for r in inputs))
        checks={k:bool(v) for k,v in checks.items()}
        reports.append(dict(case=case['case'],name=case['name'],status='PASS' if all(checks.values()) else 'FAIL',checks=checks,
            terminal=terminal,actor=aphys,prey=pphys,actor_trace=atrace,prey_trace=ptrace,samples=len(active),
            duration_s=float(times[-1]-times[0]),maximum_gap_s=float(max(np.diff(times))),client_input_samples=len(inputs)))
    passed=all(global_checks.values()) and all(c['status']=='PASS' for c in reports)
    return dict(status='PASS_CONTINUOUS_NATIVE_PURSUIT_BOTH_BRIDGE_DIRECTIONS' if passed else 'FAIL_OR_INCOMPLETE_CONTINUOUS_PURSUIT',global_checks=global_checks,errors=errors,cases=reports,limits=ref['limits'])


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--folder',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if a.out.exists():raise ValueError('Preserve evidence')
    ref=json.loads(a.reference.read_text());terrain=Path(ref['terrain']);assert sha(terrain)==ref['terrain_sha256']
    with rasterio.open(terrain) as dataset:height=dataset.read(1)
    server=a.folder/'engine.log';client=a.folder/'client-input.log'
    result=verify(ref,server.read_text(encoding='utf-8-sig'),client.read_text(encoding='utf-8-sig'),height)
    result['source_sha256']={str(p):sha(p) for p in (a.reference,server,client)}
    a.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(status=result['status'],cases=[dict(case=c['case'],status=c['status'],failed=[k for k,v in c.get('checks',{}).items() if not v]) for c in result['cases']]),indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS_') else 1)
