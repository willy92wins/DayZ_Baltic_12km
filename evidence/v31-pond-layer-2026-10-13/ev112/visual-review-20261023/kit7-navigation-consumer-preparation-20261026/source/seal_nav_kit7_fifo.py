from pathlib import Path
import hashlib,json
R=Path(__file__).parent;D=R/'nav-kit7-preparation-20261026'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=D/'launch-inputs.json';doc=json.loads(p.read_text())
assert all(sha(Path(n))==h for n,h in doc['inputs'].items())
test=json.loads((D/'coordinator-control-flow-fifo-v4.json').read_text())
assert test['status']=='CONTROL_FLOW_PASS' and test['coordinator_sha256']==sha(R/'orchestrate_nav_kit7_fifo_v4.js')
assert all(x['passed'] for x in test['cases']) and all(x['rejected'] for x in test['negative_mutations'])
backup=D/'launch-inputs-v3-before-fifo.json';assert not backup.exists();backup.write_bytes(p.read_bytes())
for f in [backup,R/'prepare_nav_kit7_fifo.py',R/'orchestrate_nav_kit7_fifo_v4.js',R/'test_nav_kit7_fifo_v4.cjs',D/'coordinator-control-flow-fifo-v4.json',D/'fifo-user-request.json',Path(__file__)]:doc['inputs'][str(f)]=sha(f)
doc.update(coordinator=str(R/'orchestrate_nav_kit7_fifo_v4.js'),coordinator_sha256=sha(R/'orchestrate_nav_kit7_fifo_v4.js'),queue_mode='Native lifecycle FIFO at explicit user request; no periodic availability checks, no takeover.')
p.write_text(json.dumps(doc,indent=2)+'\n')
a=R/'ACTIVE-WORK.md';s=a.read_text(encoding='utf-8');a.write_text('# ACTIVO — cola FIFO solicitada por Guillermo\n\nAutomatización periódica PAUSED. Coordinadororchestrate_nav_kit7_fifo_v4.js listo, SHA'+doc['coordinator_sha256']+'. Entradas selladas. Próxima llamada Functions ejecutará generateKit7Navigation:dayz_test_run(on_busy=queue,wait_for_box_s=600,takeover=false), cola nativa de lease sin preadquirir. No crear otra espera ni lanzar otro run.\n\n## Historia\n'+s,encoding='utf-8')
print(json.dumps(dict(status='FIFO_COORDINATOR_READY',inputs=len(doc['inputs']),sha=doc['coordinator_sha256'])))

