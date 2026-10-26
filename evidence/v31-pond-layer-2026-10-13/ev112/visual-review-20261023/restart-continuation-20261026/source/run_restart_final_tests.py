from pathlib import Path
import subprocess,hashlib,json,time,sys
R=Path(__file__).parent;O=R/'restart-final-tests-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
assert not O.exists();O.mkdir()
paths=[W/'tools/navigation/observe_owned_server_exit.ps1',W/'tests/test_server_exit_observer.py']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):sha(p) for p in paths}
args=[sys.executable,'-I','-m','unittest','discover','-s','tests'];start=time.time()
with (O/'stdout.log').open('wb') as out,(O/'stderr.log').open('wb') as err:q=subprocess.run(args,cwd=W,stdout=out,stderr=err,timeout=180)
assert before=={str(p):sha(p) for p in paths}
receipt=dict(returncode=q.returncode,args=args,seconds=time.time()-start,source_sha256=before)
(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2));raise SystemExit(q.returncode)
