"""Scientific before/after terrain plots; not a runtime visual acceptance."""
from pathlib import Path
import json,argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource,Normalize
ap=argparse.ArgumentParser();ap.add_argument('--version',default='v25');args=ap.parse_args()
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/f'tests/regional_outline_smoothing_{args.version}'
ref=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');base=ref['candidate'];candidate=np.load(OUT/'reference.npz')['candidate'];wet=ref['wet']|ref['ocean']
light=LightSource(azdeg=315,altdeg=35)
fig,axes=plt.subplots(2,2,figsize=(14,13),layout='constrained')
for col,(h,label) in enumerate([(base,'V10 actual'),(candidate,args.version.upper()+' candidato')]):
    rgb=light.shade(h[::2,::2],cmap=plt.get_cmap('terrain'),norm=Normalize(-12,200),vert_exag=1,dx=12,dy=12,blend_mode='soft')
    axes[0,col].imshow(rgb,extent=[0,12282,0,12282]);axes[0,col].set_title(label+' — relieve sin textura')
    x0,x1,z0,z1=7850,8550,10100,10800;c0,c1=int(x0//6),int(x1//6);r0,r1=int((12282-z1)//6),int((12282-z0)//6)
    subset=h[r0:r1,c0:c1];shade=light.shade(subset,cmap=plt.get_cmap('gist_earth'),norm=Normalize(-2,8),vert_exag=1,dx=6,dy=6)
    shade[subset<1.1,:3]=[.25,.65,.85]
    axes[1,col].imshow(shade,extent=[c0*6,c1*6,12282-r1*6,12282-r0*6]);axes[1,col].plot(8203,10433,'ro',markersize=4);axes[1,col].set_title(label+' — orilla; azul = cota menor de1.1m')
    for ax in axes[:,col]:ax.set_xlabel('Este del juego (m)');ax.set_ylabel('Norte del juego (m)')
fig.suptitle('Geometría calculada: comparación previa a Terrain Builder / DayZ')
fig.savefig(OUT/'terrain-comparison.png',dpi=130);plt.close(fig)
edge=np.zeros(base.shape,bool);edge[:2]=edge[-2:]=True;edge[:,:2]=edge[:,-2:]=True
bad=(~wet)&(~edge)&(candidate<1.4-1e-5);r,c=np.where(bad);order=np.argsort(candidate[r,c])
report=dict(count=len(r),minimum=float(candidate[r,c].min()) if len(r) else None,fairway_overlap=int((bad&ref['fairway_support']).sum()),examples=[dict(row=int(r[k]),col=int(c[k]),xz=[int(c[k]*6),int(12282-r[k]*6)],before=float(base[r[k],c[k]]),after=float(candidate[r[k],c[k]])) for k in order[:20]])
(OUT/'dry-floor-diagnostic.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
