"""Archive exact small sources/receipts; large artifacts stay pinned externally."""
import hashlib,json,shutil
from pathlib import Path
G=Path(__file__).resolve().parent
WP=G/'G/wet-bank-pilot'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OUT=W/'evidence/v30-global-bank-extension-2026-10-10/wet-bank-pilot-checkpoint'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
groups={
 'wet-bank':(WP,['PLAN.md','RUN_PROTOCOL.md','select_wet_bank.py','selection.json','prepare_wet_bank_matrices.py','run_once.py','plot_profile.py',
     'prepared-runs/attempt-08/preparation.json','prepared-runs/attempt-08/independent-review.json','prepared-runs/attempt-08/prepared.npz',
     'coverage-consumer/check_coverage.py','coverage-consumer/baseline-run-01-source.py','coverage-consumer/baseline-run-01.json',
     'coverage-consumer/baseline-run-02.json','coverage-consumer/binding-fixtures-01.json','coverage-consumer/optimized-python-negative.log',
     'coverage-consumer/candidate-run-01.json','review-window-fixture/fixture-report.json','review-window-fixture/test_context_guard.py',
     'solve-once/invocation.json','solve-once/progress.jsonl','solve-once/solve-result.json','solve-once/solution.npz',
     'solve-once/root-shape-diagnostic.json','solve-once/native-profile-diagnostic.json',
     'postsolve-consumer/verify_wet_bank_result.py','postsolve-consumer/postsolve-review.json',
     'postsolve-consumer/diagnose_crossing_quantization.py','postsolve-consumer/quantization-diagnostic.json']),
 'global-census':(G/'ev95-global-shape-census',['census_ev95.py','report.json','exposure-classification/classify_residuals.py','exposure-classification/report.json']),
 'global-sizing':(G/'global-operator-prototype/global-sizing-ev95/run-05',['preflight_global_resources.py','preflight.json','review.md','masks.npz']),
 'civil-preservation':(G/'global-operator-prototype/global-civil-ev95',['verify_ev95_unchanged.py','ev95-civil-preservation.json'])}
references=[WP/'solve-once/unaccepted-candidate-terrain.npz',WP/'solve-once/native-profile-diagnostic.png',G/'ev95-global-shape-census/worsened-hinges.csv',G/'ev95-global-shape-census/exposure-classification/residual-hinges.csv']
for prefix,(root,names) in groups.items():
    for name in names:
        if not (root/name).is_file():raise FileNotFoundError(root/name)
for p in references:
    if not p.is_file():raise FileNotFoundError(p)
if OUT.exists():raise FileExistsError('Preserve the existing checkpoint')
OUT.mkdir(parents=True)
records=[]
for prefix,(root,names) in groups.items():
    for name in names:
        source=root/name;dest=OUT/prefix/name;dest.parent.mkdir(parents=True,exist_ok=True)
        before=sha(source);shutil.copyfile(source,dest)
        if sha(dest)!=before or sha(source)!=before:raise RuntimeError('Copy identity changed')
        records.append({'source':str(source),'copy':str(dest.relative_to(OUT)),'sha256':before,'bytes':source.stat().st_size})
refrecords=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in references]
# Preserve all prior preparation attempts by immutable references; the accepted matrix freeze is copied above.
prior=[]
for folder in sorted((WP/'prepared-runs').glob('attempt-*')):
    if folder.name=='attempt-08':continue
    for p in sorted(folder.glob('*')):
        if p.is_file():prior.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
manifest={'copied':records,'external_references':refrecords,'prior_preparation_attempts':prior,
    'scope':'Evidence only. Copying a candidate does not accept, package or deploy it.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
post=json.loads((WP/'postsolve-consumer/postsolve-review.json').read_text(encoding='utf-8'))
census=json.loads((G/'ev95-global-shape-census/report.json').read_text(encoding='utf-8'))
(OUT/'README.md').write_text('# Oredezh and EV95 global diagnostic checkpoint\n\n'
    'The prepared local wet-bank operator passed independent preflight; one numerical call produced an explicitly unaccepted candidate. '
    'The postsolve result is authoritative: `'+str(post.get('status'))+'`. Coverage of compiled physical and visible water is independently linked in its receipt. '
    'No threshold was relaxed and no candidate was promoted by this archive.\n\n'
    'The global census covers all native hinges of B and EV95 and distinguishes diagnostic populations. '
    'Civil source heights are preserved at every vertex in the global road/bridge guard. Neither is a native or visual acceptance.\n\n'
    'Large terrain/image/CSV artifacts and earlier preparation attempts remain external with SHA256 in manifest.json. '
    'BASE 1.0, whole-map bank shaping, water/render and runtime verification remain open.\n',encoding='utf-8')
shutil.copyfile(Path(__file__),OUT/'checkpoint_wet_bank_and_census.py')
print(json.dumps({'checkpoint':str(OUT),'copies':len(records),'external_refs':len(refrecords),'postsolve_status':post.get('status')}))
