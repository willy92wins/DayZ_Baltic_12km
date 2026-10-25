"""Offline diagnostic of the actual native mesh; never an acceptance gate."""
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
ROOT=Path(__file__).resolve().parent
PREP=ROOT/'prepared-runs/attempt-08/prepared.npz'
SOLUTION=ROOT/'solve-once/solution.npz'
RESULT=ROOT/'solve-once/solve-result.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if sha(PREP)!='52409a8d074d15ec068bddc6e9265bc3782e84e9d54582b8a6d7b0a6675a787f':raise ValueError('Prepared drift')
result=json.loads(RESULT.read_text(encoding='utf-8'))
if sha(SOLUTION)!=result['outputs']['solution.npz']:raise ValueError('Solution drift')
pins={str(p):sha(p) for p in (PREP,SOLUTION,RESULT,Path(__file__))}
with np.load(PREP,allow_pickle=False) as z:
    B=z['base_heights_context'];F=z['F_cells_float64'];P=z['P_cells_float64']
with np.load(SOLUTION,allow_pickle=False) as z:H=z['closed_float32_grid']
if B.shape!=H.shape or B.shape!=(15,15):raise ValueError('Profile shape')
fig=plt.figure(figsize=(16,11),layout='constrained')
gs=fig.add_gridspec(3,3,height_ratios=[1.8,1,1])
x=np.arange(15)*6.-42.;z=42.-np.arange(15)*6.
xx,zz=np.meshgrid(x,z);ii=np.arange(225).reshape(15,15)
tris=[]
for r in range(14):
    for c in range(14):
        nw,ne,sw,se=ii[r,c],ii[r,c+1],ii[r+1,c],ii[r+1,c+1]
        tris.extend(((nw,ne,se),(nw,se,sw)))
tri=mtri.Triangulation(xx.ravel(),zz.ravel(),triangles=np.asarray(tris))
for col,ground,title in ((0,B,'EV95: referencia'),(1,H,'Piloto: sin aceptar')):
    ax=fig.add_subplot(gs[0,col],projection='3d')
    ax.plot_trisurf(tri,ground.ravel(),cmap='terrain',vmin=float(B.min()),vmax=float(B.max()),linewidth=.25,edgecolor='#444444',antialiased=True)
    ax.set(xlabel='Este desde foco (m)',ylabel='Norte desde foco (m)',zlabel='Altura (m)',title=title,zlim=(float(min(B.min(),H.min())),float(max(B.max(),H.max()))))
    ax.set_box_aspect((1,1,.65));ax.view_init(elev=29,azim=-63)
ax=fig.add_subplot(gs[0,2]);d=H-B
img=ax.imshow(d,extent=(-45,45,-45,45),origin='upper',vmin=-.5,vmax=.5,cmap='RdBu_r')
ax.scatter(0,0,c='black',s=18);ax.set(title='Cambio de altura',xlabel='Este desde foco (m)',ylabel='Norte desde foco (m)')
fig.colorbar(img,ax=ax,label='m')
for j,row in enumerate((4,7,10)):
    ax=fig.add_subplot(gs[1,j]);ax.plot(x,B[row],color='#444444',marker='.',label='EV95')
    ax.plot(x,H[row],color='#d97706',marker='.',label='Piloto')
    # At the native vertex row use the north edge of each incident south cell.
    # F values are shown per cell, separately; no averaging or invented bridge over NaNs.
    for c in range(14):
        fv=F[row,c,[0,1]]
        if np.isfinite(fv).all():ax.plot(x[c:c+2],fv,color='#1677a8',lw=2,label='F visible' if c==0 else None)
        if np.isfinite(P[row,c]):ax.plot(x[c:c+2],[P[row,c]]*2,color='#1677a8',ls=':',lw=1)
    ax.set(title=f'Sección E–O: Z={12282-6*(855+row):.0f} m',xlabel='Este desde foco (m)',ylabel='Altura (m)')
    ax.grid(alpha=.25);ax.legend(fontsize=8)
ax=fig.add_subplot(gs[2,:]);ax.axis('off')
ax.text(.01,.98,'Oredezh · river_041 · malla nativa de 6 m\n'
        'Diagnóstico de alturas: no es una captura del juego ni una aceptación del candidato.\n'
        'Triangulación NW–SE explícita. Los perfiles unen los vértices reales; no se aplica suavizado de dibujo.\n'
        'Las vistas 3D exageran la escala vertical para mostrar los quiebros; los ejes conservan las unidades.\n'
        f'{np.count_nonzero(d)} vértices modificados · intervalo [{float(d.min()):.6f}, {float(d.max()):.6f}] m\n'
        f'Coste numérico {result["objective"]["baseline"]:.3f} → {result["objective"]["closed_float32"]:.3f}',
        va='top',fontsize=11,linespacing=1.6)
fig.suptitle('Perfil conjunto de cauce y taludes — candidato de diagnóstico',fontsize=17)
out=ROOT/'solve-once/native-profile-diagnostic.png'
if out.exists():raise FileExistsError('Do not overwrite diagnostic evidence')
fig.savefig(out,dpi=150);plt.close(fig)
after={p:sha(p) for p in pins}
if pins!=after:raise RuntimeError('Readset drift')
receipt={'status':'OFFLINE_DIAGNOSTIC_ONLY','source_pins_start':pins,'source_pins_end':after,'output':str(out),'output_sha256':sha(out)}
(out.with_suffix('.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(out),'sha256':sha(out)}))
