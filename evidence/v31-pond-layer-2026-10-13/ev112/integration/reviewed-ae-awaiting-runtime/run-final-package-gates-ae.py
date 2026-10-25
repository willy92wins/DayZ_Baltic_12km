from pathlib import Path
import os,sys,json,subprocess,time,hashlib
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=O/'surface-gates-b'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();runs=[]
def run(name,args,verdict=None):
 t=time.time();cmd=[sys.executable,'-I',*map(str,args)]
 with (O/f'final-package-ae-{name}.log').open('w',encoding='utf-8') as f:rc=subprocess.run(cmd,cwd=P,stdout=f,stderr=subprocess.STDOUT).returncode
 result=json.loads((O/'surface-gates-ae-results'/verdict).read_text())['result'] if verdict and rc==0 else None
 runs.append(dict(step=name,rc=rc,result=result,seconds=time.time()-t,cmd=cmd));(O/'final-package-ae-steps.json').write_bytes((json.dumps(runs,indent=2)+'\n').encode());print(name,rc,result,round(time.time()-t,1),flush=True)
 if rc or (verdict and result!='PASS'):sys.exit(rc or 1)
assert all(v['rc']==0 for v in json.loads((O/'final-ae-stage-compile.json').read_text()))
assert all(v['rc']==0 for v in json.loads((O/'final-ae-surface-steps.json').read_text()))
run('pack',[P/'tools/terrain/package_surface_patch_v31.py',O/'surface-final-ae/manifest.json',O/'package-final-ae','--wrp-from',O/'stage-forest-ae/out/narva_trial.pbo'])
os.environ.update(SURFACE_GATE_ROOT=str(O),SURFACE_PATCH_DIR=str(O/'surface-final-ae'),SURFACE_PACKAGE_DIR=str(O/'package-final-ae'),SURFACE_GATE_OUT=str(O/'surface-gates-ae-results'),SURFACE_TARGET_TERRAIN=str(O/'terrain-ev112-c.npz'),SURFACE_TARGET_TERRAIN_SHA256=sha(O/'terrain-ev112-c.npz'),SURFACE_EV112_BINDING=str(O/'surface-scope-ae-binding.json'))
sys.path.insert(0,str(D));import gate_lib as G
wrp=G.Pbo(O/'stage-forest-ae/out/narva_trial.pbo').read('baltic_trial.wrp');assert wrp[:4]==b'OPRW';os.environ['SURFACE_TARGET_WRP_SHA256']=hashlib.sha256(wrp).hexdigest()
prefix=[]
with (O/'stage-forest-ae-report.json').open(encoding='utf-8') as f:
 for line in f:
  if line.lstrip().startswith('"added": ['):break
  prefix.append(line)
 else:raise ValueError('stage report missing added list')
stage=json.loads(''.join(prefix).rstrip().rstrip(',')+'\n}')
assert all(stage['checks'].values()) and stage['terrain_sha256']==sha(O/'terrain-ev112-c.npz')
assert stage['wrp_sha256']==sha(O/'stage-forest-ae/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp')
binding=dict(terrain_sha256=stage['terrain_sha256'],stage_checks=stage['checks'],staged_wrp_sha256=stage['wrp_sha256'],compiled_wrp_sha256=os.environ['SURFACE_TARGET_WRP_SHA256'],compiled_wrp_version=int.from_bytes(wrp[4:8],'little'),compiled_pbo_sha256=sha(O/'stage-forest-ae/out/narva_trial.pbo'),surface_manifest_sha256=sha(O/'surface-final-ae/manifest.json'))
(O/'final-ae-build-binding.json').write_bytes((json.dumps(binding,indent=2)+'\n').encode());del wrp
for name,script,verdict in [('g1','g1_default_identity.py','G1_default_identity.json'),('g2','g2_road_paint.py','G2_road_paint.json'),('g3','g3_overlaps.py','G3_overlaps.json'),('g4','g4_outside.py','G4_outside_zone.json'),('g5','g5_manifest.py','G5_manifest.json'),('g6','g6_dry_dam_bed.py','G6_dry_dam_bed.json')]:run(name,[D/script],verdict)
