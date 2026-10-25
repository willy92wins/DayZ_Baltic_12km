"""Multi-scale relief inventory, never an automatic aesthetic PASS.

Measures symmetric chord residuals in four directions at 6/12/24/48m lags.
A plane is identically zero. Ridges/terraces are visible without being strict
local peaks or exceeding a 20-degree dihedral. Protected candidates stay OPEN.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation
sys.path.insert(0,str(Path(__file__).resolve().parent))
import despike_v31 as D


def scale_fields(H,lag):
    H=np.asarray(H,float)
    if H.ndim!=2 or not np.isfinite(H).all() or not isinstance(lag,int) or lag<1 or min(H.shape)<=2*lag:
        raise ValueError('finite 2D grid larger than twice a positive integer lag required')
    center=H[lag:-lag,lag:-lag];residual=np.zeros_like(center);ring=[]
    for dr,dc in ((1,0),(0,1),(1,1),(1,-1)):
        pair=[]
        for sign in (-1,1):
            r=lag+sign*dr*lag;c=lag+sign*dc*lag
            pair.append(H[r:r+center.shape[0],c:c+center.shape[1]])
        residual=np.maximum(residual,abs(center-(pair[0]+pair[1])/2));ring.extend(pair)
    peak=np.maximum(0,center-np.maximum.reduce(ring));pit=np.maximum(0,np.minimum.reduce(ring)-center)
    return dict(chord_residual_m=residual,ring_peak_m=peak,ring_pit_m=pit)


def main():
    p=argparse.ArgumentParser();p.add_argument('terrain',type=Path);p.add_argument('footprint',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    z=np.load(a.terrain);H=z['heights'].astype(float);fp=np.load(a.footprint);assert H.shape==(2048,2048)
    masks={k:z[k].astype(bool) for k in ('reserve','platform','narva','v31_dam','v31_kit','v31_bridge_cut','v31_bridge_fill','v31_shore_ramp','v31_causeway','v31_continuous_pilot') if k in z.files}
    rr,cc=np.mgrid[:2048,:2048];masks['protected_01545_60m']=np.hypot(cc*6-10397.4,12282-rr*6-9421.9)<=60
    masks['pond_corners']=D.env_vertex_plane(fp['plane'])[0]
    masks['kit_guard_12m']=binary_dilation(masks.get('v31_kit',np.zeros(H.shape,bool)),iterations=2)
    protected=np.logical_or.reduce(list(masks.values()));masks['outside_listed_domains']=~protected;masks['whole_map']=np.ones(H.shape,bool)
    # All native vertices are inventoried. Wet/support vertices are separately
    # attributable, not silently passed as visible land or removed from counts.
    masks['native_sea_below_075']=H<.75
    result={}
    for lag in (1,2,4,8):
        fields=scale_fields(H,lag);rows={}
        for name,m in masks.items():
            mask=m[lag:-lag,lag:-lag];count=int(mask.sum());metrics={}
            for metric,field in fields.items():
                vals=field[mask]
                metrics[metric]=None if not count else dict(max=float(vals.max()),p50_p90_p99=np.percentile(vals,[50,90,99]).tolist(),
                    diagnostic_above_m={str(t):int((vals>t).sum()) for t in (.03,.3,.5,1,2)})
            ranked=np.where(mask,fields['chord_residual_m'],-np.inf).ravel();n=min(12,count)
            best=np.argpartition(ranked,-n)[-n:] if n else []
            worst=[]
            for flat in sorted(best,key=lambda i:-ranked[i]):
                r,c=np.unravel_index(flat,mask.shape);r+=lag;c+=lag
                worst.append(dict(x=int(c*6),z=int(12282-r*6),height=float(H[r,c]),chord_residual_m=float(ranked[flat])))
            rows[name]=dict(vertices=count,metrics=metrics,worst=worst,status='OPEN_DIAGNOSTIC')
        result[str(lag*6)]=rows
    pk,pt=D.prominence(H)
    native={name:dict(peak_over_030=int(((pk>.3)&m).sum()),pit_over_030=int(((pt>.3)&m).sum()),
                      peak_max=float(pk[m].max()) if m.any() else None,pit_max=float(pt[m].max()) if m.any() else None) for name,m in masks.items()}
    report=dict(status='DIAGNOSTIC_PENDING_VISUAL_CALIBRATION',schema='ev112-relief-multiscale-v1',lags_m=result,native_small_shape_prominence=native,
                inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a.terrain,a.footprint,Path(__file__),Path(D.__file__))},
                limitations=['No aesthetic cutoff is inferred from road tolerances or 20-degree bins.',
                             'Domains overlap. Borders excluded by each lag are not measured at that lag.',
                             'Native supports under pilot water/bed are not the visible model surface.',
                             'Protected candidates remain open; this inventory grants no edit permission.'])
    a.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(dict(status=report['status'],native=native['whole_map'],scales={k:v['whole_map']['metrics'] for k,v in result.items()}),indent=2))

if __name__=='__main__':main()
