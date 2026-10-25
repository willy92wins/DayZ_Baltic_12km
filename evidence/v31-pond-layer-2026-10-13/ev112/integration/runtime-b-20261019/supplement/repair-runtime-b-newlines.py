"""Repair this session's doubled Windows newlines while retaining exact foreign history."""
from pathlib import Path
import hashlib,json
O=Path(__file__).parent;W=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');rows=[]
start=b'<!-- LIVE-STATE:START -->';end=b'<!-- LIVE-STATE:END -->'
for p,original in [(W/'HANDOFF.md',O/'review-runtime-b-minor-backups/03-HANDOFF.md'),(Path('P:/DayZ_Baltic_12km_dev/HANDOFF.md'),O/'review-runtime-b-minor-backups/04-HANDOFF.md')]:
 raw=p.read_bytes();old=original.read_bytes();a=raw.index(start);b=raw.index(end);oa=old.index(start);ob=old.index(end)
 assert raw[:a].replace(b'\r',b'')==old[:oa].replace(b'\r',b'') and raw[b:].replace(b'\r',b'')==old[ob:].replace(b'\r',b''),'foreign content differs'
 assert b'\r\r\n' not in old,'anchor already has doubled newlines'
 live=raw[a:b].replace(b'\r',b'');nl=b'\r\n' if b'\r\n' in old else b'\n';live=live.replace(b'\n',nl)
 new=old[:oa]+live+old[ob:];assert new!=raw and b'\r\r\n' not in new
 backup=O/('runtime-b-newline-before-'+('worktree' if p.parent==W else 'root')+'.md');assert not backup.exists();backup.write_bytes(raw)
 assert p.read_bytes()==raw;p.write_bytes(new);assert p.read_bytes()==new and new[:oa]==old[:oa] and new[new.index(end):]==old[ob:]
 rows.append(dict(path=str(p),before=hashlib.sha256(raw).hexdigest(),after=hashlib.sha256(new).hexdigest(),backup=str(backup),exact_history_anchor=str(original),outside_live_exact=True))
q=O/'runtime-b-newline-repair.json';q.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');print(json.dumps(rows,indent=2))
# Validate byte-preserved shared histories without universal-newline translation.
v=O/'verify-runtime-b-closeout.py';s=v.read_text(encoding='utf-8')
s=s.replace("changes=read(O/'handoff-runtime-b-backups/manifest.json')['changes'];fresh=[];links=[];history=[]","changes=read(O/'handoff-runtime-b-backups/manifest.json')['changes'];fresh=[];links=[];history=[]\nrepairs={r['path']:r for r in read(O/'runtime-b-newline-repair.json')}")
s=s.replace("==c['after']","==repairs.get(str(p),c)['after']")
s=s.replace("old=Path(c['backup']).read_text(encoding='utf-8');new=raw.decode('utf-8')","old=Path(c['backup']).read_bytes().decode('utf-8').replace('\\r','');new=raw.decode('utf-8').replace('\\r','')")
v.write_text(s,encoding='utf-8')
