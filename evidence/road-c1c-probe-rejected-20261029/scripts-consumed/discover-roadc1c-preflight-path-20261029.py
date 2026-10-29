from pathlib import Path
import os,json,hashlib,time,stat
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c-path-discriminator-20261029';D.mkdir(exist_ok=False);start=time.monotonic();alias=Path('C:/Users/guill/.agents/skills/dayz-preflight/preflight.py');canonical=alias.resolve(strict=True);paths=[alias.parent,Path(os.readlink(alias.parent)),canonical.parent]
rows=[]
for p in paths:
 s=p.lstat();rows.append({'path':str(p),'attributes':getattr(s,'st_file_attributes',None),'tag':getattr(s,'st_reparse_tag',None),'link_target':os.readlink(p) if getattr(s,'st_file_attributes',0)&1024 else None,'dev':s.st_dev,'ino':s.st_ino})
def read(p):
 with p.open('rb') as f:
  pre=os.fstat(f.fileno());b=f.read(16385);post=os.fstat(f.fileno())
 assert len(b)<=16384 and (pre.st_dev,pre.st_ino,pre.st_size,pre.st_mtime_ns)==(post.st_dev,post.st_ino,post.st_size,post.st_mtime_ns)
 return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'dev':pre.st_dev,'ino':pre.st_ino,'mtime_ns':pre.st_mtime_ns}
records=[read(alias),read(canonical),read(R/'road-c1c-probe-20261029/tools/AddonBuilder/logger.xml')]
out={'status':'SAVED_FAILURE_PATH_DISCRIMINATOR','rows':rows,'canonical':str(canonical),'reads':records,'seconds':time.monotonic()-start,'probe_r0_reclassified':False,'execution_count_preflight_help_build':0,'logger_original_expected_sha':'1d24d7d4afb5249efbef3435195bbea4d1a2d6317292637c7f834b69f8470005'}
(D/'report.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))
