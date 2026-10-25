from pathlib import Path
import json,hashlib,shutil,sys
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-water-visual-fix-2026-10-08'
B=Path('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=Path('P:/Mods/@DayZ_Baltic_FlatWaterPreview/Addons/narva_trial.pbo')
world=B/'stitched-world/out/narva_trial.pbo';water=B/'stitched-water/water/packed/baltic_water_v30.pbo'
_,p0,a=read_pbo(base);_,p1,b=read_pbo(world)
assert p0==p1 and set(a)==set(b)
changed=[k for k in a if a[k]!=b[k]];assert changed==['baltic_trial.wrp']
dest=Path('P:/Mods/@DayZ_Baltic_StitchedWaterPilot/Addons');dest.mkdir(parents=True,exist_ok=False)
for p in (world,water):shutil.copyfile(p,dest/p.name);assert sha(p)==sha(dest/p.name)
report=dict(status='ISOLATED_VISUAL_PILOT_NOT_ACCEPTED',destination=str(dest.parent),files={p.name:sha(p) for p in dest.glob('*.pbo')},changed_world_entries=changed,terrain_exact=True,
source_world_sha256=sha(B/'stitched-world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'))
(E/'stitch-deploy.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
