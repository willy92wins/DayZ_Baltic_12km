from pathlib import Path
import subprocess,sys,json,hashlib,time
R=Path(__file__).parent;O=R/'dry-apron-linear-run-20261027';O.mkdir(exist_ok=False)
paths=[R/'pilot_dry_apron.py',R/'test_dry_apron_pilot.py'];before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};start=time.monotonic()
test=subprocess.run([sys.executable,'-I',str(paths[1])],capture_output=True,timeout=60)
(O/'tests.stdout.log').write_bytes(test.stdout);(O/'tests.stderr.log').write_bytes(test.stderr)
assert test.returncode==0 and b'Ran 10 tests' in test.stderr and b'OK' in test.stderr
timeout=False
with (O/'stdout.log').open('wb') as out,(O/'stderr.log').open('wb') as err:
 try:p=subprocess.run([sys.executable,'-I',str(paths[0])],stdout=out,stderr=err,creationflags=0x08000000,timeout=900);rc=p.returncode
 except subprocess.TimeoutExpired:timeout=True;rc=None
receipt=dict(returncode=rc,timeout=timeout,seconds=time.monotonic()-start,inputs=before,source_unchanged=all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v for k,v in before.items()),dayz_runs=0)
(O/'completion.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if rc:sys.exit(rc)
