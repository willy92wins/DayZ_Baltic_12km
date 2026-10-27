"""Prepare and deploy a new generation-only candidate; never launch DayZ."""
from pathlib import Path
import hashlib,json,re,shutil,sys
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/playtest'),str(W/'tools/navigation')]
from attach_navmesh import read_pbo
from package_nav12_config_ev112 import verify_config_delta
D=R/'nav-kit7-12m-preparation-20261027';B=R/'package-kit7-nav12-input-20261027'
DEST=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Nav12Input');BASE=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not D.exists() or not any(D.iterdir()), 'Preparation output is not empty'
v=read(B/'verification.json');assert v['status']=='PASS_ISOLATED_NAV12_CONFIG_PACKAGE' and v['unchanged_entries']==6826
world=B/'Addons/narva_trial.pbo';assert sha(world)==v['pbo_sha256']=='ed1acb1d993a705996edad1bc3008f14e0b904483ad207d5b903a4d2aee35287'
assert sha(BASE/'Addons/narva_trial.pbo')=='10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc'
_,_,old=read_pbo(BASE/'Addons/narva_trial.pbo');_,_,new=read_pbo(world)
assert set(old)==set(new) and [k for k in old if old[k]!=new[k]]==['config.bin','navmesh/baltic_trial.nm']
assert hashlib.sha256(new['baltic_trial.wrp']).hexdigest()=='0da63d3f258923e784a62bcb59bb1d7f2ab99866816f530bfe73cd4211b23254'
assert old['config.bin']==(B/'original.bin').read_bytes()
assert new['config.bin']==(B/'config.bin').read_bytes()
verify_config_delta((B/'original.cpp').read_text(encoding='utf-8'),(B/'roundtrip.cpp').read_text(encoding='utf-8'))
del old,new
phys=read(R/'kit7-overlap-native-20261026/full/result.json')
assert phys['status']=='SERVER_PROBE_PASS' and phys['points']==6801 and phys['failure_count']==0 and phys['identity_bound'] and phys['inputs_unchanged']
D.mkdir(exist_ok=True);(DEST/'Addons').mkdir(parents=True,exist_ok=True)
packages={}
for name,source in [('narva_trial.pbo',world),('baltic_water_v30.pbo',BASE/'Addons/baltic_water_v30.pbo'),('baltic_stream_pilot.pbo',BASE/'Addons/baltic_stream_pilot.pbo')]:
    target=DEST/'Addons'/name;digest=sha(source)
    if target.exists(): assert sha(target)==digest, 'Existing deployment changed'
    else: shutil.copyfile(source,target)
    assert sha(target)==digest;packages[str(target)]=digest
bridge=Path('P:/Mods/@DayZ_MCP/Addons/DayZ_MCP.pbo');packages[str(bridge)]=sha(bridge)
assert {Path(p).name.lower():h for p,h in packages.items()}=={'narva_trial.pbo':v['pbo_sha256'],'baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43','baltic_stream_pilot.pbo':'3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6','dayz_mcp.pbo':'7078c2e4ac2231976d7afd4a0b0ee677f9822c371f3faa927b2ea356212e600a'}
source=(R/'orchestrate_nav_kit7_fifo_v4.js').read_text(encoding='utf-8')
old_block=re.search(r'const requiredPackages=\{[\s\S]*?\};',source).group()
replacements={'generateKit7Navigation':'generateKit7Nav12','nav-kit7-preparation-20261026':'nav-kit7-12m-preparation-20261027','navmesh-kit7-v9-20261026':'navmesh-kit7-12m-v9-20261027','@DayZ_Baltic_EV112_Kit7Overlap':'@DayZ_Baltic_EV112_Kit7Nav12Input','@dayz_baltic_ev112_kit7overlap':'@dayz_baltic_ev112_kit7nav12input','10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc':v['pbo_sha256'],'máximo7200s':'máximo18000s','--timeout-s 7200':'--timeout-s 18000','-MaxSeconds 7500':'-MaxSeconds 18300','rounds>750':'rounds>1830','navKit7':'navKit7Twelve'}
for a,b in replacements.items():assert a in source,a;source=source.replace(a,b)
needle="const frozenPackages=packageMap(prepared.packages),physicalPackages=packageMap(physical.packages);"
assert needle in source;source=source.replace(needle,old_block.replace('requiredPackages','physicalRequiredPackages')+'\n'+needle)
old_gate="[frozenPackages,physicalPackages].some(v=>Object.keys(v).length!==4||Object.entries(requiredPackages).some(([path,hash])=>v[path]!==hash))"
new_gate="Object.keys(frozenPackages).length!==4||Object.entries(requiredPackages).some(([path,hash])=>frozenPackages[path]!==hash)||Object.keys(physicalPackages).length!==4||Object.entries(physicalRequiredPackages).some(([path,hash])=>physicalPackages[path]!==hash)"
assert old_gate in source;source=source.replace(old_gate,new_gate)
coordinator=R/'orchestrate_kit7_nav12_generation.js';assert not coordinator.exists();coordinator.write_text(source,encoding='utf-8')
test=(R/'test_nav_kit7_fifo_v4.cjs').read_text(encoding='utf-8')
physical_block=re.search(r' const packages=\{[\s\S]*?\};',test).group().replace('const packages','const physicalPackages')
for a,b in {**replacements,'orchestrate_nav_kit7_fifo_v4.js':'orchestrate_kit7_nav12_generation.js','coordinator-control-flow-fifo-v4.json':'generation-controls.json'}.items():test=test.replace(a,b)
anchor=" const gateFailure=name.startsWith('physics_')"
assert anchor in test;test=test.replace(anchor,physical_block+'\n'+anchor)
test=test.replace('packages:{...packages}','packages:{...physicalPackages}')
test=re.sub(r'phys\.packages\[Object\.keys\(packages\)\[(\d)\](\.toLowerCase\(\))?\]',r'phys.packages[Object.keys(physicalPackages)[\1]\2]',test)
test=test.replace('=Object.values(packages)[0]','=Object.values(physicalPackages)[0]')
test=test.replace("Object.entries(packages).map(([p,h],i)","Object.entries(physicalPackages).map(([p,h],i)")
harness=R/'test_kit7_nav12_generation.cjs';assert not harness.exists();harness.write_text(test,encoding='utf-8')
paths=[world,B/'verification.json',B/'original.cpp',B/'roundtrip.cpp',B/'original.bin',B/'config.bin',R/'kit7-overlap-native-20261026/full/result.json',Path(__file__),coordinator,harness,
       W/'plans/ev112-kit7-nav12-cost-20261027.md',W/'tools/navigation/generate_navmesh_console.py',W/'tools/navigation/observe_owned_server_exit.ps1',W/'tools/navigation/inspect_navmesh_v9_ev112.py',W/'tools/navigation/package_nav12_config_ev112.py',
       W/'tests/test_navmesh_generator_identity.py',W/'tests/test_navmesh_v9_prefixes_ev112.py',W/'tests/test_server_exit_observer.py',W/'tests/test_nav12_config_ev112.py',
       Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticKit7NavData.BalticTrial/init.c'),Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/NavMeshGenerator/NavMeshGenerator_x64.exe'),Path('E:/SteamLibrary/steamapps/common/DayZ Exp/DayZDiag_x64.exe')]
for name in ['record_nav_c_event.ps1','capture_owned_server_identity.ps1','bind_nav_c_rpt_clock.ps1','capture_nav_c_generator.ps1','cancel_owned_nav_c_generator.ps1','copy_owned_server_rpt.ps1']:paths.append(R/name)
inputs={str(p):sha(p) for p in paths};inputs.update(packages)
(D/'launch-inputs.json').write_text(json.dumps(dict(status='PREPARED_PENDING_CODE_REVIEW',packages=packages,inputs=inputs,observer_sha256=sha(W/'tools/navigation/observe_owned_server_exit.ps1'),coordinator=str(coordinator),coordinator_sha256=sha(coordinator),generation_seconds=18000,observer_seconds=18300,physical_lineage=dict(exact_unchanged_entries=6825,changed_entries=['config.bin','navmesh/baltic_trial.nm'],source_world_sha256='10e09e3fbec79e786db65e5e9f5bd9e4f5ed7d7efc8121cbbab87c4bf266f9bc',config_only_nav_tile_width=True)),indent=2)+'\n')
print(json.dumps(dict(status='PREPARED_PENDING_CODE_REVIEW',packages=packages,inputs=len(inputs))))
