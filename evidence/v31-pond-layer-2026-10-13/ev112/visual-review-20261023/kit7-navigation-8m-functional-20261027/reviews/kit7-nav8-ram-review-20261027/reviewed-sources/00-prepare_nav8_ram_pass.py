"""Bind one fresh empty-server RAM pass after native607 acceptance; no launch."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav8-ram-ab-20261027'
sys.path.insert(0,str(W/'tools/performance'))
from bind_server_baseline_ev112 import prepare
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert __debug__ and len(sys.argv)==2
n=int(sys.argv[1]);assert 1<=n<=6
gate=read(D/'accepted.json');assert gate['status']=='ACCEPTED_AFTER_REVIEW'
assert all(sha(p)==h for p,h in gate['inputs'].items())
native=R/'kit7-nav8-consumer-20261027'
assert read(native/'result.json')['status']=='PASS_KIT7_NATIVE_GRAPH'
assert read(native/'identity-verification.json')['status']=='PASS_BOUND_NATIVE_PROBE_INPUTS'
dep=read(native/'deployment.json');assert all(sha(p)==h for p,h in dep['inputs'].items())
manifest=read(D/'missions.json');row=manifest['passes'][n-1];assert row['order']==n and manifest['order']=='A-B-B-A-A-B'
mission=Path(row['mission'])/'init.c';assert sha(mission)==row['mission_sha256']
out=D/f'pass-{n:02d}';assert not out.exists()
if n>1:
 previous=D/f'pass-{n-1:02d}';assert read(previous/'result.json')['status']=='PASS_COMPLETE_EMPTY_SERVER_MEASUREMENT'
 clean=read(previous/'cleanup.json');assert clean['close']['run_retired'] and clean['self']['state']=='none' and not clean['cleanup_degraded'] and not clean['own_run_present'] and not clean['pending_commands'] and not clean['error'] and not clean['cleanup_error']
exe=Path('E:/SteamLibrary/steamapps/common/DayZ Exp/DayZDiag_x64.exe');assert sha(exe)=='a500be804ffed5cde369337aeb6ab477ef5ee0b5015764be2b1953c85ec3060d'
vanilla=sorted((exe.parent/'Addons').glob('*.pbo'));assert len(vanilla)>100
assert {'worlds_chernarusplus.pbo','worlds_chernarusplus_data.pbo','worlds_chernarusplus_nav.pbo','worlds_chernarusplus_ce.pbo'}<={p.name for p in vanilla}
extras=[Path(p) for p in dep['packages'] if row['world']=='BalticTrial' or Path(p).name.lower()=='dayz_mcp.pbo']
assert len(extras)==(4 if row['world']=='BalticTrial' else 1)
for p in extras:assert sha(p)==dep['packages'][str(p)]
spec=dict(world=row['world'],artifacts=dict(mission=str(mission),executable=str(exe),server_config='C:/temp/DayZ_MCP_130_dev/_server/serverDZ.cfg'),packages=list(map(str,vanilla+extras)))
out.mkdir();write(out/'spec.json',spec);snapshot=prepare(spec);write(out/'before.json',snapshot)
proofs=[native/'result.json',native/'identity-verification.json',native/'deployment.json',D/'accepted.json',D/'missions.json',Path(__file__)]
write(out/'benchmark-gate.json',dict(status='BOUND_AFTER_NATIVE607',inputs={**gate['inputs'],**{str(p):sha(p) for p in proofs}},expected_loaded_packages={str(p):sha(p) for p in extras},mission=row,previous_passes_required=n-1))
print(json.dumps(dict(status='RAM_PASS_BOUND_NOT_LAUNCHED',order=n,world=row['world'],loaded_extra_packages=len(extras),all_packages=len(vanilla+extras))))
