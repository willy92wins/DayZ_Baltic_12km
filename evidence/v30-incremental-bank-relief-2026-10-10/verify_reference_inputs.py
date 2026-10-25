"""Verify all current EV80 PNG/PAA layers before any incremental surface build."""
from pathlib import Path
import sys,json,hashlib
B=Path(__file__).parent; R=B.parent; PREV=R/'v30-mixed-bank-constrained-20261010'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
MOD=Path('P:/Mods/@DayZ_Baltic_MixedBankPreviewV1/Addons')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
blob_sha=lambda b:hashlib.sha256(b).hexdigest()
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
assert sha(PREV/'candidate/terrain.npz')=='0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b'
assert sha(PREV/'reference-inputs.json')=='b3bc7347c914c5fcab726991667fd939f49eeb664adac3db862f4eb8e4881ac0'
assert sha(PREV/'surface-verification.json')=='0dc7e498301231ef8b83456ba00b0f2d8d26566d9100016705b4c69aeae88916'
assert sha(MOD/'narva_trial.pbo')=='ec3785d1eab89eb18503e358a9f7d786dca35f9eef829301bae45a1ec28d7038'
assert sha(MOD/'baltic_water_v30.pbo')=='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
old=json.loads((PREV/'reference-inputs.json').read_text()); prev=json.loads((PREV/'surface-verification.json').read_text())
assert old['status']=='PASS_EV79_COMPOSITE_REFERENCE' and prev['status']=='PASS_EV80_AFFECTED_SURFACE'
assert all(prev['gates'].values()) and len(prev['files'])==459
index=old['textures'].copy()
for tile in prev['files']:
    a,b=tile['tile']
    for kind,suffix in [('s','lco'),('m','lca')]:
        stem=f'{kind}_{a:03d}_{b:03d}_{suffix}'; t=tile['files'][kind]
        index[stem]=dict(png=str(PREV/'surface/layers'/(stem+'.png')),png_sha256=t['png_sha256'],
                         pbo_entry=f'data/layers/{stem}.paa',paa_sha256=t['paa_sha256'])
_,props,entries=read_pbo(MOD/'narva_trial.pbo')
assert len(entries)==6827 and len(index)==2048
assert blob_sha(entries['baltic_trial.wrp'])=='3ae8f82cfc7279cec5c58dd8f253b9da79bfbfe52004695ebe02cb5587383680'
for stem,t in index.items():
    assert sha(Path(t['png']))==t['png_sha256'],stem
    assert blob_sha(entries[t['pbo_entry']])==t['paa_sha256'],stem
report=dict(status='PASS_EV80_COMPOSITE_REFERENCE',world_sha256=sha(MOD/'narva_trial.pbo'),
            water_sha256=sha(MOD/'baltic_water_v30.pbo'),entries=len(entries),
            png_and_deployed_paa_verified=len(index),reference_tiles=1024,ev80_overlay_tiles=459,
            reference_reports={str(p):sha(p) for p in [PREV/'reference-inputs.json',PREV/'surface-verification.json']},textures=index)
(B/'reference-inputs.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='textures'},indent=2))
