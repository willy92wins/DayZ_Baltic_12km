"""One frozen AE development candidate. Stop before the next pair after any failure."""
from pathlib import Path
import sys,json,subprocess,concurrent.futures,hashlib
O=Path(__file__).parent;results=[];source=hashlib.sha256((O/'forest-candidate-ae/forest_v31.py').read_bytes()).hexdigest()
def run(seed):
    rc=subprocess.run([sys.executable,'-I',str(O/'run-forest-ae-regression.py'),str(seed)]).returncode
    p=O/f'forest-ae-{seed}-regression-steps.json';d=json.loads(p.read_text()) if p.exists() else {'steps':[]}
    ok=rc==0 and len(d['steps'])==5 and all(v['rc']==0 for v in d['steps']) and d['source_sha256']==source
    print('KNOWN COMPLETE',seed,'PASS' if ok else 'FAIL',flush=True)
    return dict(seed=seed,rc=rc,all_gates_pass=ok)
for pair in ((171,172),(173,22),(144,31),(165,162),(51,)):
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:batch=list(ex.map(run,pair))
    results.extend(batch)
    (O/'forest-ae-known-driver.json').write_text(json.dumps(dict(scope=__doc__,source_sha256=source,results=results),indent=2)+'\n')
    if not all(v['all_gates_pass'] for v in batch):raise SystemExit(1)
