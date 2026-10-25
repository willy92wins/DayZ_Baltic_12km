from pathlib import Path
import json,re,csv,hashlib
import numpy as np
B=Path(__file__).parent
a=json.loads((B/'analysis.json').read_text());s=np.load(B/'scores.npz');dry=s['dry'];cohort=s['cohort'];thr=max(r['threshold'] for r in a['rows']);m=[cohort&(s[r['phase']]>thr) for r in a['rows']]
joint=dict(A_B_overlap=int((m[0]&m[1]).sum()),B_Areturn_overlap=int((m[1]&m[2]).sum()),all_three_overlap=int((m[0]&m[1]&m[2]).sum()),B_retains_effect=True)
rtA=json.loads(Path('E:/DayZ-Baltic-Build/v30-native-projection-ab-20261009/runtime-A.json').read_text())
rtB=json.loads((B/'runtime-B.json').read_text());rtR=json.loads((B/'runtime-Areturn.json').read_text())
assert rtA['camera']['camera']['matrix']==rtB['camera']['camera']['matrix']==rtR['camera']['camera']['matrix']
logs=[]
for phase in ['B','Areturn']:
    rows=[line.split(';') for line in (B/('sea-'+phase+'.log')).read_text().splitlines() if line.startswith('SEA;')]
    vals=np.array([[float(x) for x in row[1:]] for row in rows]);assert len(vals)>30
    logs.append(dict(phase=phase,samples=len(vals),sea_range=[float(vals[:,2].min()),float(vals[:,2].max())],wind_range=[float(vals[:,6].min()),float(vals[:,6].max())]))
    logs[-1]['strict_20ms_identity']=bool(np.max(abs(vals[:,6]-20))<.001)
assert joint['all_three_overlap']>100
report=dict(status='B_REPRODUCES_EFFECT_WITHOUT_PONDS_STRICT_WIND_MATCH_FAILED',joint=joint,identical_camera_matrices=True,logs=logs,source_A='EV48 stable 6-frame reference; same package/camera/projection, weather command but not exact wind readback',limits=['Initial strict 20m/s readback assertion failed in B; retained as a failed comparison dimension.','The B counterexample shows the effect without the four instances. Counts do not establish an isolated effect-size comparison across A/B/A.','Not proof of the specific ocean shader mechanism.','The omitted designed ponds must be restored, never removed as a production fix.','Unchanged baseline dry mask, common control pixels and threshold are used; actual pond interiors excluded.'])
(B/'discrimination.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
rows=list(csv.DictReader(open('E:/DayZ-Baltic-Build/v30-low-water-components-20261009/physical-components.csv')))
low=[r for r in rows if float(r['area_m2'])>=1 and r['has_flowing']=='False' and float(r['below_sea_crest_m2'])>0]
print('LOW_STANDING',len(low),'ENGINEERING',sum(r['engineering']=='True' for r in low),'NARVA',sum(r['narva']=='True' for r in low))
print(json.dumps([{k:r[k] for k in ['component','area_m2','minimum_bed_m','classes','engineering','narva']} for r in sorted(low,key=lambda r:float(r['area_m2']),reverse=True)[:12]],indent=2))
