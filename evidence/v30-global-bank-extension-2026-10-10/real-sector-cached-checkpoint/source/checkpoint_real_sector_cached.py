"""Archive the closed telemetry correction and numerical attempt, not active geometry work."""
from pathlib import Path
import hashlib
import json
import shutil

G = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
R = G / 'global-operator-prototype/real-sector-preflight'
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
DEST = W / 'evidence/v30-global-bank-extension-2026-10-10/real-sector-cached-checkpoint'

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()

names = [
    'AMENDMENT_CACHED_TELEMETRY.md', 'solve_real_sector_cached.py',
    'verify_real_sector_cached.py', 'root-cached-review.json',
    'cached-preflight-array-comparison.json', 'preflight-cached-independent-review.json',
    'preflight-run-02/preflight.json', 'solve-run-02/solver.started',
    'solve-run-02/progress.jsonl', 'solve-run-02/solve-result.json', 'solve-run-02.log',
    'attempts-numeric-comparison.json', 'telemetry_pointer_cache_probe.py',
    'run_telemetry_pointer_cache.ps1', 'telemetry-pointer-cache/findings.md',
    'telemetry-pointer-cache/attempt-03/summary.json',
    'telemetry-pointer-cache/attempt-03/original.stdout.txt',
    'telemetry-pointer-cache/attempt-03/original.stderr.txt',
    'telemetry-pointer-cache/attempt-03/cached.stdout.txt',
    'telemetry-pointer-cache/attempt-03/cached.stderr.txt',
    'cached-telemetry-review/findings.md', 'cached-telemetry-review/review.json',
    'cached-telemetry-review/review_cached_telemetry.py',
]
result = json.loads((R / 'solve-run-02/solve-result.json').read_text(encoding='utf-8'))
assert result['status'] == 'SOLVER_NOT_CONVERGED'
assert result['candidate_path'] is None
assert result['diagnostics']['status'] == 'ITERATION_LIMIT'
assert sha(R / 'solve-run-02/solve-result.json') == 'bb988ab08db0cc141275d27b1e36fb6e44f7ca8168e276ff8003fab0a78bf979'
assert sha(R / 'solve_real_sector_cached.py') == '5e75e0e1d3e3c6938679cd31e87f4f317353e64ff919c471d79d1a04d50f98f9'
assert sha(R / 'verify_real_sector_cached.py') == '3e7a6996f5e4b637ba7d94ad20dd3add6643f52db31d7098c6baa32e238d4799'
sources = [(R / name, name) for name in names]
sources.append((Path(__file__).resolve(), 'checkpoint_real_sector_cached.py'))
for src, _ in sources:
    if not src.is_file():
        raise FileNotFoundError(src)
    if src.stat().st_size > 8 * 1024**2:
        raise RuntimeError(f'Unexpected large source: {src}')
refs = []
for name in ['preflight-run-02/prepared.npz', 'solve-run-02/solver-state.npz']:
    p = R / name
    refs.append({'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size})
assert refs[0]['sha256'] == '8a8a1cf8e9b6906b1aab8053877383d01a92baa5bd2c18b54b1b9e43c8c37a21'
assert refs[1]['sha256'] == 'edd871719397d957fb61ba08372dd86a0c304c69ce1b87477d794f03f960cd7c'
before = {name: sha(src) for src, name in sources}
if DEST.exists():
    raise FileExistsError(DEST)
DEST.mkdir(parents=True)
copied = []
for src, name in sources:
    dst = DEST / 'source' / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    assert sha(src) == sha(dst) == before[name]
    copied.append({'source': str(src), 'relative_path': name, 'sha256': before[name],
                   'bytes': dst.stat().st_size})
manifest = {
    'status': 'ARCHIVED_ITERATION_LIMIT_NO_CANDIDATE', 'copied_files': copied,
    'copy_count': len(copied), 'large_references': refs,
    'prior_checkpoint': '../real-sector-resource-limit-checkpoint/manifest.json',
    'scope': 'Closed telemetry correction and bounded solve02; no map candidate or acceptance. '
             'Subsequent focus geometry and last-iterate diagnostics are separate active work.',
}
(DEST / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': manifest['status'], 'copied': len(copied),
                  'references': len(refs), 'destination': str(DEST)}))
