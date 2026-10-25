from pathlib import Path
import hashlib,json,shutil

G=Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-global-bank-extension-2026-10-10/preflight-checkpoint'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(4194304),b''):h.update(chunk)
    return h.hexdigest()

def main():
    summary=json.loads((G/'preflight-segment02/window-summary.json').read_text(encoding='utf-8'))
    final=json.loads((G/'preflight-segment02/migration-final.json').read_text(encoding='utf-8'))
    if summary['status']!='COMPLETE_READONLY_PREFLIGHT' or summary['processed_count']!=703 or summary['error_count']:
        raise AssertionError('preflight has not completed')
    if final['segment02_summary_sha256']!=sha(G/'preflight-segment02/window-summary.json'):
        raise AssertionError('final receipt does not bind summary')
    if D.exists():raise FileExistsError('immutable checkpoint already exists')
    files=[G/x for x in ('plan.md','preflight-plan.md','author-stage-plan.md','WORKING_STATE.md',
                         'preflight-segment02-launcher.py','archive_preflight.py')]
    roots=[G/x for x in ('ev93-face-index','queue','preflight','preflight-segment02')]
    for root in roots:
        files.extend(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for rel in ('review-independent/verify_face_index.py','review-independent/prebuild-review.md',
                'review-independent/preflight-final-review.md','review-independent/whole-surface-next-step.md',
                'review-independent/aggregate_preflight.py','review-independent/preflight-inventory.json'):
        p=G/rel
        if p.is_file():files.append(p)
    root=G/'review-independent/runs/attempt-01'
    files.extend(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    D.mkdir(parents=True)
    rows=[]
    for p in sorted(set(files)):
        if p.is_symlink():raise AssertionError(f'unexpected symlink: {p}')
        before=sha(p); rel=p.relative_to(G); size=p.stat().st_size; copied=None
        if size<=450000 and p.suffix.lower() not in {'.npz','.npy','.pyc'} and 'window-details' not in p.parts:
            dst=D/'archive'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,dst)
            if sha(dst)!=before:raise AssertionError('copy mismatch')
            copied=str(dst.relative_to(D))
        if sha(p)!=before:raise AssertionError(f'changed during checkpoint: {p}')
        rows.append({'path':str(p),'sha256':before,'bytes':size,'archive':copied})
    report={'status':'READONLY_PREPARATION_COMPLETE_NOT_TERRAIN_ACCEPTANCE',
            'preflight_summary':summary,'artifacts':rows}
    (D/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifacts':len(rows),'copied':sum(x['archive'] is not None for x in rows),
                      'external':sum(x['archive'] is None for x in rows),'path':str(D)}))

if __name__=='__main__':main()
