"""Raise-only nine-cell terminal taper on Msta; no changes to the frozen water planes."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import shapely
from shapely.geometry import LineString,Point,Polygon
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-river-end-tapers-20261009')
E=W/'evidence/v30-river-end-tapers-2026-10-09'
sys.path[:0]=[str(W/'tools/terrain')]
from v30_common import cell_planes,tri_sample,vertex_plane_bounds
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def native_polygon(h,p,box):
    xmin,zmin,xmax,zmax=box
    polys=[]
    for r in range(max(0,int((12282-zmax)//6)),min(2047,int((12282-zmin)//6)+1)):
        for c in range(max(0,int(xmin//6)),min(2047,int(xmax//6)+1)):
            lev=p[r,c]
            if not np.isfinite(lev):continue
            for dr,dc in [(0,1),(1,0)]:
                rc=[(r,c),(r+dr,c+dc),(r+1,c+1)]
                xy=np.array([(j*6,12282-i*6) for i,j in rc]);d=np.array([lev-h[i,j] for i,j in rc]);out=[]
                for i,j in [(0,1),(1,2),(2,0)]:
                    if d[i]>0:out.append(xy[i])
                    if d[i]*d[j]<0:out.append(xy[i]+d[i]/(d[i]-d[j])*(xy[j]-xy[i]))
                if len(out)>=3:polys.append(Polygon(out))
    return shapely.union_all(polys,grid_size=1e-7)


def section(h,p,axis,s):
    pt=axis.interpolate(s);a=np.array(axis.interpolate(max(0,s-.3)).coords[0]);b=np.array(axis.interpolate(min(axis.length,s+.3)).coords[0]);v=b-a;v/=np.linalg.norm(v)
    normal=np.array([-v[1],v[0]]);d=np.arange(-30.,30.001,.1);xy=np.array(pt.coords[0])+d[:,None]*normal
    r=np.clip(((12282-xy[:,1])/6).astype(int),0,2046);c=np.clip((xy[:,0]/6).astype(int),0,2046)
    wet=p[r,c]-tri_sample(h,xy[:,0],xy[:,1])>1e-5
    spans=[];start=None
    for i,v in enumerate(np.r_[wet,False]):
        if v and start is None:start=i
        if not v and start is not None:
            spans.append((float(d[start]),float(d[i-1]),(i-start)*.1));start=None
    nearest=min(spans,key=lambda q:max(q[0],-q[1],0),default=(0,0,0))
    return dict(s=s,point=list(pt.coords[0]),width_m=round(nearest[2],3),axis_wet=bool(wet[len(d)//2]),span=nearest[:2])


def main():
    source=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009/measured-bank-bed-r2/terrain.npz')
    assert sha(source)=='e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c'
    t=dict(np.load(source));h=t['heights'].astype(float);p=cell_planes(t['cls'],t['level'],sea_cut=.51);pmin,pmax=vertex_plane_bounds(p)
    profile=Path('E:/DayZ-Baltic-Build/v30-v11/design/profiles.npz')
    original=LineString(np.load(profile)['river_057'][:,1:3]);cut=LineString([(12222,1750),(12222,1820)])
    end=original.intersection(cut);assert end.geom_type=='Point';station=original.project(end)
    s=np.arange(0,90.01,1.);points=np.array([original.interpolate(station-q).coords[0] for q in s]);axis=LineString(points)
    box=(points[:,0].min()-24,points[:,1].min()-24,12228,points[:,1].max()+24)
    old=native_polygon(h,p,box)
    # Cross-section width derives from the actual native water rather than the design's median width.
    discs=[];radii=[]
    for s in np.arange(0,72.01,1):
        xy=np.array(axis.interpolate(s).coords[0]);pt=Point(xy)
        radius=max(.01,pt.distance(old.boundary)) if old.covers(pt) else .01
        u=min(s/54,1);radius*=np.sqrt(max(0,2*u-u*u))
        discs.append(pt.buffer(max(radius,.001),quad_segs=16));radii.append([float(s),float(radius)])
    target=shapely.union_all(discs).intersection(old)
    v=h.copy();records=[];converted=[]
    xmin,zmin,xmax,zmax=box
    for r in range(max(0,int((12282-zmax)//6)),min(2048,int((12282-zmin)//6)+2)):
        for c in range(max(0,int(xmin//6)),min(2048,int(xmax//6)+2)):
            x,z=c*6,12282-r*6;pt=Point(x,z);along=axis.project(pt)
            if not (0<=along<54) or axis.distance(pt)>18 or t['cls'][r,c]!=5:continue
            assert not t['reserve'][r,c] and not t['platform'][r,c] and not t['beach'][r,c]
            if not np.isfinite(pmax[r,c]):continue
            inside=target.covers(pt);dist=pt.distance(target.boundary)
            # Existing wet depths can decrease only on this non-navigable terminal;
            # preserve at least 0.201 m at its remaining wet support vertices.
            if inside:
                wanted=min(pmax[r,c]-.15*dist,pmin[r,c]-.201)
            else:
                wanted=max(pmax[r,c]+.35,1.4)
            blend=np.clip((54-along)/12,0,1);blend=blend*blend*(3-2*blend)
            new=max(h[r,c],h[r,c]+max(0,wanted-h[r,c])*blend)
            if new<=h[r,c]+1e-7:continue
            v[r,c]=new
            if new>=pmax[r,c]+.34999:converted.append((r,c))
            records.append(dict(row=r,col=c,x=x,z=z,along_m=along,inside=bool(inside),before=float(h[r,c]),after=float(new)))
    v=v.astype(np.float32)
    out=B/'candidate-msta';out.mkdir(parents=True,exist_ok=False)
    # Keep metadata exact until the numeric geometry gates decide whether this is usable.
    np.savez_compressed(out/'terrain.npz',**dict(t,heights=v))
    np.save(out/'frozen_planes.npy',p)
    (out/'axis.json').write_text(json.dumps(points.tolist())+'\n')
    sections=[]
    for s in np.arange(0,66.01,3):
        a,b=section(h,p,axis,float(s)),section(v,p,axis,float(s));sections.append(dict(before=a,after=b))
    report=dict(status='CANDIDATE_NOT_PACKAGED',source_sha256=sha(source),terrain_sha256=sha(out/'terrain.npz'),
        profile_sha256=sha(profile),feature='river_057',length_m=54,box=box,changes=records,proposed_dry_vertices=converted,
        old_native=mapping_safe(old),target=mapping_safe(target),radii=radii,sections=sections,
        limits=['Metadata remains frozen for this proposal, so newly dry source classes are explicitly recorded.',
                'No lowering, no new water, no water model change. Candidate requires independent topology/engineering/shape gates.'])
    (out/'authoring.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('old_native','target','radii','sections','changes')},indent=2))
    print(json.dumps(sections,indent=1))


def mapping_safe(g):return json.loads(shapely.to_geojson(g))
if __name__=='__main__':main()
