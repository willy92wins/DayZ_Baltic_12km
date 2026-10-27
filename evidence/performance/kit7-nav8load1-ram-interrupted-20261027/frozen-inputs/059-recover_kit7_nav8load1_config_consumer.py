"""Reprocess the same captured config after isolated-CLI import failure; no DayZ run."""
from pathlib import Path
import hashlib,json,sys,subprocess,datetime
R=Path(__file__).parent;D=R/'kit7-nav8load1-consumer-20261027';V=R/'kit7-nav8load1-recovery-review-20261027'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
assert __debug__
review=read(V/'response.json');assert not review['is_error'] and not review.get('permission_denials') and 'claude-fable-5-1' in review['modelUsage']
assert read(V/'completion.json')['returncode']==0 and read(V/'adjudication.json')['status']=='ACCEPTED_AFTER_REVIEW'
adjudication=read(V/'adjudication.json');reviewed=read(V/'source-hashes.json')
assert set(reviewed)<=set(adjudication['inputs'])
assert all(adjudication['inputs'][p]==h for p,h in reviewed.items() if p not in adjudication['post_review_changes'])
for p,h in adjudication['inputs'].items():assert sha(p)==h,p
assert not any((D/n).exists() for n in ['config-result.json','joint-result.json','config-recovery.json','config-consumer-recovery.stdout.log','config-consumer-recovery.stderr.log'])
assert 'ModuleNotFoundError' in (D/'config-consumer.stderr.log').read_text() and 'verify_nav_config_types_ev112' in (D/'config-consumer.stderr.log').read_text()
# Reuse the exact frozen admission and lifecycle checks, stopping before any write.
original=(R/'finish_kit7_nav8load1_probe.py').read_text()
first="assert not (O/'identity-verification.json').exists()"
start="observer=read(O/'observer/terminal.json')";stop="(O/'identity-verification.json').write_text"
assert original.count(first)==original.count(start)==original.count(stop)==1
scope={'__file__':str(R/'finish_kit7_nav8load1_probe.py')}
exec(compile(original[:original.index(first)],'frozen_native_admission','exec'),scope)
exec(compile(original[original.index(start):original.index(stop)],'frozen_native_lifecycle','exec'),scope)
binding=read(D/'log-binding.json');host=read(D/'host-identity.json');identity=read(D/'identity-verification.json');nav=read(D/'result.json');frozen=read(D/'frozen.json');dep=read(D/'deployment.json')
assert identity['status']=='PASS_BOUND_NATIVE_PROBE_INPUTS' and identity['run_id']==host['run_id'] and identity['packages']==dep['packages']
assert nav['status']=='PASS_KIT7_NATIVE_GRAPH' and nav['log_sha256']==sha(D/'runtime.log') and nav['reference_sha256']==sha(D/'reference.json')
assert sha(D/'config-runtime.log')==binding['config_sha256'] and Path(binding['config_source']).name==frozen['config_log_name']
utc=lambda x:datetime.datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(datetime.timezone.utc)
assert utc(host['created_utc'])<=utc(binding['config_source_last_write_utc'])<=scope['utc'](scope['intents'][0]['utc'])
control=read(D/'isolated-wrapper-controls.json');assert control['status']=='PASS_ISOLATED_CLI_WRAPPER' and control['consumer_sha256']==sha(W/'tools/navigation/verify_nav8_load1_config_ev112.py')
bootstrap='import sys,runpy;sys.path.insert(0,sys.argv[1]);script=sys.argv.pop(1)+"/verify_nav8_load1_config_ev112.py";sys.argv[0]=script;runpy.run_path(script,run_name="__main__")'
args=[sys.executable,'-I','-c',bootstrap,str(W/'tools/navigation'),'--probe-id',frozen['probe_id'],'--log',str(D/'config-runtime.log'),'--out',str(D/'config-result.json')]
p=subprocess.run(args,capture_output=True)
with (D/'config-consumer-recovery.stdout.log').open('xb') as f:f.write(p.stdout)
with (D/'config-consumer-recovery.stderr.log').open('xb') as f:f.write(p.stderr)
config=read(D/'config-result.json')
joint=dict(status='PASS_LOAD1_CONFIG_AND_NATIVE607' if p.returncode==0 and config['status']=='PASS_NATIVE_LOAD1_CONFIG' else 'FAIL_LOAD1_CONFIG_OR_NATIVE607',config_status=config['status'],native_status=nav['status'],run_id=host['run_id'],packages=dep['packages'],ram_measured=False,global_acceptance=False,recovery='Same original logs; explicit isolated Python import path; original failure preserved')
write(D/'joint-result.json',joint)
write(D/'config-recovery.json',dict(status='RECOVERED_SAME_CAPTURE' if p.returncode==0 else 'RECOVERY_REJECTED',run_id=host['run_id'],native_runs_added=0,consumer_returncode=p.returncode,review_inputs=read(V/'source-hashes.json'),outputs={str(D/n):sha(D/n) for n in ['config-result.json','joint-result.json','result.json']},original_failure_sha256=sha(D/'config-consumer.stderr.log')))
print(json.dumps(joint));raise SystemExit(0 if joint['status']=='PASS_LOAD1_CONFIG_AND_NATIVE607' else 1)
