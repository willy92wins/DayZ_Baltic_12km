"""Exhaustive read-only pond contour survey; no terrain authoring."""
from pathlib import Path
import csv,json,sys,time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from discover_native_turns import B,B9,B10,B12,sha,graph,positions

start=time.monotonic();source=B/'candidate-feasible/terrain.npz'
assert sha(source)=='cff6d175da46a0080bd761c327babf9c0ef4c53434744ceec9241bc9cc28c82c'
h=np.load(source)['heights'].astype(float);f=np.load(B12/'preserved-field.npy');p=np.load(B10/'frozen-field-reference/plane.npy')
valid=np.isfinite(p);rr,cc=np.nonzero(valid)
d=np.c_[h[rr,cc],h[rr,cc+1],h[rr+1,cc],h[rr+1,cc+1]]-f[rr,cc]
mixed=(d.min(1)<=0)&(d.max(1)>0);cells=list(zip(rr[mixed],cc[mixed]))
g=graph(h,f,cells);points=positions(h,g['nodes'])
fixed=np.load(B9/'candidate-a/masks.npz')['fixed'];fixed|=np.load(B9/'candidate-a/masks.npz')['corridor']
fixed|=np.load(B/'R1-constraints.npz')['controls']
rows=[];observations=[];shorts=0;length_total=0.
for chain_id,chain in enumerate(g['chains']):
    pts=points[chain];dist=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))];length=float(dist[-1]);length_total+=length
    if length<=24:shorts+=1;continue
    s=np.arange(0,length,2);sample=np.c_[np.interp(s,dist,pts[:,0]),np.interp(s,dist,pts[:,1])]
    a=sample[3:-3]-sample[:-6];b=sample[6:]-sample[3:-3]
    angle=np.degrees(np.arctan2(abs(a[:,0]*b[:,1]-a[:,1]*b[:,0]),np.sum(a*b,axis=1)))
    support=np.unique(np.array([g['nodes'][i]['ids'] for i in chain]).ravel());fixed_count=int(fixed.ravel()[support].sum())
    row=dict(chain=chain_id,closed=chain[0]==chain[-1],length_m=length,samples=len(angle),p90_deg=float(np.percentile(angle,90)),
             max_deg=float(angle.max()),over30_share=float(np.mean(angle>30)),support=len(support),fixed=fixed_count,
             x0=float(pts[:,0].min()),z0=float(pts[:,1].min()),x1=float(pts[:,0].max()),z1=float(pts[:,1].max()))
    rows.append(row)
    for j in np.flatnonzero(angle>30):observations.append(dict(chain=chain_id,x=float(sample[j+3,0]),z=float(sample[j+3,1]),angle_deg=float(angle[j])))
with (B/'whole-map-contour-chains.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
with (B/'whole-map-contour-angles.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=['chain','x','z','angle_deg']);writer.writeheader();writer.writerows(observations)
fig,ax=plt.subplots(figsize=(10,10),layout='constrained')
ax.scatter(points[:,0],points[:,1],s=.12,c='#bdd7d0',label='Contorno de agua')
if observations:
    xy=np.array([(r['x'],r['z'],r['angle_deg']) for r in observations]);plot=ax.scatter(xy[:,0],xy[:,1],c=xy[:,2],s=2,vmin=30,vmax=120,cmap='magma');fig.colorbar(plot,ax=ax,label='Giro a escala de 6 m (grados)')
ax.set(xlim=(0,12282),ylim=(0,12282),aspect='equal',xlabel='X (m)',ylabel='Z (m)',title='Censo completo de quiebros en orillas de estanques y ríos')
fig.savefig(B/'whole-map-contour-survey.png',dpi=180);plt.close(fig)
report=dict(status='GLOBAL_CONTOUR_INVENTORY_NOT_ACCEPTANCE',terrain_sha256=sha(source),all_pond_cells=int(valid.sum()),mixed_cells=len(cells),
            contour_nodes=len(g['nodes']),segments=len(g['segments']),chains_total=len(g['chains']),chains_over24m=len(rows),short_chains=shorts,
            branch_nodes=len(g['branch_nodes']),exact_zero_support=len(g['exact_zero_support']),total_contour_length_m=length_total,
            samples=sum(r['samples'] for r in rows),samples_over30=len(observations),
            long_chains_with_over30=sum(r['over30_share']>0 for r in rows),
            entirely_fixed_long_chains=sum(r['fixed']==r['support'] for r in rows),
            largest_mean_turn_chains=sorted(rows,key=lambda r:r['p90_deg'],reverse=True)[:20],seconds=time.monotonic()-start,
            limits=['All finite frozen pond cells inspected; ocean shore and terrain-only creases are separate domains.',
                    'More than 30 degrees marks candidates for geometric inspection, not automatic defects at legitimate corners or small islands.',
                    'No field/terrain changes. Branch and exact-zero nodes need explicit treatment before any global optimizer.'])
(B/'whole-map-contour-survey.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='largest_mean_turn_chains'},indent=2),flush=True)
