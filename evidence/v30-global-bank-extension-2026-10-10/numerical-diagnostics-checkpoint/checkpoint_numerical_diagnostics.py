"""Archive corrected diagnostics and frozen global operators, without promotion."""
from pathlib import Path
import hashlib
import json
import shutil

G=Path(__file__).resolve().parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OUT=W/'evidence/v30-global-bank-extension-2026-10-10/numerical-diagnostics-checkpoint'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
groups={
 'physical-crossing':(G/'G/wet-bank-pilot/postsolve-consumer',[
     'crossing-geometry-fraction-v2.py','crossing-geometry-fraction-v2.json','quantization-diagnostic-errata-v2.json']),
 'bound-rounding':(G/'global-operator-prototype/global-sizing-ev95',[
     'audit_rounding_direction.py','rounding-direction-audit.json','preflight_global_resources.py']),
 'global-operator':(G/'global-operator-prototype/global-structured-operator',[
     'structured_operator.py','test_structured_operator.py','fixture-report.json',
     'independent_review.py','independent-review.json','measure_global_actions.py',
     'test_measure_global_actions.py','measurement-driver-review.json',
     'measurement/run-01/bench-invocation.started.json','measurement/run-01/measurement.json']),
 'plan':(G/'global-operator-prototype',['GLOBAL_OPERATOR_ACTION_PLAN.md']),
}
for _,(root,names) in groups.items():
    for name in names:
        if not (root/name).is_file():raise FileNotFoundError(root/name)
if OUT.exists():raise FileExistsError(OUT)
OUT.mkdir(parents=True)
records=[]
for prefix,(root,names) in groups.items():
    for name in names:
        source=root/name;dest=OUT/prefix/name;before=sha(source)
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        if sha(source)!=before or sha(dest)!=before:raise RuntimeError('Source/copy drift')
        records.append({'source':str(source),'copy':str(dest.relative_to(OUT)),'sha256':before,'bytes':source.stat().st_size})
(OUT/'manifest.json').write_text(json.dumps({'copied':records},indent=2)+'\n',encoding='utf-8')
(OUT/'README.md').write_text('''# Corrected numeric diagnostics and global operator measurement

No terrain is accepted or promoted by this checkpoint. EV95 remains the latest isolated preview.

The original wet-bank proposal is still unaccepted. The first exact CSR-crossing gate also rejected the baseline by floating-point roundoff, and its metadata indexing was wrong. The old 0-of-3^13 enumeration is therefore not a physical infeasibility proof. Direct rational crossing reconstruction passes all 116 baseline checks and finds 20 candidate incidences on five native edges outside their physical interval, by at most about 1.12 micrometres. A separate bounded conversion unit is required; the original solver call is not repeated.

The frozen sizing run-05 helper rounded bounds outward despite its name. The live helper is corrected and its fixtures pass. Reconstructing the true inward bounds changes 684,315 lower and 185,062 upper variable bounds, but produces zero infeasible nodes, no domain change, and keeps EV95 feasible. Thus operator counts remain valid; the old run-05 bounds must not be used for a solver.

The matrix-free operator is independently compared with the frozen CSR reference. The measurement receipt records the one real-map action/adjoint invocation, including any resource abort. It is not a solve, convergence claim, terrain acceptance or native/render proof. The measurement uses the explicit run_benchmark(review_path, review_sha) API with the separate driver review; the default CLI points to the earlier operator-only review.

BASE 1.0, full-map bank shaping, dynamic water, gray-water rendering and native EV95 validation remain open.
''',encoding='utf-8')
shutil.copyfile(Path(__file__),OUT/Path(__file__).name)
print(json.dumps({'checkpoint':str(OUT),'copies':len(records)}))
