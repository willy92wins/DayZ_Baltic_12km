"""Accept the completed engine replay and reject the reproduced regressions."""
from pathlib import Path
import copy
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/playtest'))
from read_water_temporal_v30 import read_series,read_order,controls

ref=json.loads((OUT/'wave-fixed-reference.json').read_text())
text=(OUT/'wave-fixed-runtime.log').read_text(encoding='utf-8-sig')
result=read_series(ref,text)
order=read_order(ref,text,(OUT/'wave-fixed-order.log').read_text(encoding='utf-8-sig'))
actual={p['id']:p for p in result['results']}
before=json.loads((OUT/'wave-verification.json').read_text())
baseline={p['id']:p for p in before['results']}
checks=dict(both_weather_phases_pass=result['gate']['status']=='PASS_SHALLOW_DEPTH_BOTH_PHASES',
            declared_controls_pass=result['control_gate']['status']=='PASS_REFERENCE_CONTROLS',
            all17_points_302_samples=result['point_count']==17 and result['samples_per_point']==302,
            fixed_points_positive=all(actual[i]['pond_true']==302 and actual[i]['positive_depth_samples']==302 for i in (765,1176)),
            unchanged_presence_controls=all(actual[i]['pond_true']==p['pond_true'] and actual[i]['sea_true']==p['sea_true'] for i,p in baseline.items()),
            unchanged_dry_stays_dry=all(actual[i]['positive_depth_samples']==0 for i,p in baseline.items() if p['positive_depth_samples']==0))
# A baseline negative control retains current eligibility but uses its actual
# ground: it must fail the two sites even in the storm that did reach weather.
oldref=copy.deepcopy(ref)
for p in oldref['points']:p['expected_ground_m']=p['before_repair_ground_m']
old=read_series(oldref,(OUT/'wave-runtime.log').read_text(encoding='utf-8-sig'))
storm=next(p for p in old['gate']['phases'] if p['name']=='storm')
checks['baseline_storm_reproduces_two_failures']=storm['weather_reached'] and {p['id'] for p in storm['failing']}=={765,1176}
negative=[]
for name,field,value in [('pond_lost',6,'false'),('bed_exposed',9,'-0.01'),('storm_weather_missing',15,'0.1')]:
    lines=text.splitlines()
    for j,line in enumerate(lines):
        f=line.split(';')
        if len(f)==17 and f[0]=='T' and int(f[1])==151 and int(f[2])==(13 if name=='storm_weather_missing' else 765):
            f[field]=value;lines[j]=';'.join(f);break
    else:raise AssertionError('No mutation site')
    rejected=read_series(ref,'\n'.join(lines)+'\n')['gate']['status']!='PASS_SHALLOW_DEPTH_BOTH_PHASES'
    assert rejected,name
    negative.append(name)
checks['real_series_negative_controls_rejected']=len(negative)==3
paths=['wave-reference.json','wave-runtime.log','wave-fixed-reference.json','wave-fixed-runtime.log','wave-fixed-order.log']
report=dict(status='PASS_CURRENT_SHALLOW_WAVE_REPAIR' if all(checks.values()) else 'FAIL',checks=checks,
            current=result,order=order,baseline_storm=storm,negative_controls=negative,reader_controls=controls(),
            files={p:hashlib.sha256((OUT/p).read_bytes()).hexdigest() for p in paths},
            limits=['Two repaired sites and five unchanged current shallow sites; no map-wide visual closure.',
                    'Historical points that became dry before this fix are retained as dry controls, never silently removed.',
                    'BALTIC-012 fairway proposal is not part of this deployed package.'])
(OUT/'wave-fixed-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status=report['status'],checks=checks,minima={i:actual[i]['ranges']['depth_bed']['min'] for i in (765,1176)}),indent=1))
raise SystemExit(0 if all(checks.values()) else 1)
