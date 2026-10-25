"""Read/copy the completed diagnostic of a real owned run before orderly close."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,uuid
O=Path(__file__).parent;D=O/'water-temporal-runtime-b'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
read=lambda p:json.loads(Path(p).read_text())
launch=read(D/'launch.json');request=launch['request'];result=launch['tool_result']
assert result['status']=='succeeded' and result['project']==request['project']=='DayZ_MCP' and result['mode']==request['mode']=='server'
assert str(uuid.UUID(result['run_id']))==result['run_id']
assert request['no_base_mods'] and request['no_file_patching'] and request['build'] is False and request['takeover'] is False
dep=read(O/'deploy-runtime-b.json');review=read(O/'build-review-closure-runtime-b.json');bind=read(D/'binding.json')
assert bind['deploy_sha256']==review['deploy_sha256']==sha(O/'deploy-runtime-b.json') and review['ready_for_server_probe']
assert review['critical_major_open']==0 and review['review_round']==2 and sha(review['raw_review'])==review['raw_review_sha256']
assert list(map(Path,request['extra_mods']))==[Path(dep['mod'])]
for name,key in [('narva_trial.pbo','world_sha256'),('baltic_water_v30.pbo','water_sha256')]:assert sha(Path(dep['mod'])/'Addons'/name)==dep[key]==review[key]
mission=Path(request['mission']);assert mission==Path(bind['mission'])
assert all(sha(D/n)==h for n,h in bind['files'].items())
for name in ('init.c','points.csv'):assert sha(mission/name)==bind['files'][name]
assert len(result['artifacts_paths'])==1
profile=Path(result['artifacts_paths'][0]).resolve();assert profile.parent.name=='_server'
raw=profile/'baltic_water_temporal_ev112.log';requested=datetime.fromisoformat(launch['requested_at_utc']);assert requested.tzinfo
mtime=raw.stat().st_mtime;assert mtime>=requested.timestamp()-2,'stale temporal log'
dest=D/raw.name;assert not dest.exists();before=sha(raw);shutil.copyfile(raw,dest);assert sha(raw)==sha(dest)==before
lines=dest.read_text().splitlines();assert lines[0]=='BALTIC_WATER_TEMPORAL_EV112;BalticTrial' and lines[1]=='BEGIN;30;8' and lines[-1]=='END;30;8' and len(lines)==243
receipt=dict(status='CAPTURED_FRAME_ONLY',run_id=result['run_id'],captured_at_utc=datetime.now(timezone.utc).isoformat(),original_log=str(raw),original_mtime_utc=datetime.fromtimestamp(mtime,timezone.utc).isoformat(),raw_log_sha256=before,world_sha256=dep['world_sha256'],water_sha256=dep['water_sha256'],deploy_sha256=sha(O/'deploy-runtime-b.json'),launch_sha256=sha(D/'launch.json'),binding_sha256=sha(D/'binding.json'),scope=__doc__)
(D/'capture.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
