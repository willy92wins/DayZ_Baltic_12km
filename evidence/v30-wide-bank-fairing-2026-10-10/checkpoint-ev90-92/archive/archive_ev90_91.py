from pathlib import Path
import hashlib,json,shutil
Q=Path('E:/DayZ-Baltic-Build/v30-wide-bank-fairing-pilot-20261010')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-wide-bank-fairing-2026-10-10/checkpoint-ev90-92'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if D.exists():raise FileExistsError('immutable checkpoint exists')
D.mkdir(parents=True)
rows=[]
roots=[Q/'next-method-preflight',Q/'next-method-consumer',Q/'ev90-author',Q/'ev91-descent',Q/'ev92-damped',Path('E:/DayZ-Baltic-Build/v30-bank-multiscale-census-20261010')]
files=[Q/'next-method-plan.md',Q/'WORKING_STATE.md',Path(__file__)]
for root in roots:
    files.extend(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for p in sorted(set(files)):
    if not p.is_file():continue
    before=sha(p);relative=p.relative_to(Q) if p.is_relative_to(Q) else Path('multiscale-census')/p.relative_to(roots[-1])
    copy=None
    if p.stat().st_size<=450000 and p.suffix.lower() not in {'.npz','.npy'}:
        dest=D/'archive'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dest)
        if sha(dest)!=before or sha(p)!=before:raise AssertionError('copy identity failed')
        copy=str(dest.relative_to(D))
    rows.append({'path':str(p),'sha256':before,'bytes':p.stat().st_size,'archive':copy})
manifest={'status':'OFFLINE_UNIT_NOT_MAP_ACCEPTANCE','artifacts':rows}
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'artifacts':len(rows),'copied':sum(x['archive'] is not None for x in rows),'destination':str(D)}))
