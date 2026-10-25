"""Classify final native road grades with the previously frozen wet/Narva exclusions."""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.ndimage import distance_transform_edt
from waterway_common import sample
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    roadpath=ROOT/'tests/regional_foundation_roads_v6/reference.npz'
    heightpath=ROOT/'tests/regional_foundation_combined_v10/reference.npz'
    chainpath=ROOT/'evidence/regional-foundation-v1/road-grade-chains-v6.json'
    out=ROOT/'evidence/foundation-followup-2026-10-01/road-scope.json'
    assert not out.exists(),'Preserve evidence'
    roads=np.load(roadpath);data=np.load(heightpath);xy=roads['xy'];h=data['candidate']
    wet=data['wet']|data['ocean'];distance=distance_transform_edt(~wet)*6
    chains=json.loads(chainpath.read_text(encoding='utf-8'))['chains']
    centre=np.array([2417.1428225906,6889.8850822322])
    totals={'eligible_length_m':0.,'excluded_length_m':0.,'eligible_grade_failures':0,'excluded_grade_failures':0}
    candidates=[];failures=[]
    for number,indices in enumerate(chains):
        p=xy[indices]
        if len(p)<4:continue
        station=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        ds=np.diff(station)
        if np.any(ds<1e-8):raise ValueError('Zero length edge')
        rr=np.clip(np.rint((12282-p[:,1])/6).astype(int),0,2047);cc=np.clip(np.rint(p[:,0]/6).astype(int),0,2047)
        eligible=(distance[rr,cc]>48)&(np.linalg.norm(p-centre,axis=1)>470)
        y=sample(h,p[:,0]+200000,p[:,1]);grade=np.abs(np.diff(y)/ds)
        pairs=eligible[:-1]&eligible[1:];bad=grade>.065
        for key,mask in [('eligible',pairs),('excluded',~pairs)]:
            totals[key+'_length_m']+=float(ds[mask].sum())
            totals[key+'_grade_failures']+=int((bad&mask).sum())
        for j in np.flatnonzero(bad):
            failures.append(dict(chain=number,index=int(j),xz=p[j].tolist(),grade=float(grade[j]),eligible=bool(pairs[j]),water_distance_m=float(distance[rr[j],cc[j]])))
        valid=eligible&(station>18)&(station<station[-1]-18)
        padded=np.r_[False,valid,False];starts=np.flatnonzero(np.diff(padded.astype(int))==1);ends=np.flatnonzero(np.diff(padded.astype(int))==-1)
        for lo,hi in zip(starts,ends):
            length=station[hi-1]-station[lo]
            if length<600:continue
            q=p[lo:hi];delta=np.gradient(q,axis=0);normal=np.column_stack([-delta[:,1],delta[:,0]])/np.linalg.norm(delta,axis=1)[:,None]
            edges=np.array([sample(h,q[:,0]+normal[:,0]*v+200000,q[:,1]+normal[:,1]*v) for v in [-4,0,4]])
            localds=ds[lo:hi-1];heights=edges[1]
            chord=abs(heights[1:-1]-(heights[:-2]*localds[1:]+heights[2:]*localds[:-1])/(localds[:-1]+localds[1:]))
            candidates.append(dict(chain=number,lo=int(lo),hi=int(hi),length_m=float(length),centre_xz=q.mean(axis=0).tolist(),maximum_grade=float(grade[lo:hi-1].max()),maximum_cross_height_m=float(np.ptp(edges,axis=0).max()),maximum_chord_m=float(chord.max()),elevation_range_m=[float(heights.min()),float(heights.max())]))
    report=dict(status='SCOPE_AUDIT_NOT_DRIVING_ACCEPTANCE',inputs={str(p):sha(p) for p in [roadpath,heightpath,chainpath]},totals=totals,candidates=sorted(candidates,key=lambda x:-x['length_m']),worst_grades=sorted(failures,key=lambda x:-x['grade'])[:60],limits=['Same >48m wet distance and >470m Narva exclusions as verify_combined_foundation.py.','Excluded water approaches require future bridge/corridor design; do not fill navigable channels.','Eligible geometry is not a physical driving PASS.'])
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(totals=totals,candidates=report['candidates'])))

if __name__=='__main__':main()
