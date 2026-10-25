"""Compare measured client motion with native heading and requested relative angle."""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np

def vec(s):return np.array([float(x) for x in s[1:-1].split(',')])
def wrap(v):return (v+180)%360-180
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',required=True,type=Path);ap.add_argument('--log',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();assert not a.out.exists()
    ref=json.loads(a.reference.read_text(encoding='utf-8'));goals={c['case']+1:np.array(c['goal']) for c in ref['cases']};rows=[];samples=[]
    for line in a.log.read_text(encoding='utf-8-sig').splitlines():
        f=line.split(';')
        if len(f)==12 and f[0]=='D':rows.append(dict(t=float(f[1]),command=int(f[3]),p=vec(f[4]),native_heading=float(f[5])*180/math.pi,angle=float(f[11])))
    for u,v in zip(rows,rows[1:]):
        if u['command'] not in goals or u['command']!=v['command']:continue
        delta=v['p']-u['p'];step=np.linalg.norm(delta[[0,2]]);wanted=goals[u['command']]-u['p']
        if step<.05 or np.linalg.norm(wanted[[0,2]])<3 or not .19<v['t']-u['t']<.5 or abs(u['native_heading'])<10:continue
        actual=math.degrees(math.atan2(delta[0],delta[2]));desired=math.degrees(math.atan2(wanted[0],wanted[2]))
        samples.append(dict(command=u['command'],native_heading=u['native_heading'],motion_vs_desired=abs(wrap(actual-desired)),motion_vs_angle_minus_heading=abs(wrap(actual-u['angle']+u['native_heading'])),motion_vs_angle_plus_heading=abs(wrap(actual-u['angle']-u['native_heading']))))
    result=dict(status='MEASURED_KINEMATICS_NOT_ENGINE_INTERNAL_CAUSALITY',samples=len(samples),source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [a.reference,a.log]},commands=sorted(set(s['command'] for s in samples)),metrics={})
    for k in ['motion_vs_desired','motion_vs_angle_minus_heading','motion_vs_angle_plus_heading']:
        values=[s[k] for s in samples];result['metrics'][k]={str(q):float(np.quantile(values,q)) if values else None for q in [.5,.9,.99,1.]}
    result['limits']='Movement samples with nonzero measured native heading. Association of input convention and trajectory, not an AI/Navmesh internal root cause.'
    a.out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))

if __name__=='__main__':main()
