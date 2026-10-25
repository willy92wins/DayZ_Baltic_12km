"""Independent dense native-triangle consumer for a localized Narva crossing."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio
from shapely.geometry import LineString
from waterway_common import sample

ROOT=Path(__file__).resolve().parents[2]


def audit(folder, report_path):
    design=json.loads((folder/'solve.json').read_text())
    old=np.load(ROOT/'tests/regional_foundation_combined_v9/reference.npz')
    base=old['candidate'];data=np.load(folder/'reference.npz');h=data['candidate']
    asc=folder/'baltic_regional_foundation_v10.asc'
    asc_sha=hashlib.sha256(asc.read_bytes()).hexdigest()
    with rasterio.open(asc) as ds: persisted=ds.read(1)
    protected=old['wet']|old['ocean']|old['fairway_support']|old['island_support_conservative']
    checks={'finite':bool(np.isfinite(h).all()),'asc_matches':np.array_equal(h,persisted),
            'candidate_sha':asc_sha==design['candidate_sha256'],
            'water_and_island_vertices_exact':np.array_equal(h[protected],base[protected]),
            'other_reference_arrays_exact':all(np.array_equal(old[k],data[k],equal_nan=True) for k in old.files if k not in ('candidate','changed'))}
    delta=np.load(folder/'delta-from-v9.npz');changed=h!=base
    allowed=np.zeros(h.shape,bool);allowed[delta['row'],delta['col']]=True
    checks['delta_exact']=bool(np.array_equal(changed,allowed) and np.array_equal(base[allowed],delta['before']) and np.array_equal(h[allowed],delta['after']))
    f=json.loads((ROOT/'evidence/narva/evidence/narva-fit.json').read_text());c=np.array(f['bridge_centre_tb'])-[200000,0]
    rr,cc=np.where(changed)
    checks['localized']=bool(np.all(abs(cc*6-c[0])<680)&np.all(abs(12282-rr*6-c[1])<240))
    a,b,ccv,d=h[:-1,:-1],h[:-1,1:],h[1:,:-1],h[1:,1:]
    slope=np.maximum(np.degrees(np.arctan(np.hypot(b-a,d-b)/6)),np.degrees(np.arctan(np.hypot(d-ccv,ccv-a)/6)))
    affected=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]
    checks['affected_slope_below_35_01']=bool(np.all(slope[affected]<=35.01))
    roads=[]
    for route in design['routes']:
        line=LineString(route['coordinates'])
        # Freeze every quarter metre, plus endpoint; neither optimization stations
        # nor fitted heights are read by this consumer.
        station=np.r_[np.arange(0,line.length,.25),line.length]
        p=np.array([line.interpolate(float(s)).coords[0] for s in station])
        lo=np.maximum(station-.05,0);hi=np.minimum(station+.05,line.length)
        before=np.array([line.interpolate(float(s)).coords[0] for s in lo]);after=np.array([line.interpolate(float(s)).coords[0] for s in hi])
        tangent=after-before;tangent/=np.linalg.norm(tangent,axis=1)[:,None]
        normal=np.column_stack([-tangent[:,1],tangent[:,0]])
        offsets=np.linspace(-4,4,33)
        xy=p[None,:,:]+offsets[:,None,None]*normal[None,:,:]
        y=sample(h,xy[:,:,0]+200000,xy[:,:,1]);ds=np.diff(station)
        grade=np.diff(y,axis=1)/ds
        cross=np.ptp(y,axis=0)
        # Six-metre sliding chords, every quarter metre, not only disjoint windows.
        chords=[]
        for k in range(1,24):
            if y.shape[1]<=24:break
            weight=(station[k:-24+k]-station[:-24])/(station[24:]-station[:-24])
            expected=y[:,:-24]*(1-weight)+y[:,24:]*weight
            chords.append(np.abs(y[:,k:-24+k]-expected))
        chord=float(np.max(chords)) if chords else 0
        grade6=(y[:,24:]-y[:,:-24])/(station[24:]-station[:-24])
        jump=float(np.max(abs(grade6[:,24:]-grade6[:,:-24])))
        r={'side':route['side'],'samples':int(y.size),'length_m':line.length,
           'max_longitudinal_grade':float(abs(grade).max()),'max_cross_height_m':float(cross.max()),
           'max_sliding_6m_chord_m':chord,'max_adjacent_6m_grade_change':jump,
           'joint_max_error_m':float(abs(y[:,0]-11).max())}
        r['pass']=bool(r['max_longitudinal_grade']<=.065 and r['max_cross_height_m']<=.03 and chord<=.03 and r['joint_max_error_m']<=.01)
        roads.append(r)
    checks['smooth_approaches']=all(r['pass'] for r in roads)
    report={'status':'PASS_LOCAL_OFFLINE_GEOMETRY' if all(checks.values()) else 'FAIL',
            'checks':checks,'candidate_sha256':asc_sha,'changed_vertices':int(changed.sum()),
            'maximum_affected_slope_degrees':float(slope[affected].max()),'approaches':roads,
            'limits':['Regional consumer still required.','No native import, physics, road pieces, wave maximum or navmesh accepted.','West approach terminates in reserved terrain; western road and base mapping are not designed here.']}
    if report_path.exists():raise ValueError('Preserve prior verification')
    report_path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return all(checks.values())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raise SystemExit(0 if audit(a.candidate,a.out) else 1)
