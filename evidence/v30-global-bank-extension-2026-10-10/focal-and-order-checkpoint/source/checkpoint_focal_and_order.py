"""Archive completed focal acceptance and local order-closure evidence exactly."""
from pathlib import Path
import hashlib
import json
import shutil

G = Path('E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
RS = G/'global-operator-prototype/real-sector-preflight'
W = Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
DEST = W/'evidence/v30-global-bank-extension-2026-10-10/focal-and-order-checkpoint'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


names = [
    'PLAN_FOCUS_1981.md', 'author_focus_1981.py', 'derive_focus_univariable_bound.py',
    'focus-1981-univariable-bound.json', 'measure_focus_local_coverage.py',
    'focus-1981-local-coverage-diagnostic.json', 'PLAN_ORDER_CLOSURE.md',
    'ev93-versus-B-sector-comparison.json', 'ev93-pilot-overlap-precheck.json',
    'focus-unit/verify_focus_1981.py', 'focus-unit/verify_focus_1981_v2.py',
    'focus-unit/finalize_focal_report.py', 'focus-unit/verify_focal_composition.py',
    'focus-unit/root-review.json', 'focus-unit/root-acceptance-review.json',
    'focus-unit/author-run-01/receipt.json', 'focus-unit/consumer-run-01/review.json',
    'focus-unit/consumer-run-01/acceptance-supplement.json',
    'focus-unit/composition-run-01/review.json',
    'order-closure/projection.py', 'order-closure/author_order_closure.py',
    'order-closure/test_order_closure.py', 'order-closure/verify_order_closure.py',
    'order-closure/test_verify_order_closure.py', 'order-closure/root-source-review.json',
    'order-closure/author-run-01/receipt.json', 'order-closure/consumer-run-01/review.json',
    'order-closure/PLAN_CORRIDOR_NONREGRESSION.md',
    'order-closure/verify_corridor_nonregression.py',
    'order-closure/consumer-run-01/incremental-nonregression.json',
    'order-closure/corridor-failure-diagnosis.json', 'order-closure/ev93-composition-study.md',
]
sources = [(RS/n, n) for n in names] + [(Path(__file__).resolve(), Path(__file__).name)]
expected = {
    'focus-unit/composition-run-01/review.json': 'a5a5aaa1f1f2c06c646bbd54a41ea8fd89d8dee8ffa14d2e59af4d7bc07b05e3',
    'order-closure/consumer-run-01/review.json': 'a9112811a7d23fee0fe94735683174d3d3f67e2200a7519b7633c247b82b10fa',
    'order-closure/consumer-run-01/incremental-nonregression.json': '13f0b58dd287fb75dd8ba7f24e83b56464bb4468d904066b85f750b9df7f365b',
}
for name, digest in expected.items():
    assert sha(RS/name) == digest
references = []
for name, digest in [
    ('focus-unit/author-run-01/candidate-terrain.npz', '30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1'),
    ('order-closure/author-run-01/candidate-local.npz', 'ec1df1c7749fe478f4d5fc943acdc74bb498d68123bf568d07f5aa4d88ae21ba'),
    ('preflight-run-03-continuation/prepared.npz', '8a8a1cf8e9b6906b1aab8053877383d01a92baa5bd2c18b54b1b9e43c8c37a21'),
    ('solve-run-03-continuation/solver-state.npz', '8618d5941d7c8b235bedce6ad5e21a0053ec61a2a32c17532fec98ff9db3dfa9'),
]:
    p = RS/name
    assert sha(p) == digest
    references.append({'path': str(p), 'sha256': digest, 'bytes': p.stat().st_size})
before = {n: sha(p) for p, n in sources}
assert all(p.stat().st_size < 8*1024**2 for p, _ in sources)
DEST.mkdir(parents=True, exist_ok=False)
copies = []
for p, name in sources:
    dest = DEST/'source'/name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    assert sha(dest) == sha(p) == before[name]
    copies.append({'source': str(p), 'relative_path': name, 'sha256': before[name], 'bytes': p.stat().st_size})
manifest = {'status': 'FOCAL_COMPOSITION_ACCEPTED_OFFLINE_ORDER_LOCAL_ONLY',
            'scope': 'Focal terrain is accepted incrementally offline; build/native pending. Order closure on B has a separate 23-gate nonregression verdict; original full-sector FAIL preserved. Direct composition with EV93 fails 8 D8 edges and is not exported. Rebase preparation is a new unit.',
            'copy_count': len(copies), 'copied_files': copies, 'large_references': references,
            'global_contract_status': 'OPEN_INHERITED_MAP_DEFECTS',
            'p9_status': 'OPEN_INHERITED_P9_COVERAGE'}
(DEST/'manifest.json').write_bytes((json.dumps(manifest, indent=2)+'\n').encode())
print(json.dumps({'status': manifest['status'], 'files': len(copies), 'refs': len(references)}))
