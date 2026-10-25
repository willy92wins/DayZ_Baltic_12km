"""Stream a fresh S3 candidate: combined heights, exact kit replacement, forest support."""
from pathlib import Path
from collections import Counter
import hashlib,json,shutil,struct,sys
import numpy as np
import shapely
from shapely.geometry import Polygon
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
Q=Path('E:/DayZ-Baltic-Build/qc-council-20261024');B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sys.path[:0]=[str(W/'tools/vegetation'),str(W/'tools/terrain'),str(W/'tools/water')]
from prune_visual_forest_v31 import prefix,objects
from wrp0wzd import object_record
from streambed_kit_v31 import tri_h
from review_compact_collision_v31 import load,vertices
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(name,matrix):return name.lower().replace('/','\\').lstrip('\\'),struct.pack('<12f',*matrix)
base=Q/'stage-s3';source=base/'root/dayz_baltic_12km_dev/tb/narva_trial';src=source/'baltic_trial.wrp'
assert sha(src)=='f07926200627c24f26a8da4df54a03df03e5776f92e2821dd676bbb07dab3f77'
P=R/'combined-pilot';M=R/'combined-merged';review=json.loads((P/'binary-review.json').read_text())
assert review['status']=='BINARY_PASS' and review['pbo_sha256']==sha(P/'packed/baltic_stream_pilot.pbo')
assert json.loads((M/'merge-verification.json').read_text())['status']=='WATER_FOOTPRINT_EXACT'
terrain=M/'terrain-buried.npz';H=np.load(terrain)['heights'];H0=np.load(Q/'road-merged-s3/terrain-buried.npz')['heights']
meta=json.loads((base/'stage-report.json').read_text());ref=Path(meta['forest_reference']['path']);assert sha(ref)==meta['forest_reference']['sha256'];models=json.loads(ref.read_text())['models']
author=json.loads((R/'river-131-compact-a/author-report.json').read_text());polygons=[]
for inst in author['instances']:
    path=R/'river-131-compact-a/source'/inst['model'].replace('\\','/');assert sha(path)==inst['sha256']
    _,lods,_=load(path);tri=vertices(lods[0],[f for f in lods[0].faces if 'water_streambed.rvmat' not in f.material])+inst['origin']
    polygons.extend(Polygon(t[:,[0,2]]) for t in tri)
bed=shapely.union_all(polygons);assert bed.is_valid and bed.geom_type=='Polygon';bounds=bed.bounds
oldrecords=[r for r in json.loads((B/'water-fix-b/kit/kit-records.json').read_text()) if r['site']=='131.0-0']
remaining=Counter(key(r['model'],r['matrix']) for r in oldrecords);assert len(oldrecords)==74
records=[r for r in json.loads((P/'records.json').read_text()) if r['site']=='131.0-0'];assert len(records)==27
out=R/'stage-combined';target=out/'root/dayz_baltic_12km_dev/tb/narva_trial';target.parent.mkdir(parents=True,exist_ok=False)
shutil.copytree(source,target,ignore=shutil.ignore_patterns('baltic_trial.wrp'))
dest=target/'baltic_trial.wrp';shifts=[];removed=[];excluded=[];count=0;maximum_id=0;expected=hashlib.sha256();seen=set()
def flush(batch,g):
    global count,maximum_id
    raw=[r for _,_,r in batch];drop=np.zeros(len(batch),bool)
    indices=[]
    for i,(ident,name,r) in enumerate(batch):
        assert ident not in seen;seen.add(ident);maximum_id=max(maximum_id,ident)
        mat=struct.unpack_from('<12f',r);k=key(name,mat)
        if remaining[k]:remaining[k]-=1;drop[i]=True;removed.append(dict(id=ident,model=name,matrix=list(mat)));continue
        if name.startswith(('dz\\plants\\','dz\\plants_bliss\\','dz\\rocks\\')):
            assert name in models;indices.append(i)
    if indices:
        mats=np.array([struct.unpack_from('<12f',raw[i]) for i in indices]);bc=np.array([models[batch[i][1]]['bc'] for i in indices])
        roots=mats[:,9:12]-np.einsum('nji,nj->ni',mats[:,:9].reshape(-1,3,3),bc)
        scales=np.linalg.norm(mats[:,:9].reshape(-1,3,3),axis=2).max(1)
        radius=np.array([models[batch[i][1]]['base_radius_plan'] for i in indices])*scales+.5
        near=(roots[:,0]>=bounds[0]-radius)&(roots[:,0]<=bounds[2]+radius)&(roots[:,2]>=bounds[1]-radius)&(roots[:,2]<=bounds[3]+radius)
        clearance=np.full(len(indices),np.inf)
        clearance[near]=shapely.distance(shapely.points(roots[near][:,[0,2]]),bed)-radius[near]
        for j in np.flatnonzero(clearance<0):
            i=indices[j];drop[i]=True;excluded.append(dict(id=batch[i][0],model=batch[i][1],root=roots[j].tolist(),radius_m=float(radius[j]),clearance_m=float(clearance[j]),matrix=mats[j].tolist()))
        inside=(roots[:,0]>=0)&(roots[:,0]<=12282)&(roots[:,2]>=0)&(roots[:,2]<=12282)
        dy=np.zeros(len(indices));dy[inside]=tri_h(H,roots[inside,0],roots[inside,2])-tri_h(H0,roots[inside,0],roots[inside,2])
        for j in np.flatnonzero(dy):
            i=indices[j]
            if drop[i]:continue
            before=raw[i];after=bytearray(before);new=float(np.float32(mats[j,10]+dy[j]));struct.pack_into('<f',after,40,new)
            assert before[:40]+before[44:]==after[:40]+after[44:]
            raw[i]=bytes(after);shifts.append(dict(id=batch[i][0],model=batch[i][1],before=float(mats[j,10]),after=new,root=roots[j].tolist(),ground_delta=float(dy[j])))
    for i,r in enumerate(raw):
        if not drop[i]:g.write(r);expected.update(r);count+=1
with src.open('rb') as f,dest.open('wb') as g:
    pre=prefix(f);old=np.frombuffer(pre,'<f4',count=2048*2048,offset=24).reshape(2048,2048);assert np.array_equal(old,H0[::-1])
    updated=pre[:24]+np.ascontiguousarray(H[::-1],dtype='<f4').tobytes()+pre[24+2048*2048*4:];g.write(updated)
    iterator=objects(f);batch=[]
    while True:
        try:batch.append(next(iterator))
        except StopIteration as stop:terminator=stop.value;break
        if len(batch)==4096:flush(batch,g);batch=[]
    if batch:flush(batch,g)
    assert not sum(remaining.values()) and len(removed)==74
    for i,r in enumerate(records,1):
        raw=object_record(r['matrix'],maximum_id+i,r['model'].encode('ascii'));g.write(raw);expected.update(raw);count+=1
    g.write(terminator)
actual=hashlib.sha256();actual_count=0;actual_pilot=0
with dest.open('rb') as f:
    assert prefix(f)==updated;iterator=objects(f)
    while True:
        try:ident,name,raw=next(iterator)
        except StopIteration as stop:assert stop.value==terminator;break
        actual.update(raw);actual_count+=1;actual_pilot+=name.startswith('baltic_stream_pilot\\')
assert actual_count==count and actual.digest()==expected.digest() and actual_pilot==62
for name in ('baseline-config.bin','baseline-config.cpp','decode-config.log'):shutil.copy2(base/name,out/name)
np.save(out/'forest-height-delta.npy',np.array([(q['id'],q['before'],q['after']) for q in shifts]))
report=dict(status='SOURCE_COMPOSITION_VERIFIED',forest=True,source_wrp_sha256=sha(src),wrp_sha256=sha(dest),terrain_sha256=sha(terrain),pilot_pbo_sha256=review['pbo_sha256'],object_count=count,
    remaining_objects=count-62,added_models=62,new_models=27,removed_old_kit_records=len(removed)+meta['removed_old_kit_records'],newly_removed_old_kit_records=len(removed),forest_height_adjustments=len(shifts),forest_excluded=len(excluded),forest_reference=meta['forest_reference'],pilot=str(P),merged=str(M),
    terrain_vertices=int((H!=H0).sum()),objects_digest=actual.hexdigest(),config_unchanged_from_s3=True,limits=['Source parity only; compiled heights/poses, motor and forest consumer acceptance pending.','Forest exclusion against full saved new bed; density/context must be reviewed.'])
(out/'stage-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(out/'object-delta.json').write_text(json.dumps(dict(shifts=shifts,removed_old_kit=removed,excluded_forest=excluded,appended=records),indent=2),encoding='utf-8')
(out/'new-bed-footprint.wkb').write_bytes(bed.wkb)
print(json.dumps(report,indent=2),flush=True)
