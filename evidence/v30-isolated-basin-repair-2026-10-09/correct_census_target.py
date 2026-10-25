from pathlib import Path
import json
import numpy as np
B=Path(__file__).parent;path=B/'risk-census/census.json';r=json.loads(path.read_text());q=r['target'];h=np.load(B/'candidate/terrain.npz')['heights'];p=np.load(B/'candidate/plane.npy');f=np.load(B/'candidate/visible-field.npy');x,z=q['x'],q['z'];row,col=int((12282-z)//6),int(x//6);fc,fr=x/6-col,(12282-z)/6-row
w=np.array([1-fc,fc-fr,0,fr]) if fc>=fr else np.array([1-fr,0,fr-fc,fc]);ground=float(w@np.array([h[row,col],h[row,col+1],h[row+1,col],h[row+1,col+1]]));visible=float(w@f[row,col]) if np.isfinite(p[row,col]) else .85;values=[1.79999-ground,ground-float(np.fmax(p[row,col],.85)),ground-visible]
assert abs(ground-q['height_m'])<1e-12
(B/'risk-census/census-before-point-flag-correction.json').write_bytes(path.read_bytes())
q['inside_elevation_risk_band']=bool(np.all(np.array(values)>0));q['positive_constraints']=values
r['instrument_correction']='Point membership now tests all three halfplanes at the point itself; an intersected triangle does not imply its whole area is inside the band. Aggregate areas/index unchanged.'
path.write_text(json.dumps(r,indent=2)+'\n')
for script in [B/'prepare_census.py',B/'risk-census/census_low_dry.py']:
    s=script.read_text();s=s.replace("inside_elevation_risk_band=bool(idx>=0 and component_by_face[idx,face]>=0)","inside_elevation_risk_band=bool(idx>=0 and np.all(constraints[idx][:,CORNERS[face]]@weights>0))")
    script.write_text(s)
print(json.dumps(q,indent=2))
