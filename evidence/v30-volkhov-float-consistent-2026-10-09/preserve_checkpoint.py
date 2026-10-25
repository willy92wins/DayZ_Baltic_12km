from pathlib import Path
import json, hashlib, shutil
import numpy as np

B=Path(__file__).parent
R=B.parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'v30-strict-dry-composition-20261009/candidate'
base=dict(np.load(source/'terrain.npz'))
candidate=dict(np.load(B/'candidate/terrain.npz'))
layer={}
for key in base:
    if np.array_equal(base[key],candidate[key],equal_nan=True):continue
    assert key in ['heights','level'],key
    a,b=base[key].ravel(),candidate[key].ravel()
    idx=np.flatnonzero(~((a==b)|(np.isnan(a)&np.isnan(b))))
    layer['terrain_'+key+'_index']=idx
    layer['terrain_'+key+'_before']=a[idx]
    layer['terrain_'+key+'_after']=b[idx]
for name,key in [('plane.npy','plane'),('visible-field.npy','field')]:
    a,b=np.load(source/name).ravel(),np.load(B/'candidate'/name).ravel()
    idx=np.flatnonzero(~((a==b)|(np.isnan(a)&np.isnan(b))))
    layer[key+'_index']=idx;layer[key+'_before']=a[idx];layer[key+'_after']=b[idx]
np.savez_compressed(B/'proposal-layer.npz',**layer)
saved=np.load(B/'proposal-layer.npz')
replay=B/'layer-replay';replay.mkdir(exist_ok=True)
for key in ['heights','level']:
    out=base[key].ravel();idx=saved['terrain_'+key+'_index']
    assert np.array_equal(out[idx],saved['terrain_'+key+'_before'],equal_nan=True)
    out[idx]=saved['terrain_'+key+'_after']
assert all(np.array_equal(base[k],candidate[k],equal_nan=True) for k in base)
np.savez_compressed(replay/'terrain.npz',**base)
for name,key in [('plane.npy','plane'),('visible-field.npy','field')]:
    array=np.load(source/name);out=array.ravel();idx=saved[key+'_index']
    assert np.array_equal(out[idx],saved[key+'_before'],equal_nan=True)
    out[idx]=saved[key+'_after'];np.save(replay/name,array)
hashes={name:sha(replay/name) for name in ['terrain.npz','plane.npy','visible-field.npy']}
assert all(v==sha(B/'candidate'/name) for name,v in hashes.items())
(B/'layer-replay.json').write_text(json.dumps(dict(status='PASS_BYTE_EXACT_REPLAY',source_terrain_sha256=sha(source/'terrain.npz'),files=hashes,layer_sha256=sha(B/'proposal-layer.npz'),changed={k:int(len(v)) for k,v in layer.items() if k.endswith('_index')},policy_pending=True),indent=2)+'\n')

manifest=[]
sets=[
    (67,R/'v30-surface-aligned-20261009','v30-surface-aligned-2026-10-09'),
    (68,B,'v30-volkhov-float-consistent-2026-10-09'),
]
for ev,src,name in sets:
    target=W/'evidence'/name;target.mkdir(exist_ok=True)
    for p in sorted(src.iterdir()):
        if not p.is_file() or p.suffix not in ['.py','.json','.md','.ps1','.npz','.log']:continue
        dest=target/p.name
        if dest.exists():assert sha(dest)==sha(p),str(dest)
        else:shutil.copyfile(p,dest)
        assert sha(p)==sha(dest)
        manifest.append(dict(evidence=ev,path=dest.relative_to(W).as_posix(),sha256=sha(dest),bytes=dest.stat().st_size))
    if ev==68:
        init=B/'missions/BalticVolkhovBedFullWaterV1.BalticTrial/init.c'
        dest=target/'probe-init.c';shutil.copyfile(init,dest);assert sha(init)==sha(dest)
        manifest.append(dict(evidence=ev,path=dest.relative_to(W).as_posix(),sha256=sha(dest),bytes=dest.stat().st_size))
for name in ['check_float_feasibility.py','float-feasibility.json']:
    src=R/'v30-volkhov-constrained-apron-20261009'/name
    dest=W/'evidence/v30-volkhov-constrained-apron-2026-10-09'/name
    assert not dest.exists();shutil.copyfile(src,dest);assert sha(src)==sha(dest)
    manifest.append(dict(evidence=66,path=dest.relative_to(W).as_posix(),sha256=sha(dest),bytes=dest.stat().st_size))
dest=W/'evidence/v30-volkhov-float-consistent-2026-10-09/evidence-manifest.json'
dest.write_text(json.dumps(manifest,indent=2)+'\n')
assert json.loads(dest.read_text())==manifest
print(json.dumps(dict(status='PRESERVED_EV67_EV68_NOT_RUNTIME_ACCEPTED',files=len(manifest),bytes=sum(x['bytes'] for x in manifest),replay=hashes),indent=2))
