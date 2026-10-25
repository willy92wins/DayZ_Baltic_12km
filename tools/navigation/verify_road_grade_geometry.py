"""Audit actual native triangles on the road design, not just graph profile values."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2]
EV=ROOT/'evidence/regional-foundation-v1'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version',choices=('v1','v2','v3','v4','v5','v6'),default='v1')
args=parser.parse_args()
data=np.load(ROOT/f'tests/regional_foundation_roads_{args.version}/reference.npz')
chains=json.loads((EV/f'road-grade-chains-{args.version}.json').read_text())['chains']
xy=data['xy'];h=data['candidate']
water=np.load(ROOT/'tests/regional_outline_v3/reference.npz')['water']
wet_distance=distance_transform_edt(~water)*6
fit=json.loads((ROOT/'evidence/narva/evidence/narva-fit.json').read_text())
centre=np.array(fit['bridge_centre_tb'])-[200000,0]
stats=[]
for number,indices in enumerate(chains):
    p=xy[indices]
    if len(p)<4:continue
    delta=np.gradient(p,axis=0)
    norms=np.linalg.norm(delta,axis=1)
    if np.any(norms<1e-8):continue
    normal=np.column_stack([-delta[:,1],delta[:,0]])/norms[:,None]
    c=np.clip(np.rint(p[:,0]/6).astype(int),0,2047)
    r=np.clip(np.rint((12282-p[:,1])/6).astype(int),0,2047)
    valid=(wet_distance[r,c]>48)&(np.linalg.norm(p-centre,axis=1)>470)
    # Exclude the first/last 18m from the interior gate; junctions need their own consumer.
    station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    valid&=(station>18)&(station<station[-1]-18)
    elevations=[]
    for offset in (-4,0,4):
        q=p+normal*offset
        elevations.append(sample(h,q[:,0]+200000,q[:,1]))
    elev=np.array(elevations)
    cross=elev.max(axis=0)-elev.min(axis=0)
    ds=np.diff(station);grades=np.diff(elev[1])/ds
    pairs=valid[:-1]&valid[1:]
    triplets=valid[:-2]&valid[1:-1]&valid[2:]
    curvature=np.abs(np.diff(grades))/((ds[:-1]+ds[1:])/2)
    chord=np.abs(elev[1,1:-1]-(elev[1,:-2]*ds[1:]+elev[1,2:]*ds[:-1])/(ds[:-1]+ds[1:]))
    if not valid.any():continue
    stats.append({'chain':number,'valid_samples':int(valid.sum()),
                  'max_transverse_height_difference_m':float(cross[valid].max()),
                  'max_grade':float(np.abs(grades[pairs]).max()) if pairs.any() else None,
                  'max_vertical_curvature_per_m':float(curvature[triplets].max()) if triplets.any() else None,
                  'max_6m_chord_deviation_m':float(chord[triplets].max()) if triplets.any() else None,
                  'rough_samples':int(((cross>.03)&valid).sum()),
                  'grade_failures':int(((np.abs(grades)>.065)&pairs).sum()),
                  'chord_failures':int(((chord>.03)&triplets).sum())})
report={'status':'PASS_INTERIORS_ONLY' if all(s['rough_samples']==s['grade_failures']==s['chord_failures']==0 for s in stats) else 'FAIL_INTERIOR_GEOMETRY',
        'independent_consumer':'6m native NW-SE triangles, road centre and +/-4m edges; no sampled design elevations used as terrain output.',
        'evaluated_chains':len(stats),'samples':sum(s['valid_samples'] for s in stats),
        'rough_samples':sum(s['rough_samples'] for s in stats),'grade_failures':sum(s['grade_failures'] for s in stats),
        'chord_failures':sum(s['chord_failures'] for s in stats),'chains':stats,
        'limits':['Junctions, water approaches and preserved Narva transition excluded and still require validation.','No physical vehicle or native editor acceptance.']}
(EV/f'road-grade-geometry-{args.version}.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='chains'},indent=2))
raise SystemExit(0 if report['status'].startswith('PASS_') else 1)
