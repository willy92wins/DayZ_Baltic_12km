"""Consume candidate triangles independently; no producer eligibility import."""
from pathlib import Path
import hashlib,json
import numpy as np
from shapely.geometry import Polygon

B=Path(__file__).parent
S=Path('E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009/candidate')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def wet_polygon(xyz,water):
    # 3-D edge/plane intersections; evaluate output area through GEOS, not producer masks.
    d=np.asarray(water)-xyz[:,1]
    out=[]
    for i in range(3):
        j=(i+1)%3
        if d[i]>0:out.append(xyz[i,[0,2]])
        if (d[i]>0)!=(d[j]>0):
            q=d[i]/(d[i]-d[j]);out.append((xyz[i]+q*(xyz[j]-xyz[i]))[[0,2]])
    return Polygon(out) if len(out)>=3 else Polygon()

def scan(h,v,p,f):
    delta=h!=v;rows,cols=np.nonzero(delta)
    cells=set()
    for r,c in zip(rows,cols):
        for dr,dc in [(0,0),(-1,0),(0,-1),(-1,-1)]:
            rr,cc=int(r+dr),int(c+dc)
            if 0<=rr<2047 and 0<=cc<2047:cells.add((rr,cc))
    maxshore=0.;bad_draft=0;faces=0;min_draft=float('inf');maxslope_before=0.;maxslope_after=0.;new_steep=0;bad=[]
    for r,c in sorted(cells):
        verts=[(r,c),(r,c+1),(r+1,c),(r+1,c+1)]
        for ids in [(0,1,3),(0,2,3)]:
            ij=[verts[i] for i in ids]
            if not any(delta[a,b] for a,b in ij):continue
            faces+=1
            xyz=np.array([[b*6,h[a,b],12282-a*6] for a,b in ij],float)
            xyz2=xyz.copy();xyz2[:,1]=[v[a,b] for a,b in ij]
            for typ,w in [('physical',np.full(3,p[r,c])),('visible',f[r,c,list(ids)])]:
                before=wet_polygon(xyz,w);after=wet_polygon(xyz2,w)
                diff=before.symmetric_difference(after).area
                maxshore=max(maxshore,diff)
                draft=float(np.min(w-xyz2[:,1]));min_draft=min(min_draft,draft)
                if draft<.95-1e-8:
                    bad_draft+=1
                    if len(bad)<10:bad.append(dict(row=r,col=c,face=list(ids),kind=typ,min_draft=draft))
            a=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);b=np.cross(xyz2[1]-xyz2[0],xyz2[2]-xyz2[0])
            da=float(np.degrees(np.arctan2(np.hypot(a[0],a[2]),abs(a[1]))));db=float(np.degrees(np.arctan2(np.hypot(b[0],b[2]),abs(b[1]))))
            maxslope_before=max(maxslope_before,da);maxslope_after=max(maxslope_after,db)
            new_steep+=db>max(da,35)+1e-6
    return dict(changed_faces=faces,shore_symmetric_difference_max_m2=maxshore,bad_draft_faces_representations=bad_draft,min_draft_changed_faces_m=min_draft,max_slope_before_degrees=maxslope_before,max_slope_after_degrees=maxslope_after,new_steep_faces=int(new_steep),draft_examples=bad)

def main():
    t=dict(np.load(S/'terrain.npz'));u=dict(np.load(B/'candidate/terrain.npz'));h=t['heights'].astype(float);v=u['heights'].astype(float)
    p=np.load(S/'plane.npy');f=np.load(S/'visible-field.npy');ch=h!=v
    stats=scan(h,v,p,f)
    rr,cc=np.indices(h.shape);dist=(cc*6-2417.1428225906)**2+(12282-rr*6-6889.8850822322)**2
    gates=dict(metadata_exact=all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights'),reserve_platform_exact=not bool(np.any(ch&(t['reserve']|t['platform']))),inside_narva_circle=not bool(np.any(ch&(dist>480**2))),only_class3=bool(np.all(t['cls'][ch]==3)),only_raise_up_to_1m=bool(np.all(v>=h)&np.all(v[ch]<=1)),shore_geometry_exact=stats['shore_symmetric_difference_max_m2']<1e-9,draft_all_changed_faces=stats['bad_draft_faces_representations']==0,no_new_steep_faces=stats['new_steep_faces']==0,optical_cell_treated=bool(np.all(v[889:891,402:404]==1)),bridge_control_exact=bool(np.array_equal(v[898:900,402:404],h[898:900,402:404])))
    # Analytic independently known triangle: split by water at halfway -> 3/4 of 18m2.
    tri=np.array([[0,0,0],[6,0,0],[6,2,-6]],float)
    assert abs(wet_polygon(tri,[1,1,1]).area-13.5)<1e-10
    mutant=tri.copy();mutant[0,1]=1.5
    assert wet_polygon(tri,[1,1,1]).symmetric_difference(wet_polygon(mutant,[1,1,1])).area>1
    report=dict(status='PASS_DIAGNOSTIC_SOURCE' if all(gates.values()) else 'FAIL_DIAGNOSTIC_SOURCE',gates=gates,stats=stats,controls=['analytic_13_5m2_triangle','shore_mutant_rejected'],input_sha256=sha(S/'terrain.npz'),candidate_sha256=sha(B/'candidate/terrain.npz'),limits=['Not visual acceptance or map promotion.','Bed slope reported, not artistic acceptance.','Nominal and visible draft, not worst weather phase.'])
    (B/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
