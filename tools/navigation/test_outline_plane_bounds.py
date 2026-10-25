"""Compare the corner bound against full polygon clipping on real cases."""
import json
import numpy as np
from shapely.geometry import shape
from verify_outline_smoothing import ROOT,EV,minimum_margin,exact_reference_minimum_margin
OUT=ROOT/'tests/regional_outline_smoothing_v30';out=OUT/'plane-bound-controls.json';assert not out.exists()
current=np.load(OUT/'reference.npz')['candidate'];old=np.load(ROOT/'tests/regional_outline_smoothing_v25/reference.npz')['candidate'];features=json.loads((EV/'protected-islands-game.json').read_text())['features'];levels=json.loads((EV/'island-support-v7.json').read_text())['islands'];records=[]
for i in (41,49,164,220):
    g=shape(features[i]['geometry']);target=levels[i]['adjacent_water_ceiling_m']
    for name,h in [('V30',current),('rejected_V25',old)]:
        fast,n=minimum_margin(h,g,target);exact,m=exact_reference_minimum_margin(h,g,target);records.append(dict(island=i,case=name,bounded_margin_m=fast,exact_clipped_margin_m=exact,classification_equal=(fast>=-1e-5)==(exact>=-1e-5),lower_bound_valid=fast<=exact+1e-6))
assert any(r['exact_clipped_margin_m']< -1e-5 for r in records)
report=dict(status='PASS_CONSERVATIVE_PLANE_BOUND_CONTROLS' if all(r['classification_equal'] and r['lower_bound_valid'] for r in records) else 'FAIL',cases=records,scope='Four real island polygons in accepted-candidate and rejected-height contexts; negative margins must still reject.')
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['status'].startswith('PASS')
