"""Independent failure injections for the scoped native-water/terrain integration."""
from pathlib import Path
import json,sys
import numpy as np,shapely
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
scope={};code=(B/'verify_contour_valley.py').read_text()
exec(code[:code.index('cut=before.boundary')],scope)
h,v,fixed,wet=scope['h'],scope['v'],scope['fixed'],scope['wet']
before=scope['before'];audit=scope['component_audit'];E=scope['E']
def inv(a):
    return dict(protected_exact=not bool(((a!=h)&fixed).any()),floor=not bool((wet&(a<1.-1e-6)&~(scope['oldwet']&(h<1))).any()),wet_not_exposed=not bool((wet&np.isfinite(scope['pmin'])&(a>scope['pmin']-.02+1e-5)&~scope['oldexposed']).any()))
positive=inv(v);neg={}
q=v.copy();p=tuple(np.argwhere(fixed)[0]);q[p]+=1.;neg['changed_fixed_support']=not inv(q)['protected_exact']
q=v.copy();p=tuple(np.argwhere(wet&(h>=1))[0]);q[p]=.5;neg['new_floor_below_one_metre']=not inv(q)['floor']
q=v.copy();p=tuple(np.argwhere(wet&np.isfinite(scope['pmin'])&~scope['oldexposed'])[0]);q[p]=scope['pmin'][p]+.2;neg['wet_vertex_exposed']=not inv(q)['wet_not_exposed']
cut=before.difference(shapely.box(7100,5758,7500,5760))
neg['missing_water_strip_splits_channel']=not audit(before,cut)['no_split_or_missing']
parts=list(getattr(before,'geoms',[before]));small=min(parts,key=lambda p:p.area)
missing=before.difference(small)
neg['missing_small_water_body']=not audit(before,missing)['no_split_or_missing']
shrunk=shapely.union_all([p if p!=small else p.buffer(-2) for p in parts])
neg['shrunk_small_body']=not audit(before,shrunk)['area_preserved']
region=(scope['x']>7170)&(scope['x']<7470)&(scope['z']>5630)&(scope['z']<5920)&~scope['oldwet']
original_curvature=scope['curvature'](h,region)
def enough_improvement(a):return 1.-scope['curvature'](a,region)/original_curvature>=.15
positive['required_R3_improvement']=enough_improvement(v)
neg['unchanged_input_fails_R3_improvement']=not enough_improvement(h.copy())
# Consumer samples are frozen outside authoring, checked with native interpolation.
refs=[scope['W']/'evidence/v30-bug-recheck-2026-10-08/wave-fixed-reference.json']
controls=[]
for ref in refs:
 for p in json.loads(ref.read_text())['points']:
  a=float(scope['tri_sample'](h,p['x'],p['z']));b=float(scope['tri_sample'](v,p['x'],p['z']))
  controls.append(dict(id=p['id'],before=a,after=b,error=abs(a-b)))
positive['historical_controls_exact']=all(p['error']<1e-6 for p in controls)
pond=[]
for p in json.loads((scope['W']/'evidence/v30-water-visual-fix-2026-10-08/stitch-probe-reference.json').read_text())['points']:
 level=p.get('actual_pond_level_m')
 if level is None:continue
 old=level-float(scope['tri_sample'](h,p['x'],p['z']));new=level-float(scope['tri_sample'](v,p['x'],p['z']))
 pond.append(dict(id=p['id'],old_depth=old,new_depth=new))
positive['no_exposed_previously_wet_pond_control']=all(p['new_depth']>=min(.101,p['old_depth'])-1e-6 for p in pond if p['old_depth']>.02)
out=dict(status='PASS' if all(positive.values()) and all(neg.values()) else 'FAIL',positive=positive,negative_controls=neg,historical_controls=controls,pond_controls=pond,limits=['The unchanged-input negative checks the required strict curvature improvement, not whether input data are valid.','Native polygon strip removal models missing coverage; staged WRP/PBO object bytes are checked separately. No engine acceptance.','The local polygon domains contain no >=1 m2 island holes; island preservation there is vacuous. Global island geometry is not accepted by this test.'])
(E/f'negative-controls-{scope["label"]}.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='historical_controls'},indent=2))
