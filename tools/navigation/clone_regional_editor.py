"""Copy the complete editable baseline with a reread hash receipt."""
import shutil
from prepare_regional_outline import ROOT,sha,save

source=ROOT/'tb/narva_navigation_v3'
target=ROOT/'tb/regional_outline_v3'
if target.exists():
    raise ValueError('Fresh destination required')
items=list(source.rglob('*'))
if any(p.is_symlink() or p.is_junction() for p in items):
    raise ValueError('Unexpected reparse point')
files=[p for p in items if p.is_file()]
before={str(p.relative_to(source)).replace('\\','/'):sha(p) for p in files}
shutil.copytree(source,target)
for rel,digest in before.items():
    if sha(source/rel)!=digest or sha(target/rel)!=digest:
        raise ValueError('Source or destination changed: '+rel)
save(ROOT/'evidence/regional-outline-v3/editor-clone.json',
     {'status':'PASS_COMPLETE_EDITABLE_COPY','source':str(source),'target':str(target),
      'file_count':len(files),'hashes':before})
print('Complete editable copy verified:',len(files),'files')
