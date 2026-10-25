"""Deploy the exact four-vertex correction into a fresh mod after affected gates.

Baseline evidence remains historical. This grants only offline readiness for OT7;
it never turns historical phase failures, concrete joints or runtime into PASS.
"""
from pathlib import Path
import hashlib,json,shutil
O=Path(__file__).parent;D=O/'water-fix-b'
MOD=Path('P:/Mods/@DayZ_Baltic_EV112_RuntimeMarginsV2')
WT=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
evidence={}
def read(p):
 p=O/p;evidence[str(p)]=sha(p);return json.loads(p.read_text(encoding='utf-8'))
def steps(p,n):
 d=read(p);s=d['steps'] if isinstance(d,dict) else d
 assert len(s)==n and all(v['rc']==0 for v in s),p;return s
out=O/'deploy-runtime-b.json';assert not MOD.exists() and not out.exists()
old=read('deploy.json');assert old['offline_status']=='PASS' and old['forest_tag']=='ae'
assert all(sha(p)==h for p,h in old['evidence'].items()),'baseline evidence drift'
for name,key in [('narva_trial.pbo','world_sha256'),('baltic_water_v30.pbo','water_sha256')]:
 assert sha(Path(old['mod'])/'Addons'/name)==old[key]
closure=read('water-fix-b/terrain-closure.json')
assert closure['status']=='PASS_AFFECTED_OFFLINE_TERRAIN_CONSUMERS' and all(closure['checks'].values())
assert all(sha(p)==h for p,h in closure['evidence'].items())
assert sha(D/'terrain.npz')==closure['terrain_sha256']=='07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62'
assert closure['regenerated_footprint_sha256']==old['footprint_sha256']==sha(D/'bury-work/fp0/footprint.npz')
steps('water-fix-b/build-steps.json',3);steps('water-fix-b/package-chain.json',3)
for p in ('water-fix-b/forest-g1-resume-execution.json','water-fix-b/forest-g4-execution.json'):
 assert read(p)['rc']==0
sp=steps('runtime-b-package-steps.json',7);assert all(v['result']=='PASS' for v in sp if v['step']!='pack')
ps=steps('forest-painted-runtime-b-steps.json',5);assert {v['step'] for v in ps}=={'g2g3','g8','g7','g2pilot','g3pilot'}
for p in ('g2g3-painted.json','g8-painted.json','g7-painted.json','g2pilot-painted.json','g3pilot-painted.json'):read('water-fix-b/'+p)
source=WT/'tools/terrain/apply_engine_water_margins_v31.py'
assert sha(source)=='e024c5edea15248c7fffcc3b7555e5107b0b0ac299c1f5f048aaddf784e20743';evidence[str(source)]=sha(source)
world=O/'package-runtime-b/packed/narva_trial.pbo';water=O/'water-prepared-fp49ee/baltic_water_v30.pbo'
pack=read('package-runtime-b/package.json');build=read('runtime-b-build-binding.json')
assert sha(world)==pack['pbo_sha256'] and sha(pack['manifest'])==pack['manifest_sha256']
assert read('forest-painted-runtime-b-steps.json')['pbo_sha256']==sha(world)
manifest=json.loads(Path(pack['manifest']).read_text())
assert pack['changed_entries']==sorted(manifest['changed_entries']+['baltic_trial.wrp'])
assert sha(pack['base_pbo'])==pack['base_pbo_sha256']==old['base_world_sha256']
assert sha(pack['wrp_from'])==pack['wrp_from_sha256']==build['compiled_pbo_sha256']
assert build['terrain_sha256']==closure['terrain_sha256'] and all(build['stage_checks'].values())
assert build['surface_manifest_sha256']==pack['manifest_sha256']
wrp=read('wrp-readback-runtime-b/result.json')
assert wrp['result']=='PASS' and wrp['forest']['result']=='PASS' and wrp['staged']['result']=='PASS'
assert wrp['inputs']['pbo']['sha256']==sha(world) and wrp['compiled_wrp_sha256']==build['compiled_wrp_sha256']
assert wrp['inputs']['staged']['sha256']==build['staged_wrp_sha256']==sha(wrp['inputs']['staged']['path'])
assert sha(O/'forest-map-51ae/records.json')==old['forest_records_sha256'] and wrp['forest']['count']==old['forest_instances']
assert sha(water)==old['water_sha256']
probe=read('probe-runtime-b/manifest.json');assert probe['points']==4114 and all(sha(p)==h for p,h in probe['inputs'].items())
assert sha(O/'probe-runtime-b/points.csv')==sha(O/'probe-c/points.csv')
probe_binding={str(O/'probe-runtime-b'/n):sha(O/'probe-runtime-b'/n) for n in ('points.json','points.csv','families.json','bridges-points.json','shores-points.json','dam-points.json','manifest.json')}
probe_binding[str(O/'evaluate-runtime-probe-runtime-b.py')]=sha(O/'evaluate-runtime-probe-runtime-b.py')
for p,h in read('probe-c/manifest.json')['inputs'].items():assert sha(p)==h
addons=MOD/'Addons';addons.mkdir(parents=True,exist_ok=False)
for p in (world,water):
 target=addons/p.name;shutil.copyfile(p,target);assert sha(target)==sha(p)
receipt=dict(schema='ev112-runtime-margins-deploy.v1',mod=str(MOD),forest_tag='ae',terrain_revision='runtime-b',world_sha256=sha(addons/world.name),water_sha256=sha(addons/water.name),terrain_sha256=closure['terrain_sha256'],footprint_sha256=old['footprint_sha256'],compiled_wrp_sha256=build['compiled_wrp_sha256'],forest_records_sha256=old['forest_records_sha256'],forest_instances=old['forest_instances'],base_world=pack['base_pbo'],base_world_sha256=pack['base_pbo_sha256'],changed_entries=pack['changed_entries'],evidence=evidence,probe_binding=probe_binding,baseline_deploy_sha256=sha(O/'deploy.json'),offline_status='PASS_AFFECTED_CONSUMERS_WITH_INHERITED_BASELINE',independent_build_review='PENDING_R2',server_probe='NOT_RUN_ON_THIS_PACKAGE',personal_view='PREPARED_NOT_ACCEPTED',protected_exception_01545='60m disk PENDING; never PASS',limits=closure['limits'])
out.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ('mod','world_sha256','water_sha256','terrain_sha256','offline_status')}))
