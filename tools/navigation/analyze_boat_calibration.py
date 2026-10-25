"""Report measured transmission per phase without declaring river navigation."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from waterway_common import sha

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--log',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args()
lines=args.log.read_text(encoding='utf-8-sig').splitlines()
header=[row for row in csv.reader(lines,delimiter=';') if row[0]=='COLUMNS']
if len(header)!=1: raise ValueError('Missing or ambiguous schema')
rows=[]
for row in csv.reader(lines,delimiter=';'):
    if row[0]!='B': continue
    if len(row)!=len(header[0]): raise ValueError('Bad row width')
    values={}
    for name,raw in zip(header[0][1:],row[1:]):
        if name in {'engine','active','authority','proxy'}:
            if raw not in {'true','false','0','1'}: raise ValueError('Invalid boolean')
            values[name]=raw in {'true','1'}
        else:
            values[name]=float(raw)
            if not np.isfinite(values[name]): raise ValueError('Nonfinite sample')
    rows.append(values)
if not rows: raise ValueError('No motion records')
complete=bool(lines[-1].startswith('END;'))
end=lines[-1][4:] if complete else 'INCOMPLETE'
ground=[line.split(';') for line in lines if line.startswith('G;')]
expected={(x,z) for x in range(1880,2121,24) for z in range(11080,11321,24)}
actual={(float(g[1]),float(g[2])) for g in ground}
water_valid=len(ground)==len(expected) and actual==expected and all(float(g[3])<=-3 and g[4] in {'true','1'} for g in ground)
phases=[]
for phase in sorted({int(row['phase']) for row in rows}):
    part=[r for r in rows if r['phase']==phase]
    start,endrow=part[0],part[-1]
    delta=np.array([endrow['x']-start['x'],endrow['z']-start['z']])
    phases.append({'phase':phase,'samples':len(part),
        'time_s':[start['t'],endrow['t']],
        'net_horizontal_displacement_m':float(np.linalg.norm(delta)),
        'max_horizontal_speed_m_s':max(r['horizontal_speed'] for r in part),
        'rpm_min_median_max':[min(r['rpm'] for r in part),float(np.median([r['rpm'] for r in part])),max(r['rpm'] for r in part)],
        'clutch_values':sorted({r['clutch'] for r in part}),
        'gear_values':sorted({r['gear'] for r in part}),
        'future_gear_values':sorted({r['future_gear'] for r in part}),
        'neutral_values':sorted({r['neutral'] for r in part}),
        'prop_omega_min_max':[min(r['prop_omega'] for r in part),max(r['prop_omega'] for r in part)],
        'throttle_min_max':[min(r['throttle'] for r in part),max(r['throttle'] for r in part)]})
positions=np.array([[r['x'],r['z']] for r in rows])
distance=float(np.linalg.norm(positions[-1]-positions[0]))
health=[r['health'] for r in rows]
checks={'correct_header':lines[0] in {'BALTIC_BOAT_CALIBRATION_V1','BALTIC_BOAT_INPUT_V2'},
        'complete':complete,'water_reference':water_valid,
        'strictly_increasing_time':all(b['t']>a['t'] for a,b in zip(rows,rows[1:])),
        'no_damage':min(health)>=health[0]-1,
        'authority_and_no_proxy':all(r['authority'] and not r['proxy'] for r in rows)}
if lines[0]=='BALTIC_BOAT_INPUT_V2':
    checks['input_callbacks_measured']=all(b['input_calls']>a['input_calls'] for a,b in zip(rows,rows[1:]))
measured=all(checks.values())
powered=[r['engine'] and r['rpm']>800 and r['gear']!=r['neutral'] and abs(r['prop_omega'])>0.01 and r['horizontal_speed']>0.5 for r in rows]
streak=longest=0
for item in powered:
    streak=streak+1 if item else 0
    longest=max(longest,streak)
movement=distance>10 and longest>=10 and end in {'CALIBRATION_COMPLETE','DISTANCE_SAFETY_STOP'}
report={'status':'PASS_CALIBRATION_MOVEMENT_ONLY' if measured and movement else 'INCONCLUSIVE',
    'checks':checks,'log_sha256':sha(args.log),'end_reason':end,'samples':len(rows),
    'distance_m':distance,'health_first_min_last':[health[0],min(health),health[-1]],
    'powered_motion_samples':sum(powered),'longest_powered_motion_streak':longest,
    'active_samples':sum(r['active'] for r in rows),'phases':phases,
    'clutch_readback':'UNUSABLE_UNVALIDATED_NATIVE_INT; do not infer actual clutch engagement',
    'limits':['Sequential phases, not isolated causal A/B/A/B.',
              'Empty boat in open sea, not river/bridge/crew validation.',
              'Maximum displacement is sampled; safety stop can occur between rows.']}
args.out.parent.mkdir(parents=True,exist_ok=True)
args.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
raise SystemExit(0 if measured else 1)
