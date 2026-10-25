"""Preserve an actual owned server run's probe log before orderly close.

Read/copy only. The caller supplies a redacted receipt of the real public launch;
no lease token, identity credential, config file or arbitrary process is copied.
This checks framing and artifact binding, never physical/runtime acceptance.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,sys,uuid
O=Path(__file__).resolve().parent
sys.path.insert(0,str(O));from eval_bridge_regression_ev112 import load_rows
assert len(sys.argv)==3
launch_path=Path(sys.argv[1]).resolve();dest=Path(sys.argv[2]).resolve()
assert launch_path.is_relative_to(O) and dest.is_relative_to(O) and not dest.exists()
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
launch=read(launch_path);request=launch['request'];result=launch['tool_result']
assert result['status']=='succeeded' and result['project']=='DayZ_MCP' and result['mode']=='server'
run_id=str(uuid.UUID(result['run_id']));assert run_id==result['run_id']
assert request['project']=='DayZ_MCP' and request['mode']=='server'
assert request['no_base_mods'] is True and request['no_file_patching'] is True
assert request.get('build',False) is False and request.get('takeover',False) is False
assert len(result['artifacts_paths'])==1
profile=Path(result['artifacts_paths'][0]).resolve();assert profile.parent.name=='_server'
raw=profile/'baltic_bridge_probe_v2.log';assert raw.is_file()
requested=datetime.fromisoformat(launch['requested_at_utc']);assert requested.tzinfo is not None
assert raw.stat().st_mtime>=requested.timestamp()-2,'Probe predates this launch request'
deploy=read(O/'deploy-runtime-b.json');assert deploy['terrain_revision']=='runtime-b' and deploy['offline_status']=='PASS_AFFECTED_CONSUMERS_WITH_INHERITED_BASELINE'
mod=Path(deploy['mod']);assert list(map(Path,request['extra_mods']))==[mod]
review=read(O/'build-review-closure-runtime-b.json')
assert review['verdict'] in ('SOUND','SOUND-with-fixes') and review['critical_major_open']==0
assert review['world_sha256']==deploy['world_sha256'] and review['water_sha256']==deploy['water_sha256']
assert sha(review['raw_review'])==review['raw_review_sha256']
assert review['ready_for_server_probe'] is True and review['review_round']==2
assert review['deploy_sha256']==sha(O/'deploy-runtime-b.json')
assert all(sha(p)==h for p,h in deploy['probe_binding'].items())
installed=read(O/'missions-installed-ae.json');mission=Path(request['mission'])
assert mission==Path(installed['probe_mission'])
assert sha(mission/'points.csv')==installed['points_sha256']==sha(O/'probe-runtime-b/points.csv')
original=read(O/'probe-live-prepared/manifest.json')['original_live_hashes']
assert sha(mission/'init.c')==original[str(mission/'init.c')]
assert sha(mod/'Addons/narva_trial.pbo')==deploy['world_sha256']
assert sha(mod/'Addons/baltic_water_v30.pbo')==deploy['water_sha256']
before=sha(raw);dest.mkdir();copy=dest/raw.name;shutil.copyfile(raw,copy)
assert sha(raw)==before==sha(copy),'Probe log changed during capture'
shutil.copyfile(launch_path,dest/'launch.json')
points=read(O/'probe-runtime-b/points.json');assert len(points)==4114
frame_error=None;count=None
try:count=len(load_rows(copy,points))
except (ValueError,KeyError,TypeError,IndexError,UnicodeError) as e:frame_error=str(e)
receipt=dict(status='CAPTURED_FRAME_VALID' if frame_error is None else 'CAPTURED_FRAME_INVALID',
 captured_at_utc=datetime.now(timezone.utc).isoformat(),run_id=run_id,profile=str(profile),
 original_log=str(raw),raw_log_sha256=before,raw_log_mtime_utc=datetime.fromtimestamp(raw.stat().st_mtime,timezone.utc).isoformat(),
 launch_receipt_sha256=sha(launch_path),world_sha256=deploy['world_sha256'],water_sha256=deploy['water_sha256'],
 deploy_sha256=sha(O/'deploy-runtime-b.json'),points_sha256=sha(O/'probe-runtime-b/points.json'),
 framing_consumer_sha256=sha(O/'eval_bridge_regression_ev112.py'),captured_rows=count,frame_error=frame_error,
 tool_sha256=sha(__file__),physical_acceptance='NOT_EVALUATED',scope=__doc__)
(dest/'capture.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
sys.exit(0 if frame_error is None else 1)
