"""Archive the exact compiled EV95 preview and its pending native probe."""
from pathlib import Path
import hashlib, json, shutil

G=Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
B=G/'build-wide-slope'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-global-bank-extension-2026-10-10/ev95-build-checkpoint'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()

deploy=json.loads((B/'deploy.json').read_text())
mips=json.loads((B/'changed-mips.json').read_text())
op=json.loads((B/'op_rw_verification.json').read_text())
assert mips['status']=='PASS_EV95_ALL_CHANGED_MIPS'
assert mips['changed_texture_count']==996 and mips['decoded_mip_count']==7968
assert op['status']=='PASS_EV95_PACKAGED_OPRW_IDENTITY'
manifest=json.loads((B/'source-manifest-v2.json').read_text())
for name,expected in manifest['sources'].items():
    assert sha(B/name)==expected,(name,'source drift')
names=list(manifest['sources'])+['source-manifest.json','source-manifest-v2.json','stage.json',
    'surface-verification.json','deploy.json','op_rw_verification.json','changed-mips.json',
    'native-reference.json','native-probe-lint.json','native-launch-preflight.json',
    'probe-preparation-run-02.log','package/world-addonbuilder.log']
names+=['probe-pin-failure-preserved/'+n for n in ('prepare_probe.py','verify_native.py','source-manifest.json','probe-preparation-run.log')]
sources=[(B/n,n) for n in names]+[(Path(__file__),Path(__file__).name)]
pins={n:sha(p) for p,n in sources}
refs=[]
for name,expected in deploy['files'].items():
    p=Path(deploy['mod'])/'Addons'/name
    assert sha(p)==expected
    refs.append({'path':str(p),'sha256':expected,'bytes':p.stat().st_size})
D.mkdir(parents=True,exist_ok=False)
records=[]
for p,n in sources:
    q=D/'source'/n;q.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,q)
    assert sha(q)==pins[n]==sha(p)
    records.append({'source':str(p),'relative_path':n,'sha256':pins[n],'bytes':p.stat().st_size})
out={'status':'PASS_EV95_BUILD_OFFLINE_NATIVE_PENDING','copied_files':records,'external_artifacts':refs,
    'terrain_sha256':deploy['terrain_sha256'],'native_readback':False,'visual_acceptance':False,
    'limits':['No process launched. Native mission and request validation ready; LFSkateboard occupies test box.',
              'Grey water rectangles, dynamic dry-land artifacts, wet banks and map-wide acceptance remain open.',
              'Initial probe preparation stopped before outputs on a stale verifier hash; corrected pin/output names only.']}
(D/'manifest.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':out['status'],'copies':len(records),'external':len(refs)}))
