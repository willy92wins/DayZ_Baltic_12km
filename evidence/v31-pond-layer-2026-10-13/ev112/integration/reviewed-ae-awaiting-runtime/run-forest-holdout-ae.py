"""Ten unseen seeds after frozen development/map/partition acceptance; at most three jobs.

Each placement runs a fresh global prepass and fresh nonbush and bush calibration/placement stages.
Stop dispatching on the first failure; already-running seed finishes its own checks.
No source, bands, seed selection or acceptance changes during the reserved run.
"""
from pathlib import Path
import sys,json,subprocess,time,hashlib,re,threading
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
O=Path(__file__).parent;tag=sys.argv[1];assert tag=='ae'
D=O/f'forest-final-tools-{tag}';sys.path.insert(0,str(D/'gates'));import gcfg as C
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
frozen_path=O/f'forest-{tag}-frozen.json';frozen=json.loads(frozen_path.read_text())['files'];frozen_sha=sha(frozen_path)
validation_path=O/'forest-validation-inputs.json';validation=json.loads(validation_path.read_text())['files'];validation_sha=sha(validation_path)
assert all(sha(p)==h for p,h in validation.items())
for name,n,exception in ((f'forest-map-51{tag}-steps.json',13,'g8-unpainted'),(f'forest-development-{tag}-final-steps.json',10,None),(f'forest-original-regressions-{tag}-steps.json',10,None),(f'partition-{tag}250-steps.json',2,None)):
 steps=json.loads((O/name).read_text())['steps'];assert len(steps)==n and all(s['rc']==0 for s in steps if s['step']!=exception),name
known=json.loads((O/'forest-ae-all-known-steps.json').read_text());assert len(known['steps'])==45 and all(r['rc']==0 for r in known['steps'])
package=json.loads((O/'pipeline-ae-package.json').read_text());assert len(package)==8 and all(r['rc']==0 for r in package)
painted=json.loads((O/'forest-painted-ae-steps.json').read_text());assert len(painted['steps'])==5 and all(r['rc']==0 for r in painted['steps'])
guide=json.loads((O/'forest-ae-map-canopy-binding.json').read_text());assert guide['status']=='PASS' and guide['source_sha256']==sha(D/'forest_v31.py')
calibration=json.loads((O/'forest-ae-calibration-controls.json').read_text());assert calibration['status']=='PASS' and calibration['positive']==1 and calibration['negatives']==19 and calibration['source_sha256']==sha(D/'forest_v31.py')
identity=json.loads((O/'forest-ae-map-nonbush-identity.json').read_text());assert identity['status']=='NON_BUSH_IDENTICAL'
clearings=json.loads((O/'forest-painted-development-ae/binding.json').read_text());assert clearings['all_gates_pass'] and clearings['planned_mask_matches_independent']
seeds=list(range(181,191));reservation=O/f'forest-holdout-{tag}-reservation.json';assert not reservation.exists()
assert not any((O/f'forest-holdout-{tag}-seed{k}').exists() for k in seeds)
# Previous candidates may not have consumed this holdout under a different tag.
for p in O.glob('forest-holdout-*-reservation.json'):
 assert not set(json.loads(p.read_text())['seeds']) & set(seeds),p
assert all(sha(p)==h for p,h in frozen.items())
reservation.write_bytes((json.dumps(dict(status='RESERVED_BEFORE_EXECUTION',seeds=seeds,frozen_manifest_sha256=frozen_sha,parallel_seeds=3,workers_per_placement=2,acceptance='All ten original strict pilot G2/G3/G7 PASS; no tolerance or seed replacement.'),indent=2)+'\n').encode())
rows=[];lock=threading.Lock();failed=False
def record(row):
 with lock:
  rows.append(row)
  out=O/f'forest-holdout-{tag}-steps.json';tmp=out.with_suffix('.tmp')
  tmp.write_bytes((json.dumps(dict(scope=__doc__,frozen_manifest_sha256=frozen_sha,steps=rows),indent=2)+'\n').encode());tmp.replace(out)
def run_seed(seed):
 R=O/f'forest-holdout-{tag}-seed{seed}';assert not R.exists()
 args=[D/'forest_v31.py','--terrain',C.TERRAIN,'--footprint',C.FOOTPRINT,'--stage-wrp',C.STAGE_WRP,'--pbo',C.PBO,'--exclude',C.EXCLUSIONS]
 for ld in C.LAYER_DIRS:args+=['--layer-dir',ld]
 args+=['--cover',C.LAYERS,'--reference',C.REFERENCE,'--seed',str(seed),'--out',R,'--region','7600,4300,10800,7950','--workers','2']
 steps=[('place',args),('subset',[D/'gates/pilot_subset.py',R/'records.json',R/'pilot-subset.json']),('g2r2',[C.R2_GATES/'g2_g3.py',R/'pilot-subset.json','G2','--dense','A-reserva','--json',R/'g2r2.json']),('g3r2',[C.R2_GATES/'g2_g3.py',R/'pilot-subset.json','G3','--json',R/'g3r2.json']),('g7r2',[C.R2_GATES/'g7_bog.py',R/'pilot-subset.json','--json',R/'g7r2.json'])]
 for name,args in steps:
  assert sha(frozen_path)==frozen_sha and all(sha(p)==h for p,h in frozen.items())
  assert sha(validation_path)==validation_sha and all(sha(p)==h for p,h in validation.items())
  cmd=[sys.executable,'-I',*map(str,args)];start=time.time()
  with (O/f'forest-holdout-{tag}{seed}-{name}.log').open('w',encoding='utf-8') as out:
   rc=subprocess.run(cmd,cwd=O,stdout=out,stderr=subprocess.STDOUT).returncode
  record(dict(seed=seed,step=name,rc=rc,seconds=time.time()-start,cmd=cmd));print(seed,name,rc,flush=True)
  if rc:return False
 return True
next_seed=iter(seeds)
with ThreadPoolExecutor(max_workers=3) as pool:
 active={pool.submit(run_seed,next(next_seed)) for _ in range(3)}
 while active:
  done,active=wait(active,return_when=FIRST_COMPLETED)
  for f in done:
   if not f.result():failed=True
  if not failed:
   for _ in done:
    seed=next(next_seed,None)
    if seed is not None:active.add(pool.submit(run_seed,seed))
assert sha(frozen_path)==frozen_sha and all(sha(p)==h for p,h in frozen.items())
assert sha(validation_path)==validation_sha and all(sha(p)==h for p,h in validation.items())
passed=not failed and len(rows)==50 and all(s['rc']==0 for s in rows)
print('HOLDOUT', 'PASS' if passed else 'FAIL',len(rows),'steps',flush=True)
sys.exit(0 if passed else 1)
