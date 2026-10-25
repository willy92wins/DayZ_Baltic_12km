"""Freeze reviewed build inputs; never bypass a failing consumer."""
from pathlib import Path
import argparse
import hashlib
import json

D=Path(__file__).parent
R=D.parent
B=R.parent/'v30-mixed-bank-incremental-fixed-20261010'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--review-sha',required=True)
    args=ap.parse_args()
    target=D/'build-inputs.json'
    assert not target.exists(), 'Frozen build inputs must not be overwritten'
    report=R/'selective/selective-review.json'
    assert sha(report)==args.review_sha
    review=json.loads(report.read_text())
    assert review['status']=='PASS_INCREMENTAL_NONREGRESSION'
    assert review['global_representation_status']=='FAIL_WITH_INHERITED_OPEN'
    assert review['information']['global_contract_status']=='FAIL_WITH_INHERITED_OPEN' and review['information']['inherited_open']
    assert review['gates'] and all(review['gates'].values())
    candidate=R/'selective/candidate-terrain.npz'
    digest=sha(candidate)
    assert digest=='8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b'
    assert review['inputs'][str(candidate)]==digest
    paths=set(review['inputs'])
    for p,expected in review['inputs'].items():
        assert sha(p)==expected
    paths.update(str(p) for p in D.glob('*.py'))
    paths.update(str(p) for p in [report,R/'plan.md',R/'author_ev87.py',
        R/'metadata-normalization-receipt.json',R/'review-independent/verify_ev87.py',
        R/'review-independent/p99-sector-harness-correction-receipt.json',
        D/'reference-inputs.json',D/'native-adapter-receipt.json',
        D/'selective-adoption-receipt.json',R/'selective-integration-plan.md',
        R/'selective/integration-receipt.json',R/'selective/verify_selective.py',
        B/'build_changed_surface.py',B/'compile_native_world.ps1',
        B/'native-reference.json',B/'native-verification.json',B/'native-snapshot.log',
        W/'tools/terrain/build_surface_v30.py',W/'tools/terrain/wrp0wzd.py',
        W/'tools/terrain/v30_common.py',W/'tools/playtest/attach_navmesh.py',
        W/'evidence/v30-full-mipmap-audit-2026-10-09/audit_mipmaps.py',
        R.parent/'v30-surface-aligned-20261009/compile_and_verify_surface.py'])
    inputs={p:sha(p) for p in sorted(paths)}
    payload=dict(status='FROZEN_AFTER_INDEPENDENT_PASS',candidate_sha256=digest,
                 geometry_review_sha256=args.review_sha,inputs=inputs)
    target.write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps(dict(status=payload['status'],inputs=len(inputs),sha256=sha(target))))

if __name__=='__main__':main()
