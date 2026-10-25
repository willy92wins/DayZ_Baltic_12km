"""Archive the completed and globally rejected EV93 unit without embedding large terrain/solver arrays."""
from pathlib import Path
import hashlib
import json
import shutil

G = Path(__file__).resolve().parent
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D = W / 'evidence/v30-global-bank-extension-2026-10-10/layer1-rejected-checkpoint'

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(4194304), b''):
            h.update(block)
    return h.hexdigest()

def main():
    receipt = json.loads((G / 'fairing-layer1/authoring.json').read_text())
    review_path = G / 'consumer-global/runs/attempt-04/ev93-review.json'
    review = json.loads(review_path.read_text())
    if receipt['status'] != 'AUTHORED_PENDING_GLOBAL_CONSUMER':
        raise AssertionError('author is incomplete')
    if review['status'] != 'FAIL_INCREMENTAL_NONREGRESSION' or {k for k,v in review['gates'].items() if not v} != {'physical_support_holes_lt_1e_7m2','visible_support_holes_lt_1e_7m2'}:
        raise AssertionError('unexpected global verdict; archive scope must be revised')
    if review['information']['candidate_sha256'] != receipt['candidate_sha256']:
        raise AssertionError('candidate does not match review')
    if D.exists():
        raise FileExistsError('immutable layer checkpoint already exists')
    files = [G / p for p in ('archive_layer1_rejected.py', 'summarize_layer.py',
        'layer1-results-summary.json', 'author-stage-plan.md', 'next-method-crests.md')]
    for name in ('fairing-layer1', 'consumer-global', 'build'):
        files += [p for p in (G / name).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    # BUILD must still be preparation-only; compiled datasets belong in a later checkpoint.
    if any((G / 'build' / p).exists() for p in ('stage.json', 'surface', 'package', 'deploy.json')):
        raise AssertionError('build has started; explicit archive scope revision required')
    D.mkdir(parents=True)
    rows = []
    for p in sorted(set(files)):
        if p.is_symlink():
            raise AssertionError(f'unexpected symlink: {p}')
        before, size, copied = sha(p), p.stat().st_size, None
        binary = p.suffix.lower() in {'.npz', '.npy', '.pyc'}
        per_window = p.parent.name in {'attempts', 'results', 'deltas'}
        if size <= 1500000 and not binary and not per_window:
            target = D / 'archive' / p.relative_to(G)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
            if sha(target) != before:
                raise AssertionError('copy changed bytes')
            copied = str(target.relative_to(D))
        if sha(p) != before:
            raise AssertionError(f'input changed during archive: {p}')
        rows.append({'path': str(p), 'sha256': before, 'bytes': size, 'archive': copied})
    output = {'status': 'REJECTED_COMPOUND_SUPPORT_HOLES_NO_BUILD',
        'terrain_accepted': False, 'failed_gates': [k for k,v in review['gates'].items() if not v],
        'candidate_sha256': receipt['candidate_sha256'], 'changed_vertices': receipt['changed_vertices'],
        'author_counts': receipt['result_counts'], 'consumer_path': str(review_path),
        'consumer_sha256': sha(review_path), 'artifacts': rows,
        'limits': ['Engine, dynamic waves, visual smoothing and all-map completion remain open.',
                   'No accepted layer exists from EV93 yet. Original local results and failing compound are preserved.']}
    (D / 'manifest.json').write_text(json.dumps(output, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(D), 'artifacts': len(rows),
        'copied': sum(r['archive'] is not None for r in rows),
        'external': sum(r['archive'] is None for r in rows)}))

if __name__ == '__main__':
    main()
