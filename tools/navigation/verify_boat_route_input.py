"""Independent spatial/transmission checks of the OnInput Narva route log."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from shapely.geometry import shape, Point, LineString
from waterway_common import ROOT, FIT, sha

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--log',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
geometry_path=a.out.with_name(a.out.stem+'-geometry.json')
proc=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/navigation/verify_boat_probe.py'),
                     '--log',str(a.log),'--out',str(geometry_path)],capture_output=True)
if not geometry_path.exists(): raise RuntimeError(proc.stderr.decode(errors='replace'))
geometry=json.loads(geometry_path.read_text())
lines=a.log.read_text(encoding='utf-8-sig').splitlines()
rows=[r.split(';') for r in lines if r.startswith('B;')]
if not rows or any(len(r)!=23 for r in rows): raise ValueError('Missing or bad motion schema')
num=np.array([[float(v) if i!=9 else float(v=='true') for i,v in enumerate(r) if i>0] for r in rows])
if not np.isfinite(num).all(): raise ValueError('Nonfinite sample')
positions=num[:,[1,3]]
design=json.loads((ROOT/'tests/narva_navigation_v3/design.json').read_text())
axis=shape(design['river_axis_tb'])
route=LineString([(axis.interpolate(s).x-200000,axis.interpolate(s).y) for s in range(55,176,10)])
distance=np.array([route.distance(Point(pos)) for pos in positions])
fit=json.loads(FIT.read_text())
center=np.array(fit['bridge_centre_tb'])-np.array([200000,0])
u=np.array(fit['axis_east_unit']); normal=np.array([u[1],-u[0]])
signed=(positions-center)@normal
along=(positions-center)@u
dt=np.diff(num[:,0]); steps=np.linalg.norm(np.diff(positions,axis=0),axis=1)
powered=(num[:,8]==1)&(num[:,15]>800)&(num[:,9]!=num[:,17])&(abs(num[:,16])>.01)&(num[:,5]>.5)
streak=longest=0
for item in powered:
    streak=streak+1 if item else 0
    longest=max(longest,streak)
near=abs(signed)<5
end=lines[-1][4:] if lines[-1].startswith('END;') else None
checks={
    'header':lines[0]=='BALTIC_BOAT_ROUTE_INPUT_V1',
    'engine_geometry':geometry['geometry_status']=='PASS_SAMPLED_CHANNEL_AND_DECKS',
    'route_end_marker':end=='OUTWARD_ROUTE_REACHED_EMPTY_BOAT_ONLY',
    'increasing_time':bool((dt>0).all()),
    'continuous_samples':bool((dt<=.75).all() and (steps<=2).all()),
    'no_health_loss':bool(num[:,6].min()>=num[0,6]-1),
    'inside_6m_route_corridor':bool(distance.max()<=6.02),
    'engine_route_distance_agrees':bool(abs(distance-num[:,19]).max()<=.025),
    'first_last_route_points':bool(np.linalg.norm(positions[0]-route.coords[0])<1 and np.linalg.norm(positions[-1]-route.coords[-1])<=6),
    'both_sides_of_bridge':bool(signed.min() < -10 and signed.max() > 10),
    'samples_under_central_span':bool(near.any() and abs(along[near]).max()<6.2),
    'powered_motion':longest>=10,
    'input_callbacks_executed':bool(num[-1,18]>100),
}
report={'status':'PASS_EMPTY_BOAT_LOCAL_OUTWARD' if all(checks.values()) else 'INCONCLUSIVE_OR_FAIL',
    'checks':checks,'log_sha256':sha(a.log),'end_reason':end,'samples':len(rows),
    'horizontal_net_m':float(np.linalg.norm(positions[-1]-positions[0])),
    'max_horizontal_step_m':float(steps.max()) if len(steps) else None,
    'max_distance_from_route_m':float(distance.max()),
    'max_route_distance_readback_error_m':float(abs(distance-num[:,19]).max()),
    'bridge_signed_position_min_max_m':[float(signed.min()),float(signed.max())],
    'max_along_bridge_offset_when_under_m':float(abs(along[near]).max()) if near.any() else None,
    'health_first_min_last':[float(num[0,6]),float(num[:,6].min()),float(num[-1,6])],
    'longest_powered_motion_streak':longest,
    'limits':['Empty boat; no seated crew, return journey or medium vessel.','Native TB persistence and new navmesh remain pending.','Local 120m route only; not regional river navigation.','Steering sign/controller tested only by this bounded route.']}
a.out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
