"""Bind each native unit to its own runtime before interpreting measurements."""
from pathlib import Path
from datetime import datetime
import hashlib,json,sys
R=Path(__file__).resolve().parent;O=R/'dry-road-full-native-20261028';W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');sys.path.insert(0,str(W/'tools/quality'))
from buried_roadway_semantics_ev112 import require,verify_frozen,verify_package_set
from dry_road_native_consumer_ev112 import evaluate,parse,calibrate
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
require(len(sys.argv)==2 and sys.argv[1] in ('calibration','probe'),'mode_required');mode=sys.argv[1];D=O/mode
require(not (D/'result.json').exists(),'fresh_result_required')
dep=read(O/'deployment.json');pre=read(O/'prelaunch.json');accept=read(O/'accepted.json');unit=dep['units'][mode]
require(accept['status']=='REVIEWED_FULL_NATIVE_READY','not_accepted')
for mapping in (dep['inputs'],accept['inputs']):verify_frozen(mapping)
host=read(D/'host-identity.json');m=read(D/'mcp-identity.json');capture=read(D/'log-capture.json');cleanup=read(D/'cleanup.json');launch=read(D/'launch.json')
require(launch['mode']==mode and launch['accepted_sha256']==sha(O/'accepted.json'),'launch_seal_binding')
require(host['run_id']==m['run_id']==m['server_run_id']==launch['run_id']==cleanup['close']['run_id'],'run_binding')
require(m['server_binding']=='BOUND' and m['version_state']=='ok' and m['poll_age_s']<10,'bridge_binding')
require(len(m['processes'])==1 and m['processes'][0]['role']=='server' and m['processes'][0]['pid']==host['pid']==capture['pid'],'process_binding')
require(datetime.fromisoformat(m['processes'][0]['creation_time_utc'])==datetime.fromisoformat(capture['created_utc']),'capture_creation_binding')
require(abs((datetime.fromisoformat(host['created_utc'])-datetime.fromisoformat(capture['created_utc'])).total_seconds())<=.000001,'host_creation_binding')
require(datetime.fromisoformat(capture['last_write_utc'])>=datetime.fromisoformat(host['created_utc']),'stale_log')
require(host['navmesh_data_server'] and all(x['state']=='not_started' for x in m['client_diagnostics']),'runtime_mode')
require(Path(host['mission_path'])==Path(unit['mission']) and host['mission_sha256']==unit['producer_sha256'],'mission_binding')
require(host['executable_file_sha256']==pre['executable_sha256'] and sha(host['executable'])==pre['executable_sha256'],'engine_binding')
expected={**dep['deployed'],pre['bridge_pbo']:pre['bridge_sha256']};verify_package_set(expected,host['package_hashes'])
require(capture['sha256']==sha(D/'native.log') and capture['count']==unit['count'],'log_binding')
require(cleanup['close']['run_retired'] and cleanup['self']['state']=='none' and not cleanup['own_run_present'] and not cleanup['cleanup_degraded'] and cleanup['pending_commands']==0 and not cleanup['error'] and not cleanup['cleanup_error'],'lifecycle_not_closed')
paths=[D/n for n in ('host-identity.json','mcp-identity.json','log-capture.json','cleanup.json','launch.json','native.log')]+[O/'deployment.json',O/'prelaunch.json',O/'accepted.json']
if mode=='calibration':
    cal=calibrate((D/'native.log').read_text(encoding='utf-8-sig'));result=dict(status='CALIBRATION_PASS',calibration=cal)
else:
    cr=O/'calibration/result.json';require(launch['calibration_sha256']==sha(cr),'launch_calibration_binding');reference=read(cr);verify_frozen(reference['inputs'])
    require(reference['status']=='CALIBRATION_PASS' and reference['identity_bound'] and reference['engine_sha256']==pre['executable_sha256'] and reference['packages']==expected,'calibration_binding')
    require(reference['run_id']!=host['run_id'] and datetime.fromisoformat(reference['created_utc'])<datetime.fromisoformat(host['created_utc']),'calibration_order')
    points=read(O/'points.json')['points'];csv=''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in points)
    require((Path(unit['mission'])/'points.csv').read_text(encoding='ascii')==csv,'point_csv_binding')
    result=evaluate(points,parse((D/'native.log').read_text(encoding='utf-8-sig'),unit['count']),reference['calibration']);paths.extend([cr,O/'points.json'])
result.update(run_id=host['run_id'],created_utc=host['created_utc'],log_sha256=sha(D/'native.log'),packages=expected,engine_sha256=pre['executable_sha256'],identity_bound=True,inputs={str(p):sha(p) for p in paths})
(D/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ('rows','packages','inputs','failures','inconclusive')},indent=2))
raise SystemExit(0 if result['status'] in ('CALIBRATION_PASS','SERVER_PROBE_PASS') else 2 if result['status']=='INCONCLUSIVE_COVERAGE' else 1)
