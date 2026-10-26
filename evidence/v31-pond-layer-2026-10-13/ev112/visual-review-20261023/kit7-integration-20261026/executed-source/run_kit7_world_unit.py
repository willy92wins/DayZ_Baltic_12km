"""One bounded world build followed by complete compiled-object readback."""
from pathlib import Path
import subprocess,sys,json,time,hashlib
R=Path(__file__).parent;O=R/'kit7-world-unit-20261026';S=R/'stage-kit7-fc-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
gate=read(R/'kit7-world-review-20261026/accepted.json');assert gate['status']=='ACCEPTED_TECHNICAL_WORLD_ONLY' and gate['inputs']
assert all(sha(p)==h for p,h in gate['inputs'].items())
assert read(O/'dependencies.json')['status']=='EXACT_COMPILED_PILOT_DEPENDENCIES_READY'
_,_,dependency_entries=read_pbo(R/'package-kit7-fc-pilot-v2-20261026/Addons/baltic_stream_pilot.pbo')
dependency_root=R/'pilot-kit7-fc-20261026/temp/baltic_stream_pilot'
def check_dependencies():
 actual={p.relative_to(dependency_root).as_posix():p.read_bytes() for p in dependency_root.rglob('*') if p.is_file()}
 assert actual==dependency_entries,'compiled pilot dependency drift'
check_dependencies()
stages=[('compile',['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(W/'tools/terrain/compile_visual_pilot_ev112.ps1'),'-Stage',str(S),'-Pilot',str(R/'pilot-kit7-fc-20261026')],900),('readback-package',[sys.executable,'-I',str(R/'package_kit7_fc_world.py')],900)]
for label,args,budget in stages:
 assert not (O/(label+'.receipt.json')).exists();began=time.time();timeout=False
 with (O/(label+'.stdout.log')).open('wb') as out,(O/(label+'.stderr.log')).open('wb') as err:
  p=subprocess.Popen(args,cwd=W,stdout=out,stderr=err,creationflags=0x08000000)
  (O/(label+'.process.json')).write_text(json.dumps(dict(pid=p.pid,args=args,start_epoch=began),indent=2)+'\n')
  try:rc=p.wait(timeout=budget)
  except subprocess.TimeoutExpired:
   # Only this still-live child/tree, never DayZ or a process discovered by name.
   timeout=True
   if p.poll() is None:
    kill=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=30,creationflags=0x08000000)
    (O/(label+'.timeout-cleanup.log')).write_bytes(kill.stdout+kill.stderr)
   try:p.wait(timeout=30);rc=p.returncode
   except subprocess.TimeoutExpired:rc=None
 check_dependencies()
 same=all(sha(q)==h for q,h in gate['inputs'].items());result=dict(returncode=rc,timeout=timeout,seconds=time.time()-began,inputs_unchanged=same,args=args)
 if label=='compile' and (S/'out/narva_trial.pbo').exists():result['compiled_pbo_sha256']=sha(S/'out/narva_trial.pbo')
 (O/(label+'.receipt.json')).write_text(json.dumps(result,indent=2)+'\n');print(label,rc,flush=True)
 if rc!=0 or timeout or not same:raise SystemExit(1)
print('TECHNICAL_WORLD_OBJECTS_AND_PAYLOAD_VERIFIED_BOUNDARY_PENDING')
