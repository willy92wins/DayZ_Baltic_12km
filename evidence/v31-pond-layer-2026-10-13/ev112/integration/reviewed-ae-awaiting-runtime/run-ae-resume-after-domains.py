"""Finish AE diagnostics after the observed successful paired-domain control run.

Original chain/import/regional failures stay immutable. This runner never changes
source, gates, bands, product files, reserved seeds, deployment or DayZ state.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,time
O=Path(__file__).parent;out=O/'forest-ae-resume-after-domains.json';assert not out.exists()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
read=lambda name:json.loads((O/name).read_text())
execution=read('forest-ae-negative-domains-execution.json');domain_script=O/'run-final-forest-negatives-ae-domains.py'
assert execution['exit_code']==0 and execution['runner_sha256']==sha(domain_script)
assert execution['command']==[sys.executable,'-I',str(domain_script)]
domains=read('forest-final-negatives-ae/domain-binding.json');assert domains['status']=='PASS' and domains['runner_sha256']==sha(domain_script)
assert execution['binding_sha256']==sha(O/'forest-final-negatives-ae/domain-binding.json')
acceptance=read('forest-final-negatives-ae/acceptance.json');assert acceptance['result']=='PASS' and acceptance['positive_gates']==6 and acceptance['negative_controls']==25
prior_path=O/'pipeline-ae-package.json';prior=read(prior_path.name)
assert len(prior)==6 and all(v['rc']==0 for v in prior[:5]) and prior[-1]['step']=='negatives' and prior[-1]['rc']==1
first=read('pipeline-ae-package.attempt1-import-failure.json');assert prior[:5]==first[:5]
failed_resume=read('forest-ae-resume-after-import.json');assert failed_resume['status']=='FAILED' and failed_resume['steps']==[prior[-1]]
backup=O/'pipeline-ae-package.attempt2-regional-failure.json';assert not backup.exists();backup.write_bytes(prior_path.read_bytes())
frozen=read('forest-ae-frozen.json');inputs=read('forest-validation-inputs.json');runners=read('forest-ae-runner-bindings.json')
package=read('package-final-ae/package.json');report=read('forest-map-51ae/report.json')
assert sha(package['pbo'])==package['pbo_sha256'] and sha(O/'forest-map-51ae/records.json')==report['records_sha256']
assert report['records_sha256']==domains['records_sha256'] and report['tool_sha256']==domains['source_sha256']
negative_row=dict(step='negatives',rc=execution['exit_code'],cmd=execution['command'],execution_receipt=str(O/'forest-ae-negative-domains-execution.json'),domain_binding=str(O/'forest-final-negatives-ae/domain-binding.json'))
base=dict(scope=__doc__,runner_sha256=sha(__file__),original_chain_failure_sha256=sha(O/'forest-ae-validated-chain.json'),original_import_resume_sha256=sha(O/'forest-ae-resume-after-import.json'),original_pipeline_attempt2=str(backup),original_pipeline_attempt2_sha256=sha(backup),negative_execution_sha256=sha(O/'forest-ae-negative-domains-execution.json'),negative_domain_binding_sha256=sha(O/'forest-final-negatives-ae/domain-binding.json'),frozen_manifest_sha256=sha(O/'forest-ae-frozen.json'),source_sha256=report['tool_sha256'],records_sha256=report['records_sha256'],pbo_sha256=package['pbo_sha256'],negative_row=negative_row,release_acceptance=False)
steps=[]
def save(status,**extra):out.write_text(json.dumps(dict(base,status=status,steps=steps,**extra),indent=2)+'\n')
def check():
 assert all(sha(p)==h for p,h in frozen['files'].items()) and all(sha(p)==h for p,h in inputs['files'].items())
 assert all(sha(v['path'])==v['sha256'] for v in runners['runners'])
 assert all(sha(p)==h for p,h in runners['literal_script_dependencies'].items())
 assert sha(O/'run-forest-holdout-ae.py')==runners['holdout_script_sha256']
 assert sha(domain_script)==execution['runner_sha256'] and sha(O/'forest-final-negatives-ae/domain-binding.json')==execution['binding_sha256']
def run(name,args,pipeline):
 check();cmd=[sys.executable,'-I',*map(str,args)];start=time.time();print('START',name,flush=True)
 with (O/f'forest-ae-domain-resume-{name}.log').open('w',encoding='utf-8') as f:rc=subprocess.run(cmd,cwd=O,stdout=f,stderr=subprocess.STDOUT).returncode
 row=dict(step=name,rc=rc,seconds=time.time()-start,cmd=cmd,continuation=str(out));steps.append(row)
 if pipeline:prior_path.write_text(json.dumps(prior[:5]+[negative_row]+steps,indent=2)+'\n')
 save('RUNNING',current=name);print('END',name,rc,flush=True);assert rc==0,row
try:
 save('RUNNING');check()
 run('rim-counts',[O/'audit-final-rim-counts.py',O/'forest-map-51ae',O/'forest-painted-rasters-ae',O/'final-rim-counts-ae.json'],True)
 run('renders',[O/'render-final-forest-ae.py',O/'forest-painted-rasters-ae',O/'forest-final-renders-ae'],True)
 assert len(read('pipeline-ae-package.json'))==8 and all(v['rc']==0 for v in read('pipeline-ae-package.json'))
 run('fresh-diagnostics',[O/'audit-forest-r2-diagnostics.py',O/'forest-map-51ae',O/'forest-painted-rasters-ae',O/'forest-r2-diagnostics-ae-painted'],False)
 check();assert sha(package['pbo'])==package['pbo_sha256']
 save('MEASURED_AWAITING_VISUAL_INSPECTION_AND_FRESH_HOLDOUTS')
except BaseException as e:
 save('FAILED',error=repr(e));raise
print('Diagnostics complete; actual visual inspection and fresh holdouts still required.',flush=True)
