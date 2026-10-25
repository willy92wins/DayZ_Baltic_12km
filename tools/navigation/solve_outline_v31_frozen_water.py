"""Use exact protected-land planes instead of conservative wet-vertex floors."""
from pathlib import Path
import json,hashlib,time,math,shutil,csv
import numpy as np
from scipy.sparse import load_npz,coo_matrix,vstack,hstack,eye,csr_matrix,save_npz
from scipy.ndimage import distance_transform_edt
from scipy.optimize import linprog
from rasterio.features import rasterize
import rasterio
from affine import Affine
from shapely import polygons,intersection,get_coordinates,area
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parents[2];F=ROOT/'tests/regional_outline_smoothing_v28';OUT=ROOT/'tests/regional_outline_smoothing_v31';EV=ROOT/'evidence/regional-foundation-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();started=time.monotonic()
    A=load_npz(F/'constraints.npz');d=np.load(F/'variables.npz');ix=d['variables'];macro=d['macro'];n=len(ix);lookup=np.full(macro.size,-1,np.int32);lookup[ix]=np.arange(n)
    ref=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');base=ref['candidate'];wet=ref['wet']|ref['ocean'];editable=d['editable'];varcells=editable[:-1,:-1]|editable[:-1,1:]|editable[1:,:-1]|editable[1:,1:]
    indices=[];columns=[];values=[];rhs=[];impossible=[]
    def add(points,target):
        before=len(rhs)
        for x,z in points:
            c=min(2046,max(0,int(x//6)));r=min(2046,max(0,int((12282-z)//6)));u=x/6-c;v=(12282-z)/6-r
            if v<=u:ids=np.array([r*2048+c,r*2048+c+1,(r+1)*2048+c+1]);weights=-np.array([1-u,u-v,v])
            else:ids=np.array([r*2048+c,(r+1)*2048+c+1,(r+1)*2048+c]);weights=-np.array([1-v,u,v-u])
            cols=lookup[ids];free=(cols>=0)&(np.abs(weights)>1e-12);limit=-target+1e-6-float(weights[~free]@macro.ravel()[ids[~free]])
            if not free.any():
                if limit< -1e-5:impossible.append(dict(xz=[x,z],violation=-limit))
                continue
            indices.extend([len(rhs)]*int(free.sum()));columns.extend(cols[free]);values.extend(weights[free]);rhs.append(limit)
        return len(rhs)-before
    fs=json.loads((EV/'protected-islands-game.json').read_text())['features'];levels=json.loads((EV/'island-support-v7.json').read_text())['islands'];records=[]
    for i,(f,level) in enumerate(zip(fs,levels)):
        g=shape(f['geometry']);count=0
        for land,target in [(g,level['adjacent_water_ceiling_m']),(g.buffer(-6),level['adjacent_water_ceiling_m']+.35)]:
            if land.is_empty:continue
            cells=rasterize([(land,1)],out_shape=(2047,2047),transform=Affine(6,0,0,0,-6,12282),all_touched=True,dtype='uint8').astype(bool)&varcells;r,c=np.where(cells)
            if not len(r):continue
            x=c*6;z=12282-r*6;aa=np.c_[x,z];bb=np.c_[x+6,z];dd=np.c_[x+6,z-6];ee=np.c_[x,z-6]
            for verts in [np.stack([aa,bb,dd],axis=1),np.stack([aa,dd,ee],axis=1)]:
                clips=intersection(polygons(verts),land);count+=add(get_coordinates(clips[area(clips)>1e-8]),target)
        p=g.representative_point();count+=add([[p.x,p.y]],level['adjacent_water_ceiling_m']+.35);records.append(dict(index=i,rows=count))
        if i%40==0:print('Island rows',i,len(rhs),flush=True)
    extra=coo_matrix((values,(indices,columns)),shape=(len(rhs),n)).tocsr();save_npz(OUT/'island-constraints.npz',extra);np.save(OUT/'island-rhs.npy',np.array(rhs))
    # These coordinates, classes and depths were frozen before V10 runtime.
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
    (OUT/'frozen-point-rows.json').write_text(json.dumps(dict(source_sha256=sha(pointfile),total_points=len(frozen_rows),constraints=point_records,constant_failures=point_constants),indent=2)+'\n')
    assert not point_constants,point_constants[:10]
    B=vstack([A,extra,points_matrix],format='csr');limits=np.r_[d['rhs'],rhs,pb]

    h=base.ravel()[ix].astype(float);lo=np.where(wet.ravel()[ix],h-6,np.maximum(h-6,1.4));hi=h+6;bad=[]
    for start in range(0,len(limits),250000):
        chunk=B[start:start+250000];minimum=chunk.maximum(0)@lo+chunk.minimum(0)@hi;bad.extend((start+np.flatnonzero(minimum>limits[start:start+len(minimum)]+1e-7)).tolist())
    chosen=B[bad];assert np.all(chosen.data<=1e-9),'Non-land bound conflict'
    seeds=np.unique(chosen.indices);grid=np.zeros(base.shape,bool);grid.ravel()[ix[seeds]]=True;region=distance_transform_edt(~grid)*6<=48 if len(seeds) else np.zeros(base.shape,bool);exception=region.ravel()[ix]&wet.ravel()[ix];hi[exception]=h[exception]+15
    pre=dict(status='FROZEN_BEFORE_SOLVE',parent_matrix_sha256=sha(F/'constraints.npz'),parent_variables_sha256=sha(F/'variables.npz'),source_npz_sha256=sha(ROOT/'tests/regional_foundation_combined_v10/reference.npz'),island_source_sha256=sha(EV/'protected-islands-game.json'),seed_vertices=[dict(xz=[int(ix[k]%2048*6),int(12282-ix[k]//2048*6)],height=float(h[k])) for k in seeds],island_constraint_tolerance_m=1e-6,island_rows=len(rhs),impossible_fixed=impossible,exception_vertices=int(exception.sum()),island_contract='Whole clipped land at local level;6m interior and representative at level+.35m. Macro outside variable collar is a pointwise majorant of V10 on island support.')
    (OUT/'pre-solve.json').write_text(json.dumps(pre,indent=2)+'\n');shutil.copyfile(F/'shore-transition.json',OUT/'shore-transition.json');print(json.dumps({k:v for k,v in pre.items() if k not in ('seed_vertices','impossible_fixed')}),flush=True);assert not impossible
    I=eye(n,format='csr');big=vstack([hstack([B,csr_matrix(B.shape)]),hstack([I,-I]),hstack([-I,-I])],format='csr');wanted=d['target'].ravel()[ix]
    result=linprog(np.r_[np.zeros(n),np.ones(n)],A_ub=big,b_ub=np.r_[limits,wanted,-wanted],bounds=list(zip(lo,hi))+[(0,None)]*n,method='highs',options={'time_limit':300,'threads':1,'primal_feasibility_tolerance':1e-8})
    report=dict(status=str(result.message),success=bool(result.success),elapsed_s=time.monotonic()-started)
    if result.success:
        candidate=macro.astype('float32');candidate.ravel()[ix]=result.x[:n].astype('float32');old=np.load(ROOT/'tests/regional_foundation_combined_v9/reference.npz')['candidate'];fixed=ref['fairway_support']|(base!=old);fixed[:2]=fixed[-2:]=True;fixed[:,:2]=fixed[:,-2:]=True;floor=(~wet)&(~fixed)&(candidate<np.float32(1.4));candidate[floor]=np.float32(1.4)
        report['maximum_residual']=float((B@candidate.ravel()[ix]-limits).max());assert report['maximum_residual']<1e-4
        asc=OUT/'baltic_outline_smoothing_v31.asc'
        with asc.open('w',newline='\n') as f:f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(f,candidate,fmt='%.9g')
        with rasterio.open(asc) as ds:assert np.array_equal(candidate,ds.read(1))
        payload={k:ref[k] for k in ref.files};payload.update(candidate=candidate,parent=base,changed=candidate!=base);np.savez_compressed(OUT/'reference.npz',**payload);report.update(status='CANDIDATE_REQUIRES_INDEPENDENT_GATES',asc_sha256=sha(asc))
    (OUT/'solve.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
