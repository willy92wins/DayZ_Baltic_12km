from pathlib import Path
import hashlib,json
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
R=Path(r'E:/DayZ-Baltic-Build/shape-repair-20261025')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=R/'prism-b3f-package-20261028';approval=R/'b3f-execution-approval-20261028.json'
assert not out.exists() and not approval.exists() and not (R/'b3f-execution-driver-20261028.log').exists()
review=R/'b3f-code-review-20261028';suite=R/'b3f-tests-final-20261028/report.json'
s=json.loads(suite.read_bytes());c=json.loads((review/'completion.json').read_bytes())
assert c['complete'] and c['within_budget'] and c['inputs_unchanged'] and c['models']==['claude-fable-5-1']
assert s['status']=='TESTS_PASS' and s['tests']==29 and s['seconds']<=120
for p,h in s['postimages'].items():assert sha(Path(p))==h,p
files=[*[Path(p) for p in s['postimages']],W/'plans/ev112-b3f-package-composition-20261028.md',review/'adjudication.md',review/'completion.json',review/'review.md',review/'inputs.json',suite,R/'run_b3f_execution_20261028.py',R/'b3f-review-claims-20261028/report.json']
data=dict(schema='B3F_EXECUTION_V1',status='REVIEW_ADJUDICATED_TESTS_PASS',output=str(out),review_adjudication=str(review/'adjudication.md'),tests=str(suite),pins={str(p):sha(p) for p in files},budgets={'preparation_preflight_seconds':60,'pack_seconds':120,'consumer_seconds':120,'outer_seconds':300,'max_bytes':2147483648},no_deployment_or_dayz=True)
approval.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
p=R/'ACTIVE-WORK.md';prior=p.read_text(encoding='utf-8')
p.write_text('# B3F ejecución única preparada — 28-10-2026\n\nCódigo revisado Fable116s y adjudicado; 29testsPASS5.203s.\nAprobación b3f-execution-approval-20261028.json ligada a postimágenes.\nRunner nuevo run_b3f_execution_20261028.py, salida prism-b3f-package-20261028.\nSeguir su resultado si existen eventos/log; NO DUPLICAR ni relanzar.\nPreflight60s/pack120s/consumer120s,2GiB,outer300s. Sólo composición201.\nNo DayZ, despliegue, lease ni run. RoadB0 sigue borrador pendiente revisión.\n\n---\n'+prior,encoding='utf-8')
print(json.dumps({'approval':str(approval),'sha256':sha(approval),'output':str(out)}))
