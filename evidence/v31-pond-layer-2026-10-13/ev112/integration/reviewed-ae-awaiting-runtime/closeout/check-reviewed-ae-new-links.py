"""Check only links introduced by this owner update, preserving unrelated vault debt."""
from pathlib import Path
from urllib.parse import unquote
from collections import Counter
import hashlib,json,re
O=Path(__file__).parent;R=json.loads((O/'reviewed-ae-handoff-update.json').read_text())
pattern=r'\[[^\]\n]*\]\((<[^>\n]+>|[^)\n]+)\)'
def links(text):return {v.strip('<>') for v in re.findall(pattern,text)}
checked=[];drift=[]
for i,row in enumerate(R['files']):
 path=Path(row['path']);before=(O/'reviewed-ae-handoff-backups'/f'{i:02d}-{path.name}').read_bytes();current=path.read_bytes()
 assert hashlib.sha256(before).hexdigest()==row['before_sha256']
 if hashlib.sha256(current).hexdigest()!=row['after_sha256']:drift.append(str(path))
 for target in links(current.decode('utf-8'))-links(before.decode('utf-8')):
  if target.startswith(('https://','http://','app://','#')):continue
  target=unquote(target.split('#',1)[0]);dest=Path(target)
  if not re.match(r'^[A-Za-z]:[/\\]',target):dest=path.parent/target
  assert dest.exists(),(str(path),target)
  checked.append(dict(source=str(path),target=str(dest.resolve())))
AI=Path('C:/Users/guill/ObsidianVault/AI');index=AI/'30_Sessions/index.md';root=index.parent.resolve();targets=[]
for raw in re.findall(pattern,index.read_text(encoding='utf-8')):
 target=unquote(raw.strip('<>').split('#',1)[0])
 if target.startswith(('http://','https://')):continue
 path=(index.parent/target).resolve()
 if path.parent==root and path.suffix.lower()=='.md' and path!=index:targets.append(str(path).casefold())
duplicates={k:v for k,v in Counter(targets).items() if v>1}
own=str((root/'2026-10-18-dayz-baltic-ev112-ot1-execution.md').resolve()).casefold();assert Counter(targets)[own]==1
root_handoff=Path('P:/DayZ_Baltic_12km_dev/HANDOFF.md');snapshot=(O/'reviewed-ae-handoff-backups/01-HANDOFF.md').read_bytes()
assert root_handoff.read_bytes().startswith(snapshot.split(b'<!-- LIVE-STATE:START -->')[0]),'Foreign asset preface changed'
out=dict(status='PASS_ALL_NEW_LOCAL_TARGETS',new_links=len(checked),checks=checked,shared_files_changed_since_own_write=drift,
 own_session_index_entries=Counter(targets)[own],duplicate_exact_session_targets=len(duplicates),duplicates=duplicates,
 duplicate_scope='Markdown links in the canonical index resolved to .md files directly under30_Sessions; no claim about non-Markdown aliases.',root_asset_preface_preserved=True)
(O/'reviewed-ae-new-links-check.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
