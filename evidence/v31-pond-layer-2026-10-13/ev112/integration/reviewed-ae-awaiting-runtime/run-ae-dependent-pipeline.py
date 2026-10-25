"""Current-session dependent jobs for frozen AE; abort on every reported prerequisite failure."""
from pathlib import Path
import sys,json,subprocess,time,hashlib
O=Path(__file__).parent;lane=sys.argv[1];assert lane=='package';rows=[]
def read_steps(name):
 try:
  d=json.loads((O/name).read_text());return d['steps'] if isinstance(d,dict) else d
 except (FileNotFoundError,json.JSONDecodeError):return None
def no_failures():
 for name in ('forest-map-51ae-steps.json','forest-development-ae-final-steps.json','forest-original-regressions-ae-steps.json','partition-ae250-steps.json','forest-holdout-ae-steps.json'):
  steps=read_steps(name)
  if steps is not None:assert all(s['rc']==0 for s in steps if s['step']!='g8-unpainted'),(name,[(s['step'],s['rc']) for s in steps])
def wait_ready(prerequisites):
 start=time.time();print('Waiting',prerequisites,flush=True)
 while True:
  no_failures();ready=True
  for name,count in prerequisites:
   steps=read_steps(name);ready &= steps is not None and len(steps)>=count
  if ready:return
  assert time.time()-start<3600,'Prerequisite wait exceeded one hour'
  time.sleep(10)
def run(name,args):
 no_failures();cmd=[sys.executable,'-I',*map(str,args)];start=time.time();print('START',name,flush=True)
 with (O/f'pipeline-ae-{lane}-{name}.log').open('w',encoding='utf-8') as out:
  rc=subprocess.run(cmd,cwd=O,stdout=out,stderr=subprocess.STDOUT).returncode
 rows.append(dict(step=name,rc=rc,seconds=time.time()-start,cmd=cmd))
 (O/f'pipeline-ae-{lane}.json').write_bytes((json.dumps(rows,indent=2)+'\n').encode());print('END',name,rc,flush=True)
 if rc:sys.exit(rc)
full=[('forest-map-51ae-steps.json',13),('forest-development-ae-final-steps.json',10),('forest-original-regressions-ae-steps.json',10),('forest-ae-all-known-steps.json',45)]
wait_ready(full)
for name in ('surface','stage-compile','package-gates','painted'):
 script={'surface':'run-final-surface-ae.py','stage-compile':'run-stage-compile-ae.py','package-gates':'run-final-package-gates-ae.py','painted':'run-painted-forest-ae.py'}[name]
 run(name,[O/script])
run('wrp-readback',[O/'audit-wrp-readback-v2.py','--pbo',O/'package-final-ae/packed/narva_trial.pbo','--staged',O/'stage-forest-ae/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp','--records',O/'forest-map-51ae/records.json','--forest-report',O/'forest-map-51ae/report.json','--out',O/'wrp-readback-ae'])
run('negatives',[O/'run-final-forest-negatives-ae.py'])
run('rim-counts',[O/'audit-final-rim-counts.py',O/'forest-map-51ae',O/'forest-painted-rasters-ae',O/'final-rim-counts-ae.json'])
run('renders',[O/'render-final-forest-ae.py',O/'forest-painted-rasters-ae',O/'forest-final-renders-ae'])
print('Finished',lane,'dependent steps; independent review/runtime/personal acceptance not implied',flush=True)
