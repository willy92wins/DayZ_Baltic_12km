"""Copy only this task's evidence and helpers, checking SHA256 at destination."""
from pathlib import Path
import json,hashlib,shutil
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-valley-smoothing-2026-10-08'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=[]
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)
    assert sha(src)==sha(dst)
    manifest.append(dict(source=str(src),copy=str(dst.relative_to(E)),sha256=sha(dst)))
for p in list(B.glob('*.py'))+list(B.glob('*.ps1')):copy(p,E/'scripts'/p.name)
for root in ('land160-visual','land180-visual','c1r3p-visual'):
    for p in (B/root).rglob('*'):
        if p.is_file() and p.suffix in ('.jpg','.json','.log'):copy(p,E/root/p.relative_to(B/root))
copy(Path(r'C:/Users/guill/AppData/Local/Temp/codex-clipboard-c0834cb1-11a9-467c-aee6-ce0874aa7056.png'),E/'user-images/LAND160-residual-confirmed.png')
(E/'preserved-files.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(files=len(manifest),all_hashes_match=True)))
