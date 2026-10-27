"""Bind one fresh empty-server RAM pass after native607 acceptance; no launch."""
from pathlib import Path
import hashlib,json,sys,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav8load1-ram-ab-20261027'
sys.path.insert(0,str(W/'tools/performance'))
from bind_server_baseline_ev112 import prepare
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert __debug__ and len(sys.argv)==2
n=int(sys.argv[1]);assert 1<=n<=6
gate=read(D/'accepted.json');assert gate['status']=='ACCEPTED_AFTER_REVIEW'
review=R/'kit7-nav8load1-ram-review-20261027'
reviewed=read(review/'source-hashes.json');adjudication=read(review/'adjudication.json')
assert adjudication['status']=='ACCEPTED_AFTER_REVIEW' and reviewed
required=adjudication['inputs']
assert set(reviewed)<=set(required)<=set(gate['inputs'])
changed={str(R/n) for n in ('prepare_nav8load1_ram_pass.py','finalize_nav8load1_ram_ab.py','test_nav8load1_joint_gate.py')}|{str(D/'joint-gate-controls.json')}
assert set(adjudication['post_review_changes'])==changed
assert all(required[p]==h for p,h in reviewed.items() if p not in changed)
followup=R/'kit7-nav8load1-recovery-review-20261027'
final_review=read(followup/'adjudication.json');assert final_review['status']=='ACCEPTED_AFTER_REVIEW'
assert all(required[p]==final_review['inputs'][p] for p in changed)
assert all(gate['inputs'][p]==h for p,h in required.items())
for proof in (review/'source-hashes.json',review/'adjudication.json',followup/'source-hashes.json',followup/'adjudication.json'):
 assert gate['inputs'].get(str(proof))==sha(proof)
assert all(sha(p)==h for p,h in gate['inputs'].items())
native=R/'kit7-nav8load1-consumer-20261027'
nav=read(native/'result.json');config=read(native/'config-result.json');joint=read(native/'joint-result.json')
identity=read(native/'identity-verification.json');host=read(native/'host-identity.json');deployment=read(native/'deployment.json')
assert nav['status']=='PASS_KIT7_NATIVE_GRAPH' and config['status']=='PASS_NATIVE_LOAD1_CONFIG'
assert joint['status']=='PASS_LOAD1_CONFIG_AND_NATIVE607' and identity['status']=='PASS_BOUND_NATIVE_PROBE_INPUTS'
assert joint['run_id'] and joint['run_id']==identity['run_id']==host['run_id']
assert joint['config_status']==config['status'] and joint['native_status']==nav['status']
canonical=lambda rows:{str(Path(p).resolve()).casefold():h for p,h in rows.items()}
assert len(deployment['packages'])==4
assert canonical(joint['packages'])==canonical(identity['packages'])==canonical(host['package_hashes'])==canonical(deployment['packages'])
dep=read(native/'deployment.json');assert all(sha(p)==h for p,h in dep['inputs'].items())
manifest=read(D/'missions.json');row=manifest['passes'][n-1];assert row['order']==n and manifest['order']=='A-B-B-A-A-B'
mission=Path(row['mission'])/'init.c';assert sha(mission)==row['mission_sha256']
assert {p.name for p in mission.parent.iterdir()}=={'init.c'},'Fresh mission inventory required'
assert re.fullmatch(r'baltic_ab_\d{2}_[0-9a-f]{12}\.log',row['profile_log'])
assert mission.read_text(encoding='utf-8-sig').count(row['profile_log'])==2
out=D/f'pass-{n:02d}';assert not out.exists()
if n>1:
 previous=D/f'pass-{n-1:02d}';assert read(previous/'result.json')['status']=='PASS_COMPLETE_EMPTY_SERVER_MEASUREMENT'
 clean=read(previous/'cleanup.json');assert clean['close']['run_retired'] and clean['self']['state']=='none' and not clean['cleanup_degraded'] and not clean['own_run_present'] and not clean['pending_commands'] and not clean['error'] and not clean['cleanup_error']
exe=Path('E:/SteamLibrary/steamapps/common/DayZ Exp/DayZDiag_x64.exe');assert sha(exe)=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'
vanilla=sorted((exe.parent/'Addons').glob('*.pbo'));assert len(vanilla)>100
assert {'worlds_chernarusplus.pbo','worlds_chernarusplus_data.pbo','worlds_chernarusplus_nav.pbo','worlds_chernarusplus_ce.pbo'}<={p.name for p in vanilla}
extra_pairs=[(Path(p),h) for p,h in dep['packages'].items() if row['world']=='BalticTrial' or Path(p).name.lower()=='dayz_mcp.pbo']
extras=[p for p,h in extra_pairs]
assert len(extras)==(4 if row['world']=='BalticTrial' else 1)
for p,h in extra_pairs:assert sha(p)==h
spec=dict(world=row['world'],artifacts=dict(mission=str(mission),executable=str(exe),server_config='C:/temp/DayZ_MCP_130_dev/_server/serverDZ.cfg'),packages=list(map(str,vanilla+extras)))
attempts=D/'attempt-reservations';attempts.mkdir(exist_ok=True)
with (attempts/f'pass-{n:02d}.json').open('x',encoding='utf-8') as f:
 json.dump(dict(order=n,mission=row,accepted_sha256=sha(D/'accepted.json')),f,indent=2)
out.mkdir();write(out/'spec.json',spec);snapshot=prepare(spec);write(out/'before.json',snapshot)
proofs=[native/'config-result.json',native/'joint-result.json',native/'result.json',native/'identity-verification.json',native/'deployment.json',D/'accepted.json',D/'missions.json',Path(__file__)]
write(out/'benchmark-gate.json',dict(status='BOUND_AFTER_LOAD1_CONFIG_AND_NATIVE607',inputs={**gate['inputs'],**{str(p):sha(p) for p in proofs}},expected_loaded_packages={str(p):sha(p) for p in extras},mission=row,previous_passes_required=n-1))
print(json.dumps(dict(status='RAM_PASS_BOUND_NOT_LAUNCHED',order=n,world=row['world'],loaded_extra_packages=len(extras),all_packages=len(vanilla+extras))))
