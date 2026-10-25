"""Conservative global dry-pass guard from verified compiled face ranges.

Bboxes are intentionally a superset of exact XZ coverage. This is protection,
not a measurement of rendered water, exposed faces or holes.
"""
from pathlib import Path
import hashlib,json,time
import numpy as np

HERE=Path(__file__).resolve().parent
G=HERE.parent.parent
INDEX=G/'ev93-face-index/runs/20261010T092417Z-63d4cec3'
MANIFEST=INDEX/'manifest.json'
MANIFEST_SHA='c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def rectangle_union(ranges,n):
    ranges=np.asarray(ranges,dtype=np.int32).reshape(-1,4)
    valid=np.all(ranges>=0,axis=1)
    if np.any(np.any(ranges<0,axis=1)&valid):raise ValueError('mixed off-grid range')
    rr=ranges[valid]
    if np.any(rr[:,0]>rr[:,1]) or np.any(rr[:,2]>rr[:,3]) or np.any(rr>=n):raise ValueError('bad rectangle')
    diff=np.zeros((n+1,n+1),np.int32)
    r0,r1,c0,c1=rr.T
    for r,c,v in ((r0,c0,1),(r1+1,c0,-1),(r0,c1+1,-1),(r1+1,c1+1,1)):
        np.add.at(diff,(r,c),v)
    count=diff.cumsum(0,dtype=np.int32).cumsum(1,dtype=np.int32)[:-1,:-1]
    if count.min()<0:raise AssertionError('negative overlap')
    return count>0,int(valid.sum())

def fixtures():
    r=np.asarray([[0,0,0,0],[1,3,2,4],[2,4,3,5],[5,5,0,5],[-1,-1,-1,-1]],np.int32)
    actual,n=rectangle_union(r,6);direct=np.zeros((6,6),bool)
    for a,b,c,d in r[:4]:direct[a:b+1,c:d+1]=True
    assert n==4 and np.array_equal(actual,direct)
    try:rectangle_union([[0,6,0,1]],6)
    except ValueError:pass
    else:raise AssertionError('invalid range accepted')

def main():
    fixtures();out=HERE/'run-01'
    if out.exists():raise FileExistsError(out)
    t=time.perf_counter();assert sha(MANIFEST)==MANIFEST_SHA
    m=json.loads(MANIFEST.read_text());assert m['status']=='COMPLETE'
    civil=HERE.parent/'global-civil-ev95/run-01/inventory.json'
    assert sha(civil)=='cdebbbce50644407642e791388e44c40b15499041844607650b885d1bc618856'
    assert json.loads(civil.read_text())['objects_exact_vs_B'] is True
    deploy=G/'build-wide-slope/deploy.json';d=json.loads(deploy.read_text())
    assert d['files']['baltic_water_v30.pbo']==m['base_identity']['water_pbo_sha256']
    before={str(p):sha(p) for p in (MANIFEST,civil,deploy,Path(__file__))}
    all_ranges=[];counts={'physical':0,'visible':0};degenerate=0
    for shard in m['shards']:
        p=INDEX/shard['path'];assert sha(p)==shard['sha256'];before[str(p)]=sha(p)
        with np.load(p,allow_pickle=False) as z:
            a=z['cell_range_rc'];kind=z['kind'];deg=z['degenerate']
            assert a.shape==(shard['records'],4) and a.dtype==np.int32
            assert kind.shape==(len(a),) and np.all(kind<=1)
            assert np.all(np.all(a>=0,axis=1)|np.all(a==-1,axis=1))
            all_ranges.append(a)
            counts['physical']+=int((kind==0).sum());counts['visible']+=int((kind==1).sum());degenerate+=int(deg.sum())
    a=np.concatenate(all_ranges);assert len(a)==883308
    mask,in_grid=rectangle_union(a,2047)
    # Independent integral-image audit checks every rectangle is wholly frozen.
    prefix=np.pad(mask.astype(np.int32),((1,0),(1,0))).cumsum(0).cumsum(1)
    rr=a[np.all(a>=0,axis=1)];r0,r1,c0,c1=rr.T
    sums=prefix[r1+1,c1+1]-prefix[r0,c1+1]-prefix[r1+1,c0]+prefix[r0,c0]
    assert np.array_equal(sums,(r1-r0+1)*(c1-c0+1))
    vertices=np.zeros((2048,2048),bool)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):vertices[dr:dr+2047,dc:dc+2047]|=mask
    after={p:sha(p) for p in before};assert before==after
    out.mkdir();np.savez_compressed(out/'water-guard.npz',fixed_vertices=vertices,face_bbox_cells=mask)
    report={'status':'PREPARED_CONSERVATIVE_GLOBAL_WATER_GUARD_ONLY','source_pins_start':before,'source_pins_end':after,
        'faces':len(a),'by_kind':counts,'degenerate_faces':degenerate,'in_grid_faces':in_grid,
        'bbox_guard_cells':int(mask.sum()),'fixed_vertices':int(vertices.sum()),
        'all_face_rectangles_fully_guarded':True,'mask_sha256':sha(out/'water-guard.npz'),
        'elapsed_s':time.perf_counter()-t,'terrain_edited':False,
        'limits':['Closed XZ bboxes overprotect compared with exact projected triangles; this is a dry-pass guard only.',
                  'No claim of physical/visible exposure, coverage, holes or engine rendering.',
                  'P/F/SEA crossings, P9, partial F and semantic water protection still require separate masks.']}
    (out/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','faces','bbox_guard_cells','fixed_vertices','elapsed_s')}))

if __name__=='__main__':main()
