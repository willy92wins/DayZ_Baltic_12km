from pathlib import Path
import contextlib,hashlib,json,subprocess,sys,time,unittest
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
S=Path('E:/DayZ-Baltic-Build/qc-council-20261024/road-merged-s3');B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=R/'terrain-free-final/terrain.npz';out=R/'terrain-free-final-merged';out.mkdir(exist_ok=False)
assert json.loads((src.parent/'report.json').read_text())['status']=='LOCAL_OFFLINE_PASS'
assert np.array_equal(np.load(src)['heights'],np.load(R/'terrain-free-c/terrain.npz')['heights'])
for name in ('cover.npy','envelope.npy'):(out/name).write_bytes((S/name).read_bytes())
cmd=[sys.executable,'-I',str(W/'tools/water/bury_edges_v31.py'),str(src),str(S/'terrain-buried.npz'),str(out/'cover.npy'),str(out/'envelope.npy'),str(S/'bury-work/fp0/footprint-report.json'),str(out/'terrain-buried.npz'),str(out/'bury-work'),str(out/'bury-report.json')]
with (out/'bury.log').open('w',encoding='utf-8') as f:subprocess.run(cmd,check=True,stdout=f,stderr=subprocess.STDOUT)
bury=json.loads((out/'bury-report.json').read_text());assert bury['changed_vs_input']==0 and not bury['final_new_exposed']
assert np.array_equal(np.load(src)['heights'],np.load(out/'terrain-buried.npz')['heights'])
old,new=np.load(S/'bury-work/fp0/footprint.npz'),np.load(out/'bury-work/fp0/footprint.npz')
assert old.files==new.files and all(np.array_equal(old[k],new[k],equal_nan=True) for k in old.files)
(out/'merge-verification.json').write_text(json.dumps(dict(status='WATER_FOOTPRINT_EXACT',bury_changes=0,arrays=old.files,terrain_sha256=sha(out/'terrain-buried.npz'),source_sha256=sha(src)),indent=2))
cmd=[sys.executable,'-I',str(W/'tools/terrain/review_visual_roads_ev112.py'),str(B),str(R/'terrain-free-final-roads'),'--terrain',str(out/'terrain-buried.npz'),'--expected-terrain-sha256',sha(out/'terrain-buried.npz')]
with (R/'terrain-free-final-roads.log').open('w',encoding='utf-8') as f:subprocess.run(cmd,cwd=W,check=True,stdout=f,stderr=subprocess.STDOUT)
sys.path.insert(0,str(W/'tools/quality'));from screen_shapes_ev112 import terrain_screen
with (R/'terrain-free-final-shapes.log').open('w',encoding='utf-8') as f,contextlib.redirect_stdout(f):shapes,h=terrain_screen(out/'terrain-buried.npz',out/'bury-work/fp0/footprint.npz')
shapes['terrain_sha256']=sha(out/'terrain-buried.npz');shapes['footprint_sha256']=sha(out/'bury-work/fp0/footprint.npz')
(R/'terrain-free-final-shapes.json').write_text(json.dumps(shapes,indent=2),encoding='utf-8')
patterns=json.loads((R/'tests-full.json').read_text())['patterns'];suite=unittest.TestSuite()
for pattern in patterns:suite.addTests(unittest.defaultTestLoader.discover(str(W/'tests'),pattern=pattern))
with (R/'tests-final.log').open('w',encoding='utf-8') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
rep=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),success=result.wasSuccessful(),patterns=patterns,
         sources={str(p):sha(p) for p in [W/'tests'/x for x in patterns]+list((W/'tools/terrain').glob('*constraints_ev112.py'))+[W/'tools/terrain/repair_free_shapes_ev112.py',W/'tools/water/continuous_stream_pilot_v31.py',W/'tools/water/review_continuous_stream_pilot_v31.py']})
(R/'tests-final.json').write_text(json.dumps(rep,indent=2),encoding='utf-8')
print(json.dumps(dict(tests=rep['tests'],success=rep['success'],terrain=shapes['finding_counts']),indent=2))
assert result.wasSuccessful() and not result.skipped
