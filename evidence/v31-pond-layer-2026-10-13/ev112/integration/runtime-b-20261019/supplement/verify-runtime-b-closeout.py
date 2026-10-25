from pathlib import Path
import json,hashlib,re,difflib,urllib.parse,datetime
O=Path(__file__).parent;W=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
A=W/'evidence/v31-pond-layer-2026-10-13/ev112/integration/runtime-b-20261019'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
manifest=read(A/'MANIFEST.json');copied=[e for e in manifest['entries'] if e['archived']]
assert all(sha(A/e['archived'])==e['sha256'] for e in copied)
changes=read(O/'handoff-runtime-b-backups/manifest.json')['changes'];fresh=[];links=[];history=[]
repairs={r['path']:r for r in read(O/'runtime-b-newline-repair.json')}
for c in changes:
 p=Path(c['path']);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==repairs.get(str(p),c)['after'],('later writer',p)
 old=Path(c['backup']).read_bytes().decode('utf-8').replace('\r','');new=raw.decode('utf-8').replace('\r','');fresh.append(dict(path=str(p),sha256=sha(p)))
 if p.name=='HANDOFF.md':
  start='<!-- LIVE-STATE:START -->';end='<!-- LIVE-STATE:END -->'
  assert old.split(start,1)[0]==new.split(start,1)[0] and old.split(end,1)[1].replace('\r\n','\n')==new.split(end,1)[1].replace('\r\n','\n')
  history.append(dict(path=str(p),outside_live_preserved=True))
 if p.name=='2026-10-18-dayz-baltic-ev112-ot1-execution.md':
  marker='## Histórico de ejecución, conservado';assert old.split(marker,1)[1].replace('\r\n','\n')==new.split(marker,1)[1].replace('\r\n','\n')
  history.append(dict(path=str(p),historical_section_preserved=True))
 a=old.splitlines();b=new.splitlines()
 for tag,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():
  if tag not in ('insert','replace'):continue
  for label,target in re.findall(r'\[([^\]]+)\]\((<[^>]+>|[^)\s]+)\)', '\n'.join(b[k:l])):
   target=urllib.parse.unquote(target.strip('<>')).split('#',1)[0]
   if not target or re.match(r'^(https?|mailto|app|codex):',target):continue
   dest=Path(target);dest=dest if dest.is_absolute() else p.parent/dest
   assert dest.exists(),(p,target);links.append(dict(source=str(p),target=str(dest),exists=True))
for p in (A/'README.md',O/'personal-view-runtime-b/README.md',O/'personal-view-runtime-b/launch-request.json'):
 p.read_text(encoding='utf-8');assert p.exists()
root=Path('P:/DayZ_Baltic_12km_dev')
assert (root/'PROJECT-MAP.md').stat().st_mtime >= (root/'HANDOFF.md').stat().st_mtime
assert (W/'PROJECT-MAP.md').stat().st_mtime >= (W/'HANDOFF.md').stat().st_mtime
for folder,log in [('runtime-capture-runtime-b-20261019','baltic_bridge_probe_v2.log'),('water-temporal-runtime-b','baltic_water_temporal_ev112.log')]:
 c=read(O/folder/'capture.json');assert c['raw_log_sha256']==sha(O/folder/log)
t=read(O/'water-temporal-runtime-b/diagnosis.json');assert t['raw_sha256']==sha(O/'water-temporal-runtime-b/baltic_water_temporal_ev112.log')
index=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/index.md').read_text(encoding='utf-8')
assert index.count('](./2026-10-18-dayz-baltic-ev112-ot1-execution.md)')==1
result=dict(status='PASS_OWNED_CLOSEOUT',time_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),archive_entries=len(manifest['entries']),copied_files_verified=len(copied),new_or_changed_links_verified=links,shared_files_reread=fresh,preserved_history=history,project_maps_fresh=True,canonical_index_exactly_once=True,raw_captures_match=True,limits='This is not a global vault/regression-gate PASS. The global audit is recorded separately.')
(A/'closeout-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ('new_or_changed_links_verified','shared_files_reread','preserved_history')},indent=2))
