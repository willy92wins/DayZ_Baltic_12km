"""Inspect then copy the candidate to a new isolated mod; keep canonical V30."""
from pathlib import Path
import hashlib,json,shutil,sys,datetime
import numpy as np
R=Path('P:/DayZ_Baltic_12km_dev');E=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'tools/playtest'));sys.path.insert(0,str(R/'tools/terrain'))
from attach_navmesh import read_pbo
from wrp0wzd import read
from audit_fairway_triangles_v30 import save,sha
B=Path('E:/DayZ-Baltic-Build/v30-delta-preview')
original=Path('P:/Mods/@DayZ_Baltic_V30/Addons/narva_trial.pbo')
world=B/'out/Addons/narva_trial.pbo';water=B/'out/Addons/baltic_water_v30.pbo'
assert sha(original)=='69140d41ef4841078a5c159222814490a85832e319977b8b22c18be940e24811'
assert sha(world)=='8b2d404a72f30150c62463e85868360cc9fa34f610aaca6719255154f3fa9ef1'
assert sha(water)=='e9b52b8c4fc07df8bc4854dcd9e144e16875af8006221f16efaa6ab95de56681'
assert json.loads((E/'packed-content.json').read_text())['status']=='PASS_PACKED_CONTENT'
_,props,packed=read_pbo(world)
packed={k.replace('\\','/').lower():v for k,v in packed.items()}
old=json.loads((R/'evidence/v30-shore-pilot-2026-10-02/packed-content.json').read_text())
# Compare against canonical entries, not against the unaccepted Narva pilot.
_,_,canonical=read_pbo(original);canonical={k.replace('\\','/').lower():v for k,v in canonical.items()}
assert set(packed)==set(canonical)
changed=[k for k in packed if packed[k]!=canonical[k]]
allowed=lambda k: k in {'baltic_trial.wrp','navmesh/baltic_trial.nm','texheaders.bin'} or (k.startswith('data/layers/') and k.endswith('.paa'))
assert all(allowed(k) for k in changed),changed
raw=read(str(B/'world/stage/BalticTrialWorld/baltic_trial.wrp'))
parent=read('E:/DayZ-Baltic-Build/v30-preview6/world/stage/BalticTrialWorld/baltic_trial.wrp')
npz=Path('E:/DayZ-Baltic-Build/v30-delta-candidate/terrain_v30.npz')
assert np.array_equal(raw['heights'][::-1,:],np.load(npz)['heights'])
assert [o['bytes'] for o in raw['objects']]==[o['bytes'] for o in parent['objects']]
assert raw['header']==parent['header'] and raw['materials']==parent['materials']
nm=hashlib.sha256(packed['navmesh/baltic_trial.nm']).hexdigest()
assert nm=='eb0f131e5fc0f80d81c60b1f332d8ecfa6396cab9e09ffd36cd1c8504885c496'
wrp_hash=hashlib.sha256(packed['baltic_trial.wrp']).hexdigest()
save(E/'preview-package.json',dict(status='PASS_VISUAL_AND_GEOMETRY_PREVIEW_ONLY',pbo_sha256=sha(world),compiled_wrp_sha256=wrp_hash,
 raw_wrp_all_heights_exact=True,objects_identical=len(raw['objects']),config_and_materials_identical=True,changed_entries=changed,
 stale_navmesh_sha256=nm,limits=['Inherited V29 navmesh; cannot accept navigation until regeneration from this compiled WRP.']))
dest=Path('P:/Mods/@DayZ_Baltic_DeltaV30/Addons');assert not dest.parent.exists();dest.mkdir(parents=True)
files=[]
for p in (world,water):
 d=dest/p.name;shutil.copyfile(p,d);assert sha(p)==sha(d);files.append(dict(name=p.name,bytes=d.stat().st_size,sha256=sha(d)))
assert sha(original)=='69140d41ef4841078a5c159222814490a85832e319977b8b22c18be940e24811'
report=dict(status='ISOLATED_CANDIDATE_DEPLOYED',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),path=str(dest),files=files,compiled_wrp_sha256=wrp_hash,canonical_unchanged=True,navmesh='STALE_PREVIEW_ONLY')
save(E/'deployment.json',report);print(json.dumps(report))
