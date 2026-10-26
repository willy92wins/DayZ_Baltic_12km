"""Isolated compile and existing binary consumer; no deployment or DayZ lifecycle."""
from pathlib import Path
import subprocess,json,hashlib,sys,time,os
R=Path(__file__).parent;K=R/'river-kit7-midpoint-a-20261026';V=R/'kit7-midpoint-saved-review-20261026';O=R/'kit7-midpoint-build-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
write=lambda p,x:Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
receipt=read(V/'receipt.json');assert receipt['status']=='PASS_SAVED_KIT7_COLLISION' and receipt['inputs_unchanged'] and receipt['contact_sha256']==sha(V/'contact.json')
frozen=read(V/'inputs.json');assert all(sha(p)==h for p,h in frozen.items())
builder=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/AddonBuilder/AddonBuilder.exe')
reader=Path('C:/temp/moto_lanes/review_g3/tools/odol_reader.py')
assert sha(reader)=='fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57'
dependencies=[Path('P:/'),Path('P:/DZ'),Path('P:/bin'),Path('P:/core'),Path('P:/Mods'),builder,Path('P:/DZ/water/streambed/streambed_leaf_long_straight.p3d')]
assert all(p.exists() for p in dependencies)
assert not (K/'packed').exists() and not (K/'temp').exists()
O.mkdir(exist_ok=False)
extra=[Path(__file__),W/'tools/water/pack_continuous_stream_pilot_v31.ps1',W/'tools/water/verify_compiled_stream_pilot_v31.py',W/'tools/water/mesh_quality_v31.py',W/'tools/playtest/attach_navmesh.py',reader,builder,V/'receipt.json',V/'contact.json']
frozen.update({str(p):sha(p) for p in extra});write(O/'inputs.json',frozen)
write(O/'preflight.json',dict(status='MANUAL_DEPENDENCIES_PRESENT',dependencies=[str(p) for p in dependencies],reader_sha256=sha(reader),reason='Shared dayz-preflight/preflight.py fails to parse at line213 (unescaped Windows backslash); direct checks used, shared skill untouched.',scope='No mount/deploy/process operation. Isolated builder also validates P:/DZ,bin,core before adding junctions inside the new source root.'))
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
stages=[('compile',['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(W/'tools/water/pack_continuous_stream_pilot_v31.ps1'),'-Pilot',str(K)],900),('binary',[sys.executable,'-I',str(W/'tools/water/verify_compiled_stream_pilot_v31.py'),str(K),'--reader-root',str(reader.parent)],900)]
for label,args,budget in stages:
 began=time.time();timeout=False
 with (O/(label+'.stdout.log')).open('wb') as out,(O/(label+'.stderr.log')).open('wb') as err:
  try:q=subprocess.run(args,env=env,cwd=W,stdout=out,stderr=err,timeout=budget,creationflags=0x08000000|0x00004000);code=q.returncode
  except subprocess.TimeoutExpired:code=None;timeout=True
 same=all(sha(p)==h for p,h in frozen.items())
 write(O/(label+'.receipt.json'),dict(returncode=code,timeout=timeout,seconds=time.time()-began,inputs_unchanged=same,args=args))
 print(label,code,flush=True)
 if code!=0 or timeout or not same:raise SystemExit(1)
binary=read(K/'binary-review.json');assert binary['status']=='BINARY_PASS' and binary['pbo_sha256']==sha(K/'packed/baltic_stream_pilot.pbo') and len(binary['models'])==139 and (K/'records.json').is_file()
write(O/'receipt.json',dict(status='ISOLATED_KIT7_BINARY_PASS_CONTACT_PENDING',pbo_sha256=binary['pbo_sha256'],binary_review_sha256=sha(K/'binary-review.json'),records_sha256=sha(K/'records.json'),models=139,inputs_unchanged=True,limits='No WRP integration/deploy/native/visual acceptance; packed full-contact overlay remains pending.'))
print('ISOLATED_KIT7_BINARY_PASS_CONTACT_PENDING')
