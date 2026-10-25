from pathlib import Path
import json,hashlib,shutil,io
import numpy as np
B=Path(__file__).parent;R=Path('E:/DayZ-Baltic-Build');W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save_layer():
    old=dict(np.load(R/'v30-native-hinge-finish-20261009/candidate/terrain.npz'));new=dict(np.load(B/'candidate/terrain.npz'));data={};changed={}
    for key in old:
        a,b=old[key],new[key];different=(a!=b)&~(np.isnan(a)&np.isnan(b)) if np.issubdtype(a.dtype,np.floating) else a!=b
        if different.any():
            ids=np.flatnonzero(different);data[key+'_ids']=ids;data[key+'_before']=a.ravel()[ids];data[key+'_after']=b.ravel()[ids];changed[key]=len(ids)
    for name,ap,bp in [('plane',R/'v30-global-water-risk-20261009/frozen-field-reference/plane.npy',B/'candidate/plane.npy'),('field',R/'v30-frozen-water-stitch-20261009/preserved-field.npy',B/'candidate/visible-field.npy')]:
        a,b=np.load(ap),np.load(bp);ids=np.flatnonzero((a!=b)&~(np.isnan(a)&np.isnan(b)));data[name+'_ids']=ids;data[name+'_before']=a.ravel()[ids];data[name+'_after']=b.ravel()[ids];changed[name]=len(ids)
        v=a.copy();v.ravel()[ids]=data[name+'_after'];assert np.array_equal(v,b,equal_nan=True)
        buf=io.BytesIO();np.save(buf,v);assert hashlib.sha256(buf.getvalue()).hexdigest()==sha(bp)
    np.savez_compressed(B/'accepted-terrain-layer.npz',**data)
    replay={k:a.copy() for k,a in old.items()}
    for key in old:
        if key+'_ids' in data:replay[key].ravel()[data[key+'_ids']]=data[key+'_after']
    buf=io.BytesIO();np.savez_compressed(buf,**replay);assert hashlib.sha256(buf.getvalue()).hexdigest()==sha(B/'candidate/terrain.npz')
    record=dict(status='BYTE_EXACT_REPLAY_PASS',source_terrain_sha256=sha(R/'v30-native-hinge-finish-20261009/candidate/terrain.npz'),result_terrain_sha256=sha(B/'candidate/terrain.npz'),result_plane_sha256=sha(B/'candidate/plane.npy'),result_field_sha256=sha(B/'candidate/visible-field.npy'),changed_scalars=changed,layer_sha256=sha(B/'accepted-terrain-layer.npz'))
    (B/'layer-replay.json').write_text(json.dumps(record,indent=2)+'\n')
def copy_set(src,dst,subdirs=()):
    dst.mkdir(parents=True,exist_ok=False);records=[]
    files=[p for p in src.iterdir() if p.is_file() and p.suffix.lower() in ('.py','.ps1','.md','.json','.csv','.log','.png','.npz')]
    for sub in subdirs:
        folder=src/sub
        if folder.exists():files.extend(p for p in folder.iterdir() if p.is_file())
    for p in files:
        if p.name in ('scores.npz','native-rays.npz'):continue
        q=dst/p.relative_to(src);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);assert sha(p)==sha(q)
        records.append(dict(path=q.relative_to(dst).as_posix(),sha256=sha(q),bytes=q.stat().st_size))
    (dst/'preservation-manifest.json').write_text(json.dumps(dict(source=str(src),files=records),indent=2)+'\n');return len(records)
save_layer()
jobs=[('v30-pond-omission-runtime-20261009','v30-pond-omission-runtime-2026-10-09',['captures/A-stable','captures/B-setup','captures/B-stable','captures/Areturn-setup','captures/Areturn-stable']),('v30-isolated-basin-scope-20261009','v30-isolated-basin-scope-2026-10-09',[]),('v30-native-terminal-topology-20261009','v30-native-terminal-topology-2026-10-09',[]),('v30-native-boundary-solve-20261009','v30-native-boundary-solve-2026-10-09',[]),('v30-coupled-native-shore-20261009','v30-coupled-native-shore-2026-10-09',[]),('v30-coupled-native-shore-corrected-20261009','v30-coupled-native-shore-corrected-2026-10-09',[]),('v30-translation-native-review-20261009','v30-translation-native-review-2026-10-09',[]),('v30-isolated-basin-repair-20261009','v30-isolated-basin-repair-2026-10-09',['runtime/setup','runtime/basin-stable','runtime/nazia','risk-census'])]
print(json.dumps({dst:copy_set(R/src,W/'evidence'/dst,subs) for src,dst,subs in jobs},indent=2))
