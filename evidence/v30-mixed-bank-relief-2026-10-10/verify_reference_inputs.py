"""Resolve and verify every EV79 deployed texture against the EV72+EV79 PNG provenance."""
from pathlib import Path
import sys, json, hashlib

B = Path(__file__).parent
R = B.parent
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OLD = R / 'v30-complete-dry-surface-20261009'
PREV = R / 'v30-narva-dry-bank-relief-20261010'
MOD = Path('P:/Mods/@DayZ_Baltic_NarvaDryBankPreviewV1/Addons')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
blob_sha = lambda b: hashlib.sha256(b).hexdigest()
sys.path.insert(0, str(W / 'tools/playtest'))
from attach_navmesh import read_pbo

assert sha(PREV/'candidate/terrain.npz') == 'dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
assert sha(MOD/'narva_trial.pbo') == 'df00806c598181e9ddca160781790cd0edc9314095262f6f106a87ed4d464213'
assert sha(MOD/'baltic_water_v30.pbo') == '3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14'
old = json.loads((OLD/'surface-verification.json').read_text())
prev = json.loads((PREV/'surface-verification.json').read_text())
assert old['status'] == 'PASS_COMPLETE_SURFACE_SOURCE_COMPILED'
assert prev['status'] == 'PASS_AFFECTED_SURFACE'
assert len(old['tiles']) == 1024 and len(prev['files']) == 18
tiles = {tuple(t['tile']): (OLD, t) for t in old['tiles']}
for t in prev['files']:
    tiles[tuple(t['tile'])] = (PREV, t)
_, props, entries = read_pbo(MOD/'narva_trial.pbo')
assert len(entries) == 6827
# Explicit digest, independent of package reports.
assert blob_sha(entries['baltic_trial.wrp']) == 'fee7cad702d5d2278697976654fd62e2ba0f2afbd4ab7c7d9f26369c15099f76'
names = {Path(k).name.lower(): k for k in entries}
assert len(names) == len(entries)
index = {}
for (a, b), (folder, tile) in sorted(tiles.items()):
    for kind, suffix in [('s', 'lco'), ('m', 'lca')]:
        stem = f'{kind}_{a:03d}_{b:03d}_{suffix}'
        png = folder/'surface/layers'/(stem+'.png')
        identity = tile['files'][kind]
        key = names[stem+'.paa']
        assert sha(png) == identity['png_sha256'], str(png)
        assert blob_sha(entries[key]) == identity['paa_sha256'], key
        index[stem] = dict(png=str(png), png_sha256=identity['png_sha256'],
                           pbo_entry=key, paa_sha256=identity['paa_sha256'])
assert len(index) == 2048
report = dict(status='PASS_EV79_COMPOSITE_REFERENCE', world_sha256=sha(MOD/'narva_trial.pbo'),
              water_sha256=sha(MOD/'baltic_water_v30.pbo'), entries=len(entries),
              png_and_deployed_paa_verified=len(index), reference_tiles=1024, ev79_overlay_tiles=18,
              reference_reports={str(p):sha(p) for p in [OLD/'surface-verification.json',PREV/'surface-verification.json']},
              textures=index)
(B/'reference-inputs.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='textures'},indent=2))
