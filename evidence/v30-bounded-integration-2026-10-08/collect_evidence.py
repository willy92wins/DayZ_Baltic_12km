"""Copy immutable diagnostic receipts; make measured shore crossings reviewable."""
from pathlib import Path
import json
import shutil
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

EV = Path(__file__).resolve().parent
B = Path('E:/DayZ-Baltic-Build/v30-bounded-integration-20261008')
reports = EV/'reports'
reports.mkdir(exist_ok=True)
sources = ['luga-margin/report.json', 'verification-r2/margin-verification.json',
           'combined/report.json', 'combined-verification.json', 'verify-combined.json',
           'roads-combined.json', 'pbo-diff.json', 'pbo-verified.json', 'deploy-receipt.json',
           'package-combined/build-receipt.json', 'focus-v12-corrected.csv', 'focus-combined.csv']
for source in sources:
    name = source.replace('/','-')
    target = reports/name
    if target.exists():
        assert target.read_bytes() == (B/source).read_bytes()
    else:
        shutil.copyfile(B/source, target)

s = np.load(B/'verification-r2/stations-interleaved_1m.npz')
p, n, rid, keep = (s[k] for k in ['points','normal','ring_id','keep'])
fig, axes = plt.subplots(1, 3, figsize=(15, 5), layout='constrained')
for ax, (x,z,title) in zip(axes, [(7702.875,2812.049,'Contacto con lecho protegido'),
                                (9464.735,2262.415,'Recodo del Luga'),
                                (9492,2076,'Orilla leída en DayZ')]):
    for key, color, label in [('before','#ad5438','V12'),('after','#1565a0','Margen acotado')]:
        q = p+n*s[key][:,None]
        valid = keep & np.isfinite(s[key]) & (abs(p[:,0]-x)<75) & (abs(p[:,1]-z)<75)
        starts = np.flatnonzero(valid & ~np.r_[False, valid[:-1] & (rid[:-1] == rid[1:])])
        for i in starts:
            j=i+1
            while j<len(p) and valid[j] and rid[j]==rid[i]: j+=1
            ax.plot(q[i:j,0],q[i:j,1],color=color,linewidth=1.8,label=label)
    handles, labels = ax.get_legend_handles_labels()
    unique = dict(zip(labels,handles))
    ax.legend(unique.values(),unique.keys(),loc='best')
    ax.set(xlim=(x-60,x+60),ylim=(z-60,z+60),title=title,xlabel='X (m)',ylabel='Z (m)')
    ax.set_aspect('equal');ax.grid(alpha=.2)
fig.suptitle('Luga · cruces de agua medidos en estaciones independientes\nMismas normales y búsqueda ±8 m; 0,25 m; cortes = muestras ausentes/excluidas, no huecos de agua',fontsize=12)
fig.savefig(EV/'figures/shore-crossings.png',dpi=140);plt.close(fig)
receipt = dict(build=str(B), copied={p:hashlib.sha256((B/p).read_bytes()).hexdigest() for p in sources},
               external_stations={str(B/'verification-r2'/f'stations-{label}.npz'):hashlib.sha256((B/'verification-r2'/f'stations-{label}.npz').read_bytes()).hexdigest() for label in ['frozen','interleaved_1m']})
(EV/'artifact-locations.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(copied=len(sources),figure='figures/shore-crossings.png')))
