"""Check each local reach's bank rings before authoring a rigid water translation."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.ndimage import distance_transform_edt
B=Path(__file__).parent;R=B.parent;S=R/'v30-strict-dry-composition-20261009/candidate'
sys.path.insert(0,str(R/'v30-isolated-basin-repair-20261009'))
from author import corners,bounds,slope
t=dict(np.load(S/'terrain.npz'));h=t['heights'];p=np.load(S/'plane.npy');row=next(q for q in json.loads((B/'scope.json').read_text())['groups'] if q['group']==349)
objects={q['id']:q for q in json.loads((R/'v30-low-water-components-20261009/compiled-instance-bounds.json').read_text())['objects']};support=np.load(R/'v30-low-water-components-20261009/physical-component-labels.npz')['support_domains'];ids=set();corecells=np.zeros(p.shape,bool)
for oid in row['objects']:
    r0,r1,c0,c1=bounds(objects[oid],1);ids.update(np.unique(support[r0:r1,c0:c1]).tolist());r0,r1,c0,c1=bounds(objects[oid]);corecells[r0:r1,c0:c1]=True
ids.discard(0);cells=np.isin(support,list(ids));corecells|=cells;core=corners(corecells);assert int(core.sum())==row['core_vertices'];rr,cc=np.nonzero(core);r0,r1=max(0,rr.min()-12),min(2048,rr.max()+13);c0,c1=max(0,cc.min()-12),min(2048,cc.max()+13);sl=np.s_[r0:r1,c0:c1];fixed=t['reserve']|t['platform']|t['beach']|corners(np.isfinite(p)&~cells)
distance=distance_transform_edt(~core[sl],sampling=6);s=np.clip(1-distance/36,0,1);weight=s*s*s*(10+s*(-15+6*s));weight[fixed[sl]]=0;shift=row['proposed_shift_m'];trial=(h[sl].astype(float)+shift*weight).astype(np.float32);allwater=corners(np.isfinite(p))
reports=[];bad=[]
for r,c in zip(*np.nonzero(cells)):
    # Median dry surroundings local to each 6m plane cell, avoiding the global maximum of a flowing profile.
    ar,br=max(r0,r-10),min(r1,r+12);ac,bc=max(c0,c-10),min(c1,c+12);rows,cols=np.mgrid[ar:br,ac:bc];dist=np.hypot(rows-r-.5,cols-c-.5)*6;natural=(t['cls'][ar:br,ac:bc]==0)&~allwater[ar:br,ac:bc]&~fixed[ar:br,ac:bc]
    for lo,hi in [(12,36),(36,60)]:
        ring=natural&(dist>lo)&(dist<=hi)
        if not ring.any():continue
        old=float(p[r,c]-np.median(h[ar:br,ac:bc][ring]));new=float(p[r,c]+shift-np.median(trial[ar-r0:br-r0,ac-c0:bc-c0][ring]));ok=new<=max(.3,old)+1e-6
        rec=dict(row=int(r),col=int(c),inner=lo,outer=hi,vertices=int(ring.sum()),perched_before=old,perched_after=new,pass_gate=ok);reports.append(rec)
        if not ok:bad.append(rec)
gates=dict(isolated_scope=row['eligible'],fixed_core=not(core&fixed).any(),no_navigable_or_sea_or_narva_metadata=not(core&np.isin(t['cls'],[1,3,6])).any(),floor=float(trial[core[sl]].min())>=1,perched_policy=not bad,no_new_steep_faces=max(float(np.max(a-np.maximum(b,35),initial=0)) for a,b in zip(slope(trial),slope(h[sl])))<=1e-4)
np.savez_compressed(B/'volkhov-policy-domain.npz',core=core,cells=cells,box=np.array([r0,r1,c0,c1]),weight=weight,trial=trial,fixed=fixed)
report=dict(status='PASS_LOCAL_REACH_POLICY_NOT_AUTHORED' if all(gates.values()) else 'FAIL_LOCAL_REACH_POLICY_NO_AUTHORITY_TO_PROMOTE',group=349,shift_m=shift,gates={k:bool(v) for k,v in gates.items()},source_classes=sorted(map(int,np.unique(t['cls'][core]))),minimum_bed_after=float(trial[core[sl]].min()),rings=len(reports),failures=bad,all_rings=reports,limits=['One deterministic proposed shift from the bed>=1.001 rule; no level changed yet.','Local rings appropriate to varying river levels, unlike one maximum level for an entire river.'])
(B/'volkhov-policy.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['failures','all_rings']},indent=2));print('Failing rings',len(bad));print(json.dumps(bad[:5],indent=2))
