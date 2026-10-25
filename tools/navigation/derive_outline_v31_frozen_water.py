"""Add the unchanged, previously accepted runtime points to the V30 solve."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
src=ROOT/'tools/navigation/solve_outline_v30_island_planes.py'
dest=ROOT/'tools/navigation/solve_outline_v31_frozen_water.py'
assert not dest.exists()
text=src.read_text().replace('import json,hashlib,time,math,shutil','import json,hashlib,time,math,shutil,csv')
text=text.replace('regional_outline_smoothing_v30','regional_outline_smoothing_v31').replace('baltic_outline_smoothing_v30.asc','baltic_outline_smoothing_v31.asc')
anchor="    B=vstack([A,extra],format='csr');limits=np.r_[d['rhs'],rhs]"
assert text.count(anchor)==1
replacement='''    # These coordinates, classes and depths were frozen before V10 runtime.
    # Keep every point; do not relocate or reclassify a failed shoreline point.
    manifest=EV/'consumer-reference-v5.json'
    assert sha(manifest)=='78fd406f340efcc8b3de2218ee8b8ae14b25b36ef8bf13eb9d3c206078d21b0c'
    frozen=json.loads(manifest.read_text());pointfile=ROOT/'missions/BalticFoundationConsumerV5.BalticTrial/water-points.csv'
    assert sha(pointfile)==frozen['water_file_sha256']
    assert sha(F/'constraints.npz')=='fd321b02bd6027cc1fcf13fb4ccac52a8c7549eb9c8b061d1a9800b75500c254'
    assert sha(F/'variables.npz')=='7ee7fa04049bed00d7ce807aa2731d17cbfef809eaf39b30045d7ed5611e8501'
    pi=[];pj=[];pv=[];pb=[];point_constants=[];point_records=[]
    frozen_rows=list(csv.reader(pointfile.read_text().splitlines(),delimiter=';'))
    assert len(frozen_rows)==81212
    for row in frozen_rows:
        kind,index,position,old_ground,water,depth,group=row
        x,y,z=np.array(list(map(float,position.split())),dtype='float32').astype(float)
        c=min(2046,max(0,int(x//6)));r=min(2046,max(0,int((12282-z)//6)));u=x/6-c;v=(12282-z)/6-r
        if v<=u:ids=np.array([r*2048+c,r*2048+c+1,(r+1)*2048+c+1]);weights=np.array([1-u,u-v,v])
        else:ids=np.array([r*2048+c,(r+1)*2048+c+1,(r+1)*2048+c]);weights=np.array([1-v,u,v-u])
        limit=float(water)-float(depth) if kind=='W' else -1.25
        if kind=='L':weights=-weights
        js=lookup[ids];free=(js>=0)&(abs(weights)>1e-12)
        limit+=1e-6-float(weights[~free]@macro.ravel()[ids[~free]])
        if not free.any():
            if limit < -1e-5:point_constants.append(dict(index=int(index),group=group,violation=-limit))
            continue
        pi.extend([len(pb)]*int(free.sum()));pj.extend(js[free]);pv.extend(weights[free]);pb.append(limit)
        point_records.append(dict(index=int(index),group=group,row=len(pb)-1))
    points_matrix=coo_matrix((pv,(pi,pj)),shape=(len(pb),n)).tocsr()
    save_npz(OUT/'frozen-point-constraints.npz',points_matrix);np.save(OUT/'frozen-point-rhs.npy',np.array(pb))
    (OUT/'frozen-point-rows.json').write_text(json.dumps(dict(source_sha256=sha(pointfile),total_points=len(frozen_rows),constraints=point_records,constant_failures=point_constants),indent=2)+'\\n')
    assert not point_constants,point_constants[:10]
    B=vstack([A,extra,points_matrix],format='csr');limits=np.r_[d['rhs'],rhs,pb]
'''
text=text.replace(anchor,replacement)
dest.write_text(text)
print(dest)
