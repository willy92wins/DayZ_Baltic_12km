from pathlib import Path
import hashlib
import json
import re
import shutil

G = Path(__file__).resolve().parent
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OUT = W / 'evidence/v30-global-bank-extension-2026-10-10/diagnostic-integration-checkpoint'
POST = G / 'G/wet-bank-pilot/postsolve-consumer'
AS = POST / 'rejected-diagnostic-assessment-v1'
AN = POST / 'diagnostic-polish-consumer-v1/analysis-v2-recovery'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    note_path = G / 'diagnostic-integration-note.md'
    note = note_path.read_text(encoding='utf-8')
    groups = {
        'underlay-A-analysis': G / 'water-lod-discriminator-plan/v2/runtime/A/analysis-A',
        'current-crossings': G / 'current-reserve-crossings',
        'global-preview-preparation': G / 'build-global-dry-preview-v1',
        'rejected-diagnostic-assessment': AS,
    }
    chosen = []
    for label, folder in groups.items():
        files = sorted(p for p in folder.rglob('*') if p.is_file()
                       and p.suffix.lower() in {'.py', '.ps1', '.json', '.jsonl', '.md', '.csv'}
                       and '__pycache__' not in p.parts)
        if not files:
            raise ValueError(f'No evidence in {folder}')
        for source in files:
            if source.stat().st_size > 2 * 1024 * 1024:
                raise ValueError(f'Unexpected large artifact; use explicit external reference: {source}')
            chosen.append((source, Path(label) / source.relative_to(folder)))
    for name in ('coordinated_crossing_component.py', 'coordinated-crossing-component.json',
                 'coordinated-crossing-component.md', 'energy-lower-bound-design.md'):
        chosen.append((AN / name, Path('local-energy-analysis') / name))
    lower_bound = AN / 'energy-lower-bound-v2'
    if lower_bound.exists():
        for source in sorted(lower_bound.rglob('*')):
            if source.is_file() and source.suffix in {'.py', '.md', '.json'} and '__pycache__' not in source.parts:
                chosen.append((source, Path('local-energy-analysis/energy-lower-bound-v2') / source.relative_to(lower_bound)))
    chosen.append((Path(__file__), Path(Path(__file__).name)))
    chosen.append((G / 'diagnostic-integration-resource-snapshot.json', Path('resource-snapshot.json')))
    chosen.append((G / 'update_diagnostic_live_state.py', Path('update_diagnostic_live_state.py')))
    # Hash every selected source before any copy, then validate it again afterwards.
    frozen = [(source, relative, sha(source)) for source, relative in chosen]
    if (OUT / 'manifest.json').exists():
        raise FileExistsError('Completed checkpoint already exists')
    OUT.mkdir(parents=True, exist_ok=True)
    copied = []
    for source, relative, digest in frozen:
        target = OUT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and sha(target) != digest:
            saved = OUT / 'snapshot-before-path-fix.py'
            if target != OUT / Path(__file__).name or not saved.is_file() or sha(target) != sha(saved):
                raise ValueError(f'Existing partial checkpoint differs: {target}')
        shutil.copyfile(source, target)
        if sha(source) != digest or sha(target) != digest:
            raise ValueError(f'Copy drift: {source}')
        copied.append({'source': str(source), 'copy': relative.as_posix(), 'sha256': digest})
    (OUT / 'README.md').write_text(note, encoding='utf-8', newline='\n')
    saved = OUT / 'snapshot-before-path-fix.py'
    recovery = {'copy': saved.name, 'sha256': sha(saved), 'reason': 'Initial archive stopped before manifest because a relative name was str instead of Path; prior copies verified during resume.'} if saved.exists() else None
    (OUT / 'manifest.json').write_text(json.dumps({'copied': copied, 'archiver_recovery': recovery, 'scope': 'diagnostic evidence and build preparation only; no candidate promotion'}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'copies': len(copied), 'path': str(OUT)}))

if __name__ == '__main__':
    main()
