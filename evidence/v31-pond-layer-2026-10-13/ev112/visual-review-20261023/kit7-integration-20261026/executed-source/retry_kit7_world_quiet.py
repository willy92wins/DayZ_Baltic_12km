"""One isolated logging-only retry; original timeout and all gates remain intact."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
S=R/'stage-kit7-fc-20261026'; O=R/'kit7-world-quiet-unit-20261026'
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
old=read(R/'kit7-world-unit-20261026/compile.receipt.json')
assert old['timeout'] and old['inputs_unchanged'] and not (S/'out/narva_trial.pbo').exists()
assert not O.exists(); O.mkdir()
gate=read(R/'kit7-world-review-20261026/accepted.json')
assert gate['status']=='ACCEPTED_TECHNICAL_WORLD_ONLY'
assert all(sha(p)==h for p,h in gate['inputs'].items())
package=R/'package_kit7_fc_world_quiet.py'
original=(R/'package_kit7_fc_world.py').read_text()
replacements={
 "R/'kit7-world-review-20261026/accepted.json'":"R/'kit7-world-quiet-unit-20261026/accepted.json'",
 "R/'kit7-world-unit-20261026/compile.receipt.json'":"R/'kit7-world-quiet-unit-20261026/compile.receipt.json'",
 "S/'out/narva_trial.pbo'":"S/'out-quiet/narva_trial.pbo'",
}
expected=original
for a,b in replacements.items():
 assert a in expected;expected=expected.replace(a,b)
assert package.read_text()==expected,'unexpected packager change'
for p in [Path(__file__),package,W/'plans/ev112-kit7-compile-logging-retry-20261026.md',R/'kit7-world-unit-20261026/builder-help.txt',R/'kit7-world-unit-20261026/compile.receipt.json']:
 gate['inputs'][str(p)]=sha(p)
gate['retry_scope']='Only extended logging disabled; fresh output/temp; same source, tools and acceptance; one 900-second retry.'
(O/'accepted.json').write_text(json.dumps(gate,indent=2)+'\n')
_,_,entries=read_pbo(R/'package-kit7-fc-pilot-v2-20261026/Addons/baltic_stream_pilot.pbo')
dep=R/'pilot-kit7-fc-20261026/temp/baltic_stream_pilot'
def stable():
 assert {p.relative_to(dep).as_posix():p.read_bytes() for p in dep.rglob('*') if p.is_file()}==entries
 return all(sha(p)==h for p,h in gate['inputs'].items())
assert stable()
out=S/'out-quiet';temp=S/'temp-quiet'
assert not out.exists() and not temp.exists();out.mkdir()
args=[r'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\AddonBuilder\AddonBuilder.exe',str(S/'root/dayz_baltic_12km_dev/tb/narva_trial'),str(out),'-prefix=dayz_baltic_12km_dev\\tb\\narva_trial','-project='+str(S/'root'),'-temp='+str(temp),'-binarizeNoLogs','-include=C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290/packages/baltic-road-v29/tools/include.lst']
for label,argv,budget in [('compile',args,900),('readback-package',[sys.executable,'-I',str(package)],900)]:
 assert stable();began=time.time();timeout=False
 with (O/(label+'.stdout.log')).open('wb') as stdout,(O/(label+'.stderr.log')).open('wb') as stderr:
  p=subprocess.Popen(argv,cwd=W,stdout=stdout,stderr=stderr,creationflags=0x08000000)
  (O/(label+'.process.json')).write_text(json.dumps(dict(pid=p.pid,args=argv,start_epoch=began),indent=2)+'\n')
  try:rc=p.wait(timeout=budget)
  except subprocess.TimeoutExpired:
   timeout=True
   if p.poll() is None:
    k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=30,creationflags=0x08000000)
    (O/(label+'.timeout-cleanup.log')).write_bytes(k.stdout+k.stderr)
   try:p.wait(timeout=30);rc=p.returncode
   except subprocess.TimeoutExpired:rc=None
 result=dict(returncode=rc,timeout=timeout,seconds=time.time()-began,inputs_unchanged=stable(),args=argv)
 if label=='compile' and (out/'narva_trial.pbo').exists():result['compiled_pbo_sha256']=sha(out/'narva_trial.pbo')
 (O/(label+'.receipt.json')).write_text(json.dumps(result,indent=2)+'\n');print(label,rc,flush=True)
 assert rc==0 and not timeout and result['inputs_unchanged']
 if label=='compile':
  assert 'compiled_pbo_sha256' in result
  log=(O/'compile.stdout.log').read_text(errors='replace')+(O/'compile.stderr.log').read_text(errors='replace')
  assert 'Build Successful' in log
print('TECHNICAL_WORLD_OBJECTS_AND_PAYLOAD_VERIFIED_BOUNDARY_PENDING')
