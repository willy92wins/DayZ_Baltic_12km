"""Single composition repair: restore all tiles touching consumers' failed features."""
from pathlib import Path
import json
import numpy as np
import shapely
from shapely.geometry import Point
from verify_global_contours import B,B13,B10,B12,sha,domain,triangle_contours,samples

source=B13/'candidate-feasible/terrain.npz';candidate=B/'candidate/terrain.npz'
report=json.loads((B/'verification.json').read_text())
assert report['status']=='FAIL_GLOBAL_SOURCE'
assert set(k for k,v in report['gates'].items() if not v)=={'contour_correspondence','global_max','physical_topology','visible_topology'}
assert sha(candidate)==report['candidate_sha256']
t=dict(np.load(source));h=t['heights'].astype(float);v=np.load(candidate)['heights'].astype(float)
p=np.load(B10/'frozen-field-reference/plane.npy');f=np.load(B12/'preserved-field.npy')
tiles=[json.loads(line) for line in (B/'tiles.jsonl').read_text().splitlines()]
accepted={(tile['row'],tile['col']):tile for tile in tiles if tile['status']=='INTEGRATE_SOURCE_ONLY'}
restore=set();reasons=[]


def add_vertices(ids,reason):
    rr,cc=np.divmod(np.unique(ids),2048)
    keys=set(zip((rr//16*16).tolist(),(cc//16*16).tolist()))
    chosen=keys.intersection(accepted)
    restore.update(chosen)
    reasons.append(dict(reason=reason,tiles=[list(k) for k in sorted(chosen)]))


for label,field in (('physical',None),('visible',f)):
    before=domain(h,p,field)
    for failed in report['domains'][label]['topology']['failed_original']:
        indices=np.flatnonzero(before['labels']==failed['component']);cells=np.unique(indices//2)
        rr,cc=before['cells'];r,c=rr[cells],cc[cells]
        ids=np.c_[r*2048+c,r*2048+c+1,(r+1)*2048+c,(r+1)*2048+c+1].ravel()
        add_vertices(ids,label+'_body_'+str(failed['component']))
        reasons[-1].update(failed=failed,bounds_xz=[int(c.min()*6),int(12282-r.max()*6),int(c.max()*6+6),int(12282-r.min()*6)])

seg0,keys0,lines0=triangle_contours(h,f,p);seg1,keys1,lines1=triangle_contours(v,f,p)
assert np.array_equal(keys0,keys1)
distance=np.linalg.norm(seg1-seg0,axis=2).max(1)
for row,col,tri in keys0[distance>4.1]:
    a=int(row*2048+col);add_vertices([a,a+1,a+2048,a+2049],'serialized_contour_displacement')

old,_,_=samples(lines0)
for line in lines1:
    if line.length<=24:continue
    stats,angles,sites=samples([line])
    if stats['max_degrees']<=old['max_degrees']+1e-5:continue
    # Freeze the whole geometric chain, avoiding another change of sample phase on it.
    coords=np.asarray(line.coords)
    c=np.floor(coords[:,0]/6).astype(int);r=np.floor((12282-coords[:,1])/6).astype(int)
    ids=[]
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            rr=np.clip(r+dr,0,2047);cc=np.clip(c+dc,0,2047);ids.extend((rr*2048+cc).tolist())
    add_vertices(ids,'whole_chain_with_new_global_maximum')
    reasons[-1].update(length_m=float(line.length),bounds=list(line.bounds),max_degrees=stats['max_degrees'])

assert restore
out=v.copy();restored=0
for key in sorted(restore):
    ids=accepted[key]['ids'];out.ravel()[ids]=h.ravel()[ids];restored+=len(ids)
t['heights']=out.astype(t['heights'].dtype);folder=B/'candidate-repaired';folder.mkdir(exist_ok=False)
np.savez_compressed(folder/'terrain.npz',**t)
result=dict(status='COMPOSITION_REPAIR_REQUIRES_SAME_CONSUMER',repro='verify_global_contours.py against candidate/terrain.npz',
            defect='Local halo area diluted one complete small-body loss; local contour resampling did not bound the global maximum. Float32 exceeded one displacement limit.',
            repair='Restore all previously accepted tiles touching each failed body, complete failing contour chain, or excessive serialized displacement. No new solve and no changed thresholds.',
            restored_tiles=len(restore),restored_vertices=restored,remaining_changed_vertices=int((out!=h).sum()),reasons=reasons,
            original_candidate_sha256=sha(candidate),candidate_sha256=sha(folder/'terrain.npz'))
(B/'composition-repair.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
