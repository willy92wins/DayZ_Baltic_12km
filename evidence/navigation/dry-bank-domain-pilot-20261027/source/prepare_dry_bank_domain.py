"""Freeze one reviewed experiment before any solve; create-only paths."""
from pathlib import Path
import ast
import hashlib
import json

R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'dry-bank-domain-setup-20261027'

def main():
    O.mkdir(exist_ok=False)
    paths=dict(source=R/'river-kit7-a-on-f-20261026/kit-7-surfaces.npz',
        base=R/'rectangle-pilot-f-merged/terrain-buried.npz',
        support=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz',
        footprint=R/'rectangle-pilot-f-merged/bury-work/fp0/footprint.npz',
        author_report=R/'river-kit7-a-on-f-20261026/author-report.json',
        author=W/'tools/water/continuous_stream_pilot_v31.py',
        old_pilot=R/'pilot_dry_apron.py',attribution=R/'bank-source-attribution-20261027/result.json',
        plan=W/'plans/ev112-dry-bank-domain-pilot-20261027.md')
    additional=[W/p for p in ('tools/water/streambed_kit_v31.py','tools/terrain/shape_repair_constraints_ev112.py','tools/terrain/verify_roads_v30.py')]
    roads=json.loads(paths['author_report'].read_text(encoding='utf-8-sig'))['road_reference_hashes']
    scripts=[R/(name+'.py') for name in ('pilot_dry_bank_domain','verify_dry_bank_domain','run_dry_bank_domain','test_dry_bank_domain','prepare_dry_bank_domain')]
    for script in scripts:ast.parse(script.read_text(encoding='utf-8'))
    allpaths=list(paths.values())+additional+list(map(Path,roads))+scripts
    hashes={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in allpaths}
    expected={str(paths['source']):'9d8caf0fb75d2bd34f71b877ecd3f71079898fbc01c28e67ddab0bf8dca50063',
        str(paths['base']):'caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc',
        str(paths['support']):'815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40',
        str(paths['footprint']):'95f7a26304e88c726679ec69ef076bb149ec1f1f8bdf4a6cd1e83e40f3b6be83',
        str(paths['author']):'8b340a2ab4e25d69ff9baf46f71c8f843c9da2c02137c32fa356a0bb9deb9169'}|roads
    assert all(hashes[path]==value for path,value in expected.items())
    context=dict(worktree=str(W),paths={k:str(v) for k,v in paths.items()},hashes=hashes)
    (O/'context.json').write_text(json.dumps(context,indent=2)+'\n',encoding='utf-8')
    (O/'budget.json').write_text(json.dumps(dict(candidate_count=1,max_seconds=900,solver_iterations=500,
        prior_weight=.002,review_rounds=1,concrete_code_corrections_at_most=1,dayz_runs=0,
        gates='Approved plan: independent saved-file invariants, strict lower energy, no slope regression.',
        counterexamples=['identity-no-improvement','CAP-interior','wet-bed','water-Y','bed-XZ','outer-border',
                         'protected-point','ceiling','nonfinite','timeout','signed-zero']),indent=2)+'\n',encoding='utf-8')
    print('FROZEN',len(hashes),'files',O)

if __name__=='__main__':main()
