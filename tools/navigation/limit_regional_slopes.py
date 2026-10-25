"""Project uplift downward to bounded adjacent gradients; preserve native floor."""
import json
import numpy as np
import rasterio
from prepare_regional_outline import ROOT,TRANSFORM,sha,save


def main():
    source=ROOT/'tests/regional_outline_v2/reference.npz'
    if sha(source)!='b8414ba3b53f1f0b43bd1c4f667dc4b74862e908ce0cef6c33fa583240c41bf5':
        raise ValueError('Candidate drift')
    out=ROOT/'tests/regional_outline_v3'; ev=ROOT/'evidence/regional-outline-v3'
    if out.exists() or ev.exists():
        raise ValueError('Fresh output required')
    with np.load(source) as ref:
        data={key:ref[key] for key in ref.files}
    base=data['base']; original=data['candidate']; h=original.copy()
    # Per-axis0.48 implies triangle gradient norm <=sqrt(2)*0.48 (34.2deg).
    # Existing stronger native edges remain the floor; final consumer check
    # independently rejects any affected triangle above35deg.
    xcost=np.maximum(2.88,np.abs(np.diff(base,axis=1)))
    ycost=np.maximum(2.88,np.abs(np.diff(base,axis=0)))
    history=[]
    for iteration in range(256):
        next_h=h.copy()
        next_h[:,1:]=np.minimum(next_h[:,1:],h[:,:-1]+xcost)
        next_h[:,:-1]=np.minimum(next_h[:,:-1],h[:,1:]+xcost)
        next_h[1:,:]=np.minimum(next_h[1:,:],h[:-1,:]+ycost)
        next_h[:-1,:]=np.minimum(next_h[:-1,:],h[1:,:]+ycost)
        np.maximum(next_h,base,out=next_h)
        difference=float(np.max(h-next_h))
        history.append(difference); h=next_h
        if difference<.0001:
            break
    else:
        raise ValueError('Projection did not converge')
    out.mkdir();ev.mkdir()
    candidate=h
    data['candidate']=candidate;data['changed']=candidate!=base
    asc=out/'baltic_regional_outline_v3.asc'
    with asc.open('w',encoding='ascii',newline='\n') as handle:
        handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(handle,candidate,fmt='%.9f')
    with rasterio.open(asc) as ds:
        if not np.array_equal(ds.read(1),candidate):
            raise ValueError('ASC did not preserve float32')
    np.savez_compressed(out/'reference.npz',**data)
    for name,values in [('height',candidate),('delta',candidate-base)]:
        with rasterio.open(out/f'{name}.tif','w',driver='GTiff',height=2048,width=2048,count=1,
                           dtype='float32',transform=TRANSFORM,compress='deflate') as ds:
            ds.write(values,1)
    report={'status':'PROJECTED_PENDING_INDEPENDENT_CHECK','source_sha256':sha(source),
            'candidate_sha256':sha(asc),'reference_sha256':sha(out/'reference.npz'),
            'iterations':len(history),'iteration_max_change_m':history,
            'maximum_m':float(candidate.max()),'changed_from_v2_vertices':int(np.count_nonzero(candidate!=original)),
            'max_lowering_from_v2_m':float(np.max(original-candidate)),
            'design':'Only reduce proposed uplift; never lower native terrain or change controls.0.48 per-axis grade cap.',
            'limits':['No hydrology acceptance, native import or navmesh yet.']}
    save(ev/'preparation.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
