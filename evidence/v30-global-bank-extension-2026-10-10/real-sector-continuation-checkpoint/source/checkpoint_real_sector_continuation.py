"""Archive the closed, rejected continuation; never promote its last iterate."""
from pathlib import Path
import hashlib
import json
import shutil

G = Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
R = G / 'global-operator-prototype/real-sector-preflight'
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
DEST = W / 'evidence/v30-global-bank-extension-2026-10-10/real-sector-continuation-checkpoint'

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

names = [
    'AMENDMENT_CONTINUATION.md', 'solve_real_sector_continuation.py',
    'verify_real_sector_continuation.py', 'test_continuation_consumer_lineage.py',
    'CONTINUATION_DRIVER_CONSUMER_REVIEW.md', 'root-continuation-source-review.json',
    'preflight-continuation-independent-review.json',
    'preflight-run-03-continuation/preflight.json',
    'solve-run-03-continuation/solver.started',
    'solve-run-03-continuation/progress.jsonl',
    'solve-run-03-continuation/solve-result.json',
]
sources = [(R / n, 'real-sector-preflight/' + n) for n in names]
for name in ['solve_resumable.py', 'test_solve_resumable.py',
             'resume-fixture-report.json', 'CONTINUATION_HELPER_REVIEW.md']:
    sources.append((R.parent / 'admm-quantized-pilot' / name,
                    'admm-quantized-pilot/' + name))
sources.append((Path(__file__).resolve(), Path(__file__).name))
result = json.loads((R / names[-1]).read_text(encoding='utf-8'))
assert result['status'] == 'REJECTED_LOCAL_NUMERIC_GATES'
assert result['candidate_path'] is None
assert result['diagnostics']['status'] == 'CONVERGED'
assert result['diagnostics']['iteration'] == 10477
assert result['closure']['reason'] == 'more_than_one_ulp'
assert not result['resource_measurement']['limit_violated']
assert sha(R / 'solve_real_sector_continuation.py') == '7a8625a43f1610322f1f32bc1d20bbb5b7fcace1e3259bec7577c0c27660e9cb'
assert sha(R / 'verify_real_sector_continuation.py') == '5952de0210215275cf8ed67d644dd4a9bd0325b95c1dfda07751510ad9ad821f'
refs = []
for name, expected in [
    ('preflight-run-03-continuation/prepared.npz', '8a8a1cf8e9b6906b1aab8053877383d01a92baa5bd2c18b54b1b9e43c8c37a21'),
    ('solve-run-03-continuation/solver-state.npz', '8618d5941d7c8b235bedce6ad5e21a0053ec61a2a32c17532fec98ff9db3dfa9'),
]:
    p = R / name
    assert sha(p) == expected
    refs.append({'path': str(p), 'sha256': expected, 'bytes': p.stat().st_size})
before = {}
for src, name in sources:
    if not src.is_file() or src.stat().st_size > 8 * 1024**2:
        raise RuntimeError(f'Missing or oversized source: {src}')
    before[name] = sha(src)
DEST.mkdir(parents=True, exist_ok=False)
copied = []
for src, name in sources:
    dst = DEST / 'source' / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert sha(src) == sha(dst) == before[name]
    copied.append({'source': str(src), 'relative_path': name,
                   'sha256': before[name], 'bytes': dst.stat().st_size})
manifest = {'status': 'ARCHIVED_CONVERGED_BUT_FLOAT32_REJECTED_NO_CANDIDATE',
            'copy_count': len(copied), 'copied_files': copied, 'large_references': refs,
            'prior_checkpoint': '../real-sector-cached-checkpoint/manifest.json',
            'scope': 'Single authorized continuation closed. No further continuation, '
                     'no candidate and no map acceptance. Independent preflight passed; '
                     'candidate consumer was not run because no candidate exists.'}
(DEST / 'manifest.json').write_bytes((json.dumps(manifest, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'status': manifest['status'], 'copied': len(copied),
                  'references': len(refs), 'destination': str(DEST)}))
