"""Add explicit shallow-lake retention to the frozen V25 shoreline system."""
from pathlib import Path
import json,hashlib,time,math
import numpy as np
from scipy.sparse import load_npz,coo_matrix,eye,hstack,vstack,csr_matrix,save_npz
from scipy.optimize import linprog
from rasterio.features import rasterize
import rasterio
from affine import Affine
from shapely import polygons,intersection,get_coordinates
from shapely.geometry import shape
ROOT=Path(__file__).resolve().parents[2];F=ROOT/'tests/regional_outline_smoothing_v24a';P=ROOT/'tests/regional_outline_smoothing_v25';OUT=ROOT/'tests/regional_outline_smoothing_v27'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();start=time.monotonic()
    # Exact pins recorded by V25 before its successful solve.
    pins=json.loads((P/'pre-solve.json').read_text());assert sha(F/'constraints.npz')==pins['parent_matrix_sha256'];assert sha(F/'variables.npz')==pins['parent_variables_sha256']
    A=load_npz(F/'constraints.npz');d=np.load(F/'variables.npz');ix=d['variables'];macro=d['macro'];n=len(ix);lookup=np.full(macro.size,-1,np.int32);lookup[ix]=np.arange(n)
    source=ROOT/'tests/regional_foundation_combined_v10/reference.npz';assert sha(source)==pins['source_npz_sha256'];ref=np.load(source);base=ref['candidate']
    rows=[];cols=[];values=[];rhs=[];bodies=[];impossible=[]
    def add(points,limit):
        before=len(rhs)
        for x,z in points:
            c=min(2046,max(0,int(x//6)));r=min(2046,max(0,int((12282-z)//6)));u=x/6-c;v=(12282-z)/6-r
            if v<=u:ids=np.array([r*2048+c,r*2048+c+1,(r+1)*2048+c+1]);w=np.array([1-u,u-v,v])
            else:ids=np.array([r*2048+c,(r+1)*2048+c+1,(r+1)*2048+c]);w=np.array([1-v,u,v-u])
            j=lookup[ids];free=j>=0;bound=limit-float(w[~free]@macro.ravel()[ids[~free]])
            if not free.any():
                if bound< -1e-6:impossible.append(dict(xz=[x,z],residual=-bound))
                continue
            rows.extend([len(rhs)]*int(free.sum()));cols.extend(j[free]);values.extend(w[free]);rhs.append(bound)
        return len(rhs)-before
    features=json.loads((ROOT/'evidence/regional-foundation-v1/water-surfaces-contour-v2.geojson').read_text())['features']
    for f in features:
        if not f['properties']['body'].startswith('lake_'):continue
        g=shape(f['geometry'])
        if not g.buffer(-6*math.sqrt(2)).is_empty:continue
        core=g.buffer(-4.5);count=0;mode='4.5m_inset'
        if core.is_empty:
            mode='representative';p=g.representative_point();count=add([[p.x,p.y]],float(f['properties']['level_m']-.15))
        else:
            mask=rasterize([(core,1)],out_shape=(2047,2047),transform=Affine(6,0,0,0,-6,12282),all_touched=True,dtype='uint8');r,c=np.where(mask);x=c*6;z=12282-r*6;aa=np.c_[x,z];bb=np.c_[x+6,z];dd=np.c_[x+6,z-6];ee=np.c_[x,z-6]
            for vertices in [np.stack([aa,bb,dd],axis=1),np.stack([aa,dd,ee],axis=1)]:count+=add(get_coordinates(intersection(polygons(vertices),core)),float(f['properties']['level_m']-.15))
        bodies.append(dict(body=f['properties']['body'],mode=mode,rows=count,level_m=f['properties']['level_m']))
    extra=coo_matrix((values,(rows,cols)),shape=(len(rhs),n)).tocsr();save_npz(OUT/'small-lake-constraints.npz',extra);np.save(OUT/'small-lake-rhs.npy',np.array(rhs))
    pre={**pins,**dict(status='FROZEN_BEFORE_SOLVE',parent_pre_solve_sha256=sha(P/'pre-solve.json'),lake_depth_m=.15,small_core_inset_m=4.5,bodies=bodies,impossible_fixed=impossible,extra_rows=len(rhs))};(OUT/'pre-solve.json').write_text(json.dumps(pre,indent=2)+'\n');print(json.dumps({k:v for k,v in pre.items() if k!='seed_vertices'}),flush=True)
    if impossible:raise SystemExit(2)
    B=vstack([A,extra],format='csr');limits=np.r_[d['rhs'],rhs];bounds=np.load(P/'local-exception.npz');lo,hi=bounds['lo'],bounds['hi'];I=eye(n,format='csr')
    big=vstack([hstack([B,csr_matrix(B.shape)]),hstack([I,-I]),hstack([-I,-I])],format='csr');wanted=d['target'].ravel()[ix]
    result=linprog(np.r_[np.zeros(n),np.ones(n)],A_ub=big,b_ub=np.r_[limits,wanted,-wanted],bounds=list(zip(lo,hi))+[(0,None)]*n,method='highs',options={'time_limit':300,'threads':1,'primal_feasibility_tolerance':1e-8})
    report=dict(status=str(result.message),solver_success=bool(result.success),elapsed_s=time.monotonic()-start)
    if result.success:
        h=macro.astype('float32');h.ravel()[ix]=result.x[:n].astype('float32');report['maximum_residual']=float((B@h.ravel()[ix]-limits).max());assert report['maximum_residual']<1e-4
        old=np.load(ROOT/'tests/regional_foundation_combined_v9/reference.npz')['candidate'];fixed=ref['fairway_support']|(base!=old);fixed[:2]=fixed[-2:]=True;fixed[:,:2]=fixed[:,-2:]=True;wet=ref['wet']|ref['ocean'];repair=(~wet)&(~fixed)&(h<np.float32(1.4));h[repair]=np.float32(1.4)
        asc=OUT/'baltic_outline_smoothing_v27.asc'
        with asc.open('w',newline='\n') as f:f.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n');np.savetxt(f,h,fmt='%.9g')
        with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),h)
        payload={k:ref[k] for k in ref.files};payload.update(candidate=h,parent=base,changed=h!=base);np.savez_compressed(OUT/'reference.npz',**payload)
        report.update(status='CANDIDATE_REQUIRES_INDEPENDENT_GATES',asc_sha256=sha(asc),floor_repaired_vertices=int(repair.sum()))
    (OUT/'solve.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
