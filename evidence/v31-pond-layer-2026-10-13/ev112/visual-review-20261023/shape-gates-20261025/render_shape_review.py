from pathlib import Path
import json,sys,numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).parent;S=R/sys.argv[1];O=S/'figures';O.mkdir(exist_ok=True)
r=json.loads((S/'rivers.json').read_text());lines=np.load(S/'river-lines.npz')
rows=[a for a in r['sites'] if a.get('joins')]
selected=[]
for row in rows:
 for j in row['joins']:
  if j['turn_deg']>45:
   selected.append((row,j));break
 if len(selected)==4:break
fig,axes=plt.subplots(2,2,figsize=(12,11),constrained_layout=True)
for ax,(row,j) in zip(axes.flat,selected):
 sid=row['site'];x,z=j['xy'];paths=[lines[k] for k in lines.files if k.startswith(sid+'__')]
 for i,p in enumerate(paths):
  if np.min(np.linalg.norm(p-[x,z],axis=1))<40:ax.plot(p[:,0],p[:,1],lw=2,label=str(i))
 ax.scatter([x],[z],c='red',s=45,zorder=6);ax.set(xlim=(x-35,x+35),ylim=(z-35,z+35),title=f"{sid}: join {j['before_piece']} / {j['after_piece']}, {j['turn_deg']:.1f}°")
 ax.set_aspect('equal');ax.grid(alpha=.2);ax.ticklabel_format(useOffset=False,style='plain');ax.set_xlabel('X (m)');ax.set_ylabel('Z (m)')
fig.suptitle('Ejes derivados de las piezas colocadas: empalmes por revisar\nExtremos diagonales corregidos como proxy; no representa la orilla renderizada',fontsize=13);fig.savefig(O/'river-joins.png',dpi=150);plt.close(fig)
H=np.load('E:/DayZ-Baltic-Build/qc-council-20261024/road-merged-s3/terrain-buried.npz')['heights'];t=json.loads((S/'terrain.json').read_text());fs=t['findings']
pick=[f for f in fs if f['kind']=='rectangular_terrain_transition'][:2]
pick+=sorted([f for f in fs if f['kind']=='native_spike' and not any(k in f['domains'] for k in ['pond_corners','sea_bed','v31_continuous_pilot'])],key=lambda f:-f['prominence_m'])[:4-len(pick)]
fig=plt.figure(figsize=(13,10),constrained_layout=True)
for i,f in enumerate(pick[:4]):
 ax=fig.add_subplot(2,2,i+1,projection='3d');r,c=int(round(f['row'])),int(round(f['col']));n=12
 rr,cc=np.mgrid[max(0,r-n):min(len(H),r+n+1),max(0,c-n):min(len(H),c+n+1)];h=H[rr,cc]
 ax.plot_surface(cc*6,12282-rr*6,h,cmap='terrain',edgecolor='#333333',linewidth=.2,alpha=.95)
 ax.set_title(f"{f['kind']} ({c*6}, {12282-r*6})\n"+', '.join(f['domains']),fontsize=10);ax.set_xlabel('X');ax.set_ylabel('Z');ax.set_zlabel('m');ax.ticklabel_format(useOffset=False,style='plain');ax.view_init(35,-55)
fig.suptitle('Relieve nativo S3: candidatos; altura vertical exagerada para inspección',fontsize=14);fig.savefig(O/'terrain-candidates.png',dpi=150);plt.close(fig)
print(O)
