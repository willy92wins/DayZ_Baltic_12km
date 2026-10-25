"""AE development only. Both tree and bush calibration/placement stages are new."""
from pathlib import Path
import sys,json,subprocess,time,hashlib
O=Path(__file__).parent;D=O/'forest-candidate-ae';sys.path.insert(0,str(D/'gates'));import gcfg as C
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
seed=int(sys.argv[1]);assert seed in (171,172,173,22,144,31,165,162,51)
source=sha(D/'forest_v31.py');rows=[];R=O/f'forest-development-ae-calibrated{seed}';assert not R.exists()
a=[O/'run-forest-known-cache-v5.py',D,'--terrain',C.TERRAIN,'--footprint',C.FOOTPRINT,'--stage-wrp',C.STAGE_WRP,'--pbo',C.PBO,'--exclude',C.EXCLUSIONS]
for ld in C.LAYER_DIRS:a+=['--layer-dir',ld]
a+=['--cover',C.LAYERS,'--reference',C.REFERENCE,'--seed',str(seed),'--out',R,'--region','7600,4300,10800,7950','--workers','4']
steps=[('place',a),('subset',[D/'gates/pilot_subset.py',R/'records.json',R/'pilot-subset.json']),('g2',[C.R2_GATES/'g2_g3.py',R/'pilot-subset.json','G2','--dense','A-reserva','--json',R/'g2.json']),('g3',[C.R2_GATES/'g2_g3.py',R/'pilot-subset.json','G3','--json',R/'g3.json']),('g7',[C.R2_GATES/'g7_bog.py',R/'pilot-subset.json','--json',R/'g7.json'])]
for name,args in steps:
    assert sha(D/'forest_v31.py')==source
    cmd=[sys.executable,'-I',*map(str,args)];t=time.time()
    with (O/f'forest-development-ae-{seed}-{name}.log').open('w') as f:
        rc=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT).returncode
    rows.append(dict(seed=seed,step=name,rc=rc,seconds=time.time()-t,cmd=cmd))
    (O/f'forest-ae-{seed}-regression-steps.json').write_text(json.dumps(dict(scope=__doc__,source_sha256=source,steps=rows),indent=2)+'\n')
    print(seed,name,rc,round(time.time()-t,1),flush=True)
    if rc and name in ('place','subset'):sys.exit(rc)
sys.exit(0 if all(r['rc']==0 for r in rows) else 1)
