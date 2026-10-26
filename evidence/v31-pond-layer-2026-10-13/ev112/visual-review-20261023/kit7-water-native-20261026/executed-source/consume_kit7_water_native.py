"""Bind the native log to its owned run before invoking unchanged judges."""
from pathlib import Path
from datetime import datetime
import hashlib,json,sys
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;O=R/'kit7-water-native-20261026';W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/water'));from eval_visual_probe_v31 import calibrate,parse,judge
kind=sys.argv[1];assert kind in ('full','calibration');D=O/kind
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not (D/'result.json').exists()
dep=read(O/'deployment.json');pre=read(O/'prelaunch.json');accept=read(O/'accepted.json')
assert accept['status']=='ACCEPTED_FOR_NATIVE_RUNS'
for mapping in (dep['inputs'],accept['inputs']):
 for p,h in mapping.items():assert sha(Path(p))==h,p
host=read(D/'host-identity.json');m=read(D/'mcp-identity.json');b=read(D/'log-capture.json');c=read(D/'cleanup.json');launch=read(D/'launch.json')
assert host['run_id']==m['run_id']==m['server_run_id']==launch['run_id']==c['close']['run_id']
assert m['server_binding']=='BOUND' and m['version_state']=='ok' and m['poll_age_s']<10
assert len(m['processes'])==1 and m['processes'][0]['role']=='server' and m['processes'][0]['pid']==host['pid']==b['pid']
assert datetime.fromisoformat(host['created_utc'])==datetime.fromisoformat(m['processes'][0]['creation_time_utc'])==datetime.fromisoformat(b['created_utc'])
assert datetime.fromisoformat(b['last_write_utc'])>=datetime.fromisoformat(host['created_utc'])
assert host['navmesh_data_server'] and all(x['state']=='not_started' for x in m['client_diagnostics'])
assert Path(host['mission_path'])==Path(dep['missions'][kind]) and host['mission_sha256']==dep['producers'][kind]
assert host['executable_file_sha256']==pre['executable_sha256'] and sha(Path(host['executable']))==pre['executable_sha256']
expected={**dep['deployed'],pre['bridge_pbo']:pre['bridge_sha256']};normalize=lambda d:{str(Path(p).resolve()).casefold():h for p,h in d.items()}
assert normalize(host['package_hashes'])==normalize(expected)
assert all(sha(Path(p))==h for p,h in expected.items())
assert b['sha256']==sha(D/'native.log') and b['count']==(6801 if kind=='full' else 289)
assert c['close']['run_retired'] and c['self']['state']=='none' and not c['cleanup_degraded'] and c['pending_commands']==0 and not c['error'] and not c['cleanup_error']
text=(D/'native.log').read_text(encoding='utf-8-sig')
if kind=='calibration':
 result=dict(status='FRESH_VANILLA_CALIBRATION_PASS',**calibrate(text))
else:
 ref=read(O/'calibration/result.json');assert ref['status']=='FRESH_VANILLA_CALIBRATION_PASS' and ref['log_sha256']==sha(O/'calibration/native.log') and ref['packages']==expected and ref['engine_sha256']==pre['executable_sha256']
 cal=calibrate((O/'calibration/native.log').read_text(encoding='utf-8-sig'));assert cal['margin_m']==ref['margin_m']
 doc=read(O/'points.json');points=doc['points'];assert len(points)==6801 and [p['id'] for p in points]==list(range(6801))
 csv=''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in points)
 assert (Path(dep['missions']['full'])/'points.csv').read_text(encoding='ascii')==csv
 result=judge(points,parse(text,6801),cal['margin_m']);result['calibration_log_sha256']=ref['log_sha256']
result.update(run_id=host['run_id'],log_sha256=sha(D/'native.log'),packages=expected,engine_sha256=pre['executable_sha256'],inputs_unchanged=True,identity_bound=True,client_started=False,navmesh_data_server=True,navigation_accepted=False)
(D/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('failures','packages')},indent=2))
raise SystemExit(result['status'] not in ('FRESH_VANILLA_CALIBRATION_PASS','SERVER_PROBE_PASS'))
