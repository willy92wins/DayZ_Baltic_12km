from pathlib import Path
import hashlib,json
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
suite=R/'b3e2-tests-final-20261028/report.json';review=R/'b3e2-code-review-20261028/adjudication.md';report=json.loads(suite.read_bytes());assert report['status']=='TESTS_PASS' and report['tests']==24 and report['seconds']<=120
files=[Path(p) for p in report['postimages']]+[W/'plans/ev112-b3e-build-continuation-20261028.md',suite,review,R/'b3e2-code-review-20261028/completion.json',R/'b3e2-code-review-20261028/review.md']
assert all(sha(Path(p))==h for p,h in report['postimages'].items())
approval=R/'b3e2-execution-approval-20261028.json';out=R/'prism-b3e2-pair-20261028';assert not approval.exists() and not out.exists()
a=dict(schema='B3E2_EXECUTION_V1',status='REVIEW_ADJUDICATED_TESTS_PASS',output=str(out),tests=str(suite),review_adjudication=str(review),pins={str(p):sha(p) for p in files})
approval.write_text(json.dumps(a,indent=2),encoding='utf-8')
state=R/'ACTIVE-WORK.md';old=state.read_bytes();state.write_bytes(('''# B3E2 listo: ejecución única autorizada

Código revisado Fable109.734s y adjudicado;24testsPASS6.156s.
Ejecutar una vez b3e2-execution-approval-20261028.json -> prism-b3e2-pair-20261028.
Presupuestos preflight60/build150cada/gate180cada,2GiB. Control antes de candidato.
Al aparecer eventos/driver seguir esa operación, NO duplicarla. No201/DayZ/lease.
Original47FAIL21inciertos; carreteras en preparación independiente.

---
''').encode()+old)
print(str(approval))
