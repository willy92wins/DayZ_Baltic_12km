"""Measure P11 on the pilot approaches without claiming a vehicle test."""
import json
import argparse
from pathlib import Path
import numpy as np
import rasterio
from waterway_common import ROOT, FIT, sample, sha


parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--end-distance',type=float,default=280)
parser.add_argument('--out',type=Path,default=ROOT/'evidence/navigation/approach-smoothness.json')
args=parser.parse_args()
if args.end_distance < 280 or args.end_distance > 400:
    raise ValueError('Audit extent outside pilot neighborhood')
folder=ROOT/'tests/narva_navigation_v3'
design=json.loads((folder/'design.json').read_text())
asc=folder/'narva_navigation_v1.asc'
if sha(asc)!=design['candidate_sha256']: raise ValueError('Candidate drift')
with rasterio.open(asc) as ds: h=ds.read(1)
fit=json.loads(FIT.read_text())
c=np.array(fit['bridge_centre_tb']);u=np.array(fit['axis_east_unit']);v=np.array([u[1],-u[0]])
records=[]
for side in (-1,1):
    station=np.arange(37.5,args.end_distance+.001,.25)
    offsets=np.arange(-4,4.001,.25)
    pp=c[:,None,None]+u[:,None,None]*(side*station[None,:])+v[:,None,None]*offsets[:,None]
    y=sample(h,pp[0],pp[1])
    grade=np.diff(y,axis=1)/.25
    # Average grade over6m, then compare adjacent non-overlapping6m spans.
    grade6=(y[:,24:]-y[:,:-24])/6
    jump=np.abs(grade6[:,24:]-grade6[:,:-24])
    index=np.unravel_index(np.argmax(jump),jump.shape)
    across=(y[-1]-y[0])/8
    cross_plane=y[0][None,:]+(offsets[:,None]+4)*across[None,:]
    # Vertical deviation from the straight chord within each6m window.
    deviations=[]
    for start in range(0,y.shape[1]-24,24):
        chord=y[:,start,None]+(y[:,start+24]-y[:,start])[:,None]*np.linspace(0,1,25)[None,:]
        deviations.append(float(np.max(abs(y[:,start:start+25]-chord))))
    grade_index=np.unravel_index(np.argmax(abs(grade)),grade.shape)
    records.append({'side':side,'length_m':float(station[-1]-station[0]),'road_width_m':8,
        'max_longitudinal_grade_percent':float(abs(grade).max()*100),
        'worst_grade_station_m':float(station[grade_index[1]]*side),
        'max_adjacent_6m_grade_change_percentage_points':float(jump.max()*100),
        'worst_grade_change_station_m':float(station[index[1]+24]*side),
        'worst_grade_change_lateral_offset_m':float(offsets[index[0]]),
        'max_crossfall_percent':float(abs(across).max()*100),
        'max_cross_section_nonplanarity_m':float(abs(y-cross_plane).max()),
        'max_6m_chord_deviation_m':max(deviations),
        'bridge_joint_terrain_deviation_from_9m':float(abs(y[:,0]-9).max())})
report={'status':'MEASURED_ONLY_VEHICLE_ACCEPTANCE_PENDING','candidate_sha256':sha(asc),
    'surface':'native-grid triangle interpolation; intended8m road corridor, no road pieces yet',
    'sampling_m':.25,'end_distance_m':args.end_distance,'approaches':records,
    'limits':['Gradient alone does not prove comfort or traction.',
              'No vehicle physics test, collision-joint test or driving speed accepted.',
              'Metrics describe this pilot only; regional road profiles remain to design.']}
args.out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
