"""Current task: after45 known PASS, freeze and validate full map, partition and compiled surface.

No fresh holdout reservation, source promotion, review, deployment or DayZ lifecycle.
Every dependency remains gated by actual receipts; a failure ends this chain.
"""
from pathlib import Path
import concurrent.futures,hashlib,json,subprocess,sys,time
O=Path(__file__).parent;started=time.time();steps=[];frozen=None;runner_binding=None
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=sha(O/'forest-candidate-ae/forest_v31.py')
out=O/'forest-ae-validated-chain.json'
if out.exists():
    prior=json.loads(out.read_text())
    assert sys.argv[1:]==['--resume-wait'] and prior['status']=='WAITING_45_KNOWN' and prior['steps']==[]
    assert not (O/'forest-ae-frozen.json').exists()
    backup=O/'forest-ae-validated-chain.before-wait-fix.json';assert not backup.exists();backup.write_bytes(out.read_bytes())
def state(status,**extra):
    out.write_bytes((json.dumps(dict(scope=__doc__,status=status,source_sha256=source,steps=steps,**extra),indent=2)+'\n').encode())
def read(name):
    try:return json.loads((O/name).read_text())
    except (FileNotFoundError,json.JSONDecodeError):return None
def check_files():
    assert sha(O/'forest-candidate-ae/forest_v31.py')==source
    if frozen:
        assert all(sha(p)==h for p,h in frozen['files'].items())
    if runner_binding:
        assert all(sha(r['path'])==r['sha256'] for r in runner_binding['runners'])
        assert all(sha(p)==h for p,h in runner_binding['literal_script_dependencies'].items())
        assert sha(O/'run-forest-holdout-ae.py')==runner_binding['holdout_script_sha256']
def check_steps(name,count,exception=None,partial=False):
    obj=read(name)
    if obj is None:
        assert partial,name
        return False
    rows=obj['steps'] if isinstance(obj,dict) else obj
    assert all(r['rc']==0 for r in rows if r['step']!=exception),(name,'FAIL')
    if not partial:assert len(rows)==count,(name,len(rows),count)
    return len(rows)>=count if partial else len(rows)==count
def run(name,args):
    check_files();t=time.time();cmd=[sys.executable,'-I',*map(str,args)]
    print('START',name,flush=True)
    with (O/f'forest-ae-chain-{name}.log').open('w',encoding='utf-8') as f:
        rc=subprocess.run(cmd,cwd=O,stdout=f,stderr=subprocess.STDOUT).returncode
    result=dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd)
    print('END',name,rc,flush=True)
    return result
def serial(name,args):
    r=run(name,args);steps.append(r);state('RUNNING',current=name);assert r['rc']==0,r
try:
    state('WAITING_45_KNOWN');print('Waiting for45actual known stages',flush=True)
    while True:
        ready=True
        for seed in (171,172,173,22,144,31,165,162,51):
            name=f'forest-ae-{seed}-regression-steps.json'
            ready=check_steps(name,5,partial=True) and ready
            obj=read(name)
            if obj:assert obj['source_sha256']==source
        if ready:break
        assert time.time()-started<7200,'Known regression wait exceeded two hours'
        time.sleep(10)
    serial('calibration-controls',[O/'check-ae-calibration.py',O/'forest-development-ae-calibrated172',O/'forest-candidate-ae',O/'forest-ae-calibration-controls.json'])
    serial('halo-control',[O/'check-ae-halo-cli.py'])
    serial('freeze',[O/'prepare-forest-ae-validation.py'])
    frozen=read('forest-ae-frozen.json');assert len(frozen['files'])==38
    lint=read('forest-ae-preparer-lint.json');assert lint['status']=='PASS'
    assert lint['preparer_sha256']==sha(O/'prepare-forest-ae-validation.py')
    assert all(sha(O/name)==h for name,h in lint['generated_scripts'].items())
    serial('bindings',[O/'audit-forest-runner-bindings.py','ae'])
    runner_binding=read('forest-ae-runner-bindings.json');assert runner_binding['status']=='PASS'
    receipt=O/'forest-ae-validation-prepared.json';assert not receipt.exists()
    receipt.write_text(json.dumps(dict(status='PREPARED_AFTER_45_KNOWN_PASS',scope=__doc__,source_sha256=source,preparer_sha256=sha(O/'prepare-forest-ae-validation.py'),runner_manifest_sha256=sha(O/'forest-ae-runners.json'),binding_sha256=sha(O/'forest-ae-runner-bindings.json'),frozen_sha256=sha(O/'forest-ae-frozen.json'),known_steps_sha256=sha(O/'forest-ae-all-known-steps.json')),indent=2)+'\n')
    state('FULL_MAP_RUNNING')
    # Only map until final placement is complete. Independent guide audit and
    # partition may then run while the remaining map consumers finish.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        map_future=pool.submit(run,'map',[O/'run-final-forest-map-ae.py'])
        t=time.time()
        while not check_steps('forest-map-51ae-steps.json',1,'g8-unpainted',partial=True):
            if map_future.done():assert map_future.result()['rc']==0,'map failed before placement receipt'
            assert time.time()-t<7200,'Full placement exceeded two hours'
            time.sleep(10)
        serial('guide',[O/'audit-accepted-canopy-records.py',O/'forest-map-51ae',O/'forest-final-tools-ae',O/'forest-ae-map-canopy-binding.json'])
        serial('partition',[O/'run-partition-ae250.py'])
        result=map_future.result();steps.append(result);assert result['rc']==0,result
    check_steps('forest-map-51ae-steps.json',13,'g8-unpainted')
    check_steps('partition-ae250-steps.json',2)
    serial('nonbush-identity',[O/'compare-forest-nonbush-records.py',O/'forest-map-51ad',O/'forest-map-51ae',O/'forest-ae-map-nonbush-identity.json'])
    serial('painted-development',[O/'run-ae-painted-development-diagnostic.py'])
    serial('build-tools-preflight',[O/'refresh-build-tools-preflight.py'])
    serial('package',[O/'run-ae-dependent-pipeline.py','package'])
    check_steps('pipeline-ae-package.json',8)
    check_steps('forest-painted-ae-steps.json',5)
    check_steps('final-package-ae-steps.json',7)
    serial('fresh-diagnostics',[O/'audit-forest-r2-diagnostics.py',O/'forest-map-51ae',O/'forest-painted-rasters-ae',O/'forest-r2-diagnostics-ae-painted'])
    check_files()
    state('MEASURED_AWAITING_VISUAL_INSPECTION_AND_FRESH_HOLDOUTS')
except BaseException as e:
    state('FAILED',error=repr(e));raise
print('Compiled consumers and fresh diagnostics complete; inspect renders before continuing. No holdouts reserved or deployment.',flush=True)
