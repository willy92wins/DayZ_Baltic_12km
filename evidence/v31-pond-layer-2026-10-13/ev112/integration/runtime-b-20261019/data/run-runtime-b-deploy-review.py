from pathlib import Path
import json,time,subprocess,sys
O=Path(__file__).parent;D=O/'water-fix-b';start=time.time()
while not (D/'package-chain.json').exists():
 for name in ('package-gates','painted','readback'):
  p=D/(name+'-chain-execution.json')
  if p.exists():assert json.loads(p.read_text())['rc']==0,name
 assert time.time()-start<2400,'Package validation wait exceeded budget'
 time.sleep(10)
for name in ('deploy-runtime-b.py','prepare-runtime-b-followup.py','run-review-runtime-b-r2.py'):
 r=subprocess.run([sys.executable,'-I',str(O/name)],cwd=O)
 assert r.returncode==0,(name,r.returncode)
