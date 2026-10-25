from pathlib import Path
import gzip,json,shutil
from discover_components import sha
B=Path(__file__).parent
E=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/evidence/v30-low-water-components-2026-10-09')
E.mkdir(exist_ok=False);files=[]
for pattern in ('*.py','*.md','*.json','*.csv','*.log','*.ps1','*.c','*.npz'):
    files.extend(p for p in B.glob(pattern) if p.name!='compiled-instance-bounds.json')
files.extend((B/'translation').glob('delta.npz'))
files.extend((B/'views').rglob('*.jpg'))
files.extend((B/'missions').rglob('init.c'));files.extend((B/'missions').rglob('points.csv'))
for p in files:
    target=E/p.relative_to(B);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);assert sha(p)==sha(target)
cache=B/'compiled-instance-bounds.json';packed=E/'compiled-instance-bounds.json.gz'
with gzip.open(packed,'wb') as f:f.write(cache.read_bytes())
assert gzip.decompress(packed.read_bytes())==cache.read_bytes()
identity={p.relative_to(E).as_posix():sha(p) for p in E.rglob('*') if p.is_file()}
(E/'preservation.json').write_text(json.dumps(dict(status='PRESERVED_DIAGNOSTIC_NOT_PROMOTED',external_root=str(B),files=identity,cache_uncompressed_sha256=sha(cache)),indent=2)+'\n')
print(json.dumps(dict(evidence=str(E),files=len(identity),bytes=sum(p.stat().st_size for p in E.rglob('*') if p.is_file()))))
