"""Build isolated candidate with all AE object bytes retained and four changed heights. No deployment."""
from pathlib import Path
import json,sys,subprocess,hashlib,time,concurrent.futures
O=Path(__file__).parent;D=O/'water-fix-b';P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert json.loads((D/'delta-audit.json').read_text())['status']=='PASS'
assert all(x['all_measurements_identical'] for x in json.loads((D/'phase-gate-comparison.json').read_text()))
assert json.loads((D/'bury-report.json').read_text())['changed_vs_input']==0
for gate in (2,3,4,7,10):
 r=json.loads((D/f'kit/gate-g{gate}.json').read_text());assert (len(r)==49 and all(s.get('passed') is True for s in r.values())) if gate in (2,3,4) else r.get('passed') is True,gate
base=O/'stage-forest-ae/root/dayz_baltic_12km_dev/tb/narva_trial';assert sha(base/'baltic_trial.wrp')=='f0cb7ba8a15e4c70cac4cb0ae7f7ca14e195cb091bc952c2f47d214d80610e95'
reader=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/tools/terrain/wrp0wzd.py');assert sha(reader)=='8b85cec46ba72851a4ec829c5b0adcc88727ee852c3f699ab7a15e31b50fee2a'
include=O/'build-review-ae-provenance/compile-include.lst';assert sha(include)=='7b1b270afdd6a21b8ef44b979353ef06350b1a75ff2be6f4b84e129b9baf3b00'
empty=D/'empty-records.json';empty.write_text('[]\n');stage=O/'stage-runtime-b/root/dayz_baltic_12km_dev/tb/narva_trial';assert not stage.exists()
compile_source=(O/'compile_world_ev112_ae.ps1').read_text();compile_source=compile_source.replace('stage-forest-ae','stage-runtime-b').replace('world-aedonbuilder.log','world-runtime-b-addonbuilder.log')
old_include="C:\\Users\\guill\\OneDrive\\Documentos\\DayZ Projects\\DayZ_Baltic_12km_dev\\.claude\\worktrees\\codex-handoff-review-74f290\\packages\\baltic-road-v29\\tools\\include.lst"
assert old_include in compile_source;compile_source=compile_source.replace(old_include,str(include));compile_source=compile_source.replace('EV112 AB forest / C terrain','EV112 AE forest / runtime-margin B terrain');compile_file=D/'compile-world.ps1';compile_file.write_text(compile_source)
binding=json.loads((O/'surface-scope-ae-binding.json').read_text());binding['terrain']=dict(path=str(D/'terrain.npz'),sha256=sha(D/'terrain.npz'));(D/'surface-scope.json').write_text(json.dumps(binding,indent=2)+'\n')
def run(name,cmd):
 t=time.time()
 with (D/(name+'.log')).open('w') as f:rc=subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,cwd=P).returncode
 row=dict(step=name,rc=rc,seconds=time.time()-t,cmd=list(map(str,cmd)));(D/(name+'-execution.json')).write_text(json.dumps(row,indent=2)+'\n');print(name,rc,round(time.time()-t,1),flush=True)
 if rc:raise RuntimeError(name)
 return row
def world():
 r=[run('stage',[sys.executable,'-I',P/'tools/terrain/stage_bridges_v31.py',base,D/'terrain.npz',empty,stage,D/'stage-report.json'])]
 r.append(run('compile',['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',compile_file]));return r
def surface():
 b=binding;base_layers=['E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010/build-wide-slope/surface/layers','E:/DayZ-Baltic-Build/v30-mixed-bank-incremental-fixed-20261010/surface/layers','E:/DayZ-Baltic-Build/v30-complete-dry-surface-20261009/surface/layers','E:/DayZ-Baltic-Build/v30-mixed-bank-constrained-20261010/surface/layers']
 return [run('surface',[sys.executable,'-I',P/'tools/terrain/patch_surface_v31.py',D/'terrain.npz',O/'surface-runtime-b','--footprint',O/'fp-ev112-c/footprint.npz','--workers','2','--include-changed','v31_causeway','--include-changed','v31_dam','--include-pad','1','--include-cells',b['explicit_native_cells']['path'],'--include-cells-sha256',b['explicit_native_cells']['sha256'],'--forest-clearings',b['clearings']['path'],'--forest-clearings-sha256',b['clearings']['sha256'],'--base-layers',';'.join(base_layers)])]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(world),pool.submit(surface)];rows=[r for future in futures for r in future.result()]
(D/'build-steps.json').write_text(json.dumps(rows,indent=2)+'\n');print('BUILT_NOT_DEPLOYED',flush=True)
