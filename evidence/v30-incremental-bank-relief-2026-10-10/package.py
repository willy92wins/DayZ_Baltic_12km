"""Package EV80 heights and affected textures over the exact deployed EV79 artifact."""
from pathlib import Path
import sys, json, hashlib, subprocess, shutil, re

B=Path(__file__).parent; R=B.parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
blob_sha=lambda b:hashlib.sha256(b).hexdigest()
BASE=Path('P:/Mods/@DayZ_Baltic_MixedBankPreviewV1/Addons')
PREV=R/'v30-mixed-bank-constrained-20261010'
check=json.loads((B/'review-luna/report.json').read_text())
assert check['status']=='PASS_EV82_CONSUMER' and all(check['gates'].values())
assert sha(B/'candidate/terrain.npz')==check['candidate_sha256']=='f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0'
assert sha(PREV/'candidate/terrain.npz')=='0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
for name in ('plane.npy','visible-field.npy'):
    assert sha(B/'candidate'/name)==sha(PREV/'candidate'/name)
exposure=json.loads((B/'compiled-exposure.json').read_text())
assert exposure['status']=='PASS_COMPILED_EXPOSURE' and exposure['terrain_sha256']==check['candidate_sha256']
surface=json.loads((B/'surface-verification.json').read_text())
assert surface['status']=='PASS_EV82_AFFECTED_SURFACE' and all(surface['gates'].values()) and surface['terrain_sha256']==check['candidate_sha256']
reference=json.loads((B/'reference-inputs.json').read_text())
assert reference['status']=='PASS_EV80_COMPOSITE_REFERENCE' and len(reference['textures'])==2048
assert sha(BASE/'narva_trial.pbo')==reference['world_sha256']=='ec3785d1eab89eb18503e358a9f7d786dca35f9eef829301bae45a1ec28d7038'
assert sha(BASE/'baltic_water_v30.pbo')==reference['water_sha256']=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
_,props,entries=read_pbo(BASE/'narva_trial.pbo')
assert blob_sha(entries['baltic_trial.wrp'])=='3ae8f82cfc7279cec5c58dd8f253b9da79bfbfe52004695ebe02cb5587383680'
for item in reference['textures'].values():
    assert sha(Path(item['png']))==item['png_sha256']
    assert blob_sha(entries[item['pbo_entry']])==item['paa_sha256']
_,_,compiled=read_pbo(B/'package/world/out/narva_trial.pbo')
wrp=compiled['baltic_trial.wrp']; assert wrp.startswith(b'OPRW') and wrp!=entries['baltic_trial.wrp']
replacement={'baltic_trial.wrp':wrp}
for tile in surface['files']:
    a,b=tile['tile']
    for kind,suffix in [('s','lco'),('m','lca')]:
        stem=f'{kind}_{a:03d}_{b:03d}_{suffix}'; path=B/'surface/layers'/(stem+'.paa')
        assert sha(path)==tile['files'][kind]['paa_sha256']
        replacement[reference['textures'][stem]['pbo_entry']]=path.read_bytes()
assert len(replacement)==1+2*len(surface['tiles'])
dest=B/'distribution/narva_trial'; dest.mkdir(parents=True,exist_ok=False)
for name,data in entries.items():
    path=dest/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(replacement.get(name,data))
out=B/'packed'; out.mkdir(exist_ok=False)
cmd=['C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/PboUtils/FileBank.exe']
for key,value in props.items():cmd+=['-property',key+'='+value]
done=subprocess.run(cmd+['-dst',str(out),str(dest)],capture_output=True,text=True)
(B/'filebank.log').write_text(done.stdout+'\n'+done.stderr); assert done.returncode==0
pbo=out/'narva_trial.pbo'; _,afterprops,after=read_pbo(pbo)
assert props==afterprops and set(entries)==set(after) and len(after)==6827
assert all(after[k]==replacement.get(k,entries[k]) for k in entries)
changed=sorted(k for k in entries if entries[k]!=after[k]); textures=[k for k in changed if k!='baltic_trial.wrp']
assert all(re.search(r'(?:^|/)[sm]_\d{3}_\d{3}_lc[oa]\.paa$',k,re.I) for k in textures)
target=Path('P:/Mods/@DayZ_Baltic_IncrementalBankPreviewV1/Addons'); target.mkdir(parents=True,exist_ok=False)
for p in [pbo,BASE/'baltic_water_v30.pbo']:
    shutil.copyfile(p,target/p.name); assert sha(p)==sha(target/p.name)
report=dict(status='DEPLOYED_EV82_PREVIEW_NATIVE_READBACK_PENDING',mod=str(target.parent),
    files={p.name:sha(p) for p in [pbo,BASE/'baltic_water_v30.pbo']},terrain_sha256=sha(B/'candidate/terrain.npz'),
    compiled_wrp_sha256=blob_sha(wrp),baseline_world_sha256=sha(BASE/'narva_trial.pbo'),
    changed_entries=changed,changed_texture_entries=textures,unchanged_entries=len(entries)-len(changed),
    total_entries=len(entries),surface_selected_tiles=len(surface['tiles']),all_expected_entries_exact=True,
    baseline_texture_identities_verified=2048,baseline_png_identities_verified=2048,water_pbo_exact=True,
    limits=['OPRW integrity/identity only; actual compiled heights must be read through native engine SurfaceY.',
            'No render or navigation acceptance; existing navmesh retained pending final terrain freeze.'])
(B/'deploy.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('changed_entries','changed_texture_entries')},indent=2))
