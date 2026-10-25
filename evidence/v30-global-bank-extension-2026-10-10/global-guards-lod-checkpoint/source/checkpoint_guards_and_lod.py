from pathlib import Path
import hashlib,json,shutil
G=Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
P=G/'global-operator-prototype'
R=Path('E:/DayZ-Baltic-Build/v30-water-render-discriminator-20261010/coarse-terrain-sensitivity-ev95')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-global-bank-extension-2026-10-10/global-guards-lod-checkpoint'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
required={
 P/'global-civil-ev95/run-01/inventory.json':'cdebbbce50644407642e791388e44c40b15499041844607650b885d1bc618856',
 P/'global-water-guard-ev95/run-01/inventory.json':'39e26373fee324e8b0e7334dd8333d3fb7373b9cc55c226350e2c607b592ce82',
 R/'native-grid-factors/report.json':'5470725d4ac0e70ede3685a06ff8f965451025c2871d6a0139e4dc5ae0699db6',
}
for p,h in required.items():assert sha(p)==h,(p,'pin drift')
files=[]
for folder in ['global-civil-ev95','global-water-guard-ev95']:
    for name in ['prepare.py','run-01/inventory.json']:
        files.append((P/folder/name,folder+'/'+name))
for p in sorted(R.rglob('*')):
    if p.is_file() and p.suffix in ('.py','.md','.json') and '__pycache__' not in p.parts:
        files.append((p,'coarse-terrain-sensitivity-ev95/'+p.relative_to(R).as_posix()))
files.append((Path(__file__),Path(__file__).name))
before={name:sha(p) for p,name in files}; D.mkdir(parents=True,exist_ok=False)
copied=[]
for p,name in files:
    dest=D/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    assert sha(dest)==before[name]==sha(p)
    copied.append({'source':str(p),'relative_path':name,'sha256':before[name]})
refs=[]
for p in [P/'global-civil-ev95/run-01/civil-mask.npz',P/'global-water-guard-ev95/run-01/water-guard.npz',*sorted(R.rglob('*.npz'))]:
    refs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
receipt={'status':'READ_ONLY_GLOBAL_GUARDS_AND_LOCAL_LOD_SENSITIVITY',
 'copied_files':copied,'external_artifacts':refs,
 'limits':['No terrain or package changed. Civil and water guards are conservative frozen masks.',
 'LOD factors are an assumed coarse terrain model, not measured DayZ runtime selection or root cause.',
 'Original arbitrary-metre diagnostic retained; the native-grid-factors directory is the requested nested-grid calculation.']}
(D/'manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'copied':len(copied),'external':len(refs)}))
