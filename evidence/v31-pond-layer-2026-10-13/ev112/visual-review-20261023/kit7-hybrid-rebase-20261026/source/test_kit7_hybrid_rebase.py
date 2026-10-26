from pathlib import Path
import hashlib,json,re,subprocess,sys,time
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/('kit7-hybrid-rebase-tests-20261026'+('-'+sys.argv[1] if len(sys.argv)>1 else ''));O.mkdir(exist_ok=False)
paths=[W/'tools/terrain'/n for n in ['repair_free_shapes_ev112.py','repair_guarded_shapes_ev112.py']]
names=['test_hybrid_witnesses_ev112','test_guarded_retention_ev112','test_guarded_relief_caps_ev112','test_shape_repair_constraints_ev112','test_rectangle_pilot_ev112']
paths += [W/'tests'/(n+'.py') for n in names]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):sha(p) for p in paths}
code="import sys,unittest; sys.path.insert(0,"+repr(str(W/'tests'))+"); suite=unittest.defaultTestLoader.loadTestsFromNames("+repr(names)+"); result=unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(not result.wasSuccessful())"
start=time.monotonic()
p=subprocess.run([sys.executable,'-I','-c',code],cwd=W,capture_output=True,timeout=300)
(O/'stdout.log').write_bytes(p.stdout);(O/'stderr.log').write_bytes(p.stderr)
assert all(sha(Path(k))==v for k,v in before.items())
count=re.search(rb'Ran (\d+) tests?',p.stderr);assert count and int(count.group(1))==29,'Nonempty expected suite required'
(O/'result.json').write_text(json.dumps(dict(returncode=p.returncode,seconds=time.monotonic()-start,inputs=before,inputs_unchanged=True,modules=names,tests_run=int(count.group(1)),stdout_file='stdout.log',stderr_file='stderr.log',stdout_sha256=sha(O/'stdout.log'),stderr_sha256=sha(O/'stderr.log')),indent=2)+'\n')
print(p.stdout.decode(errors='replace'));print(p.stderr.decode(errors='replace'));raise SystemExit(p.returncode)
