"""Archive the reviewed rebase and static sea-domain audit, without promotion."""
from pathlib import Path
import hashlib, json, shutil

G = Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
R = G / 'global-operator-prototype/real-sector-preflight/ev94-rebase'
U = G / 'unknown-p-audit'
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D = W / 'evidence/v30-global-bank-extension-2026-10-10/ev94-rebase-checkpoint'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main():
    report = read(R / 'consumer/full-run-02.json')
    source = R / 'consumer/verify_ev94_rebase.py'
    if sha(source) != report['consumer_sha256']:
        raise RuntimeError('Consumer source is not the evaluated version')
    solve = read(R / 'solve-run-01/solve-result.json')
    if sha(Path(solve['candidate_path'])) != solve['candidate_sha256']:
        raise RuntimeError('Local candidate changed after solve')
    source_list = []
    for name in ('PLAN_EV94_REBASE.md', 'EXECUTION_REVIEW.md', 'prepare_ev94.py',
                 'solve_ev94.py', 'test_solve_ev94.py', 'plot_candidate.py',
                 'review-preflight04.json', 'root-preflight05-review.json',
                 'preflight-run-04/prepare-used-601be931.py',
                 'preflight-run-04/preflight.json', 'preflight-run-05/preflight.json',
                 'solve-run-01/solve-result.json', 'solve-run-01/progress.jsonl',
                 'solve-run-01/native-sector-comparison.png',
                 'consumer/verify_ev94_rebase.py', 'consumer/verify_ev94_rebase.py.pre-fullrun01-4a50c92',
                 'consumer/test_readset_closure.py', 'consumer/contract-smoke-run-01.json',
                 'consumer/full-run-01.json', 'consumer/full-run-02.json'):
        source_list.append((R / name, 'rebase/' + name))
    for name in ('PLAN.md', 'audit_unknown_corridors.py', 'test_unknown_corridor_geometry.py',
                 'unknown-p-audit.json', 'corridor_context.py', 'corridor-domain-context.json',
                 'corridor-domain-context.md', 'current_water_polygon_context.py',
                 'current-water-polygon-context.json', 'current-water-classification.md'):
        source_list.append((U / name, 'water-context/' + name))
    source_list.append((Path(__file__), Path(__file__).name))
    if len({name for _, name in source_list}) != len(source_list):
        raise RuntimeError('Duplicate destination')
    before = {name: sha(p) for p, name in source_list}
    if any(p.stat().st_size >= 8 * 1024**2 for p, _ in source_list):
        raise RuntimeError('Unexpected large evidence file')
    refs = []
    for p in (R / 'preflight-run-05/prepared.npz', R / 'solve-run-01/candidate-local.npz',
              R / 'solve-run-01/solver-state.npz'):
        refs.append({'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size})
    D.mkdir(parents=True, exist_ok=False)
    copied = []
    for p, relative in source_list:
        dst = D / 'source' / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
        if sha(dst) != before[relative] or sha(p) != before[relative]:
            raise RuntimeError('Source or copy drift: ' + str(p))
        copied.append({'source': str(p), 'relative_path': relative,
                       'sha256': before[relative], 'bytes': p.stat().st_size})
    manifest = {'status': 'REBASE_AND_WATER_CONTEXT_CHECKPOINT',
                'consumer_status': report['status'], 'consumer_gates': report.get('gates', {}),
                'candidate_local_sha256': solve['candidate_sha256'],
                'copied_files': copied, 'external_artifacts': refs,
                'native_acceptance': False, 'visual_acceptance': False,
                'map_status': 'BASE_1_0_NOT_ACCEPTED',
                'water_context_only': True,
                'limitation': 'Local dry-relief candidate; source sea fallback is not proof of local engine water.'}
    (D / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': manifest['status'], 'consumer': report['status'],
                      'copied': len(copied), 'external_artifacts': len(refs)}))

if __name__ == '__main__':
    main()
