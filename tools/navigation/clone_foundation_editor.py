"""Fresh full editable copy. Never traverse junctions or replace a checkout."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'tb/regional_outline_v3';target=ROOT/'tb/regional_foundation_v1'
assert not target.exists(),'Fresh target required'
items=list(source.rglob('*'))
assert not any(p.is_symlink() or p.is_junction() for p in items)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for p in items if p.is_file()]
before={p.relative_to(source).as_posix():sha(p) for p in files}
shutil.copytree(source,target)
for rel,digest in before.items():
    assert sha(source/rel)==digest and sha(target/rel)==digest,rel
report={'status':'PASS_COMPLETE_EDITABLE_COPY','source':str(source),'target':str(target),'file_count':len(files),'hashes':before}
(ROOT/'evidence/regional-foundation-v1/editor-clone.json').write_text(json.dumps(report,indent=2)+'\n')
print('Verified full editable copy:',len(files),'files')
