"""Describe frozen pursuit traces and the no-infected control, without changing verdicts."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from verify_regional_chase import vec
ROOT=Path(__file__).resolve().parents[2];NIGHT=ROOT/'evidence/overnight-2026-10-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    variants=[('continuous-pursuit-v1','reference-r4.json','V1: carril de 4 m · FAIL'),('continuous-pursuit-v2','reference.json','V2: tablero principal de 6 m · FAIL'),('bridge-human-control-v1','reference.json','Mismo humano sin infectado · PASS este')]
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=NIGHT/'bridge-controller-comparison.png');args=ap.parse_args()
    out=args.out;assert not out.exists()
    fig,axes=plt.subplots(4,1,figsize=(13,10.5),gridspec_kw={'height_ratios':[1,1,1,1.3]},layout='constrained')
    inputs={};summary=[]
    colors=['#8953bd','#c64132','#23814e']
    for index,(folder,refname,title) in enumerate(variants):
        base=NIGHT/folder;rp=base/refname;sp=base/'runtime-complete/engine.log';vp=base/'runtime-complete/verification.json'
        ref=json.loads(rp.read_text(encoding='utf-8'));report=json.loads(vp.read_text(encoding='utf-8'));bridge=ref['bridge']
        for p in (rp,sp,vp):inputs[str(p)]=sha(p)
        rows=[]
        for line in sp.read_text(encoding='utf-8-sig').splitlines():
            p=line.split(';')
            if p[0]=='P' and p[1]=='1':rows.append(dict(t=float(p[2]),event=p[3],actor=vec(p[4]),prey=vec(p[5]),health=float(p[6])))
        move=next(i for i,row in enumerate(rows) if row['event']=='MOVE_BEGIN');active=rows[move:];axis=np.array(bridge['axis_xz']);normal=np.array([-axis[1],axis[0]]);center=np.array(bridge['center_xz']);ax=axes[index]
        ax.add_patch(Rectangle((-112.5,-7.1),225,14.2,color='#e7e8e9',label='aceras laterales'))
        ax.add_patch(Rectangle((-112.5,-6),225,12,color='#d3d6d9',label='tablero principal'))
        ax.axhline(4,color='#8c8c8c',ls='--',lw=.8);ax.axhline(-4,color='#8c8c8c',ls='--',lw=.8)
        prey=np.array([r['prey'] for r in active]);relative=prey[:,[0,2]]-center
        ax.plot(relative@axis,relative@normal,color='#2677bd',lw=1.4,label='humano')
        actor=np.array([r['actor'] for r in active if r['health']>0])
        if len(actor):
            relative_actor=actor[:,[0,2]]-center;ax.plot(relative_actor@axis,relative_actor@normal,color='#df8b23',lw=1.1,label='infectado')
        ax.scatter([(relative@axis)[-1]],[(relative@normal)[-1]],s=28,color=colors[index],zorder=5)
        ax.set(xlim=(-165,155),ylim=(-8.5,8.5),ylabel='Lateral (m)',title=title)
        ax.legend(loc='upper right',ncol=4,fontsize=8);ax.grid(alpha=.16)
        times=np.array([r['t'] for r in active]);dt=np.diff(times);steps=np.linalg.norm(np.diff(prey[:,[0,2]],axis=0),axis=1);valid=dt>0;speed=steps[valid]/dt[valid];t=(times[1:]-times[0])[valid]
        axes[3].plot(t,speed,color=colors[index],lw=.9,alpha=.85,label=folder)
        peak=int(np.argmax(speed));summary.append(dict(variant=folder,original_status=report['status'],case1=report['cases'][1]['status'],maximum_human_speed_mps=float(speed[peak]),maximum_human_speed_at_relative_s=float(t[peak]),terminal=active[-1]['event'],last_human_xyz=prey[-1].tolist()))
    axes[2].set_xlabel('Estación sobre el eje del puente (m); centro = 0')
    axes[3].axhline(4,color='#777777',ls='--',lw=1,label='límite congelado del humano: 4 m/s')
    axes[3].set(xlabel='Tiempo desde MOVE_BEGIN (s)',ylabel='Velocidad horizontal (m/s)',title='Movimiento humano medido por el servidor; se conservan los picos')
    axes[3].legend(fontsize=8,loc='upper right');axes[3].grid(alpha=.2)
    fig.suptitle('Narva V10 · mismo mundo y navmesh, consumidores distintos',fontsize=16)
    fig.get_layout_engine().set(rect=(0,.045,1,.95))
    fig.text(.5,.001,'Comparación descriptiva: no identifica causa única. BALTIC-002 continúa abierto; sin infectado solo se ensayó el sentido este.',ha='center',fontsize=9)
    fig.savefig(out,dpi=160);plt.close(fig)
    receipt=dict(status='DESCRIPTIVE_PLOT_NOT_ACCEPTANCE',inputs_sha256=inputs,summary=summary,output_sha256=sha(out),limits=['No verdict changed.','Main Roadway +/-6m, sidewalks +/-7.1m; collision-free width is a separate consumer question.','One no-infected direction only, no randomized causal attribution.'])
    out.with_suffix('.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps(receipt['summary']))

if __name__=='__main__':main()
