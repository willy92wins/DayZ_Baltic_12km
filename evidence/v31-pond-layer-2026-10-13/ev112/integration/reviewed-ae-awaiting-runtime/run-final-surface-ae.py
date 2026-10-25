from pathlib import Path
import sys,json,subprocess,time,hashlib
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=O/'forest-final-tools-ae';sys.path.insert(0,str(D/'gates'));import gcfg as C
R=O/'forest-map-51ae';steps=json.loads((O/'forest-map-51ae-steps.json').read_text())['steps'];assert len(steps)==13 and all(s['rc']==0 for s in steps if s['step']!='g8-unpainted')
report=json.loads((R/'report.json').read_text());moss=R/'work/moss1m.npy';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(moss)==report['work_sha256']['moss1m.npy'];assert sha(R/'records.json')==report['records_sha256'];runs=[]
def run(name,args):
 cmd=[sys.executable,'-I',*map(str,args)];t=time.time()
 with (O/f'final-ae-surface-{name}.log').open('w',encoding='utf-8') as f:rc=subprocess.run(cmd,cwd=P,stdout=f,stderr=subprocess.STDOUT).returncode
 runs.append(dict(step=name,rc=rc,seconds=time.time()-t,cmd=cmd));(O/'final-ae-surface-steps.json').write_bytes((json.dumps(runs,indent=2)+'\n').encode());print(name,rc,round(time.time()-t,1),flush=True)
 if rc:sys.exit(rc)
assert sha(O/'surface-trial-clearings400/make_forest_clearings_v31.py')=='59c493791bac9542ccc43bf6c36a08da551e48d54216639ccc1c12d0c1a273d4'
run('clearings',[O/'surface-trial-clearings400/make_forest_clearings_v31.py',R/'records.json',C.REFERENCE,O/'forest-final-rasters-c',O/'clearings-final-ae','--moss',moss,'--moss-sha256',report['work_sha256']['moss1m.npy']])
m=json.loads((O/'clearings-final-ae/manifest.json').read_text())
planned=report['planned_clearings'];assert m['mask_sha256']==sha(m['mask'])==planned['sha256']==sha(planned['path'])
assert planned['points_sha256']==report['accepted_canopy']['points']['sha256']
dry=json.loads((O/'dam-dry-bed-binding.json').read_text());assert sha(dry['path'])==dry['sha256']
binding=dict(terrain=dict(path=str(C.TERRAIN),sha256=sha(C.TERRAIN)),clearings=dict(path=m['mask'],sha256=m['mask_sha256']),include_names=['v31_causeway','v31_dam'],include_pad_cells=1,explicit_native_cells=dry)
(O/'surface-scope-ae-binding.json').write_bytes((json.dumps(binding,indent=2)+'\n').encode())
# Full-map clearings reach older EV95 packed tiles; every source still requires exact sibling PAA bytes.
base_layers=['E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/build-wide-slope/surface/layers','E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/surface/layers','E:/DayZ-Baltic-Build/v30-complete-dry-surface-20261009/surface/layers','E:/DayZ-Baltic-Build/v30-mixed-bank-constrained-20261010/surface/layers']
run('patch',[P/'tools/terrain/patch_surface_v31.py',C.TERRAIN,O/'surface-final-ae','--footprint',C.FOOTPRINT,'--workers','2','--include-changed','v31_causeway','--include-changed','v31_dam','--include-pad','1','--include-cells',dry['path'],'--include-cells-sha256',dry['sha256'],'--forest-clearings',m['mask'],'--forest-clearings-sha256',m['mask_sha256'],'--base-layers',';'.join(base_layers)])
