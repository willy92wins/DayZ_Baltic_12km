"""Install the approved probe CSV and a fresh personal mission.
CALLER MUST hold a freshly acquired DayZ MCP lease with no foreign/owned run.
No launcher/process changes, no credentials. Keep original live probe backups.
"""
from pathlib import Path
import json,sys,hashlib,shutil,re,datetime
O=Path(__file__).parent;tag=sys.argv[1];assert re.fullmatch('[a-z][a-z0-9]*',tag)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
deploy=json.loads((O/'deploy.json').read_text());assert deploy['forest_tag']==tag and deploy['offline_status']=='PASS'
mod=Path(deploy['mod']);assert sha(mod/'Addons/narva_trial.pbo')==deploy['world_sha256'] and sha(mod/'Addons/baltic_water_v30.pbo')==deploy['water_sha256']
review=json.loads((O/f'build-review-closure-{tag}.json').read_text());assert review['verdict'] in ('SOUND','SOUND-with-fixes') and review['critical_major_open']==0
assert review['world_sha256']==deploy['world_sha256'] and review['water_sha256']==deploy['water_sha256']
assert sha(review['raw_review'])==review['raw_review_sha256']
backup=O/'probe-live-prepared';manifest=json.loads((backup/'manifest.json').read_text())
mission=Path(manifest['mission']);assert mission==Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticBridgeProbeV2.BalticTrial')
original=manifest['original_live_hashes']
for p,h in original.items():
 assert sha(p)==h,(p,'Live file changed; do not overwrite')
 assert sha(backup/Path(p).name)==h
points=Path(manifest['prepared_points']);assert sha(points)==manifest['prepared_points_sha256'] and manifest['points']==4114
preview=O/f'personal-view-{tag}';route=json.loads((preview/'route.json').read_text());assert route['package_binding']['world_sha256']==deploy['world_sha256'] and route['package_binding']['water_sha256']==deploy['water_sha256']
source=Path(route['prepared_mission']);target=mission.parent/'BalticBasicEV112.BalticTrial';assert not target.exists();out=O/f'missions-installed-{tag}.json';assert not out.exists()
files=route['mission_files'];assert len(files)==16 and all(sha(source/p)==h for p,h in files.items())
target.mkdir();(target/'db').mkdir()
for rel,h in files.items():
 dst=target/rel;shutil.copyfile(source/rel,dst);assert sha(dst)==h
tmp=mission/'points.ev112.tmp';assert not tmp.exists();shutil.copyfile(points,tmp);assert sha(tmp)==manifest['prepared_points_sha256']
assert all(sha(p)==h for p,h in original.items()),'Live probe changed during preparation; do not replace'
tmp.replace(mission/'points.csv');assert sha(mission/'points.csv')==manifest['prepared_points_sha256']
assert sha(mission/'init.c')==original[str(mission/'init.c')]
receipt=dict(status='INSTALLED_NOT_RUN',time=datetime.datetime.now().astimezone().isoformat(),world_sha256=deploy['world_sha256'],water_sha256=deploy['water_sha256'],probe_mission=str(mission),points_sha256=sha(mission/'points.csv'),original_probe_backup=str(backup),personal_mission=str(target),personal_files=files,scope='CSV replacement and fresh preview files only; caller held MCP lease; no launch or visual acceptance')
out.write_bytes((json.dumps(receipt,indent=2)+'\n').encode());print('INSTALLED_NOT_RUN',mission,target)
