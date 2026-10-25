"""A continuous visible water field only across analytically wet shared edges."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
sys.path[:0]=[str(B),str(W/'tools/terrain')]
from audit_water_connections import submerged_fraction
from v30_common import cell_planes


def make_field(h,p):
    n=h.shape[0]
    pad=np.pad(p,1,constant_values=np.nan)
    # Slots around every native vertex: NW, NE, SW, SE incident cells.
    v=np.stack([pad[:-1,:-1],pad[:-1,1:],pad[1:,:-1],pad[1:,1:]])
    finite=np.isfinite(v)
    reach=np.zeros((4,4,n,n),bool)
    for k in range(4):reach[k,k]=finite[k]
    # Native shared-edge terrain endpoints. Connections use the WHOLE edge,
    # not vertex-only labels, so an edge submerged only midway still joins.
    for a,b,dh,dw in [(0,1,-1,0),(0,2,0,-1),(1,3,0,1),(2,3,1,0)]:
        other=np.roll(h,(-dh,-dw),(0,1))
        contact=finite[a]&finite[b]&(submerged_fraction(h,other,np.minimum(v[a],v[b]))>1e-8)
        if dh<0:contact[0]=False
        if dh>0:contact[-1]=False
        if dw<0:contact[:,0]=False
        if dw>0:contact[:,-1]=False
        reach[a,b]=reach[b,a]=contact
    for k in range(4):
        for a in range(4):
            for b in range(4):reach[a,b]|=reach[a,k]&reach[k,b]
    result=np.full(v.shape,np.nan)
    for a in range(4):
        count=reach[a].sum(axis=0)
        total=np.where(reach[a],np.nan_to_num(v),0).sum(axis=0)
        high=np.max(np.where(reach[a],v,-np.inf),axis=0)
        target=total/np.maximum(count,1)
        # Preserve water on shallow native wet corners without exceeding any
        # group's highest existing plane. All-dry corners remain below land.
        target=np.where(high>h,np.maximum(target,np.minimum(h+.02,high)),target)
        result[a]=np.where(finite[a],target,np.nan)
    # Per cell: NW, NE, SW, SE vertex heights. Local dry divides retain distinct values.
    return np.stack([result[3,:-1,:-1],result[2,:-1,1:],result[1,1:,:-1],result[0,1:,1:]],axis=-1)


def main():
    t=np.load(B/'measured-bank-bed-r2/terrain.npz');h=t['heights'].astype(float)
    p=cell_planes(t['cls'],t['level'],sea_cut=.51)
    field=make_field(h,p)
    assert np.isfinite(field[np.isfinite(p)]).all()
    delta=np.abs(field-p[:,:,None])
    maxdelta=float(np.nanmax(delta))
    checks=[]
    for axis in [0,1]:
        if axis==0:
            a,b=p[:-1],p[1:]; h0,h1=h[1:-1,:-1],h[1:-1,1:]
            aa,bb=field[:-1,:,2:4],field[1:,:,0:2]
        else:
            a,b=p[:,:-1],p[:,1:];h0,h1=h[:-1,1:-1],h[1:,1:-1]
            aa,bb=field[:,:-1,:][:,:,[1,3]],field[:,1:,:][:,:,[0,2]]
        both=np.isfinite(a)&np.isfinite(b)
        before=submerged_fraction(h0,h1,np.minimum(a,b))
        wet=both&(before>1e-8)
        diff=np.max(np.abs(aa-bb),axis=-1)
        assert np.max(diff[wet],initial=0)<1e-9
        # Each side's new water-ground difference is linear. Min of the two
        # is wet exactly on the intersection of their positive intervals.
        x0=aa[:,:,0]-h0;x1=aa[:,:,1]-h1;y0=bb[:,:,0]-h0;y1=bb[:,:,1]-h1
        def interval(d0,d1):
            crossing=np.clip(-d0/np.where(abs(d1-d0)>1e-12,d1-d0,1),0,1)
            lower=np.where((d0<=0)&(d1>0),crossing,0.)
            upper=np.where((d0>0)&(d1<=0),crossing,1.)
            upper=np.where((d0<=0)&(d1<=0),0.,upper)
            return lower,upper
        al,ah=interval(x0,x1);bl,bh=interval(y0,y1)
        after=np.maximum(0,np.minimum(ah,bh)-np.maximum(al,bl))
        extra=both&(before<=1e-8)&(after>1e-8)
        checks.append(dict(axis=axis,wet_contacts=int(wet.sum()),max_wet_seam_m=float(np.max(diff[wet],initial=0)),
            new_contacts_on_dry_divides=int(extra.sum()),new_dry_divide_length_m=float(after[extra].sum()*6)))
    # Independent fixture: separate 1 m / 5 m ponds divided by 8 m terrain.
    hh=np.zeros((3,3));hh[:,1]=8;pp=np.array([[1.,5.],[1.,5.]])
    f=make_field(hh,pp)
    assert np.all(f[:,0]==1) and np.all(f[:,1]==5)
    # Two adjacent underwater planes must join at 2 m, preserving their outer edges.
    f2=make_field(np.zeros((3,3)),np.array([[1.,3.],[1.,3.]]))
    assert np.all(f2[:,0,:][:,[1,3]]==2) and np.all(f2[:,1,:][:,[0,2]]==2)
    report=dict(status='CANDIDATE_FIELD_NOT_PACKAGED',terrain_sha256=hashlib.sha256((B/'measured-bank-bed-r2/terrain.npz').read_bytes()).hexdigest(),
        maximum_visible_delta_m=maxdelta,cell_corners_over_35cm=int(np.count_nonzero(delta>.35001)),
        cell_corners_changed_over_1mm=int(np.count_nonzero(delta>.001)),checks=checks,
        independent_dry_divide_and_wet_join_controls='PASS',
        limits=['The field is not yet applied to compiled objects. Current stitched pilot is not replaced by this calculation.',
                'Any new dry-divide contact is a FAIL to resolve before model authoring. Runtime and coverage gates remain required.'])
    if any(q['new_contacts_on_dry_divides'] for q in checks) or maxdelta>.35001:report['status']='FAIL_FIELD_NOT_FOR_AUTHORING'
    np.save(B/'connected_visual_corners.npy',field)
    (B/'connected-visual-field.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
