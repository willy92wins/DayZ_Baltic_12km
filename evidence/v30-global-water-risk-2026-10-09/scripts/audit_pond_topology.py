"""Whole-grid connectivity and area on the frozen horizontal pond-plane model."""
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import connected_components
def triangle_areas(d):
    positive=d>0;n=positive.sum(1);area=np.zeros(len(d))
    area[n==3]=18.
    for i in range(3):
        j,k=[v for v in range(3) if v!=i]
        one=(n==1)&positive[:,i]
        di,dj,dk=d[one,i],d[one,j],d[one,k]
        area[one]=18*di/(di-dj)*di/(di-dk)
        two=(n==2)&~positive[:,i]
        di,dj,dk=d[two,i],d[two,j],d[two,k]
        area[two]=18*(1-(-di)/(dj-di)*(-di)/(dk-di))
    return area
def domain(h,plane):
    n=plane.shape[0];valid=np.isfinite(plane);rr,cc=np.nonzero(valid)
    full=np.full((n,n),-1,np.int32);full[rr,cc]=np.arange(len(rr))
    nw=h[rr,cc];ne=h[rr,cc+1];sw=h[rr+1,cc];se=h[rr+1,cc+1];lev=plane[rr,cc]
    depths=np.stack([np.c_[lev-nw,lev-ne,lev-se],np.c_[lev-nw,lev-sw,lev-se]],axis=1).reshape(-1,3)
    areas=triangle_areas(depths);active=areas>1e-8
    lookup=np.full(len(active),-1,np.int32);lookup[active]=np.arange(active.sum())
    es=[];et=[]
    idx=np.arange(len(rr));m=np.minimum(nw,se)<lev-1e-7
    es.append(idx[m]*2);et.append(idx[m]*2+1)
    # east shared vertical edge: NE-SE of left, NW-SW of right.
    r,c=np.nonzero(valid[:,:-1]&valid[:,1:])
    a=full[r,c];b=full[r,c+1]
    m=np.minimum(h[r,c+1],h[r+1,c+1])<np.minimum(plane[r,c],plane[r,c+1])-1e-7
    es.append(a[m]*2);et.append(b[m]*2+1)
    # south shared horizontal edge: SW-SE of upper, NW-NE of lower.
    r,c=np.nonzero(valid[:-1]&valid[1:])
    a=full[r,c];b=full[r+1,c]
    m=np.minimum(h[r+1,c],h[r+1,c+1])<np.minimum(plane[r,c],plane[r+1,c])-1e-7
    es.append(a[m]*2+1);et.append(b[m]*2)
    a=lookup[np.concatenate(es)];b=lookup[np.concatenate(et)];keep=(a>=0)&(b>=0)
    graph=sparse.coo_matrix((np.ones(keep.sum(),np.uint8),(a[keep],b[keep])),shape=(int(active.sum()),int(active.sum()))).tocsr()
    number,labels=connected_components(graph,directed=False)
    body_area=np.bincount(labels,weights=areas[active],minlength=number)
    all_labels=np.full(len(active),-1,np.int32);all_labels[active]=labels
    return dict(labels=all_labels,areas=areas,body_area=body_area,cells=(rr,cc))
def compare(before,after,plane):
    a=domain(before,plane);b=domain(after,plane)
    rows=[];bad=set()
    assert not np.any((b['labels']>=0)&(a['labels']<0)),'new wet face from a raise-only edit'
    pairs=np.c_[a['labels'][b['labels']>=0],b['labels'][b['labels']>=0]]
    pairs=np.unique(pairs,axis=0)
    mapping={}
    for i,j in pairs:mapping.setdefault(int(i),[]).append(int(j))
    for i,oldarea in enumerate(a['body_area']):
        if oldarea<1.:continue
        matched=[j for j in mapping.get(i,[]) if b['body_area'][j]>=1.]
        newarea=sum(b['body_area'][j] for j in matched)
        ok=bool(len(matched)==1 and newarea>=.9*oldarea)
        if not ok:bad.add(i)
        rows.append(dict(component=i,area_before=float(oldarea),area_after=float(newarea),area_ratio=float(newarea/oldarea),components_after=len(matched),pass_gate=ok))
    badtri=np.isin(a['labels'],list(bad));badcells=badtri.reshape(-1,2).any(1)
    rr,cc=a['cells'];support=np.zeros_like(before,dtype=bool)
    for dr,dc in ((0,0),(0,1),(1,0),(1,1)):support[rr[badcells]+dr,cc[badcells]+dc]=True
    return dict(status='PASS_FROZEN_POND_MODEL' if not bad else 'FAIL',components=len(rows),
        failed_components=[r for r in rows if not r['pass_gate']],
        total_area_before=float(a['areas'].sum()),total_area_after=float(b['areas'].sum()),
        limits=['Horizontal pond-plane source model, not a render certification or exact ODOL clip.','Sea unchanged for edits above 1.4 m.']),support
def controls():
    # Analytic half-depth triangles and a two-cell channel split by a raised separator.
    assert np.allclose(triangle_areas(np.array([[1.,-1,-1],[1,1,-1],[1,1,1],[-1,-1,-1]])),[4.5,13.5,18,0])
    p=np.ones((2,2));h=np.zeros((3,3))
    a=domain(h,p);assert len(a['body_area'])==1 and abs(a['body_area'][0]-144)<1e-7
    h[:,1]=3;result,_=compare(np.zeros((3,3)),h,p);assert result['status']=='FAIL'
    return dict(analytic_triangle_areas=True,analytic_connected_square=True,channel_split_rejected=True)
