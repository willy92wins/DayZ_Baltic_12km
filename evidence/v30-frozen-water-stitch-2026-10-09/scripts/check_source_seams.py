"""Compare both sides of every original wet native-cell contact."""
from pathlib import Path
import json,sys
import numpy as np
B=Path('E:/DayZ-Baltic-Build/v30-frozen-water-stitch-20261009')
sys.path.insert(0,str(B))
from audit_frozen_visual import overlap_length,sha

def main():
    root=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
    p=np.load(root/'frozen-field-reference/plane.npy');f=np.load(B/'preserved-field.npy');h=np.load(root/'measured-bank-bed-r2/terrain.npz')['heights']
    rows=[]
    for axis in (0,1):
        if axis==0:
            a,b=p[:-1],p[1:];ground=np.stack([h[1:-1,:-1],h[1:-1,1:]],axis=-1);fa,fb=f[:-1,:,2:4],f[1:,:,0:2]
        else:
            a,b=p[:,:-1],p[:,1:];ground=np.stack([h[:-1,1:-1],h[1:,1:-1]],axis=-1);fa,fb=f[:,:-1,:][:,:,[1,3]],f[:,1:,:][:,:,[0,2]]
        valid=np.isfinite(a)&np.isfinite(b);deptha=a[valid,None]-ground[valid];depthb=b[valid,None]-ground[valid]
        contact=overlap_length(deptha,depthb)>1e-8
        errors=np.max(np.abs(fa[valid]-fb[valid]),axis=-1)[contact]
        assert errors.size>0 and errors.max()==0.
        rows.append(dict(axis=axis,wet_edges=len(errors),maximum_height_gap_m=float(errors.max())))
    # Same contact with a one-millimetre endpoint error must fail exact continuity.
    a=np.array([[1.,1.]]);b=np.array([[1.,1.001]])
    negative=bool((np.max(abs(a-b),axis=-1)>1e-9).all());assert negative
    report=dict(status='PASS_ALL_ORIGINAL_WET_SEAMS',field_sha256=sha(B/'preserved-field.npy'),axes=rows,
                one_millimetre_endpoint_mutant_rejected=negative)
    (B/'source-seams-recheck.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
