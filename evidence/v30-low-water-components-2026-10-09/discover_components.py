"""Read-only whole-map positive-width connectivity of physical water triangles."""
from pathlib import Path
import csv,json,hashlib,time
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.ndimage import label
B=Path(__file__).parent
SOURCE=Path('E:/DayZ-Baltic-Build/v30-native-hinge-finish-20261009/candidate/terrain.npz')
PLANE=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/frozen-field-reference/plane.npy')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
EPS=1e-8

def area(d):
    out=np.zeros(d.shape[0]);positive=d>0;count=positive.sum(1);out[count==3]=18
    for j in range(3):
        other=[k for k in range(3) if k!=j]
        m=(count==1)&positive[:,j];x=d[m,j];out[m]=18*x*x/((x-d[m,other[0]])*(x-d[m,other[1]]))
        m=(count==2)&~positive[:,j];x=-d[m,j];out[m]=18*(1-x*x/((x+d[m,other[0]])*(x+d[m,other[1]])))
    return out

def connected(h,p):
    rows,cols=p.shape;r,c=np.nonzero(np.isfinite(p));heights=np.stack((h[r,c],h[r,c+1],h[r+1,c],h[r+1,c+1]),axis=1)
    d=p[r,c,None]-heights;triangles=np.stack((d[:,[0,1,3]],d[:,[0,2,3]]),axis=1);active=area(triangles.reshape(-1,3)).reshape(-1,2)>1e-12
    ids=np.full((rows,cols,2),-1,np.int32);local=np.full(active.shape,-1,np.int32);local[active]=np.arange(active.sum());ids[r,c]=local
    edges=[]
    def edge(a,b,shared):
        ok=(a>=0)&(b>=0)&shared
        edges.append(np.column_stack((a[ok],b[ok])))
    edge(local[:,0],local[:,1],np.max(d[:,[0,3]],axis=1)>EPS)
    right=c<cols-1;rr,cc=r[right],c[right];pp=np.minimum(p[rr,cc],p[rr,cc+1]);shared=np.maximum(pp-h[rr,cc+1],pp-h[rr+1,cc+1])>EPS
    edge(ids[rr,cc,0],ids[rr,cc+1,1],shared)
    down=r<rows-1;rr,cc=r[down],c[down];pp=np.minimum(p[rr,cc],p[rr+1,cc]);shared=np.maximum(pp-h[rr+1,cc],pp-h[rr+1,cc+1])>EPS
    edge(ids[rr,cc,1],ids[rr+1,cc,0],shared)
    pairs=np.concatenate(edges);n=int(active.sum());graph=coo_matrix((np.ones(len(pairs),np.int8),(pairs[:,0],pairs[:,1])),shape=(n,n)).tocsr()
    count,labels=connected_components(graph,directed=False)
    components=np.full(ids.shape,-1,np.int32);components[ids>=0]=labels[ids[ids>=0]]
    return r,c,heights,d,triangles,active,local,labels,components,count,len(pairs)

def controls():
    p=np.ones((1,1));h=np.zeros((2,2));assert connected(h,p)[-2]==1
    h=np.array([[2.,0],[0,2.]]) # opposing wet corners with dry shared diagonal
    assert connected(h,p)[-2]==2
    h=np.array([[1.,0],[0,1.]]) # zero-depth contact is not a positive-width connection
    assert connected(h,p)[-2]==2
    h=np.array([[.99,0],[0,1.]])
    assert connected(h,p)[-2]==1
    h=np.zeros((2,3));p=np.array([[1.,2.]])
    assert connected(h,p)[-2]==1
    p=np.array([[1.,np.nan]])
    assert connected(h,p)[-2]==1
    assert np.allclose(area(np.array([[1,1,1],[1,-1,-1],[1,1,-1],[0,-1,-1]])),[18,4.5,13.5,0])
    return ['all_wet_connected','saddle_separated','zero_depth_line_not_passage','positive_width_restores_connection','different_levels_share_wet_edge','absent_cell_not_connection','analytic_triangle_area']

def main():
    started=time.monotonic();negative=controls();assert sha(SOURCE)=='fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6'
    assert sha(PLANE)=='d59dcdb908b4381a456629fb080a9769147b6fb1a3e321a6423bc931a0fb8803'
    t=dict(np.load(SOURCE));h=t['heights'].astype(float);p=np.load(PLANE)
    r,c,heights,d,tri,active,local,labs,comps,n,connections=connected(h,p)
    areas=area(tri.reshape(-1,3))[active.ravel()];total=np.bincount(labs,weights=areas,minlength=n)
    # Exact subarea of each physical wet triangle whose bed is also below the measured sea crest.
    sea_depth=np.minimum(p[r,c],.85)[:,None]-heights
    seas=np.stack((sea_depth[:,[0,1,3]],sea_depth[:,[0,2,3]]),axis=1)
    seaarea=np.bincount(labs,weights=area(seas.reshape(-1,3))[active.ravel()],minlength=n)
    lo=np.full(n,np.inf);hi=np.full(n,-np.inf);bed=np.full(n,np.inf);bits=np.zeros(n,np.int32)
    ymin=np.full(n,np.inf);ymax=np.full(n,-np.inf);xmin=np.full(n,np.inf);xmax=np.full(n,-np.inf)
    engineering=np.zeros(n,bool);narva=np.zeros(n,bool)
    for face,corners in enumerate(([0,1,3],[0,2,3])):
        use=active[:,face];rr,cc=r[use],c[use];labels=labs[local[use,face]];lv=p[rr,cc]
        np.minimum.at(lo,labels,lv);np.maximum.at(hi,labels,lv)
        np.minimum.at(bed,labels,np.min(heights[use][:,corners],axis=1))
        np.minimum.at(xmin,labels,cc*6);np.maximum.at(xmax,labels,(cc+1)*6);np.minimum.at(ymin,labels,12282-(rr+1)*6);np.maximum.at(ymax,labels,12282-rr*6)
        for j in corners:
            dr,dc=[(0,0),(0,1),(1,0),(1,1)][j];wet=d[use,j]>EPS
            np.bitwise_or.at(bits,labels[wet],1<<t['cls'][rr[wet]+dr,cc[wet]+dc].astype(int))
            np.logical_or.at(engineering,labels,t['reserve'][rr+dr,cc+dc]|t['platform'][rr+dr,cc+dc])
            np.logical_or.at(narva,labels,t['narva'][rr+dr,cc+dc])
    support_labels,support_n=label(np.isfinite(p),structure=np.ones((3,3)))
    records=[]
    for i in range(n):
        classes=[j for j in range(8) if bits[i]&(1<<j)]
        records.append(dict(component=i,area_m2=float(total[i]),below_sea_crest_m2=float(seaarea[i]),minimum_bed_m=float(bed[i]),level_min_m=float(lo[i]),level_max_m=float(hi[i]),classes=','.join(map(str,classes)),has_flowing=any(j in (3,5,6) for j in classes),engineering=bool(engineering[i]),narva=bool(narva[i]),xmin=float(xmin[i]),zmin=float(ymin[i]),xmax=float(xmax[i]),zmax=float(ymax[i])))
    with (B/'physical-components.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
    risky=[q for q in records if q['area_m2']>=1 and q['below_sea_crest_m2']>1]
    ponds=[q for q in risky if not q['has_flowing'] and set(q['classes'].split(','))<=set(['0','2','7'])]
    rr,cc=round((12282-6816)/6),round(2724/6);target_labs=[int(x) for x in comps[rr,cc] if x>=0]
    target=[records[i] for i in sorted(set(target_labs))]
    support=int(support_labels[rr,cc]);support_mask=support_labels==support;levels=p[support_mask]
    result=dict(status='READ_ONLY_GLOBAL_PHYSICAL_WATER_CONNECTIVITY',source_sha256=sha(SOURCE),plane_sha256=sha(PLANE),active_triangles=len(labs),positive_width_connections=connections,components=n,components_at_least_1m2=sum(q['area_m2']>=1 for q in records),total_wet_area_m2=float(total.sum()),bodies_with_bed_below_sea_crest=len(risky),standing_only_below_sea_crest=len(ponds),standing_below_sea_crest_area_m2=sum(q['below_sea_crest_m2'] for q in ponds),target_probe=[2724,6816],target_components=target,target_support_domain=dict(label=support,cells=int(support_mask.sum()),level_min=float(levels.min()),level_max=float(levels.max()),whole_map_support_domains=support_n),controls=negative,seconds=time.monotonic()-started,limits=['Positive-width connectivity of nominal physical planes; visible field and navigation draft remain separate.','Sea-under-inland-water area is a geometric exposure risk, not a diagnosis of water drawn over dry land.','No level or terrain changes. Nominal body identifiers from earlier level census are not used as hydraulic components.','Boundary boxes enclose source cells, not exact clipped shorelines.'])
    np.savez_compressed(B/'physical-component-labels.npz',triangles=comps,support_domains=support_labels)
    (B/'discovery.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
