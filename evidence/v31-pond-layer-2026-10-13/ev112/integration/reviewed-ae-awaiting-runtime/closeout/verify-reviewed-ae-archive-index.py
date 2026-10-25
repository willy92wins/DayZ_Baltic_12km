"""Verify archived measurement bytes against their SHA256 and the staged Git blobs."""
from pathlib import Path
import hashlib,json,subprocess,shutil
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
rel='evidence/v31-pond-layer-2026-10-13/ev112/integration/reviewed-ae-awaiting-runtime';A=P/rel
manifest=json.loads((A/'manifest.json').read_text());index={}
for entry in subprocess.check_output(['git','ls-files','--stage','-z'],cwd=P).split(b'\0'):
 if not entry:continue
 meta,name=entry.split(b'\t',1);mode,oid,stage=meta.split();assert stage==b'0'
 index[name.decode('utf-8')]=oid.decode()
checked=[]
for row in manifest['files']:
 if row['archived_relative'] is None:continue
 path=A/row['archived_relative'];a=hashlib.sha256();b=hashlib.sha1()
 b.update(('blob '+str(path.stat().st_size)+'\0').encode())
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):a.update(chunk);b.update(chunk)
 assert a.hexdigest()==row['sha256'],str(path)
 key=path.relative_to(P).as_posix();assert index[key]==b.hexdigest(),key
 checked.append(key)
out=dict(status='PASS_BYTE_EXACT_ARCHIVE_AND_STAGED_BLOBS',checked=len(checked),
 manifest_sha256=hashlib.sha256((A/'manifest.json').read_bytes()).hexdigest(),
 source_commit=manifest['source_commit'],raw_verdicts_unchanged=True,
 whitespace='The complete staged diff check reports trailing spaces in two original G1 logs and unified-diff context lines. Those three raw artifacts are preserved byte-for-byte; the source/document check excluding exactly those three paths passes. No production gate or source formatting rule was relaxed.')
(O/'reviewed-ae-archive-index.json').write_text(json.dumps(out,indent=2)+'\n')
D=A/'closeout';D.mkdir(exist_ok=False)
for source in (Path(__file__),O/'reviewed-ae-archive-index.json',O/'reviewed-ae-local-doc-checks.json'):
 shutil.copyfile(source,D/source.name)
print(json.dumps(out))
