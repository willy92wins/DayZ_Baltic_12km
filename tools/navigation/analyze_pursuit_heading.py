"""Compare two heading-sign predictions with recorded client displacement."""
from pathlib import Path
import hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
wrap=lambda a:(a+180)%360-180

def main():
    result=[]
    for name in ('continuous-pursuit-v1','continuous-pursuit-v2','bridge-human-control-v1'):
        p=ROOT/'evidence/overnight-2026-10-01'/name/'runtime-complete/client-input.log'
        rows=[l.split(';') for l in p.read_text(encoding='utf-8-sig').splitlines() if l.startswith('C;')]
        vec=lambda s:np.array([float(x) for x in s.strip('<>').split(',')])
        records=[]
        for a,b in zip(rows,rows[1:]):
            if a[2]!=b[2] or int(a[2])==0 or float(a[5])!=1:continue
            dt=float(b[1])-float(a[1]);pos=vec(a[3]);goal=vec(a[4]);delta=vec(b[3])-pos
            if not .15<=dt<=.5 or np.linalg.norm(delta[[0,2]])<.12:continue
            observed=np.degrees(np.arctan2(delta[0],delta[2]))
            desired=np.degrees(np.arctan2(goal[0]-pos[0],goal[2]-pos[2]))
            angle=float(a[6]);implied_heading=wrap(desired-angle)
            if abs(implied_heading)<10:continue
            records.append(dict(t=float(a[1]),command=int(a[2]),implied_heading=float(implied_heading),observed=float(observed),
                plus_error=float(abs(wrap(observed-(angle+implied_heading)))),
                minus_error=float(abs(wrap(observed-(angle-implied_heading))))))
        row=dict(run=name,source_sha256=sha(p),samples_with_nonzero_heading=len(records),records=records)
        for key in ('plus_error','minus_error'):
            row[key+'_degrees_p50_p90_max']=np.quantile([x[key] for x in records],[.5,.9,1]).tolist() if records else None
        result.append(row)
    report=dict(status='DESCRIPTIVE_KINEMATIC_SIGN_DISCRIMINATOR_NOT_CAUSAL_ENGINE_PROOF',
        method='Input formula gives implied heading=desired-angle. Compare actual later displacement with angle+heading and angle-heading; nonzero heading only.',
        limits=['Heading reconstructed from producer formula, not previously logged native getter.','No original PASS/FAIL changed.','Rates use uniform client records, not interleaved event/physics timestamps.'],cases=result)
    out=ROOT/'evidence/foundation-followup-2026-10-01/pursuit-heading-analysis.json'
    assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{k:v for k,v in r.items() if k!='records'} for r in result],indent=2))

if __name__=='__main__':main()
