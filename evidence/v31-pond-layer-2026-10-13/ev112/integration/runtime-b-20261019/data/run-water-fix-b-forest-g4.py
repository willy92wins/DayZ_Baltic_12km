from pathlib import Path
import subprocess,sys,json,time
O=Path(__file__).parent;D=O/'water-fix-b';cmd=[sys.executable,'-I',str(O/'forest-water-fix-b/gates/g4g5_map.py'),str(O/'forest-map-51ae/records.json'),'G4','--terrain',str(D/'terrain.npz')];t=time.time()
with (D/'forest-g4.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
out=dict(rc=r.returncode,seconds=time.time()-t,cmd=cmd);(D/'forest-g4-execution.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));sys.exit(r.returncode)
