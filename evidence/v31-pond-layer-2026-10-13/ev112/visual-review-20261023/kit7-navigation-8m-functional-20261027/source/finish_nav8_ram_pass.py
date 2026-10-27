import argparse, hashlib, json, os, subprocess, sys, datetime
from pathlib import Path
R=Path(r'E:\DayZ-Baltic-Build\shape-repair-20261025')
W=Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c')
PY=Path(r'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe')
a=argparse.ArgumentParser();a.add_argument('order',type=int);ns=a.parse_args()
d=R/'kit7-nav8-ram-ab-20261027'/f'pass-{ns.order:02}'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
before=load(d/'before.json');run=load(d/'run.json');host=load(d/'host-identity.json')
sys.path.insert(0,str(R))
from verify_c_orderly_close import validate_close,validate_rpt,validate_generation_exit
gate=load(d/'benchmark-gate.json');cleanup=load(d/'cleanup.json')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert gate['status']=='BOUND_AFTER_NATIVE607' and all(sha(p)==h for p,h in gate['inputs'].items())
assert cleanup['close']['run_id']==run['run_id']==host['run_id']
assert cleanup['self']['state']=='none' and not cleanup['cleanup_degraded'] and not cleanup['own_run_present'] and not cleanup['pending_commands'] and not cleanup['error'] and not cleanup['cleanup_error']
validate_close(cleanup['close']);validate_rpt(load(d/'rpt-binding.json'),host,d/'server.RPT')
assert all(x['state']=='not_started' for x in run['client_diagnostics'])
utc=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00'))
assert abs((utc(host['created_utc'])-utc(run['process']['creation_time_utc'])).total_seconds())<=.002
assert Path(host['mission_path'])==Path(gate['mission']['mission']) and run['profile_log']==gate['mission']['profile_log']
observer=load(d/'observer/terminal.json');attached=load(d/'observer/attached.json')
assert attached['status']=='ATTACHED' and attached['handle_retained'] and not attached['mutation_attempted']
assert observer['process_id']==attached['process_id']==host['pid']
assert observer['observer_sha256']==attached['observer_sha256']==sha(W/'tools/navigation/observe_owned_server_exit.ps1')
assert attached['executable_sha256']==host['executable_file_sha256']
for stamp in (observer['start_utc'],attached['start_utc']):assert abs((utc(stamp)-utc(host['created_utc'])).total_seconds())<=.002
events=[json.loads(x) for x in (d/'timeline.jsonl').read_text(encoding='utf-8-sig').splitlines()]
validate_generation_exit(observer,events,host['run_id'])
assert host['run_id']==run['run_id'] and host['pid']==run['process']['pid']
assert not host['navmesh_data_server'] and not run['client_started']
assert run['server_binding']=='BOUND' and run['server_run_id']==run['run_id']
assert Path(host['mission_path'])/'init.c'==Path(before['artifacts']['mission'])
for role,key in [('mission','mission_sha256'),('executable','executable_file_sha256'),('server_config','server_config_sha256')]:
    assert host[key]==before['inputs'][before['artifacts'][role]],role
vanilla=Path(before['artifacts']['executable']).parent/'Addons'
actual=set(p.resolve() for p in vanilla.glob('*.pbo'))
actual.update(Path(p).resolve() for p in host['package_hashes'])
assert actual==set(Path(p).resolve() for p in before['packages']),'Actual loaded package inventory differs'
expected_packages={Path(p).resolve():h for p,h in before['packages'].items()}
for p,h in host['package_hashes'].items():assert expected_packages[Path(p).resolve()]==h,p
engine=d/run['profile_log']
args=[str(PY),'-I',str(W/'tools/performance/bind_server_baseline_ev112.py'),'finish','--snapshot',str(d/'before.json'),'--run-id',run['run_id'],'--process-id',str(run['process']['pid']),'--start-utc',run['process']['creation_time_utc'],'--engine',str(engine),'--host',str(d/'host.jsonl'),'--out',str(d/'reference.json')]
for name,cmd in [('binding',args),('consumer',[str(PY),'-I',str(W/'tools/performance/read_server_baseline_ev112.py'),'--reference',str(d/'reference.json'),'--engine',str(engine),'--host',str(d/'host.jsonl'),'--out',str(d/'result.json')])]:
    proc=subprocess.run(cmd,cwd=W,capture_output=True,text=True,encoding='utf-8')
    (d/(name+'.stdout.log')).write_text(proc.stdout,encoding='utf-8')
    (d/(name+'.stderr.log')).write_text(proc.stderr,encoding='utf-8')
    if proc.returncode:
        print(json.dumps({'phase':name,'returncode':proc.returncode,'stderr':proc.stderr[-1500:],'stdout':proc.stdout[-1500:]}))
        raise SystemExit(proc.returncode)
result=load(d/'result.json')
print(json.dumps({k:result.get(k) for k in ('status','world','host_samples','measurement_samples','host_measurement_seconds','cpu_percent_one_logical_core','working_set_mib','private_mib','private_bytes_mib')},indent=2))
