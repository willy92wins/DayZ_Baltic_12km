from pathlib import Path
import sys,json,subprocess,time,hashlib
O=Path(__file__).parent;D=O/'forest-final-tools-ae';sys.path.insert(0,str(D/'gates'));import gcfg as C
P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=O/'partition-ae250';assert not R.exists()
base=O/'forest-map-51ae';frozen=json.loads((O/'forest-ae-frozen.json').read_text())['files']
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in frozen.items())
region='7600,4300,10800,7950';a=[D/'forest_v31.py','--terrain',C.TERRAIN,'--footprint',C.FOOTPRINT,'--stage-wrp',C.STAGE_WRP,'--pbo',C.PBO,'--exclude',C.EXCLUSIONS]
for ld in C.LAYER_DIRS:a+=['--layer-dir',ld]
a+=['--cover',C.LAYERS,'--reference',C.REFERENCE,'--seed','51','--out',R,'--region',region,'--workers','4','--tile','250','--calibration',base/'report.json']
steps=[('place',a),('g9',[D/'gates/g9_seams.py',base/'records.json','500',O/'partition-ae250-g9.json','--region',region,'--compare',R/'records.json','--compare-tile','250'])];rec=[]
for name,args in steps:
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in frozen.items())
 cmd=[sys.executable,'-I',*map(str,args)];t=time.time()
 with (O/('partition-ae250-'+name+'.log')).open('w',encoding='utf-8') as f:rc=subprocess.run(cmd,cwd=P,stdout=f,stderr=subprocess.STDOUT).returncode
 rec.append(dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd));(O/'partition-ae250-steps.json').write_bytes((json.dumps(dict(frozen_manifest_sha256=hashlib.sha256((O/'forest-ae-frozen.json').read_bytes()).hexdigest(),steps=rec),indent=2)+'\n').encode());print(name,rc,round(time.time()-t,1),flush=True)
 if rc:sys.exit(rc)
