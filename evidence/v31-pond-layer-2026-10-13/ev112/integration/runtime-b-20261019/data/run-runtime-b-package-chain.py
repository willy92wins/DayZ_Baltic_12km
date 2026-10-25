from pathlib import Path
import json,time,subprocess,sys,concurrent.futures
O=Path(__file__).parent;D=O/'water-fix-b';start=time.time()
while not (D/'build-steps.json').exists():
 for n in ('stage','compile','surface'):
  p=D/(n+'-execution.json')
  if p.exists():assert json.loads(p.read_text())['rc']==0,n
 assert time.time()-start<1800,'Build wait exceeded budget'
 time.sleep(10)
assert all(r['rc']==0 for r in json.loads((D/'build-steps.json').read_text()))
assert json.loads((D/'forest-g1-resume-execution.json').read_text())['rc']==0
assert json.loads((D/'forest-g4-execution.json').read_text())['rc']==0
def run(name,args):
 t=time.time();cmd=[sys.executable,'-I',*map(str,args)]
 with (D/(name+'-chain.log')).open('w') as f:rc=subprocess.run(cmd,cwd=O,stdout=f,stderr=subprocess.STDOUT).returncode
 r=dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd);(D/(name+'-chain-execution.json')).write_text(json.dumps(r,indent=2)+'\n');print(name,rc,round(time.time()-t,1),flush=True);assert rc==0,name;return r
rows=[run('package-gates',[O/'run-runtime-b-package-gates.py'])]
tasks=[('painted',[O/'run-runtime-b-painted-forest.py']),('readback',[O/'audit-wrp-readback-v2.py','--pbo',O/'package-runtime-b/packed/narva_trial.pbo','--staged',O/'stage-runtime-b/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp','--records',O/'forest-map-51ae/records.json','--forest-report',O/'forest-map-51ae/report.json','--out',O/'wrp-readback-runtime-b'])]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows+=list(pool.map(lambda t:run(*t),tasks))
(D/'package-chain.json').write_text(json.dumps(rows,indent=2)+'\n');print('PACKAGE_VALIDATED_NOT_DEPLOYED',flush=True)
