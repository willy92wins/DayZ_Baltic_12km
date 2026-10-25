"""Verify every node of a real TB export against the imported candidate."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np, rasterio
ap=argparse.ArgumentParser()
for name in ['source','candidate','native','out']:
    ap.add_argument('--'+name,type=Path,required=True)
args=ap.parse_args()
def read(p):
    with rasterio.open(p) as src: return src.read(1).astype('float64'),src.transform
original,ot=read(args.source); expected,et=read(args.candidate); actual,at=read(args.native)
assert original.shape==expected.shape==actual.shape
delta=abs(actual-expected)
result={'status':'PASS' if et==at and np.isfinite(actual).all() and delta.max()<=.00501 else 'FAIL',
 'samples':int(actual.size),'matching_grid':bool(et==at),'tolerance_m':.00501,
 'tolerance_reason':'TB ASCII rounds to centimetres',
 'max_error_m':float(delta.max()),'samples_over_tolerance':int((delta>.00501).sum()),
 'changed_candidate_nodes':int((expected!=original).sum()),
 'negative_control_original_max_error_m':float(abs(actual-original).max()),
 'hashes':{k:hashlib.sha256(getattr(args,k).read_bytes()).hexdigest() for k in ['source','candidate','native']},
 'limits':'Height serialization only; not native registration, water, player or vehicle collision.'}
args.out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['status']=='PASS' else 1)
