from pathlib import Path
import hashlib,json,re,time,os
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
MAIN=W.parents[2]
O=R/'road-b1-source-discovery-20261029'
O.mkdir(exist_ok=False); start=time.monotonic()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
roots=[W/'tb',MAIN/'tb',R/'stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb',R/'package-kit7-fc-world-20261026',W/'evidence/ftt-pilot-2026-10-03']
report=dict(status='INCONCLUSIVE_CONSUMER',roots=[],files=[],text_matches=[],excluded=[],b0_scalars=[],bytes_read=0,entries_seen=0,limits=['Read-only source inventory; no native or compiled-road consumer certification.','No parser extension, no road geometry extracted or placed.','No match in covered text is not proof that RoadNetwork is absent.'])
pattern=re.compile(r'roadnetwork|roadslib|roadlib|roads[\\/]|asf1|asf2|shape|template|\.tv4p|\.tml|\.shp',re.I)
for root in roots:
 report['roots'].append(dict(path=str(root),exists=root.exists()))
 if not root.exists():continue
 for folder,dirs,files in os.walk(root,followlinks=False):
  dirs[:]=sorted(d for d in dirs if not (Path(folder)/d).is_symlink())
  for name in sorted(files):
   report['entries_seen']+=1
   if report['entries_seen']>10000 or time.monotonic()-start>110:raise RuntimeError('discovery_budget')
   p=Path(folder)/name;s=p.stat();rel=p.relative_to(root).as_posix()
   row=dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns)
   report['files'].append(row)
   if p.suffix.lower() not in ('.txt','.xml','.tml','.tv4p','.json','.cpp','.cfg','.md','.ini'):continue
   if s.st_size>2*1024**2 or report['bytes_read']+s.st_size>20*1024**2:
    report['excluded'].append(dict(path=str(p),reason='text_size_budget'));continue
   raw=p.read_bytes();report['bytes_read']+=len(raw);row['sha256']=hashlib.sha256(raw).hexdigest()
   try:text=raw.decode('utf-8-sig')
   except UnicodeDecodeError:
    report['excluded'].append(dict(path=str(p),reason='non_utf8_text'));continue
   hits=[dict(line=i,text=line[:400]) for i,line in enumerate(text.splitlines(),1) if pattern.search(line)]
   if hits:report['text_matches'].append(dict(path=str(p),sha256=row['sha256'],count=len(hits),first=hits[:40]))
for p in sorted((R/'road-b0-discovery-r1-20261028').glob('local-faces-*.json')):
 data=json.loads(p.read_text(encoding='utf-8'));scalars={k:v for k,v in data.items() if not isinstance(v,(dict,list))}
 fields={k:v for k,v in data.items() if re.search(r'center|centre|bounding|^bc$|pivot',k,re.I)}
 report['b0_scalars'].append(dict(path=str(p),sha256=sha(p),keys=list(data),scalars=scalars,center_fields=fields))
report['seconds']=time.monotonic()-start
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],entries=report['entries_seen'],text_files=len([f for f in report['files'] if 'sha256'in f]),matching_files=len(report['text_matches']),bytes=report['bytes_read'],seconds=report['seconds'],b0_centers=[x['center_fields'] for x in report['b0_scalars']])) )
