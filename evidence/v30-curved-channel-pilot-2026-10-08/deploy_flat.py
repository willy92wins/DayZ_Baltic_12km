"""Verify compiled archive identities before an isolated test deployment."""
from pathlib import Path
import hashlib,json,shutil,sys
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008');E=W/'evidence/v30-curved-channel-pilot-2026-10-08'
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
check=json.loads((E/'flat-verification-r2.json').read_text());assert check['status']=='PASS_OFFLINE_FLAT_FALLBACK'
stage=json.loads((E/'flat-package-stage.json').read_text())
world=B/'flat-world/out/narva_trial.pbo';water=B/'flat-water/water/packed/baltic_water_v30.pbo'
assert sha(water)==stage['water_pbo_sha256']
base=Path('P:/Mods/@DayZ_Baltic_Floor095Preview/Addons/narva_trial.pbo')
assert sha(base)=='0f1e450f13aa1401f3a73d8bc9ce32ab9887cf4f60c44b09f0e2acac33cce26d'
_,props,old=read_pbo(base);_,newprops,new=read_pbo(world)
assert props==newprops and set(old)==set(new)
different=sorted(k for k in old if old[k]!=new[k]);assert different==['baltic_trial.wrp'],different
assert new['baltic_trial.wrp'][:4]==b'OPRW' and new['config.bin'][:4]==b'\0raP'
dest=Path('P:/Mods/@DayZ_Baltic_FlatWaterPreview');assert not dest.exists()
(dest/'Addons').mkdir(parents=True)
for path in (world,water):shutil.copyfile(path,dest/'Addons'/path.name);assert sha(path)==sha(dest/'Addons'/path.name)
report=dict(status='DEPLOYED_ISOLATED_FLAT_PREVIEW',destination=str(dest),files={p.name:sha(p) for p in (dest/'Addons').iterdir()},
            changed_world_entries=different,unchanged_world_entries=len(old)-1,world_source_sha256=stage['world_source_sha256'],
            terrain_sha256=sha(B/'r3-transition-proposal/terrain_flat.npz'),compiled_model_geometry_verified=len(stage['compiled_models']),
            source_verification_sha256=sha(E/'flat-verification-r2.json'),limits=['Preview only; no base promotion, engine result or final navmesh acceptance.'])
(E/'flat-deploy-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
