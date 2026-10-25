"""Offline coverage and true-scale profiles; deliberately not an engine render."""
from pathlib import Path
import json
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

B=Path(__file__).parent
review=json.loads((B/'review-independent/ev87-review.json').read_text())
assert review['status']=='PASS_EV87_GLOBAL_CONSUMER' and all(review['gates'].values())
records=[json.loads(line) for line in (B/'queue-ledger.jsonl').read_text().splitlines()]
header,final=records[0],records[-1]
candidate=B/'candidate-terrain.npz'
assert hashlib.sha256(candidate.read_bytes()).hexdigest()==final['candidate_sha256']
patches=[row for row in records if row.get('event')=='patch']
accepted=[row for row in patches if row['state']=='accepted']
rejected=[row for row in patches if row['state']!='accepted']
base=np.load(B.parent/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz')['heights']
height=np.load(candidate)['heights']
fig,ax=plt.subplots(figsize=(9,9))
for rows,color,label,size in [(header['excluded'],'#c0c5cc','Centros excluidos por proximidad/borde',3),
                               (rejected,'#bd6507',f'Sin cambio: {len(rejected)}',12),
                               (accepted,'#13714f',f'Propuestas verificadas: {len(accepted)}',13)]:
    points=np.asarray([row.get('center',row.get('coordinates')) for row in rows])
    if len(points):ax.scatter(points[:,1]*6,12282-points[:,0]*6,s=size,c=color,label=label,linewidths=0)
ax.set(xlim=(0,12282),ylim=(0,12282),xlabel='X (m)',ylabel='Z (m)',
       title='Cobertura de la pasada global EV87 · geometría verificada offline')
ax.set_aspect('equal');ax.grid(alpha=.15);ax.legend(loc='upper left',fontsize=8)
fig.tight_layout();fig.savefig(B/'coverage-map.png',dpi=160);plt.close(fig)
geometries={row['queue_id']:row for row in review['information']['patch_geometry']}
ranked=sorted(accepted,key=lambda row:geometries[row['queue_id']]['focus_delta_m'])
chosen=[];sectors=set()
for row in ranked:
    r,c=row['center'];sector=(r//256,c//256)
    if sector in sectors:continue
    chosen.append(row);sectors.add(sector)
    if len(chosen)==4:break
assert chosen
fig,axes=plt.subplots(len(chosen),2,figsize=(13,3*len(chosen)),squeeze=False)
profiles=[]
for row,patch in enumerate(chosen):
    r,c=patch['center'];v=np.arange(-3,4);distance=v*6
    for col,axis in enumerate(('Oeste–este','Norte–sur')):
        before=base[r,c+v] if col==0 else base[r+v,c]
        after=height[r,c+v] if col==0 else height[r+v,c]
        a=axes[row,col]
        a.plot(distance,before,'o-',color='#3c5b8d',label='B desplegado')
        a.plot(distance,after,'^-',color='#13714f',label='EV87 offline')
        a.set_aspect('equal',adjustable='box');a.grid(alpha=.2)
        a.set(xlabel='Distancia desde el foco (m)',ylabel='Altura (m)',title=f'{axis} · X={c*6}, Z={12282-r*6}')
        profiles.append(dict(queue_id=patch['queue_id'],row=r,col=c,axis=axis,distance_m=distance.tolist(),before_m=before.tolist(),after_m=after.tolist()))
fig.suptitle('Perfiles 1:1 · cuatro sectores con mayor descenso del foco · no son capturas DayZ')
fig.legend(*axes[0,0].get_legend_handles_labels(),loc='lower center',ncol=2)
fig.tight_layout(rect=(0,.04,1,.97));fig.savefig(B/'profiles-1to1.png',dpi=160);plt.close(fig)
(B/'profiles-1to1.json').write_text(json.dumps(dict(profiles=profiles,selection='Largest focus descent, one per 1536m sector, at most four sectors',candidate_sha256=final['candidate_sha256']),indent=2)+'\n')
print(json.dumps(dict(accepted=len(accepted),rejected=len(rejected),profiles=len(profiles))))
