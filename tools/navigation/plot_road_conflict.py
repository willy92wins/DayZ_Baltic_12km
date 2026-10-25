"""Geographic diagnostic of a frozen road-constraint conflict."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.ndimage import distance_transform_edt
ROOT=Path(__file__).resolve().parents[2]

def main():
    folder=ROOT/'tests/regional_road_network_v16/cap-certificate-scan';out=folder/'conflict-region.png';assert not out.exists()
    r=json.loads((folder/'structural-conflict-region.json').read_text(encoding='utf-8'));points=np.asarray(r['vertices']);p=np.load(ROOT/'tests/regional_foundation_combined_v10/reference.npz');v=np.load(folder.parent/'variables.npz');h=p['candidate']
    lo=points.min(axis=0)-60;hi=points.max(axis=0)+60;c0=int(lo[0]//6);c1=int(hi[0]//6)+1;r0=int((12282-hi[1])//6);r1=int((12282-lo[1])//6)+1
    extent=[c0*6-3,c1*6-3,12282-r1*6+3,12282-r0*6+3];s=np.s_[r0:r1,c0:c1]
    categories=np.zeros(h.shape,dtype=np.uint8);categories[v['support']]=1;categories[(distance_transform_edt(~(p['wet']|p['ocean']))*6)<=30]=2;categories[p['fairway_support']]=3
    fig,axes=plt.subplots(1,2,figsize=(13,5),layout='constrained')
    im=axes[0].imshow(h[s],extent=extent,cmap='terrain');fig.colorbar(im,ax=axes[0],label='Altura del terreno V10 (m)')
    axes[1].imshow(categories[s],extent=extent,cmap=ListedColormap(['#cccccc','#70bc65','#3b83bf','#44447b']),vmin=0,vmax=3)
    roads=np.load(ROOT/'tests/regional_foundation_roads_v6/reference.npz')['xy'];chains=json.loads((ROOT/'evidence/regional-foundation-v1/road-grade-chains-v6.json').read_text(encoding='utf-8'))['chains']
    for ax in axes:
        for indices in chains:
            line=roads[indices]
            if np.any((line[:,0]>=lo[0])&(line[:,0]<=hi[0])&(line[:,1]>=lo[1])&(line[:,1]<=hi[1])):ax.plot(line[:,0],line[:,1],color='white',linewidth=1)
        ax.scatter(points[:,0],points[:,1],s=5,c='#d630b2',label='Vértices del conflicto')
        ax.set(xlim=extent[:2],ylim=extent[2:],xlabel='X del mapa (m)',ylabel='Z del mapa (m)',aspect='equal')
    axes[0].set_title('Geometría original y ejes de carretera')
    axes[1].set_title('Verde: editable · azul: agua + 30 m\ngris: exterior · violeta: cauce protegido')
    axes[1].legend(loc='lower right');fig.suptitle('Diagnóstico de 189 restricciones incompatibles; terreno sin editar')
    fig.savefig(out,dpi=150);plt.close(fig);print(out)

if __name__=='__main__':main()
