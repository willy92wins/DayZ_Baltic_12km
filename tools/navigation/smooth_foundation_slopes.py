"""Bound terrain slopes while fixing graded road vertices and water clearances.

Upper/lower Lipschitz envelopes make incompatible design constraints explicit.
An infeasible envelope emits evidence and never writes an importable candidate.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/regional-foundation-v1'
OUT=ROOT/'tests/regional_foundation_combined_v3'

def majorant(values):
    h=values.copy();history=[]
    for iteration in range(128):
        n=h.copy()
        n[:,1:]=np.maximum(n[:,1:],h[:,:-1]-2.88)
        n[:,:-1]=np.maximum(n[:,:-1],h[:,1:]-2.88)
        n[1:,:]=np.maximum(n[1:,:],h[:-1,:]-2.88)
        n[:-1,:]=np.maximum(n[:-1,:],h[1:,:]-2.88)
        delta=float(np.max(n-h));history.append(delta);h=n
        if delta<.00001:return h,history
    raise ValueError('Slope envelope did not converge')

def main():
    assert not OUT.exists(),'Fresh candidate required'
    source=ROOT/'tests/regional_foundation_combined_v2/reference.npz'
    ref=np.load(source);h=ref['candidate'];surface=ref['surfaces'];wet=ref['wet'];ocean=ref['ocean'];dry=~(wet|ocean)
    fixed=ref['road_fixed_vertices'];base=ref['base']
    distance,indices=distance_transform_edt(~wet,return_indices=True)
    inside=distance_transform_edt(wet)*6
    # Raster distance minus a cell diagonal is a conservative shore-depth target.
    # It cannot demand a deep bed at a dry corner. Fairway clearance is separate.
    depth=np.minimum(8,np.maximum(0,inside-6*np.sqrt(2))*.25)
    depth[ref['fairway_support']]=np.maximum(depth[ref['fairway_support']],3.5)
    upper=np.full(h.shape,110.,dtype='float32');lower=np.full(h.shape,-20.,dtype='float32')
    upper[wet]=surface[wet]-depth[wet]
    upper[ref['fairway_support']]=np.minimum(upper[ref['fairway_support']],surface[ref['fairway_support']]-3.5)
    lower[dry]=1.25
    nearest=surface[tuple(indices)]
    bank=dry&(distance*6<=12)
    lower[bank]=np.maximum(lower[bank],nearest[bank]+.35)
    upper.ravel()[fixed]=h.ravel()[fixed];lower.ravel()[fixed]=h.ravel()[fixed]
    hi,hi_history=majorant(-upper);hi=-hi
    lo,lo_history=majorant(lower)
    gap=lo-hi;bad=gap>.001
    worst=np.argpartition(gap.ravel(),-20)[-20:]
    report={'status':'INFEASIBLE_CONSTRAINTS' if bad.any() else 'ENVELOPE_FEASIBLE_NOT_VERIFIED',
            'conflicting_vertices':int(bad.sum()),'maximum_conflict_m':float(gap.max()),
            'upper_iterations':len(hi_history),'lower_iterations':len(lo_history),
            'worst':[{'xz':[int(i%2048*6),int(12282-i//2048*6)],'lower':float(lo.ravel()[i]),'upper':float(hi.ravel()[i])} for i in worst]}
    if bad.any():
        np.savez_compressed(ROOT/'tests/regional_foundation_combined_v2/slope-conflicts.npz',upper=hi,lower=lo,conflicts=bad,road_fixed=fixed)
    else:
        smooth,base_history=majorant(base)
        candidate=np.maximum(lo,np.minimum(hi,smooth))
        assert np.max(abs(candidate.ravel()[fixed]-h.ravel()[fixed]))<.001
        OUT.mkdir(parents=True)
        asc=OUT/'baltic_regional_foundation_v3.asc'
        with asc.open('w',encoding='ascii',newline='\n') as handle:
            handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
            np.savetxt(handle,candidate,fmt='%.9g')
        with rasterio.open(asc) as ds:assert np.array_equal(ds.read(1),candidate)
        data={k:ref[k] for k in ref.files};data['candidate']=candidate;data['changed']=candidate!=base
        np.savez_compressed(OUT/'reference.npz',**data)
        report.update(asc_sha256=hashlib.sha256(asc.read_bytes()).hexdigest(),changed_vertices=int(np.count_nonzero(candidate!=base)),
                      changes_from_v2=int(np.count_nonzero(candidate!=h)))
    (EV/'slope-envelope-v3.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='worst'},indent=2))
    raise SystemExit(1 if bad.any() else 0)

if __name__=='__main__':main()
