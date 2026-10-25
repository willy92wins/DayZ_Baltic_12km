"""Freeze reviewed numerical units and their terminal evidence; no promotion."""
from pathlib import Path
import hashlib,json,shutil
G=Path(__file__).resolve().parent
P=G/'global-operator-prototype'
WP=G/'G/wet-bank-pilot/postsolve-consumer'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OUT=W/'evidence/v30-global-bank-extension-2026-10-10/conversion-global-bounds-checkpoint'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
groups={
 'fused-normal':(P/'global-structured-operator/optimized-normal',['PLAN.md','fused_normal.py','test_optimized_normal.py','fixture-report.json','independent-review.json','compare_normal_once.py','comparison/independent-review.json','comparison/run-01/comparison.json']),
 'global-bounds':(P,['GLOBAL_DRY_SOLVE_PLAN.md','prepare_global_dry_bounds.py','global-dry-solve/prepared-01/receipt.json','global-dry-solve/prepared-01/independent-review.json']),
 'admm-adapter':(P/'global-admm-adapter',['PLAN.md','matrix_free_admm.py','test_matrix_free_admm.py','fixture-report-runtime-guards.json','independent-review.json']),
 'quantization-10':(WP/'float32-neighborhood-v1',['PLAN.md','executor.py','test_executor.py','independent-preflight-review.json','pin-literal-repair.json','real-enumeration-01/receipt.json','compatibility_diagnostic.py','real-enumeration-01/compatibility-diagnostic.json','real-enumeration-01/compatibility-diagnostic.md']),
 'quantization-components':(WP/'float32-component-conversion-v1',['PLAN.md','convert_components.py','test_components.py','independent-review-terminal-receipt.json','real-conversion-01/receipt.json','ac3-diagnosis/diagnose_ac3.py','ac3-diagnosis/certificate.json','ac3-diagnosis/certificate.md']),
 'objective-screen':(P/'global-dry-unconstrained-screen',['PLAN.md','screen.py','independent_fixture.py','independent-review.json']),
}
records=[]
for prefix,(base,names) in groups.items():
 for name in names:
  p=base/name
  if not p.is_file():raise FileNotFoundError(p)
if OUT.exists():raise FileExistsError(OUT)
OUT.mkdir(parents=True)
for prefix,(base,names) in groups.items():
 for name in names:
  p=base/name;h=sha(p);d=OUT/prefix/name;d.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(p,d)
  if sha(p)!=h or sha(d)!=h:raise ValueError('Copy drift '+str(p))
  records.append({'source':str(p),'copy':str(d.relative_to(OUT)),'sha256':h,'bytes':p.stat().st_size})
refs=[]
for p in [P/'global-dry-solve/prepared-01/bounds.npz']:
 refs.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
(OUT/'manifest.json').write_text(json.dumps({'copied':records,'external':refs},indent=2)+'\n',encoding='utf-8')
(OUT/'README.md').write_text('''# Numeric conversion, prepared global bounds and rejected long-solve route

No terrain is promoted. EV95 remains the isolated preview with 66,058 changed heights versus B; native/render acceptance is pending.

The bounded 10-node quantization enumeration completed all 59,049 assignments without a feasible neighbor. A separate component-based conversion over all 121 authorized variables rejected by exact AC-3 before search. The minimal two-edge contradiction is recorded; neither receipt proves that the wider physical height problem is infeasible. Both units remain terminal and are not rerun or widened.

The fused normal matches the former action within 2.84e-14 and measured 1.1574 s -> 0.4708 s. Global dry bounds preserve 2,712,136 variables and 8,380,418 native face radii, with EV95 feasible and positive known-water clearance. The ADMM fixture matches CP but the independent review rejects claiming global resource readiness: progress/guards and cost need work. No global ADMM solve ran.

An unconstrained objective diagnostic is separately reviewed. Its first attempt stopped at the memory preflight before run-01 creation or any global PCG: 7,563,341,824 available bytes did not satisfy the conservative 3 GiB process cap plus 6 GiB reserve. It did not write terrain or an optimization vector. Do not reinterpret that resource refusal as a numerical failure.

Sources and receipts are copied byte-for-byte, including line endings. Large bounds remain an external pinned reference. BASE 1.0, wet-bank acceptance, full-map shaping, dynamic water and gray-water rendering remain open.
''',encoding='utf-8')
shutil.copyfile(Path(__file__),OUT/Path(__file__).name)
print(json.dumps({'checkpoint':str(OUT),'copies':len(records),'external':len(refs)}))
