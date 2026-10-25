from pathlib import Path
import unittest,time,json,sys
R=Path(__file__).parent;WT=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
patterns=['test_qc_false_passes.py','test_road_mesh_edges.py','test_mesh_quality_v31.py','test_relief_multiscale.py','test_forest_transforms.py','test_stream_visibility.py','test_visual_probe_v31.py','test_road_probe_evidence.py','test_creases_v31.py','test_continuous_support_v31.py','test_presentmon_evidence.py','test_static_world_inventory.py']
suite=unittest.TestSuite()
for p in patterns:suite.addTests(unittest.defaultTestLoader.discover(str(WT/'tests'),pattern=p))
t=time.monotonic()
with (R/'tests.log').open('w',encoding='utf-8') as f:result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
record=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),seconds=time.monotonic()-t,patterns=patterns,success=result.wasSuccessful())
(R/'tests.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2));sys.exit(0 if result.wasSuccessful() else 1)
