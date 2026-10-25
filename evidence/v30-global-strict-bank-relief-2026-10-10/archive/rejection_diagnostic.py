"""Diagnostic only: never an acceptance consumer or an engine image."""
from pathlib import Path
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).parent
REPORT=ROOT/'review-independent/ev87-review.json'
report=json.loads(REPORT.read_text())
assert report['status']=='FAIL_EV87_GLOBAL_CONSUMER'
candidate=ROOT/'candidate-terrain.npz'
assert hashlib.sha256(candidate.read_bytes()).hexdigest()=='a7146c27a634d3ee59bc4c2763d71050da3172724c4f2620a17fce0775fcf020'
base=np.load(ROOT.parent/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')['heights']
height=np.load(candidate)['heights']
info=report['information']
summary={'status':report['status'],'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
         'false_gates':[k for k,v in report['gates'].items() if not v],
         'sectors_false':[x for x in info['sectors'] if not x['nonworse']],
         'coverage':{k:{n:v for n,v in d.items() if n!='cells'} for k,d in info['surface_coverage']['by_surface'].items()}}
rows=[x for x in info['patch_geometry'] if x['state']=='accepted']
rows.sort(key=lambda x:x['focus_delta_m'])
chosen=[];seen=set()
for row in rows:
    r,c=row['center'];sector=r//256,c//256
    if sector in seen:continue
    chosen.append(row);seen.add(sector)
    if len(chosen)==4:break
fig,axs=plt.subplots(4,2,figsize=(13,10),squeeze=False)
profiles=[]
for i,row in enumerate(chosen):
    r,c=row['center'];v=np.arange(-8,9);distance=v*6
    for j,axis in enumerate(('Oeste–este','Norte–sur')):
        a=base[r,c+v] if j==0 else base[r+v,c]
        b=height[r,c+v] if j==0 else height[r+v,c]
        ax=axs[i,j];ax.plot(distance,a,'o-',ms=3,label='B desplegado',color='#3c5b8d')
        ax.plot(distance,b,'x-',ms=4,label='EV87 rechazado',color='#b45c18')
        ax.axvspan(-12,12,color='#b45c18',alpha=.06)
        ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.2)
        ax.set(xlabel='Distancia (m)',ylabel='Altura (m)',title=f'{axis} · X={c*6}, Z={12282-r*6}')
        profiles.append(dict(queue_id=row['queue_id'],axis=axis,distance_m=distance.tolist(),B=a.tolist(),candidate=b.tolist()))
fig.suptitle('Diagnóstico de perfiles 1:1 · candidato EV87 rechazado · sin despliegue\nCuatro sectores de mayor descenso; la banda señala el parche de 24 m')
fig.legend(*axs[0,0].get_legend_handles_labels(),loc='lower center',ncol=2)
fig.tight_layout(rect=(0,.04,1,.95));fig.savefig(ROOT/'rejected-profiles.png',dpi=150);plt.close(fig)
summary['profiles']=profiles
(ROOT/'rejection-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='profiles'},indent=2))
