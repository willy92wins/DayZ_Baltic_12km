"""Negative controls from the measured v1 engine log, not terrain synthesis."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root=Path(__file__).resolve().parents[2]
ev=root/'evidence/navigation/calibration-v1'
raw=(ev/'boat-calibration-complete.log').read_text(encoding='utf-8-sig')
lines=raw.splitlines()
header=next(line.split(';') for line in lines if line.startswith('COLUMNS;'))
drift=[]
for line in lines:
    row=line.split(';')
    if row[0]=='B':
        row[header.index('x')]=str(2000+float(row[header.index('t')]))
        row[header.index('horizontal_speed')]='1'
    drift.append(';'.join(row))
cases={
    'measured_neutral_control':(raw,0,True),
    'missing_END':('\n'.join(lines[:-1])+'\n',1,False),
    'injected_drift_without_propulsion':('\n'.join(drift)+'\n',0,True),
}
results=[]
with tempfile.TemporaryDirectory(prefix='boat-calibration-') as tmp:
    for name,(content,exit_code,complete) in cases.items():
        src=Path(tmp)/(name+'.log'); out=Path(tmp)/(name+'.json')
        src.write_text(content,encoding='utf-8')
        proc=subprocess.run([sys.executable,'-X','utf8',str(root/'tools/navigation/analyze_boat_calibration.py'),
            '--log',str(src),'--out',str(out)],capture_output=True,text=True,encoding='utf-8')
        if proc.returncode!=exit_code or not out.exists():
            raise AssertionError((name,proc.returncode,proc.stderr))
        data=json.loads(out.read_text())
        assert data['status']=='INCONCLUSIVE' and data['checks']['complete']==complete
        assert data['powered_motion_samples']==0
        if name=='injected_drift_without_propulsion': assert data['distance_m']>10
        results.append({'case':name,'exit_code':proc.returncode,'status':data['status'],
                        'distance_m':data['distance_m'],'powered_motion_samples':data['powered_motion_samples']})
(ev/'verifier-tests.json').write_text(json.dumps({'status':'PASS_NEGATIVE_CONTROLS','cases':results,
    'limits':'No positive engine propulsion result exists yet; does not prove calibration.'},indent=2)+'\n')
print(json.dumps(results,indent=2))
