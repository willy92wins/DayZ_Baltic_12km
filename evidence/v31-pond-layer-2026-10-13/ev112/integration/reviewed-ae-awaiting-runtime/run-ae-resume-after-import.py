"""Continue only unfinished AE validation after the isolated recio import failure.

Preserves the failed chain, log and pipeline receipt. No rebuild, regeneration,
source change, acceptance change, fresh-seed reservation, promotion or deployment.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,time
O=Path(__file__).parent;out=O/'forest-ae-resume-after-import.json';assert not out.exists()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1<<22),b''):h.update(block)
 return h.hexdigest()
read=lambda name:json.loads((O/name).read_text())
prior_path=O/'pipeline-ae-package.json';prior=read(prior_path.name)
assert len(prior)==6 and all(v['rc']==0 for v in prior[:5]) and prior[-1]['step']=='negatives' and prior[-1]['rc']==1
assert [v['step'] for v in prior[:5]]==['surface','stage-compile','package-gates','painted','wrp-readback']
old_chain=read('forest-ae-validated-chain.json');assert old_chain['status']=='FAILED'
repair=read('forest-ae-import-repair.json');wrapper=O/'run-final-forest-negatives-ae-importfix.py'
assert repair['status']=='IMPORT_CHECK_PASS' and repair['wrapper_sha256']==sha(wrapper)
assert sha(repair['original_failure_log'])==repair['original_failure_log_sha256']
assert not (O/'forest-final-negatives-ae').exists() and not (O/'forest-holdout-ae-reservation.json').exists()
frozen=read('forest-ae-frozen.json');validation=read('forest-validation-inputs.json');binding=read('forest-ae-runner-bindings.json')
wrp=read('wrp-readback-ae/result.json');assert wrp['result']==wrp['forest']['result']==wrp['staged']['result']=='PASS'
package=read('package-final-ae/package.json');report=read('forest-map-51ae/report.json')
assert sha(package['pbo'])==package['pbo_sha256']==wrp['inputs']['pbo']['sha256']
assert sha(O/'forest-map-51ae/records.json')==report['records_sha256']
backup=O/'pipeline-ae-package.attempt1-import-failure.json';assert not backup.exists();backup.write_bytes(prior_path.read_bytes())
base=dict(scope=__doc__,runner_sha256=sha(__file__),original_pipeline_failure=str(backup),original_pipeline_failure_sha256=sha(backup),original_chain_failure_sha256=sha(O/'forest-ae-validated-chain.json'),import_repair_receipt_sha256=sha(O/'forest-ae-import-repair.json'),wrapper_sha256=sha(wrapper),frozen_manifest_sha256=sha(O/'forest-ae-frozen.json'),runner_bindings_sha256=sha(O/'forest-ae-runner-bindings.json'),source_sha256=report['tool_sha256'],records_sha256=report['records_sha256'],pbo_sha256=package['pbo_sha256'],successful_prefix_steps=5,release_acceptance=False)
steps=[]
def save(status,**extra):
 out.write_text(json.dumps(dict(base,status=status,steps=steps,**extra),indent=2)+'\n')
def check_files():
 assert all(sha(p)==h for p,h in frozen['files'].items())
 assert all(sha(p)==h for p,h in validation['files'].items())
 assert all(sha(v['path'])==v['sha256'] for v in binding['runners'])
 assert all(sha(p)==h for p,h in binding['literal_script_dependencies'].items())
 assert sha(O/'run-forest-holdout-ae.py')==binding['holdout_script_sha256']
 assert sha(wrapper)==base['wrapper_sha256'] and sha(O/'forest-ae-import-repair.json')==base['import_repair_receipt_sha256']
def run(name,args,pipeline):
 check_files();cmd=[sys.executable,'-I',*map(str,args)];start=time.time();print('START',name,flush=True)
 with (O/f'forest-ae-resume-{name}.log').open('w',encoding='utf-8') as f:
  rc=subprocess.run(cmd,cwd=O,stdout=f,stderr=subprocess.STDOUT).returncode
 row=dict(step=name,rc=rc,seconds=time.time()-start,cmd=cmd,continuation=str(out))
 steps.append(row)
 if pipeline:prior_path.write_text(json.dumps(prior[:5]+steps,indent=2)+'\n')
 save('RUNNING',current=name);print('END',name,rc,flush=True);assert rc==0,row
try:
 save('RUNNING')
 run('negatives',[wrapper],True)
 run('rim-counts',[O/'audit-final-rim-counts.py',O/'forest-map-51ae',O/'forest-painted-rasters-ae',O/'final-rim-counts-ae.json'],True)
 run('renders',[O/'render-final-forest-ae.py',O/'forest-painted-rasters-ae',O/'forest-final-renders-ae'],True)
 assert len(read('pipeline-ae-package.json'))==8 and all(v['rc']==0 for v in read('pipeline-ae-package.json'))
 run('fresh-diagnostics',[O/'audit-forest-r2-diagnostics.py',O/'forest-map-51ae',O/'forest-painted-rasters-ae',O/'forest-r2-diagnostics-ae-painted'],False)
 check_files();assert sha(package['pbo'])==package['pbo_sha256']
 save('MEASURED_AWAITING_VISUAL_INSPECTION_AND_FRESH_HOLDOUTS')
except BaseException as e:
 save('FAILED',error=repr(e));raise
print('Pending validation completed; inspect actual renders before reserving fresh seeds.',flush=True)
