"""Whole-kit shape inventory from saved model centrelines and placed poses.
Cardinal heading share is a descriptive bin; it is never a PASS threshold.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import streambed_kit_v31 as K
from audit_stream_visibility_ev112 import route_metrics,wet_span

def heading_profile(lines):
    d=np.vstack([np.diff(p,axis=0) for p in lines]);length=np.linalg.norm(d,axis=1);d=d[length>1e-8];length=length[length>1e-8]
    if not len(length):raise ValueError('empty nonzero path coverage')
    heading=np.degrees(np.arctan2(d[:,1],d[:,0]))%180
    cardinal=np.minimum(heading%90,90-heading%90)
    hist,_=np.histogram(heading,bins=np.arange(0,181,10),weights=length)
    return dict(length_m=float(length.sum()),cardinal_within_5deg_length_share=float(length[cardinal<=5].sum()/length.sum()),
                heading_10deg_bins_length_m=hist.tolist())

def main():
    p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('pilot',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    src=a.build/'water-fix-b/kit/kit-records.json';records=json.loads(src.read_text());models=K.load_models()
    authored=json.loads((a.pilot/'author-report.json').read_text());replaced={s['site'] for s in authored['sites']};rows=[];all_lines=[]
    for site in sorted({r['site'] for r in records}):
        selected=sorted([r for r in records if r['site']==site and r['piece']!='stones'],key=lambda r:r['station'][0])
        lines=[]
        for r in selected:
            points=K.centreline_world(r,models,.5)
            keep=np.r_[True,np.linalg.norm(np.diff(points,axis=0),axis=1)>1e-8];lines.append(points[keep])
        if site in replaced:
            s=next(s for s in authored['sites'] if s['site']==site);z=np.load(a.pilot/(site+'-surfaces.npz'))
            axis=z['water'][:,[0,-1]].mean(1)[:,[0,2]];required,_=wet_span(axis,s['original_raw_endpoints']);lines=[axis[required]]
        if not lines:rows.append(dict(site=site,status='NO_CENTRELINE_OPEN'));continue
        metric=heading_profile(lines);all_lines.extend(lines)
        rows.append(dict(site=site,source='continuous_pilot' if site in replaced else 'saved_vanilla_model_centrelines',
                         pieces=len(lines),heading=metric,shape_max_within_piece_deg=max(route_metrics(q)['turn_max_deg'] for q in lines if len(q)>=3),
                         status='DIAGNOSTIC_NOT_VISUAL_ACCEPTANCE'))
    rows.sort(key=lambda r:-r.get('heading',{}).get('cardinal_within_5deg_length_share',0))
    report=dict(status='DIAGNOSTIC_NOT_VISUAL_ACCEPTANCE',sites=len(rows),global_heading=heading_profile(all_lines),rows=rows,
                inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (src,a.pilot/'author-report.json',Path(__file__),Path(K.__file__))},
                limitations=['Individual placed piece paths can overlap; summed length is not unique river length.',
                             'Junction tangent continuity and receiver connectivity remain separate.',
                             '5-degree and 10-degree bins are descriptive; no new aesthetic cutoff.',
                             'Unbuilt declared sites are outside this built-kit inventory and remain pending.'])
    a.output.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ('rows','inputs')},indent=2))

if __name__=='__main__':main()
