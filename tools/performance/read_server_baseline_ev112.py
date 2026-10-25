"""Validate synchronized empty-server CPU/memory coverage, never client FPS."""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'navigation'))
from verify_terrain_perf import verify as verify_engine


def timestamp(value):return datetime.fromisoformat(value.replace('Z','+00:00'))


def verify(world,process_id,start_utc,engine_text,rows):
    if world not in ('BalticTrial','ChernarusPlus'):raise ValueError('Unsupported expected world')
    lines=engine_text.splitlines()
    header=lines[0].split(';') if lines else []
    if len(header)!=4 or header[0]!='BALTIC_TERRAIN_PERF_V1' or header[1].lower()!=world.lower() or header[2:]!=['SERVER','NO_CE_NO_PLAYERS']:raise ValueError('Wrong engine world/header')
    # Explicit world adapter; the legacy validator's timing contract is unchanged.
    engine=verify_engine('\n'.join(['BALTIC_TERRAIN_PERF_V1;BalticTrial;SERVER;NO_CE_NO_PLAYERS',*lines[1:]]))
    if len(rows)<120 or len(rows)>1201:raise ValueError('Incomplete or excessive host capture')
    initial=lines[1];first_sample=lines[3];ending=lines[-1]
    first=None;end=None;last_init=None;marker_index=-1
    marker_indices={line:i for i,line in enumerate(lines)}
    for i,row in enumerate(rows):
        if row['sample']!=i or row['process_id']!=process_id or abs((timestamp(row['start_utc'])-timestamp(start_utc)).total_seconds())>.002:
            raise ValueError('Host process identity/order changed')
        if not all(isinstance(row[k],(int,float)) and not isinstance(row[k],bool) and math.isfinite(row[k]) for k in ('elapsed_s','cpu_total_s','working_set_bytes','private_bytes')):
            raise ValueError('Nonfinite host counter')
        if row['elapsed_s']<0 or row['cpu_total_s']<0 or min(row['working_set_bytes'],row['private_bytes'])<=0:
            raise ValueError('Invalid host counter')
        if i:
            previous=rows[i-1]
            if not .4<=row['elapsed_s']-previous['elapsed_s']<=3:raise ValueError('Host clock gap')
            if row['cpu_total_s']<previous['cpu_total_s']:raise ValueError('CPU counter regressed')
        marker=row['engine_last_line']
        if marker:
            if marker not in marker_indices or marker_indices[marker]<marker_index:raise ValueError('Unknown or regressing engine marker')
            marker_index=marker_indices[marker]
        # The mission writes columns after INIT, so this is the warmup marker.
        if marker in (initial,lines[2]) and first is None:last_init=i
        if marker==first_sample and first is None:first=i
        if marker==ending and end is None:end=i
    if first is None or end is None or last_init is None or not last_init<first<end:
        raise ValueError('Host coverage misses warmup/start/end')
    if end!=len(rows)-1:raise ValueError('Host capture continues after END')
    if first-last_init!=1:raise ValueError('Host start boundary has an unknown gap')
    part=rows[last_init:end+1];duration=part[-1]['elapsed_s']-part[0]['elapsed_s']
    if abs(duration-engine['measurement_seconds'])>2.1:raise ValueError('Host/engine duration mismatch')
    cpu=part[-1]['cpu_total_s']-part[0]['cpu_total_s']
    if cpu<=0:raise ValueError('No measured process CPU over the full engine window')
    result=dict(status='PASS_COMPLETE_EMPTY_SERVER_MEASUREMENT',world=world,engine_world=header[1],process_id=process_id,start_utc=start_utc,host_samples=len(rows),measurement_samples=len(part),host_measurement_seconds=duration,engine_measurement_seconds=engine['measurement_seconds'],cpu_seconds=cpu,cpu_percent_one_logical_core=100*cpu/duration,
                start_boundary_uncertainty_s=rows[first]['elapsed_s']-rows[last_init]['elapsed_s'],end_boundary_uncertainty_s=rows[end]['elapsed_s']-rows[end-1]['elapsed_s'],engine=engine,
                limits=['Empty dedicated server, no CE/AI/players/client. No player-capacity or client-FPS verdict.','CPU is cumulative process CPU per monotonic wall time relative to one logical core.','Host capture targets 0.5-second cadence; measured boundary uncertainty reported, not exact synchronization.','Working set and private bytes have different meanings; neither is VRAM.'])
    for key in ('working_set_bytes','private_bytes'):
        values=[r[key]/1048576 for r in part]
        result[key.replace('_bytes','_mib')]=dict(median=statistics.median(values),minimum=min(values),maximum=max(values))
    result['engine_read_unavailable_samples']=sum(r.get('engine_read_unavailable',False) is True for r in rows)
    return result


def require_inputs(ref,engine,host):
    roles=ref.get('artifacts',{})
    required=('engine','host','mission','executable','server_config')
    if any(key not in roles for key in required):raise ValueError('Missing required artifact identity')
    paths={key:Path(roles[key]).resolve() for key in required}
    if len(set(paths.values()))!=len(required) or paths['engine']!=Path(engine).resolve() or paths['host']!=Path(host).resolve():raise ValueError('Artifact paths do not match capture')
    inputs={Path(p).resolve():digest for p,digest in ref.get('inputs',{}).items()}
    if any(p not in inputs for p in paths.values()):raise ValueError('Required artifact hash missing')
    if paths['mission'].name.lower()!='init.c':raise ValueError('Mission init.c identity missing')
    for p,digest in inputs.items():
        if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('Bound input changed')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--engine',type=Path,required=True);ap.add_argument('--host',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise ValueError('Fresh result required')
    ref=json.loads(a.reference.read_text(encoding='utf-8-sig'))
    require_inputs(ref,a.engine,a.host)
    try:report=verify(ref['world'],ref['process_id'],ref['start_utc'],a.engine.read_text(encoding='utf-8-sig'),[json.loads(x) for x in a.host.read_text(encoding='utf-8-sig').splitlines()])
    except (ValueError,KeyError,IndexError,TypeError) as exc:report=dict(status='FAIL_MEASUREMENT',reason=str(exc))
    report['inputs']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.reference,a.engine,a.host)}
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
    return 0 if report['status'].startswith('PASS_') else 1


if __name__=='__main__':sys.exit(main())
