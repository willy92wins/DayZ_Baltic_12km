from pathlib import Path
import json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');O=R/'dry-apron-linear-pilot-20261027'
sys.path.insert(0,str(W/'tools/water'));from streambed_kit_v31 import tri_h
original=np.load(R/'river-kit7-a-on-f-20261026/kit-7-surfaces.npz');candidate=np.load(O/'candidate-surfaces.npz');H=np.load(R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz')['heights'];rows=json.loads((R/'bank-source-attribution-20261027/result.json').read_text(encoding='utf-8'))['rows'];result=json.loads((O/'result.json').read_text(encoding='utf-8'))
fig,axes=plt.subplots(3,1,figsize=(11,9),layout='constrained');fig.suptitle('Kit-7 · perfil de las orillas\nEnsayo offline, sin integrar — '+result['status'],fontsize=15)
for ax,(mesh,query) in zip(axes,[('nav12','kit7_piece_116_right'),('nav12p5','kit7_piece_124_right'),('nav12p5','kit7_piece_133_right')]):
 row=next(r for r in rows if r['mesh']==mesh and r['query']==query and r['index']==1);i=int(np.argmin(abs(original['station']-row['selected']['station_m'])));b=original['bed'][i];c=candidate['bed'][i];q=np.unique(np.r_[np.arange(-18,19.),-2.25,2.25]);d=np.sign(q)*np.linalg.norm(b[:,[0,2]]-original['axis'][i],axis=1);ground=tri_h(H,b[:,0],b[:,2]);water=original['level'][i]
 ax.plot(d,b[:,1],label='Orilla actual',color='#b05712',lw=2);ax.plot(d,c[:,1],label='Piloto',color='#19804f',lw=2);ax.plot(d,ground,label='Terreno soporte',color='#646464',ls='--');ax.plot([-2.25,2.25],[water,water],label='Lámina de agua',color='#238bd2',lw=3)
 ax.axvspan(-4,4,color='#dce7eb',alpha=.4,label='Interior fijo');ax.set_title(query+' · sección fuente cercana a estación '+str(round(float(original['station'][i]),1))+' m',fontsize=11);ax.set_ylabel('Cota (m)');ax.grid(alpha=.2);ax.set_xlabel('Distancia transversal real al eje (m)')
axes[0].legend(ncols=3,fontsize=9);fig.savefig(O/'profiles.png',dpi=135);plt.close(fig);print(O/'profiles.png')
