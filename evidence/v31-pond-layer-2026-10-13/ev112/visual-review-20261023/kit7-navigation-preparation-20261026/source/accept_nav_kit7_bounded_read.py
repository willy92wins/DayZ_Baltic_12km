from pathlib import Path
import hashlib,json
R=Path(__file__).parent;D=R/'nav-kit7-preparation-20261026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
old=D/'launch-inputs.json';doc=read(old)
assert doc['coordinator_sha256']=='23cd56314a539521a52976fcc6c1ff1b45b5cfdd6b4c8a2e00704ca1c1f4f51f'
assert all(sha(Path(p))==h for p,h in doc['inputs'].items())
v2=(R/'orchestrate_nav_kit7_v2.js').read_text();v3=(R/'orchestrate_nav_kit7_v3.js').read_text();delta=read(D/'manifest-read-fix.json')['source_delta']
assert v2.replace(delta[0],delta[1])==v3
for rel in ['coordinator-control-flow-v3.json','command-flow-controls-v3.json','lease-control-flow-v3.json']:
 q=read(D/rel);assert q['coordinator_sha256']==sha(R/'orchestrate_nav_kit7_v3.js') and all(c['passed'] for c in q['cases']);doc['inputs'][str(D/rel)]=sha(D/rel)
q=read(D/'bounded-manifest-read-control.json');assert q['status']=='ACTUAL_TOOL_OUTPUT_PARSE_PASS' and q['output_characters']<3000
assert {str(Path(p)):h for p,h in q['packages'].items()}==doc['packages']
backup=D/'launch-inputs-v2.json';assert not backup.exists();backup.write_bytes(old.read_bytes())
for p in [backup,R/'repair_nav_kit7_manifest_read.py',R/'orchestrate_nav_kit7_v3.js',R/'test_nav_kit7_coordinator_v3.cjs',R/'test_nav_kit7_command_v3.cjs',R/'test_nav_kit7_lease_v3.cjs',D/'manifest-read-fix.json',D/'bounded-manifest-read-control.json',Path(__file__)]:doc['inputs'][str(p)]=sha(p)
doc['coordinator_sha256']=sha(R/'orchestrate_nav_kit7_v3.js')
doc['coordinator']=str(R/'orchestrate_nav_kit7_v3.js')
doc['bounded_read_resolution']='One-line projection replaces whole-manifest JSON transfer; full pre/post hashes unchanged. Real Functions tool output parsed714characters. All v3 flow controls pass; v2 independent review remains source of unchanged lifecycle logic.'
old.write_text(json.dumps(doc,indent=2)+'\n')
resolution=dict(status='READY_NOT_LAUNCHED_BANK_OCCUPIED',physical_status='SERVER_PROBE_PASS',physical_points=6801,physical_failures=0,review='Fable5.1 SOUND on v2 lifecycle; v3 differs only in bounded field projection, tested through actual tool',coordinator_sha256=doc['coordinator_sha256'],launch_inputs_sha256=sha(old),inputs_count=len(doc['inputs']),generation_attempts=0,client_started=False)
(D/'ready-summary.json').write_text(json.dumps(resolution,indent=2)+'\n')
print(json.dumps(resolution))

