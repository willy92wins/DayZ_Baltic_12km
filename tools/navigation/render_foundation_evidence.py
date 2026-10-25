"""Plot the actual river traces over the frozen engineering terrain, not game pixels."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import rasterio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from verify_regional_chase import vec

ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reference',type=Path,required=True)
    ap.add_argument('--verification',type=Path,required=True)
    ap.add_argument('--folder',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists() or a.out.with_suffix('.json').exists():raise ValueError('Preserve figure evidence')
    ref=json.loads(a.reference.read_text(encoding='utf-8'));report=json.loads(a.verification.read_text(encoding='utf-8'))
    assert report['reference_sha256']==sha(a.reference)
    terrain=Path(ref['terrain']);assert sha(terrain)==ref['terrain_sha256']
    with rasterio.open(terrain) as ds:h=ds.read(1)
    source=ROOT/'tests/regional_foundation_combined_v10/reference.npz'
    outline=ROOT/'tests/regional_outline_v3/reference.npz'
    design=np.load(source);regions=np.load(outline)
    wet=design['wet']|design['ocean'];reserve=regions['reserve'];spb=regions['spb']
    # Only presentation is subsampled; coordinate samples retain the native 6m grid.
    step=4;field=h[::step,::step];x=np.arange(2048)[::step]*6/1000;z=(2047-np.arange(2048)[::step])*6/1000
    shade=LightSource(315,45).hillshade(field,vert_exag=3,dx=6*step,dy=6*step)
    rgb=np.empty((*field.shape,3));rgb[:]=[.72,.77,.59];rgb*=.72+.28*shade[...,None]
    rgb[reserve[::step,::step]]*=np.array([.75,1,.80]);rgb[wet[::step,::step]]=[.40,.68,.78]
    fig=plt.figure(figsize=(15,11),facecolor='#f7f7f3');grid=fig.add_gridspec(1,2,width_ratios=[3.8,1.4])
    ax=fig.add_subplot(grid[0]);side=fig.add_subplot(grid[1]);side.axis('off')
    ax.imshow(rgb,extent=(x[0]-step*.003,x[-1]+step*.003,z[-1]-step*.003,z[0]+step*.003),origin='upper')
    ax.contour(x,z,reserve[::step,::step],levels=[.5],colors=['#247048'],linewidths=1.1)
    ax.contour(x,z,spb[::step,::step],levels=[.5],colors=['#777477'],linewidths=.8,linestyles='dashed')
    roadsource=ROOT/'tests/regional_foundation_roads_v6/reference.npz'
    chainsource=ROOT/'evidence/regional-foundation-v1/road-grade-chains-v6.json'
    roads=np.load(roadsource);chains=json.loads(chainsource.read_text())['chains']
    ax.add_collection(LineCollection([roads['xy'][ids]/1000 for ids in chains],colors='#7a7770',linewidths=.5,alpha=.65))
    colors={'PASS':'#086942','FAIL_OR_INCOMPLETE':'#bd4535','INCOMPLETE':'#ba8b1b'}
    items=[];inputs={str(p):sha(p) for p in (a.reference,a.verification,terrain,source,outline,roadsource,chainsource)}
    for case in ref['cases']:
        result=next(c for c in report['cases'] if c['case']==case['case']);color=colors[result['status']]
        logfile=a.folder/f'{ref["log_prefix"]}{case["case"]}.log'
        if not logfile.exists():continue
        assert sha(logfile)==report['logs_sha256'][logfile.name];inputs[str(logfile)]=sha(logfile)
        positions=np.array([vec(line.split(';')[-1])[[0,2]] for line in logfile.read_text(encoding='utf-8-sig').splitlines() if line.startswith('B;')])/1000
        if len(positions):
            ax.plot(positions[:,0],positions[:,1],color=color,lw=1.8)
            at=positions[len(positions)//2];ax.annotate(str(case['case']),at,fontsize=8,color='#162c25',bbox=dict(facecolor='white',edgecolor='none',alpha=.85,pad=1))
        items.append(f'{case["case"]:2}  {case["river"]}\n     {case["length_m"]/1000:.2f} km  /  {result["status"]}')
    anchorsource=ROOT/'evidence/regional-foundation-v1/road-network-selection.json'
    inputs[str(anchorsource)]=sha(anchorsource)
    for anchor in json.loads(anchorsource.read_text(encoding='utf-8'))['anchors']:
        xx,zz=np.array(anchor['xz'])/1000
        ax.plot(xx,zz,'o',ms=2.5,color='#292b29');ax.annotate(anchor['name'],(xx,zz),xytext=(3,4),textcoords='offset points',fontsize=7.5,bbox=dict(facecolor='white',alpha=.7,edgecolor='none',pad=.5))
    reserve_rows,reserve_cols=np.where(reserve)
    reserve_label=(float(reserve_cols.mean()*6/1000),float((2047-reserve_rows.mean())*6/1000))
    ax.annotate('Reserva natural\nterreno protegido',reserve_label,fontsize=9,color='#15452a',ha='center',bbox=dict(facecolor='white',alpha=.8,edgecolor='none'))
    ax.set(xlim=(0,12.288),ylim=(0,12.288),aspect='equal',xlabel='X del juego (km)',ylabel='Z / norte del juego (km)')
    ax.grid(alpha=.13)
    ax.legend(handles=[Line2D([0],[0],color='#086942',lw=2,label='Ensayo completo: PASS'),Line2D([0],[0],color='#bd4535',lw=2,label='Ensayo: fallo / incompleto'),Line2D([0],[0],color='#7a7770',lw=1,label='Corredor de carretera proyectado')],loc='lower left',fontsize=8)
    side.text(0,1,'LANCHA VANILLA VACÍA',fontsize=12,weight='bold',va='top')
    side.text(0,.96,'\n\n'.join(items),fontsize=8.5,va='top',linespacing=1.2)
    side.text(0,.08,'Tramos independientes con solape.\nUn sentido; sin tripulantes.\nRojo no significa cauce bloqueado:\nconsultar el fallo exacto del ensayo.\nNo prueba un barco mediano.\n\nAgua y relieve: datos de ingeniería.\nNo es una captura del juego.',fontsize=8.5,va='top',color='#434641')
    fig.suptitle('BALTIC 12.288 km · base regional V10\nCobertura física de los cauces seleccionados',fontsize=17,x=.43,y=.97)
    fig.subplots_adjust(top=.90,bottom=.08,left=.06,right=.97,wspace=.13)
    fig.savefig(a.out,dpi=160,facecolor=fig.get_facecolor());plt.close(fig)
    receipt=dict(status='ENGINEERING_PLOT_WITH_FROZEN_ACTUAL_TRACES',verification=report['status'],inputs_sha256=inputs,output_sha256=sha(a.out),limits=['Visualization of logged trajectories, not an independent runtime test.','No buildings or trees are represented as placed assets.','Hillshade exaggerated3x for readability; heightfield unchanged.'])
    a.out.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(output=str(a.out),sha256=sha(a.out),status=receipt['status'])))

if __name__=='__main__':main()
