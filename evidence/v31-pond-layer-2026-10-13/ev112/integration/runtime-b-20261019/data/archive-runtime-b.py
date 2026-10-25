"""Archive the actual runtime correction, preserving both failed and final evidence.

No recursive traversal of junctions. Large binaries stay in place with SHA256.
The previous reviewed-ae-awaiting-runtime archive is never modified.
"""
from pathlib import Path
import os,stat,hashlib,json,shutil,datetime
O=Path(__file__).parent;WT=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
A=WT/'evidence/v31-pond-layer-2026-10-13/ev112/integration/runtime-b-20261019'
assert not A.exists()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
closure=json.loads((O/'runtime-b-closure.json').read_text(encoding='utf-8'))
assert closure['status']=='AUTHORIZED_SERVER_SCOPE_COMPLETED_WITH_EXPLICIT_PENDING'
assert all(closure['checks'].values()) and all(sha(p)==h for p,h in closure['evidence'].items())
paths=set()
folders=['water-fix-b','water-fix-a','runtime-capture-ae-20261019','runtime-eval-ae-20261019','water-temporal-ae','runtime-capture-runtime-b-20261019','runtime-eval-runtime-b-20261019','water-temporal-runtime-b','probe-runtime-b','personal-view-runtime-b','wrp-readback-runtime-b','surface-gates-runtime-b-results','forest-water-fix-b']
for folder in folders:
 root=O/folder;assert root.is_dir(),root
 for base,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=[n for n in dirs if n!='__pycache__' and not (os.lstat(Path(base)/n).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)]
  for name in files:
   p=Path(base)/name
   if not (p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT):paths.add(p)
for pattern in ('*runtime-b*.*','build-water-fix-b.py','*water-fix*.*','*water-temporal*.*','inspect-runtime-ae.py','runtime-launch-ae-20261019.json','missions-installed-ae.json','build-tools-preflight-20261019-233142.json'):
 paths.update(p for p in O.glob(pattern) if p.is_file())
for name in ('deploy.json','build-review-closure-ae.json','review-build-ae-r1.json','surface-runtime-b/manifest.json','package-runtime-b/package.json','stage-runtime-b/world-runtime-b-addonbuilder.log','stage-runtime-b/out/narva_trial.pbo','stage-runtime-b/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp','package-runtime-b/packed/narva_trial.pbo','RUNTIME-B-RESULT.md'):
 p=O/name;assert p.is_file(),p;paths.add(p)
dep=json.loads((O/'deploy-runtime-b.json').read_text(encoding='utf-8'))
for name in ('narva_trial.pbo','baltic_water_v30.pbo'):paths.add(Path(dep['mod'])/'Addons'/name)
paths.add(WT/'tools/terrain/apply_engine_water_margins_v31.py')
A.mkdir(parents=True);entries=[]
text_types={'.json','.jsonl','.log','.txt','.py','.ps1','.md','.csv','.c','.xml','.lst','.diff','.stderr'}
for p in sorted(paths,key=str):
 digest=sha(p);size=p.stat().st_size
 rel=Path('data')/p.relative_to(O) if p.is_relative_to(O) else Path('source')/p.name
 copy=size<=20*1024*1024 and p.suffix.lower() in text_types
 if copy:
  q=A/rel;q.parent.mkdir(parents=True,exist_ok=True);assert not q.exists();shutil.copyfile(p,q);assert sha(q)==digest
 entries.append(dict(source=str(p),bytes=size,sha256=digest,archived=str(rel).replace('\\','/') if copy else None,reason=None if copy else 'large or binary input retained at its verified source path'))
(A/'MANIFEST.json').write_text(json.dumps(dict(schema='ev112-runtime-evidence.v1',time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope=__doc__,entries=entries),indent=2)+'\n')
readme=(O/'RUNTIME-B-RESULT.md').read_text(encoding='utf-8')
readme+='\n\nArchivo: `MANIFEST.json` vincula '+str(len(entries))+' entradas por tamaño/SHA256; '+str(sum(bool(e['archived']) for e in entries))+' están copiadas. Los binarios grandes siguen en las rutas verificadas. El archivo previo [OT7 R1](../reviewed-ae-awaiting-runtime/README.md) conserva la evidencia anterior.\n'
(A/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps(dict(archive=str(A),entries=len(entries),copied=sum(bool(e['archived']) for e in entries),manifest_sha256=sha(A/'MANIFEST.json'))))
