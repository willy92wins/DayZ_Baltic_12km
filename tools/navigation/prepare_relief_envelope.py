"""Slope-budget landform candidate, reusing the exact frozen v1 constraints."""
import json
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter, distance_transform_edt
from prepare_regional_outline import ROOT, TRANSFORM, sha, save


def main():
    old=ROOT/'tests/regional_outline_v1/reference.npz'
    if sha(old)!='10bd6d9c9b944e2964d72055301101a7014c5bb09ff3ddc298a15897bab5c915':
        raise ValueError('Frozen constraints changed')
    out=ROOT/'tests/regional_outline_v2'
    ev=ROOT/'evidence/regional-outline-v2'
    if out.exists() or ev.exists():
        raise ValueError('Fresh candidate required')
    out.mkdir(); ev.mkdir()
    with np.load(old) as ref:
        data={key:ref[key] for key in ref.files}
    base=data['base']; controls=data['controls']
    with rasterio.open(ROOT/'source/baltic_physical_2048_6m.asc') as ds:
        physical=ds.read(1)
    x,z=np.meshgrid(np.arange(2048)*6.,12282-np.arange(2048)*6.)
    a=np.exp(-.5*(((x-5900)/1700)**2+((z-7950)/1500)**2))
    b=np.exp(-.5*(((x-4500)/1700)**2+((z-1100)/1550)**2))
    target=gaussian_filter(np.maximum(physical,0).astype('float64'),9)*(5+15*a+19*b)
    distance=distance_transform_edt(~controls,sampling=6)
    # Derivative starts at zero and approaches0.60. No protected value moves.
    cap=.60*(distance-36*(1-np.exp(-distance/36)))
    requested=np.maximum(0,target-base)
    uplift=np.minimum(gaussian_filter(np.minimum(requested,cap),4),cap)
    candidate=base.copy()
    active=(uplift>=.001)&~controls
    candidate[active]=np.round(base[active]+uplift[active],4).astype('float32')
    data['candidate']=candidate; data['changed']=candidate!=base
    asc=out/'baltic_regional_outline_v2.asc'
    with asc.open('w',encoding='ascii',newline='\n') as handle:
        handle.write('ncols 2048\nnrows 2048\nxllcorner 200000\nyllcorner 0\ncellsize 6\nNODATA_value -9999\n')
        np.savetxt(handle,candidate,fmt='%.9f')
    with rasterio.open(asc) as ds:
        if not np.array_equal(ds.read(1),candidate):
            raise ValueError('ASC roundtrip failed')
    np.savez_compressed(out/'reference.npz',**data)
    for name,values in [('height',candidate),('delta',candidate-base)]:
        with rasterio.open(out/f'{name}.tif','w',driver='GTiff',height=2048,width=2048,
                           count=1,dtype='float32',transform=TRANSFORM,compress='deflate') as ds:
            ds.write(values,1)
    design=json.loads((ROOT/'evidence/navigation/selective-relief-v1/design.json').read_text())
    slopes=np.degrees(np.arctan(np.hypot(*np.gradient(candidate,6))))
    stats={}
    for zone in design['zones']:
        cx,cz=zone['centre_game_km']; dx,dz=zone['ellipse_diameters_km']
        area=(((x/1000-cx)/(dx/2))**2+((z/1000-cz)/(dz/2))**2<=1)&~data['water']
        stats[zone['id']]={'maximum_m':float(candidate[area].max()),
                         'height_p50_p90_p99_m':np.percentile(candidate[area],[50,90,99]).tolist(),
                         'slope_p50_p95_p99_deg':np.percentile(slopes[area],[50,95,99]).tolist()}
    report={'status':'CANDIDATE_PENDING_INDEPENDENT_CHECK',
            'parent_constraints_sha256':sha(old),'candidate_sha256':sha(asc),
            'reference_sha256':sha(out/'reference.npz'),
            'native_baseline_sha256':'9625ecf593c9c17288942d98ccf06933081bbcaffb367bb307146aa338cf9b5b',
            'changed_vertices':int(data['changed'].sum()),'maximum_m':float(candidate.max()),
            'zones':stats,'changed_slope_max_deg':float(slopes[data['changed']].max()),
            'design':{'uplift_grade_limit':.60,'toe_curve_m':36,'smoothing_m':24},
            'limits':['Hydrology and road levels preserved; engineering of each route still pending.',
                      'Native import, navmesh and runtime not yet accepted.']}
    save(ev/'preparation.json',report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
