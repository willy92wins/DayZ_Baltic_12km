"""Check regional ASC against native baseline, frozen protections and mesh triangles."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/playtest'))
from verify_texture_grid_change import read
from prepare_regional_outline import sha, save, NATIVE, NATIVE_SHA


def triangle_slopes(h):
    a,b,c,d=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    return np.degrees(np.arctan(np.stack([np.hypot(b-a,d-b),np.hypot(d-c,c-a)])/6))


def verify(h,base,ref):
    changed=h!=base
    a,b,c,d=changed[:-1,:-1],changed[:-1,1:],changed[1:,:-1],changed[1:,1:]
    affected=np.stack([a|b|d,a|c|d])
    slopes=triangle_slopes(h)
    bad=affected&(slopes>35)
    where=np.argwhere(bad)
    zones={}
    for name in ['controls','water','reserve','wetlands','narva','spb','road_core']:
        zones[name]=int(np.count_nonzero(changed&ref[name]))
    report={'checks':{'shape':h.shape==(2048,2048),'finite':bool(np.isfinite(h).all()),
                      'no_lowering':bool(np.all(h>=base)),
                      'protections_unchanged':not any(zones.values()),
                      'new_relief_present':int(changed.sum())>500000 and float(h.max())>=70,
                      'changed_triangles_at_most35deg':len(where)==0,
                      'height_ceiling205m':float(h.max())<=205},
            'changed_vertices':int(changed.sum()),'changed_protected_vertices':zones,
            'changed_triangle_max_slope_deg':float(slopes[affected].max()) if np.any(affected) else 0,
            'triangles_over35deg':int(len(where)),
            'first_bad_triangles':where[:16].tolist()}
    report['pass']=all(report['checks'].values())
    return report


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if sha(NATIVE)!=NATIVE_SHA:
        raise ValueError('Native baseline drift')
    before=read(NATIVE)
    base=np.frombuffer(before['heights'],dtype='<f4').reshape(2048,2048)[::-1].copy()
    ref=np.load(ROOT/'tests/regional_outline_v1/reference.npz')
    with rasterio.open(args.candidate) as ds:
        h=ds.read(1)
        assert ds.shape==(2048,2048) and ds.res==(6,6) and ds.nodata==-9999
    report=verify(h,base,ref)
    negative_base=verify(base,base,ref)
    altered=h.copy()
    row,col=np.argwhere(ref['reserve'])[0]
    altered[row,col]+=2
    negative_reserve=verify(altered,base,ref)
    report['negative_controls']={'old_base_rejected':not negative_base['pass'],
                                'reserve_corruption_rejected':not negative_reserve['pass'],
                                'reserve_corruption_trigger':not negative_reserve['checks']['protections_unchanged']}
    report['status']='PASS_OFFLINE_GEOMETRY_ONLY' if report['pass'] and all(report['negative_controls'].values()) else 'FAIL'
    report['candidate_sha256']=sha(args.candidate)
    report['native_baseline_sha256']=NATIVE_SHA
    save(args.output,report)
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['status'].startswith('PASS') else 1)


if __name__=='__main__':
    main()
