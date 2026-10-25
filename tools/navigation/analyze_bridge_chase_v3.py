"""Describe preserved bridge failures without relaxing their original gate."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle
from verify_regional_chase import vec

ROOT=Path(__file__).resolve().parents[2];EV=ROOT/'evidence/overnight-2026-10-01/regional-chase-v3'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    rp=EV/'reference.json';vp=EV/'runtime-complete/verification.json';lp=EV/'runtime-complete/engine.log'
    ref=json.loads(rp.read_text());verified=json.loads(vp.read_text());assert sha(rp)==verified['reference_sha256'] and sha(lp)==verified['log_sha256']
    out=EV/'bridge-behavior-analysis.json';figure=out.with_suffix('.png')
    if out.exists() or figure.exists():raise ValueError('Preserve prior analysis')
    bridge=ref['bridge'];center=np.array(bridge['center_xz']);axis=np.array(bridge['axis_xz']);normal=np.array([-axis[1],axis[0]])
    rows=lp.read_text(encoding='utf-8-sig').splitlines();reports=[];traces={}
    for case in verified['cases']:
        if case['case']<12:continue
        raw=[s.split(';') for s in rows if s.startswith(f'A;{case["case"]};')]
        spawn=next(i for i,p in enumerate(raw) if p[3]=='SPAWN');raw=raw[spawn:]
        a=np.array([vec(p[4]) for p in raw]);d=a[:,[0,2]]-center;s=d@axis;w=d@normal
        minds=np.array([int(p[8]) for p in raw]);outside=(abs(s)<112.5)&(abs(w)>7.1)
        goal=np.array(next(c for c in ref['cases'] if c['case']==case['case'])['goal'])
        reports.append(dict(case=case['case'],original_status=case['status'],name=case['name'],reverse=case['reverse'],
            longitudinal_first_last_m=[float(s[0]),float(s[-1])],lateral_max_m=float(abs(w).max()),
            y_range_m=[float(a[:,1].min()),float(a[:,1].max())],outside_roadway_envelope_samples=int(outside.sum()),
            acquired_chase=bool(np.any(minds==3)),mind_counts={str(k):int(n) for k,n in zip(*np.unique(minds,return_counts=True))}))
        traces[case['case']]=(s,w,minds,(goal[[0,2]]-center)@axis,(goal[[0,2]]-center)@normal)
    failed=[r for r in reports if r['original_status']=='FAIL'];fig,axes=plt.subplots(3,2,figsize=(13,10),sharex=True,sharey=True)
    for ax,row in zip(axes.flat,failed):
        s,w,minds,gs,gw=traces[row['case']]
        ax.add_patch(Rectangle((-112.5,-7.1),225,14.2,facecolor='#e5e6e2',edgecolor='#8a8c84'))
        ax.hlines([-4,4],-135,135,color='#777777',linestyles='dashed',lw=.6)
        segments=np.stack((np.column_stack((s,w))[:-1],np.column_stack((s,w))[1:]),axis=1)
        colors=['#268a55' if state>=3 else '#cc7832' for state in minds[1:]]
        ax.add_collection(LineCollection(segments,colors=colors,linewidths=1.8))
        ax.scatter(s[0],w[0],s=35,marker='s',color='#202b26',zorder=5)
        ax.scatter(gs,gw,s=45,marker='*',color='#345fb0',zorder=5)
        ax.set_title(f'Caso {row["case"]} · {row["name"]} · '+('vuelta' if row['reverse'] else 'ida'),fontsize=10)
        ax.text(.02,.04,f'Y mínima {row["y_range_m"][0]:.2f} m · desvío {row["lateral_max_m"]:.2f} m\nPersecución registrada: '+('sí' if row['acquired_chase'] else 'no'),transform=ax.transAxes,fontsize=9)
        ax.set_xlim(-140,140);ax.set_ylim(-37,37);ax.grid(alpha=.2)
        ax.set_xlabel('Estación sobre el eje del puente (m)');ax.set_ylabel('Separación lateral (m)')
    fig.suptitle('Puente Narva V10 · trayectorias de los seis FAIL conservados\nNaranja: sin persecución; verde: CHASE/FIGHT · cuadrado: spawn · estrella: objetivo',fontsize=14)
    fig.tight_layout(rect=(0,0,1,.94));fig.savefig(figure,dpi=150);plt.close(fig)
    result=dict(status='DESCRIPTIVE_ANALYSIS_ORIGINAL_FAILS_UNCHANGED',source_sha256={str(p):sha(p) for p in (rp,vp,lp)},cases=reports,
        observations=['Four failed cases12/14/21/23 left the Roadway envelope and descended below11m; no mind3 was recorded.',
            'Cases15/17 reached while remaining near11m and within the broader7.1m envelope, but fail the frozen4m corridor.',
            'All passing bridge cases recorded chase; association alone does not isolate cause.'],
        limits=['Rectangular7.1m envelope is descriptive, not an exact collision-footprint validator.','No change to original acceptance, geometry or navmesh.','Continuous moving-human pursuit is a distinct pending experiment.'],figure_sha256=sha(figure))
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],report=str(out),figure=str(figure))))

if __name__=='__main__':main()
