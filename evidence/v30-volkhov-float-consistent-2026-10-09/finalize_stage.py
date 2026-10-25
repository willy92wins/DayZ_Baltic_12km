"""Validate the already written WRP with the writer's actual float32 serialization."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
B=Path(__file__).parent;OLD=B.parent/'v30-strict-dry-composition-20261009'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');sys.path.insert(0,str(W/'tools/terrain'))
from wrp0wzd import read,object_record
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=OLD/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';dst=B/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
a=read(src);b=read(dst);h=np.load(B/'candidate/terrain.npz')['heights'];assert np.array_equal(b['heights'],h[::-1]);assert all(a[k]==b[k] for k in ['header','materials','terminator']);assert len(a['objects'])==len(b['objects'])
shifts={int(k):v for k,v in json.loads((B/'authoring.json').read_text())['object_translations'].items()};differ=[]
for old,new in zip(a['objects'],b['objects']):
    m=list(old['matrix']);m[10]+=shifts.get(old['id'],0)
    assert old['id']==new['id'] and old['raw_name']==new['raw_name']
    exact=np.array(struct.unpack('<12f',struct.pack('<12f',*m)))
    assert np.array_equal(exact,new['matrix'])
    assert new['bytes']==(object_record(m,old['id'],old['raw_name']) if old['id'] in shifts else old['bytes'])
    obsolete=np.array(old['matrix'],dtype=np.float32);obsolete[10]+=shifts.get(old['id'],0)
    if not np.array_equal(obsolete,exact):differ.append(dict(id=old['id'],writer_y=float(exact[10]),premature_float32_y=float(obsolete[10]),delta_m=float(exact[10]-obsolete[10])))
assert differ
code=(OLD/'compile_native_world.ps1').read_text().replace(str(OLD).replace('/','\\'),str(B).replace('/','\\'))
(B/'compile_native_world.ps1').write_text(code)
report=dict(status='STAGED_VOLKHOV_PROPOSAL_POLICY_PENDING',source_wrp_sha256=sha(dst),terrain_sha256=sha(B/'candidate/terrain.npz'),objects=len(b['objects']),translated_y_only=len(shifts),other_objects_exact=True,serialization_check='pack/unpack <12f after double-precision addition, matching object_record')
(B/'stage.json').write_text(json.dumps(report,indent=2)+'\n')
(B/'package-reference.json').write_text(json.dumps(dict(world_source_sha256=sha(dst),water_sha256='3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14',plane_sha256=sha(B/'candidate/plane.npy'),field_sha256=sha(B/'candidate/visible-field.npy')),indent=2)+'\n')
(B/'stage-serialization-diagnosis.json').write_text(json.dumps(dict(status='VALIDATION_IMPLEMENTATION_FIXED_NO_WRP_REWRITE',differences=differ,maximum_error_m=max(abs(x['delta_m']) for x in differ)),indent=2)+'\n')
print(json.dumps(report,indent=2));print('Premature-rounding false mismatches:',len(differ))
