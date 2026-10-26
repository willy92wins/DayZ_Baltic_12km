from pathlib import Path
import subprocess,json,time,hashlib
R=Path(__file__).parent;O=R/'restart-final-review'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
assert not (O/'review-response.json').exists()
paths=[R/n for n in ['diagnose_next_river_bounds.py','audit_kit7_native_guards.py','diagnose_kit7_t_envelope.py','river-kit7-candidate-plan.md']]+[W/n for n in ['tools/navigation/observe_owned_server_exit.ps1','tests/test_server_exit_observer.py','tools/water/continuous_stream_pilot_v31.py']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths};(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
args=['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--tools','Read,Glob,Grep','--allowedTools','Read,Glob,Grep','--output-format','json','--no-session-persistence']
with (O/'review-response.json').open('wb') as out,(O/'review-stderr.log').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
 start=time.time();(O/'review-process.json').write_text(json.dumps(dict(pid=p.pid,start_epoch=start,args=args),indent=2))
 try:p.communicate((O/'review-brief.md').read_bytes(),timeout=600)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=30);raise
 assert before=={str(x):sha(x) for x in paths}
 (O/'completion.json').write_text(json.dumps(dict(exit_code=p.returncode,seconds=time.time()-start,inputs_unchanged=True),indent=2)+'\n')
 print('FABLE_EXIT',p.returncode);raise SystemExit(p.returncode)
