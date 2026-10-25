from pathlib import Path
import sys,json,csv,hashlib,shutil
import numpy as np
from scipy.ndimage import binary_dilation,label,distance_transform_edt
B=Path(__file__).parent;R=B.parent;S=R/'v30-volkhov-stable-derivatives-20261009/candidate';OLD=R/'v30-strict-dry-floor-20261009'
sys.path[:0]=[str(R/'v30-surface-crease-audit-20261009'),str(R/'v30-native-hinge-finish-20261009')]
from audit_native_surface import incident_any,incident_all
from verify_hinges import face_normals,edges
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
t=dict(np.load(S/'terrain.npz'));h=t['heights'].astype(float);v=np.load(OLD/'candidate/terrain.npz')['heights'].astype(float);m=np.load(OLD/'constraints.npz');allowed=m['allowed'];target=m['target'];p=np.load(S/'plane.npy')
groups,n=label(binary_dilation(allowed,structure=np.ones((3,3)),iterations=2),structure=np.ones((3,3)));groups=groups*allowed
rows={i:dict(group=i,vertices=int((groups==i).sum()),targets=int((target&(groups==i)).sum()),metrics={},accepted=True,reasons=[]) for i in range(1,n+1)}
pmax=np.full(h.shape,-np.inf)
for dr,dc in [(0,0),(0,1),(1,0),(1,1)]:np.fmax(pmax[dr:dr+2047,dc:dc+2047],p,out=pmax[dr:dr+2047,dc:dc+2047])
dry=(h>=pmax)&(h>=.85);natural=dry&~t['reserve']&~t['platform'];distance=distance_transform_edt(dry)*6;domains={'bank':natural&(distance<=54),'interior':natural&(distance>54),'natural':natural}
offsets={'diagonal':[(0,0),(0,1),(1,0),(1,1)],'vertical':[(0,0),(0,1),(1,1),(1,2)],'horizontal':[(0,0),(1,0),(1,1),(2,1)]};buffers={}
for (kind,a),(_,b) in zip(edges(*face_normals(h)),edges(*face_normals(v))):
    labs=np.stack([groups[dr:dr+a.shape[0],dc:dc+a.shape[1]] for dr,dc in offsets[kind]])
    mx=labs.max(axis=0);mn=np.where(labs>0,labs,n+1).min(axis=0);assert np.all((mx==0)|(mx==mn)),'Two editable groups share a measured edge'
    masks={key:incident_all(mask,kind) for key,mask in domains.items()};masks['incident']=mx>0
    for gid in np.unique(mx[mx>0]):
        for key,mask in masks.items():
            use=(mx==gid)&mask
            if use.any():buffers.setdefault((int(gid),key),[[],[]]);buffers[(int(gid),key)][0].append(a[use]);buffers[(int(gid),key)][1].append(b[use])
for (gid,key),(left,right) in buffers.items():
    a,b=np.concatenate(left),np.concatenate(right)
    before=dict(mean_square=float(a@a/len(a)),p99=float(np.percentile(a,99)),over30=int((a>30).sum()))
    after=dict(mean_square=float(b@b/len(b)),p99=float(np.percentile(b,99)),over30=int((b>30).sum()))
    good=after['mean_square']<=before['mean_square']+1e-9 and after['p99']<=before['p99']+1e-5 and after['over30']<=before['over30']
    rows[gid]['metrics'][key]=dict(edges=len(a),before=before,after=after,pass_gate=good)
    if not good:rows[gid]['accepted']=False;rows[gid]['reasons'].append(key+'_angular_quality')
for gid,row in rows.items():
    if not row['targets']:row['accepted']=False;row['reasons'].append('no_floor_target')
accepted=[gid for gid,row in rows.items() if row['accepted']];mask=np.isin(groups,accepted);assert accepted
out=h.copy();out[mask]=v[mask];target_accept=target&mask
dest=B/'candidate';dest.mkdir(exist_ok=False);np.savez_compressed(dest/'terrain.npz',**(t|dict(heights=out.astype(np.float32))))
for name in ['plane.npy','visible-field.npy']:shutil.copyfile(S/name,dest/name)
np.savez_compressed(B/'constraints.npz',fixed=m['fixed'],allowed=mask,target=target_accept,water_support=m['water_support'],large_lake_banks=m['large_lake_banks'])
rr,cc=np.nonzero(out!=h);np.savez_compressed(B/'terrain-delta.npz',row=rr,col=cc,before=h[rr,cc].astype(np.float32),after=out[rr,cc].astype(np.float32))
with (B/'remaining-targets.csv').open('w',newline='') as stream:
    writer=csv.writer(stream);writer.writerow(['row','col','x','z','height','group','reasons'])
    for r,c in zip(*np.nonzero(target&~mask)):
        gid=int(groups[r,c]);writer.writerow([int(r),int(c),int(c)*6,12282-int(r)*6,float(h[r,c]),gid,','.join(rows[gid]['reasons'])])
report=dict(status='COMPOSED_REQUIRES_GLOBAL_CONSUMER',source_sha256=sha(S/'terrain.npz'),rejected_whole_candidate_sha256=sha(OLD/'candidate/terrain.npz'),terrain_sha256=sha(dest/'terrain.npz'),groups=len(rows),accepted_groups=len(accepted),accepted_targets=int(target_accept.sum()),remaining_targets=int((target&~mask).sum()),changed_vertices=len(rr),max_uplift_m=float((out-h).max()),measure_edges_independent=True,receipts=list(rows.values()),limits=['No new solver. Accepted vertices copied exactly from EV60; rejected groups equal source.','Only explicitly accepted floor targets claimed. Remaining targets persist for coupled shore work.'])
(B/'composition.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(OLD/'verify.py',B/'verify.py')
print(json.dumps({k:v for k,v in report.items() if k!='receipts'},indent=2))
