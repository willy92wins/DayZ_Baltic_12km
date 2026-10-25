"""Archive the completed EV94 build; native/render acceptance stays pending."""
from pathlib import Path
import hashlib,json,shutil
G=Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
B=G/'build-focal'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-global-bank-extension-2026-10-10/focal-build-checkpoint'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
manifest=json.loads((B/'source-manifest.json').read_text())
sources=[]
for row in manifest['source_files']:
    p=Path(row['path']);assert sha(p)==row['sha256'];sources.append((p,p.name))
for name in ['source-manifest.json','stage.json','surface-verification.json','deploy.json',
             'op_rw_verification.json','changed-mips.json','native-reference.json','native-probe-lint.json',
             'runtime-bank-precheck.json','surface-generation.log','filebank.log']:
    sources.append((B/name,name))
sources.append((Path(__file__),Path(__file__).name))
assert len({name for _,name in sources})==len(sources)
required={'surface-verification.json':'PASS_EV94_AFFECTED_SURFACE','op_rw_verification.json':'PASS_EV94_PACKAGED_OPRW_IDENTITY','changed-mips.json':'PASS_EV94_ALL_CHANGED_MIPS'}
for name,status in required.items():assert json.loads((B/name).read_text())['status']==status
deploy=json.loads((B/'deploy.json').read_text())
references=[]
for name,digest in deploy['files'].items():
    p=Path(deploy['mod'])/'Addons'/name
    assert sha(p)==digest
    references.append({'path':str(p),'sha256':digest,'bytes':p.stat().st_size})
for p in [B/'candidate/terrain.npz',B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp',
          B/'mission/init.c']:
    if p.is_file(): references.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
assert all(p.stat().st_size < 8*1024**2 for p,_ in sources)
before={name:sha(p) for p,name in sources}
D.mkdir(parents=True,exist_ok=False)
rows=[]
for p,name in sources:
    dest=D/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,dest);assert sha(dest)==sha(p)==before[name]
    rows.append({'source':str(p),'relative_path':name,'sha256':before[name],'bytes':p.stat().st_size})
r={'status':'EV94_BUILD_OFFLINE_PASS_NATIVE_PENDING','copied_files':rows,'large_references':references,
   'candidate_sha256':deploy['terrain_sha256'],'world_pbo_sha256':deploy['files']['narva_trial.pbo'],
   'compiled_wrp_sha256':deploy['compiled_wrp_sha256'],'surface_tiles':deploy['surface_selected_tiles'],
   'changed_paa':len(deploy['changed_texture_entries']),'native_acceptance':False,'visual_acceptance':False,
   'global_contract_status':'OPEN_INHERITED_MAP_DEFECTS',
   'runtime_blocker':'Foreign @LFSkateboard profiles-130 owns the test box; no lease acquired and no processes touched.'}
(D/'manifest.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':r['status'],'copied':len(rows),'references':len(references)}))
