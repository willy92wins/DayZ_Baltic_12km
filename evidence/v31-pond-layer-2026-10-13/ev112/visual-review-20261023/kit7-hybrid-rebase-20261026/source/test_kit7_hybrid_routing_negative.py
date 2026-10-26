"""Synthetic mutation control only; never a terrain candidate or source edit."""
from pathlib import Path
import hashlib,io,json,sys,types,unittest
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tests'),str(W/'tools/terrain'),str(W/'tools/water')]
import test_guarded_retention_ev112 as fixture
path=W/'tools/terrain/repair_guarded_shapes_ev112.py';source=path.read_text()
needle='preserve_satisfied_witnesses=a.hybrid_witnesses';assert source.count(needle)==1
mutated=source.replace(needle,'preserve_satisfied_witnesses=False')
module=types.ModuleType('synthetic_mutant');module.__file__=str(path)
exec(compile(mutated,str(path),'exec'),module.__dict__)
fixture.author=module
output=io.StringIO();suite=unittest.TestSuite([fixture.GuardedRetention('test_fresh_hybrid_candidate_uses_all_existing_guards')])
result=unittest.TextTestRunner(stream=output,verbosity=2).run(suite)
assert result.testsRun==1 and len(result.failures)==1 and not result.errors
assert "'bounds' != 'hybrid'" in output.getvalue()
O=R/'kit7-hybrid-rebase-tests-20261026-v2';(O/'routing-negative.log').write_text(output.getvalue())
receipt=dict(status='EXPECTED_MUTATION_REJECTED',tests_run=1,expected_assertion_failures=1,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),mutation='Ignore hybrid flag when invoking the unchanged solver',scope='In-memory mutation, synthetic temporary fixture only; no authored production terrain or source change')
(O/'routing-negative.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
