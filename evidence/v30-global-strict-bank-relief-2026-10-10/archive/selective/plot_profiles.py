"""Review three predetermined classes of profiles, including the residual Q focus."""
from pathlib import Path
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;B=R.parent.parent/'v30-mixed-bank-incremental-fixed-20261010'
candidate=R/'candidate-terrain.npz'
assert hashlib.sha256(candidate.read_bytes()).hexdigest()=='8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b'
hb=np.load(B/'candidate/terrain.npz')['heights'];hh=np.load(candidate)['heights']
p=np.load(B/'candidate/plane.npy')
g=json.loads((R/'_consumer-scratch/ev87-global-report.json').read_text())['information']['patch_geometry']
eligible=[x for x in g if min(x['center'])>=12 and max(x['center'])<=2035 and hh[tuple(x['center'])]!=hb[tuple(x['center'])] and np.isfinite(p[x['center'][0]-7:x['center'][0]+8,x['center'][1]-7:x['center'][1]+8]).any()]
assert eligible
eligible.sort(key=lambda x:x['focus_energy_reduction'])
chosen=[('Residual piramidal sin corregir',(840,370)),('Mejora mediana junto al agua',tuple(eligible[len(eligible)//2]['center'])),('Mayor mejora junto al agua',tuple(eligible[-1]['center']))]
fig,axes=plt.subplots(3,2,figsize=(13,10),sharex=True)
for i,(title,(r,c)) in enumerate(chosen):
 for j,axis in enumerate(('E–O','N–S')):
  rr=np.full(25,r) if j==0 else np.arange(r-12,r+13)
  cc=np.arange(c-12,c+13) if j==0 else np.full(25,c)
  ax=axes[i,j];ax.plot(np.arange(-12,13)*6,hb[rr,cc],label='B',c='#aa563c',lw=1.4,marker='.',ms=3)
  ax.plot(np.arange(-12,13)*6,hh[rr,cc],label='S',c='#21746e',lw=1.4,marker='.',ms=3)
  ax.set_title(f'{title} · {axis}\nX={c*6}, Z={12282-r*6}',fontsize=10)
  ax.axvline(0,c='gray',lw=.5);ax.grid(alpha=.2);ax.set_ylabel('Cota (m)');ax.set_xlabel('Distancia al foco (m)')
  ax.legend(loc='best')
fig.suptitle('Perfiles nativos: B frente a EV87-S\nDiagnóstico offline; incluye un residual conocido. No prueba del render de DayZ.',fontsize=12)
fig.tight_layout(rect=(0,0,1,.95));fig.savefig(R/'profiles.png',dpi=150)
(R/'profiles.json').write_text(json.dumps({'status':'DIAGNOSTIC_ONLY','candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'selection':chosen,'changed_at_foci':[bool(hb[rc]!=hh[rc]) for _,rc in chosen]},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(R/'profiles.png'),'foci':chosen}))
