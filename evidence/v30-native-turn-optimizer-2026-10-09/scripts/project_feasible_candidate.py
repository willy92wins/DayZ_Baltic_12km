"""Single feasibility repair: clamp the unfinished solve along its source ray.

No extra optimizer iterations or changed weights. Enforces originally declared
native-face slope and conservative point-correspondence <=4.1 m constraints.
"""
import json
import numpy as np
from discover_native_turns import B,B10,B12,sha,positions


def main():
    source=B10/'measured-bank-bed-r2/terrain.npz';candidate=B/'candidate-native/terrain.npz'
    assert sha(candidate)=='b6ec4b4afed58de642d81143944e2ac49de923867ff7c0e1b143bf754176bae3'
    report=json.loads((B/'candidate-native-verification.json').read_text())
    assert report['status']=='FAIL_SOURCE_TERRAIN' and not report['gates']['slopes'] and not report['gates']['R2_distance']
    t=dict(np.load(source));u=np.load(candidate);h=t['heights'].astype(float);v=u['heights'].astype(float);out=h.copy();records={}
    for reach in ('R1','R2'):
        graph=json.loads((B/(reach+'-graph.json')).read_text());ids=np.load(B/(reach+'-constraints.npz'))['movable']
        delta=np.zeros_like(h);delta.ravel()[ids]=v.ravel()[ids]-h.ravel()[ids]
        points0=positions(h,graph['nodes']);points1=positions(h+delta,graph['nodes']);move=np.linalg.norm(points1-points0,axis=1)
        alpha=1.;bindings=[]
        for k in np.flatnonzero(move>4.1):
            node=graph['nodes'][k];ix=node['ids'];d=h.ravel()[ix]-node['water'];step=delta.ravel()[ix]
            t0=d[0]/(d[0]-d[1]);t1=(d[0]+step[0])/(d[0]-d[1]+step[0]-step[1])
            length=np.linalg.norm(np.array(node['xz'][1])-node['xz'][0]);target=t0+np.sign(t1-t0)*4.1/length
            limit=(target*(d[0]-d[1])-d[0])/(step[0]-target*(step[0]-step[1]))
            assert 0<=limit<=1
            alpha=min(alpha,float(limit));bindings.append(dict(kind='contour',node=int(k),limit=float(limit),old_displacement_m=float(move[k])))
        cells=set()
        for index in ids:
            r,c=divmod(int(index),2048);cells.update((rr,cc) for rr in (r-1,r) for cc in (c-1,c) if 0<=rr<2047 and 0<=cc<2047)
        for r,c in sorted(cells):
            a=r*2048+c;end=a+2049
            for tri,b in enumerate((a+1,a+2048)):
                vals=h.ravel()[[a,b,end]];dv=delta.ravel()[[a,b,end]];g=np.diff(vals);s=np.diff(dv)
                radius=max(float(g@g),(6*np.tan(np.deg2rad(35)))**2)
                if (g+s)@(g+s)<=radius:continue
                aa=float(s@s);bb=float(2*g@s);cc=float(g@g-radius)
                limit=(-bb+np.sqrt(bb*bb-4*aa*cc))/(2*aa)
                alpha=min(alpha,float(limit));bindings.append(dict(kind='slope',row=r,col=c,tri=tri,limit=float(limit)))
        if alpha<1:alpha*=1-1e-6  # float32 serialization margin, no widened gate.
        out+=alpha*delta
        records[reach]=dict(alpha=alpha,bindings=bindings,max_corresponding_contour_displacement_m=float(np.linalg.norm(positions(h+alpha*delta,graph['nodes'])-points0,axis=1).max()))
    folder=B/'candidate-feasible';folder.mkdir(exist_ok=False)
    t['heights']=out.astype(t['heights'].dtype);np.savez_compressed(folder/'terrain.npz',**t)
    result=dict(status='PROJECTED_ON_ORIGINAL_CONSTRAINTS_REQUIRES_CONSUMER',repro='verify_native_turns.py --candidate candidate-native',
                defect='Iteration-limited solve exported its last infeasible iterate; declared displacement gate was not constrained by the author.',
                repair='Analytic maximal ray fraction satisfying native slope discs and sufficient 4.1m point correspondence, from current source. No reoptimization.',
                original_candidate_sha256=sha(candidate),candidate_sha256=sha(folder/'terrain.npz'),reaches=records)
    (B/'feasibility-repair.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
