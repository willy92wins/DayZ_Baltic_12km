"""Actual saved river surfaces: shape diagnostics and centre-line visibility.

Uses MLOD triangles for water and bed heights. NPZ stations supply only the
declared route; nearest source-vertex agreement binds those stations to models.
No aesthetic threshold or receptor inference; unresolved branches stay OPEN.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),'C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/py3d']
import py3d
from prepare_visual_probe_v31 import height
from streambed_kit_v31 import tri_h
from stream_reference_v31 import recover,require_original_endpoints,PINS


def route_metrics(axis):
    axis=np.asarray(axis,float)
    if axis.ndim!=2 or axis.shape[1]!=2 or len(axis)<3 or not np.isfinite(axis).all():raise ValueError('finite Nx2 route required')
    d=np.diff(axis,axis=0);length=np.linalg.norm(d,axis=1)
    if (length<=1e-9).any():raise ValueError('duplicate route station')
    unit=d/length[:,None];turn=np.degrees(np.arccos(np.clip((unit[:-1]*unit[1:]).sum(1),-1,1)))
    curvature=turn/((length[:-1]+length[1:])/2)
    return dict(length_m=float(length.sum()),turn_max_deg=float(turn.max()),turn_p50_p90_p99=np.percentile(turn,[50,90,99]).tolist(),
                curvature_max_deg_per_m=float(curvature.max()),diagnostic_turns_over_45=int((turn>45).sum()))


def visibility(ground,bed,water):
    if water is None or bed is None:return False
    if not np.isfinite([ground,bed,water]).all():raise ValueError('nonfinite surface height')
    # Existing wet-centre contract, not a newly invented depth threshold.
    return bool(water-.25>ground+.1 and bed<water-.25)

def wet_span(axis,endpoints):
    """Frozen original endpoints bound the wet reach, not author wet_span.

    Geometry beyond these ends is the intentional dry blending apron. It is
    still inventoried but cannot be assigned a wet requirement by accident.
    """
    axis=np.asarray(axis,float);ends=np.asarray(endpoints,float)
    if ends.shape!=(2,2) or not np.isfinite(ends).all():raise ValueError('two finite original endpoints required')
    d=np.diff(axis,axis=0);sq=(d*d).sum(1);length=np.sqrt(sq);s=np.r_[0,np.cumsum(length)]
    if (sq<=1e-18).any():raise ValueError('duplicate route station')
    projected=[]
    for q in ends:
        t=np.clip(((q-axis[:-1])*d).sum(1)/sq,0,1);nearest=axis[:-1]+t[:,None]*d
        ix=int(np.argmin(np.linalg.norm(q-nearest,axis=1)));projected.append(float(s[ix]+t[ix]*length[ix]))
    lo,hi=sorted(projected)
    return (s>=lo-1e-6)&(s<=hi+1e-6),[lo,hi]


def main():
    p=argparse.ArgumentParser();p.add_argument('pilot',type=Path);p.add_argument('terrain',type=Path);p.add_argument('output',type=Path);p.add_argument('--build',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    author=json.loads((a.pilot/'author-report.json').read_text());H=np.load(a.terrain)['heights'];assert np.isfinite(H).all()
    original=recover(a.build,[s['site'] for s in author['sites']])
    reports=[];inputs={}
    for site in author['sites']:
        sid=site['site'];z=np.load(a.pilot/(sid+'-surfaces.npz'));wt=[];bt=[]
        require_original_endpoints(site['original_raw_endpoints'],original[sid])
        for inst in author['instances']:
            if inst['site']!=sid:continue
            src=a.pilot/'source'/inst['model'].replace('\\','/');digest=hashlib.sha256(src.read_bytes()).hexdigest()
            assert digest==inst['sha256'];inputs[str(src)]=digest
            with src.open('rb') as f:f.read(12);lod=py3d.LOD(f)
            points=np.array([v.coords for v in lod.points])+inst['origin']
            for face in lod.faces:
                ids=[v.point_index for v in face.vertices];assert len(ids)==3
                (wt if 'water_streambed.rvmat' in face.material else bt).append(points[ids])
        wt,bt=np.array(wt),np.array(bt);assert len(wt) and len(bt)
        source_error=float(cKDTree(wt.reshape(-1,3)).query(z['water'].reshape(-1,3))[0].max());assert source_error<.001
        axis=z['water'][:,[0,-1]].mean(axis=1)[:,[0,2]];width=np.linalg.norm(z['water'][:,0][:,[0,2]]-z['water'][:,-1][:,[0,2]],axis=1)
        samples=[];tapers=[];required,span=wet_span(axis,site['original_raw_endpoints'])
        points=[('station',i,q,bool(required[i])) for i,q in enumerate(axis)]+[('original_endpoint',i,np.asarray(q),True) for i,q in enumerate(site['original_raw_endpoints'])]
        for kind,i,q,wet_required in points:
            g=float(tri_h(H,*q));b=height(bt,q);w=height(wt,q)
            if not visibility(g,b,w):
                (samples if wet_required else tapers).append(dict(kind=kind,index=i,x=float(q[0]),z=float(q[1]),ground=g,bed=b,water_visual=w))
        reports.append(dict(site=sid,status='CENTRE_VISIBILITY_PASS' if not samples else 'FAIL',samples=len(points),failures=samples,
                            wet_required_stations=int(required.sum()),original_endpoint_span_m=span,dry_apron_stations=int((~required).sum()),dry_apron_nonwet=tapers,
                            diagnostics=route_metrics(axis[required]),water_width_min_max_m=[float(width[required].min()),float(width[required].max())],
                            saved_grid_to_mlod_error_m=source_error,receiver_connectivity='OPEN_NOT_INFERRED'))
    for src in (a.terrain,a.pilot/'author-report.json',Path(__file__)):inputs[str(src)]=hashlib.sha256(src.read_bytes()).hexdigest()
    report=dict(status='CENTRE_VISIBILITY_PASS' if reports and all(r['status']=='CENTRE_VISIBILITY_PASS' for r in reports) else 'FAIL',sites=reports,inputs=inputs,prekit_reference_sha256=PINS,
                limitations=['Only two declared pilot routes. Shape metrics are diagnostic, not visual acceptance.',
                             'Centre samples do not prove every continuous surface point or all lateral branches.',
                             'No receiver connection, runtime water/collision or missing reach is accepted by point coverage.'])
    a.output.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='inputs'},indent=2))
    if report['status']=='FAIL':raise SystemExit(1)

if __name__=='__main__':main()
