"""Freeze the exact existing607 contract with a fresh run marker; no launch."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,uuid
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-nav12-consumer-20261027';old=R/'kit7-nav-consumer-20261026'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not D.exists()
ref=read(old/'reference.json');oldref=json.loads(json.dumps(ref));probe=str(uuid.uuid4())
ref.update(probe_id=probe,header='BALTIC_KIT7_NAV_V1;BalticTrial;'+probe,log_name='baltic_kit7_nav_'+probe+'.log')
assert {k:v for k,v in ref.items() if k not in ('probe_id','header','log_name')}=={k:v for k,v in oldref.items() if k not in ('probe_id','header','log_name')}
for p,h in ref['inputs'].items():assert sha(p)==h,p
D.mkdir();write(D/'reference.json',ref);shutil.copyfile(old/'queries.csv',D/'queries.csv')
mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticKit7Nav12.BalticTrial');mission.mkdir(exist_ok=False)
template=W/'missions/BalticKit7NavV1.BalticTrial/init.c';code=template.read_text(encoding='utf-8');assert code.count('@PROBE_ID@')==3
(mission/'init.c').write_text(code.replace('@PROBE_ID@',probe),encoding='ascii',newline='\n');shutil.copyfile(D/'queries.csv',mission/'queries.csv')
assert sha(D/'queries.csv')==sha(old/'queries.csv')==sha(mission/'queries.csv')
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
bootstrap='import runpy,sys;sys.path.insert(0,'+repr(str(validator.parent))+');sys.argv='+repr([str(validator),str(mission),'--vanilla-root','P:/scripts'])+';runpy.run_path('+repr(str(validator))+',run_name="__main__")'
p=subprocess.run([sys.executable,'-I','-c',bootstrap],capture_output=True)
(D/'script-validator.json').write_bytes(p.stdout);(D/'script-validator.stderr.log').write_bytes(p.stderr)
assert p.returncode in (0,2)
static=read(D/'script-validator.json');assert static['status']=='PASS' and static['info']['files_scanned']==1 and not static['errors'] and not static['warnings']
repl={'probeKit7Nav':'probeKit7Nav12','kit7-nav-consumer-20261026':'kit7-nav12-consumer-20261027','BalticKit7NavV1.BalticTrial':'BalticKit7Nav12.BalticTrial',oldref['log_name']:ref['log_name'],'kit7-nav-postprocess-review-20261026':'kit7-nav12-postprocess-review-20261027','@DayZ_Baltic_EV112_Kit7NavV9':'@DayZ_Baltic_EV112_Kit7Nav12','kit7NavProbe':'kit7Nav12Probe','finish_kit7_nav_probe.py':'finish_kit7_nav12_probe.py'}
s=(R/'orchestrate_kit7_nav_probe.js').read_text(encoding='utf-8')
for a,b in repl.items():assert a in s,a;s=s.replace(a,b)
coord=R/'orchestrate_kit7_nav12_probe.js';assert not coord.exists();coord.write_text(s,encoding='utf-8')
s=(R/'finish_kit7_nav_probe.py').read_text(encoding='utf-8').replace('kit7-nav-consumer-20261026','kit7-nav12-consumer-20261027').replace('nav-kit7-preparation-20261026','nav-kit7-12m-preparation-20261027')
finish=R/'finish_kit7_nav12_probe.py';assert not finish.exists();finish.write_text(s,encoding='utf-8')
geometry=read(ref['geometry']);inputs={**ref['inputs'],**geometry['inputs']}
paths=[Path(__file__),old/'reference.json',old/'queries.csv',template,mission/'init.c',mission/'queries.csv',D/'reference.json',D/'queries.csv',W/'tools/navigation/verify_kit7_nav_ev112.py',W/'tools/navigation/verify_continuity_nav_v30.py',W/'tools/terrain/verify_v30_acceptance.py',W/'tools/navigation/prepare_patch_nav_probe_ev112.py',W/'tools/navigation/observe_owned_server_exit.ps1',R/'capture_kit7_nav_log.ps1',coord,finish,R/'capture_owned_server_identity.ps1',R/'copy_owned_server_rpt.ps1',R/'record_nav_c_event.ps1',R/'verify_c_orderly_close.py',R/'guarded-relief-batch-e-merged/terrain-buried.npz']
inputs.update({str(p):sha(p) for p in paths});assert all(sha(p)==h for p,h in inputs.items())
write(D/'frozen.json',dict(status='PREPARED_PENDING_CODE_REVIEW_AND_NAV_GENERATION',mission=str(mission),log_name=ref['log_name'],probe_id=probe,expected_count=607,inputs=inputs))
write(D/'contract-parity.json',dict(status='PASS_SAME607_CONTRACT_FRESH_ID',original_reference_sha256=sha(old/'reference.json'),reference_sha256=sha(D/'reference.json'),queries_sha256=sha(D/'queries.csv'),only_reference_changes=['probe_id','header','log_name'],unchanged_queries=607,native_acceptance=False))
print(json.dumps(dict(status='PREPARED_PENDING_CODE_REVIEW_AND_NAV_GENERATION',probe_id=probe,inputs=len(inputs))))
