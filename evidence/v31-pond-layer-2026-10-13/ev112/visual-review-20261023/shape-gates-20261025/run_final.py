import hashlib,json,subprocess,sys,time,unittest,contextlib
from pathlib import Path
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if sys.argv[1]=='tests':
    prior=json.loads(Path('E:/DayZ-Baltic-Build/qc-council-20261024/recheck-20261024-forest-boundary/tests-expanded.json').read_text())
    patterns=prior['patterns']+['test_shape_patterns_ev112.py'];suite=unittest.TestSuite()
    for pattern in patterns:suite.addTests(unittest.defaultTestLoader.discover(str(W/'tests'),pattern=pattern))
    start=time.monotonic()
    with (R/'tests-final.log').open('w',encoding='utf-8') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
        result=unittest.TextTestRunner(stream=f,verbosity=2).run(suite)
    data=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),success=result.wasSuccessful(),seconds=time.monotonic()-start,
              patterns=patterns,interpreter=sys.executable,worktree=str(W),source_hashes={str(p):sha(p) for p in [W/'tests'/s for s in patterns]+[W/'tools/quality/shape_patterns_ev112.py',W/'tools/quality/screen_shapes_ev112.py']})
    (R/'tests-final.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2));sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
else:
    previous=json.loads((R/'s3-v3-run.json').read_text());argv=previous['argv'];argv[-1]=str(R/'s3-final')
    start=time.monotonic()
    with (R/'s3-final-run.log').open('w',encoding='utf-8') as f:
        r=subprocess.run(argv,cwd=W,stdout=f,stderr=subprocess.STDOUT)
    data=dict(argv=argv,returncode=r.returncode,seconds=time.monotonic()-start,expected_review_exit=2)
    (R/'s3-final-run.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
    sys.exit(0 if r.returncode==2 else 1)
