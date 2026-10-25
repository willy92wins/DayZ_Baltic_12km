"""Trace V28 contradictions and source-water overlap with protected land."""
from pathlib import Path
import json
import numpy as np
from scipy.sparse import load_npz
from shapely.geometry import shape
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2];F=ROOT/'tests/regional_outline_smoothing_v28';EV=ROOT/'evidence/regional-foundation-v1'
A=load_npz(F/'constraints.npz');d=np.load(F/'variables.npz');ix=d['variables'];rhs=d['rhs'];build=json.loads((F/'build.json').read_text());ref=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');h=ref['candidate'].ravel()[ix].astype(float);wet=(ref['wet']|ref['ocean']).ravel()[ix];island=ref['island_support_conservative'].ravel()[ix];lo=np.where(wet,h-6,np.maximum(h-6,1.4));lo[island]=np.maximum(lo[island],h[island]);hi=h+6;bad=[];gaps=[]
for start in range(0,len(rhs),250000):
    B=A[start:start+250000];q=B.maximum(0)@lo+B.minimum(0)@hi-rhs[start:start+B.shape[0]];j=np.flatnonzero(q>1e-7);bad.extend((start+j).tolist());gaps.extend(q[j].tolist())
nd=build['category_counts']['dry_plane'];nl=build['category_counts']['lake_core'];records=[]
for i,gap in zip(bad,gaps):
    row=A.getrow(i)
    if i<nd:continue
    records.append(dict(row=i,kind='lake_core' if i<nd+nl else 'slope',minimum_violation=gap,vertices=[dict(xz=[int(ix[k]%2048*6),int(12282-ix[k]//2048*6)],base=float(h[k]),lower=float(lo[k]),upper=float(hi[k]),coefficient=float(v),island=bool(island[k]),wet=bool(wet[k])) for k,v in zip(row.indices,row.data) if abs(v)>1e-8]))
land=unary_union([shape(f['geometry']) for f in json.loads((EV/'protected-islands-game.json').read_text())['features']]);overlap=[]
for f in json.loads((EV/'water-surfaces-contour-v2.geojson').read_text())['features']:
    g=shape(f['geometry']);a=g.intersection(land).area
    if a>1e-6:overlap.append(dict(body=f['properties']['body'],overlap_protected_land_m2=a))
report=dict(status='V28_BOUND_DIAGNOSTIC',individually_impossible=len(bad),dry=sum(i<nd for i in bad),other=len(records),examples=records[:20],source_water_land_overlap=overlap)
(F/'bound-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='source_water_land_overlap'},indent=2));print('Water bodies overlapping protected land:',len(overlap),'area_m2',sum(r['overlap_protected_land_m2'] for r in overlap))
