"""Verify bounded native-AI load and join host process samples by observed phase."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median

ROOT=Path(__file__).resolve().parents[2]


def verify(text,ref):
    lines=text.splitlines()
    if lines[0]!='BALTIC_AI_LOAD_V1;BalticTrial;SERVER;NO_CE' or not lines[-1].startswith('COMPLETE;'):
        raise ValueError('Wrong or incomplete load fixture')
    groups={i:[] for i in range(4)};spawns={i:set() for i in range(4)};begins={};ends={}
    last_tick=-1
    for line in lines[2:-1]:
        r=line.split(';')
        if r[0]=='S' and len(r)==16:
            n=list(map(float,r[1:]))
            if not all(map(math.isfinite,n)): raise ValueError('Nonfinite measurement')
            if any(n[i]!=int(n[i]) for i in [0,1,3,5,8,9,10,11,12]): raise ValueError('Noninteger counter')
            if n[2]<=last_tick: raise ValueError('Nonmonotonic tick')
            last_tick=n[2]
            phase=int(n[0]);groups[phase].append(n)
        elif r[0]=='SPAWN' and len(r)==4:
            phase=int(r[1]);index=int(r[2])
            if index in spawns[phase]: raise ValueError('Duplicate spawn index')
            spawns[phase].add(index)
        elif r[0] in ('BEGIN','END') and len(r)==(6 if r[0]=='BEGIN' else 4):
            dest=begins if r[0]=='BEGIN' else ends;phase=int(r[1])
            if phase in dest: raise ValueError('Duplicate phase boundary')
            dest[phase]=r
        else: raise ValueError('Failed/unknown load record: '+r[0])
    if set(begins)!=set(groups) or set(ends)!=set(groups): raise ValueError('Missing phase boundaries')
    issues=[];results=[]
    for phase,wanted in enumerate(ref['populations']):
        rows=groups[phase]
        if [int(r[1]) for r in rows] != list(range(1,ref['samples_per_phase']+1)) or spawns[phase]!=set(range(wanted)):
            raise ValueError('Missing/duplicate samples or spawned population')
        if int(begins[phase][4]) != wanted: raise ValueError('Population differs from frozen plan')
        if rows[0][2]-float(begins[phase][2]) < ref['warmup_seconds']:
            raise ValueError('Warmup skipped')
        if float(ends[phase][2])!=rows[-1][2] or (phase and float(begins[phase][2])<float(ends[phase-1][2])):
            raise ValueError('Invalid phase timing')
        if any(r[4]<=0 or r[5]<=0 or r[6]<=0 or r[7]<0 or r[8]<0 or r[9]!=wanted or r[10]!=wanted or not 0<=r[11]<=wanted or not 0<=r[12]<=wanted or r[13]<=0 or r[14]<0 for r in rows):
            issues.append(f'phase{phase}:population_or_counter_invalid')
        if max(r[14] for r in rows)>ref['max_prey_drift_m']: issues.append(f'phase{phase}:prey_moved')
        active_samples=sum(r[11]>=wanted*ref['active_fraction'] for r in rows)
        if wanted and active_samples<ref['active_samples_required']: issues.append(f'phase{phase}:insufficient_active_AI')
        results.append(dict(phase=phase,population=wanted,samples=len(rows),measured_seconds=sum(r[4] for r in rows),tick_range=[rows[0][2]-rows[0][4],rows[-1][2]],awake_mean=mean(r[11] for r in rows),awake_min=min(r[11] for r in rows),active_samples=active_samples,moving_mean=mean(r[12] for r in rows),health_min=min(r[13] for r in rows),prey_drift_max_m=max(r[14] for r in rows),max_simulation_timeslice_s=max(r[7] for r in rows),timeslices_over_50ms=sum(r[8] for r in rows),max_sampling_window_s=max(r[4] for r in rows),update_calls_per_second=sum(r[5] for r in rows)/sum(r[4] for r in rows)))
    return dict(status='INCONCLUSIVE_ACTIVE_LOAD' if issues else 'PASS_BOUNDED_ACTIVE_AI_MEASUREMENT',issues=issues,phases=results,limits=['Single client, no CE, loot, persistence or city objects; not 100-player capacity.','OnUpdate rate and simulation timeslice are not render FPS or measured callback CPU cost.','All infected in one local cluster; population and collision stress together.'])


def host_summary(path):
    rows=[json.loads(l) for l in path.read_text(encoding='utf-8-sig').splitlines()]
    identities={(r['process_id'],r['start_utc']) for r in rows}
    if len(identities)!=1 or len(rows)<2: raise ValueError('Changed/missing host process')
    out=[]
    for phase in range(4):
        intervals=[];selected=[]
        for a,b in zip(rows,rows[1:]):
            if b['elapsed_s']<=a['elapsed_s'] or b['cpu_total_s']<a['cpu_total_s']: raise ValueError('Invalid host clock/counter')
            ma=(a.get('engine_last_line') or '').split(';');mb=(b.get('engine_last_line') or '').split(';')
            if len(ma)!=16 or len(mb)!=16 or ma[:2]!=['S',str(phase)] or mb[:2]!=['S',str(phase)]: continue
            dt=b['elapsed_s']-a['elapsed_s'];dcpu=b['cpu_total_s']-a['cpu_total_s']
            intervals.append((dt,dcpu));selected.append(b)
        if len(intervals)<10: raise ValueError('Insufficient host phase coverage')
        elapsed=sum(p[0] for p in intervals)
        out.append(dict(phase=phase,intervals=len(intervals),seconds=elapsed,cpu_percent_one_logical_core=100*sum(p[1] for p in intervals)/elapsed,cpu_peak_interval_percent_one_core=max(100*c/d for d,c in intervals),resident_mib_range=[min(r['working_set_bytes'] for r in selected)/2**20,max(r['working_set_bytes'] for r in selected)/2**20],resident_mib_median=median(r['working_set_bytes'] for r in selected)/2**20,private_mib_range=[min(r['private_bytes'] for r in selected)/2**20,max(r['private_bytes'] for r in selected)/2**20]))
    return dict(process_id=rows[0]['process_id'],start_utc=rows[0]['start_utc'],phases=out,alignment='Both interval endpoints read an S marker for the same phase. Engine marker may lag up to the actual host polling interval; phase boundaries and warmup excluded.')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--folder',type=Path,required=True)
    ap.add_argument('--reference',type=Path,default=ROOT/'evidence/performance/ai-load-reference-v1.json',
                    help='Frozen pre-run criteria and world/mission identity; defaults to original baseline')
    args=ap.parse_args()
    out=args.folder/'verification.json'
    if out.exists(): raise ValueError('Fresh result required')
    log=args.folder/'engine.log';refpath=args.reference
    try:
        result=verify(log.read_text(encoding='utf-8-sig'),json.loads(refpath.read_text(encoding='utf-8-sig')))
        result['host']={role:host_summary(args.folder/f'{role}-process.jsonl') for role in ('server','client')}
    except (ValueError,IndexError,KeyError) as exc:
        result=dict(status='FAIL_LOAD_EVIDENCE',reason=str(exc))
    result['sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [log,refpath,args.folder/'server-process.jsonl',args.folder/'client-process.jsonl']}
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)
