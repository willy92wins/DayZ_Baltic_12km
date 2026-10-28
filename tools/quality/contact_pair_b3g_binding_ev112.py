"""B3G native receipts. No claims from a complete synthetic/offline capture."""
from pathlib import Path
import math,ntpath
from water_query_native_b1_ev112 import sha,read,verify,norm,instant,package_set
from contact_pair_b3g_ev112 import require,consume,compare,contract,wire
CONTROL='ef229f3275d4c412d49f208395091e8b91faa5425e06ca2476a699a49bdf1b84'
CANDIDATE='362ef4c201a572087120cc987de14ad03dc650824c5a565a776fef74ce41ae4a'
OWN={'baltic_stream_pilot.pbo','narva_trial.pbo','baltic_water_v30.pbo','dayz_mcp.pbo'}
VANILLA={'plants.pbo','plants_bliss.pbo','structures_industrial.pbo','structures_roads.pbo','water.pbo'}

def files(root,accepted_sha):
    root=Path(root);require(sha(root/'accepted.json')==accepted_sha,'seal_drift')
    a=read(root/'accepted.json');require(a['status']=='B3G_NATIVE_READY','not_accepted');verify(a['inputs'])
    require(str(root/'deployment.json') in a['inputs'],'unsealed_deployment')
    d=read(root/'deployment.json');verify(d['inputs'])
    require(d['arm'] in ('control','candidate'),'arm')
    required=[d[k] for k in ('original','frozen','wrp','producer','csv','engine','scripts')]+list(d['packages'])+list(d['vanilla'])
    require(all(p in d['inputs'] for p in required),'incomplete_manifest')
    require(norm(d['scripts'])==norm(Path(d['engine']).parent/'dta/scripts.pbo') and d['inputs'][d['scripts']]==d['scripts_sha256'],'script_location')
    names={ntpath.basename(p).lower():h for p,h in d['packages'].items()}
    require(len(names)==len(d['packages'])==4 and set(names)==OWN,'mod_names')
    require(names['baltic_stream_pilot.pbo']==(CONTROL if d['arm']=='control' else CANDIDATE),'arm_package')
    require(names['narva_trial.pbo']=='10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc' and names['baltic_water_v30.pbo']=='97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43','world_water')
    require(len(d['vanilla'])==5 and {ntpath.basename(p).lower() for p in d['vanilla']}==VANILLA,'vanilla_names')
    require(all(norm(p)==norm(Path(d['engine']).parent/'Addons'/ntpath.basename(p)) for p in d['vanilla']),'vanilla_location')
    for p,h in {**d['packages'],**d['vanilla']}.items():require(d['inputs'][p]==h,'package_pin')
    actual={norm(p) for folder in {str(Path(p).parent) for p in d['packages']} for p in Path(folder).glob('*.pbo')}
    require(actual==set(package_set(d['packages'])),'unlisted_pbo')
    require(norm(Path(d['producer']).parent)==norm(d['mission'])==norm(Path(d['csv']).parent),'mission_files')
    require(Path(d['csv']).read_text(encoding='ascii')==wire.csv_for(contract(read(d['frozen']),read(d['original']))),'csv_source_binding')
    return d

def gate(root,accepted_sha):
    d=files(root,accepted_sha)
    require(not any((Path(root)/n).exists() for n in ('launch.json','native.log','result.json')),'unit_consumed')
    return dict(status='PRE_FIFO_GATE_PASS',arm=d['arm'],mod=d['mod'],mission=d['mission'])

def identity(d, launch, host, after, mcp, capture, cleanup, native_sha):
    require(launch['status'] == 'succeeded', 'launch_failed')
    request=launch['request']
    flags=dict(mode='server',build=False,clean=False,pack_only=False,preflight=False,no_base_mods=True,no_file_patching=True,navmesh_data_server=True,takeover=False,on_busy='queue',wait_for_box_s=600.0)
    require(all(k in request and type(request[k]) is type(v) and request[k]==v for k,v in flags.items()),'launch_flags')
    require(norm(request['mission'])==norm(d['mission']) and request['extra_mods']==[d['mod']],'launch_mission_mod')
    require(launch['readiness_budget_s']==300 and launch['capture_budget_s']==180,'launch_budget')
    require(isinstance(cleanup.get('close'),dict), 'lifecycle_not_closed')
    run = launch['run_id']
    require(run and all(x == run for x in (host['run_id'],after['run_id'],mcp['run_id'],mcp['server_run_id'],cleanup['close']['run_id'])), 'run_binding')
    require(mcp['server_binding'] == 'BOUND' and mcp['version_state'] == 'ok' and math.isfinite(mcp['poll_age_s']) and 0 <= mcp['poll_age_s'] < 10, 'bridge_binding')
    procs = mcp['processes']
    require(len(procs) == 1 and procs[0]['role'] == 'server', 'process_count')
    require(procs[0]['pid'] == host['pid'] == after['pid'] == capture['pid'], 'process_binding')
    created = instant(procs[0]['creation_time_utc'])
    require(all(abs((instant(v)-created).total_seconds()) <= .001 for v in (host['created_utc'],after['created_utc'],capture['created_utc'])), 'creation_binding')
    require(instant(capture['last_write_utc']) >= created, 'stale_log')
    require(bool(mcp['client_diagnostics']) and all(x['state'] == 'not_started' for x in mcp['client_diagnostics']) and host['navmesh_data_server'] and after['navmesh_data_server'], 'runtime_mode')
    expected = package_set(d['packages'])
    vanilla = {norm(p):h for p,h in d['vanilla'].items()}
    for h in (host,after):
        require(h.get('file_patching') is False and h.get('server_mods') == [], 'external_source_mode')
        require(norm(h['mission_path']) == norm(d['mission']) and h['mission_sha256'] == d['inputs'][d['producer']], 'mission_binding')
        require(norm(h['executable']) == norm(d['engine']) and h['executable_file_sha256'] == d['inputs'][d['engine']], 'engine_binding')
        require(package_set(h['package_hashes']) == expected, 'package_binding')
        actual = {norm(p):v for p,v in h['vanilla_hashes'].items()}
        require(len(h['vanilla_hashes']) == len(actual) == 5 and actual == vanilla, 'PACKAGE_DRIFT:vanilla')
    require(host['scripts_sha256'] == after['scripts_sha256'] == d['scripts_sha256'], 'scripts_binding')
    require(host['mods'] == after['mods'] and len(host['mods'])==2, 'effective_mods')
    for key in ('profiles','host_raw_command_line_sha256','server_config','server_config_sha256'):
        require(host[key] == after[key], 'runtime_changed:'+key)
    require(norm(capture['source']) == norm(ntpath.join(host['profiles'],'baltic_contact_b3g.log')), 'profile_log_binding')
    require(capture['count'] == 270 and capture['sha256'] == native_sha, 'log_binding')
    stopped = cleanup.get('stop')
    retired = cleanup['close']['run_retired'] or (stopped and stopped['run_id'] == run and stopped['status'] == 'succeeded')
    require(retired and cleanup['self']['state'] == 'none' and not cleanup['own_run_present'] and cleanup['pending_commands'] == 0 and not cleanup['cleanup_degraded'] and not cleanup['error'] and not cleanup['cleanup_error'], 'lifecycle_not_closed')

def consume_bound(root,accepted_sha):
    root=Path(root);require(not (root/'result.json').exists(),'result_exists');d=files(root,accepted_sha);launch=read(root/'launch.json')
    require(launch['accepted_sha256']==accepted_sha,'launch_seal_binding')
    names=('host-identity.json','host-after.json','mcp-identity.json','log-capture.json','cleanup.json')
    identity(d,launch,*[read(root/n) for n in names],sha(root/'native.log'))
    result=consume((root/'native.log').read_text(encoding='utf-8-sig'),Path(d['csv']).read_text(encoding='ascii'),read(d['frozen']),read(d['original']))
    result['adapter']['raw_file_sha256']=sha(root/'native.log')
    result.update(identity_bound=True,run_id=launch['run_id'],arm=d['arm'],deployment_sha256=sha(root/'deployment.json'),
                  inputs={str(root/n):sha(root/n) for n in (*names,'launch.json','native.log','accepted.json','deployment.json')})
    return result

def pair_bound(a,b,da,db):
    require(a['identity_bound'] and b['identity_bound'] and a['arm']=='control' and b['arm']=='candidate','pair_identity')
    require(a['run_id'] and b['run_id'] and a['run_id']!=b['run_id'],'same_run')
    for k in ('original','frozen','wrp','engine','scripts','producer','csv'):
        require(da['inputs'][da[k]]==db['inputs'][db[k]],'pair_source_changed:'+k)
    require(da['vanilla']==db['vanilla'],'pair_vanilla_changed')
    packages=lambda d:{ntpath.basename(p).lower():h for p,h in d['packages'].items()}
    pa,pb=packages(da),packages(db)
    require(set(pa)==set(pb)==OWN and pa.pop('baltic_stream_pilot.pbo')==CONTROL and pb.pop('baltic_stream_pilot.pbo')==CANDIDATE and pa==pb,'pair_intervention')
    result=compare(a,b);result.update(identity_bound=True,control_run=a['run_id'],candidate_run=b['run_id']);return result

