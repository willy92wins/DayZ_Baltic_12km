"""Compare independent engine samples with saved TB ASCII, fitting no heights."""
from pathlib import Path
import argparse, json, os
import numpy as np, rasterio
ap=argparse.ArgumentParser()
for name in ['repo','log','out']:
    ap.add_argument('--'+name,type=Path,required=True)
args=ap.parse_args()
ROOT=args.out
DEV=args.repo
OUT=args.out; OUT.mkdir(parents=True,exist_ok=True)
log=args.log
lines=log.read_text().splitlines()
grid=np.array([[float(v) for v in l.split(';')[1:]] for l in lines if l.startswith('G;')])
profile=np.array([[float(v) for v in l.split(';')[1:]] for l in lines if l.startswith('P;')])
assert grid.shape == (289,3) and profile.shape == (289,5)
assert np.isfinite(grid).all() and np.isfinite(profile).all()
with rasterio.open(DEV/'tb/narva_trial/narva_tb_export.asc') as src: native=src.read(1)

def interpolate(x,y,dx=0,dy=0,mode='NE_SW'):
    c=(x+dx)/6; r=(12288-(y+dy))/6
    ci=np.floor(c).astype(int); ri=np.floor(r).astype(int)
    a=c-ci; b=r-ri
    z00=native[ri,ci]; z10=native[ri,ci+1]; z01=native[ri+1,ci]; z11=native[ri+1,ci+1]
    if mode=='BILINEAR': return z00*(1-a)*(1-b)+z10*a*(1-b)+z01*(1-a)*b+z11*a*b
    if mode=='NW_SE': return np.where(b<=a,z00*(1-a)+z10*(a-b)+z11*b,z00*(1-b)+z01*(b-a)+z11*a)
    return np.where(a+b<=1,z00*(1-a-b)+z10*a+z01*b,z10*(1-b)+z01*(1-a)+z11*(a+b-1))

rank=[]
for dx in np.arange(-18,18.1,3):
    for dy in np.arange(-18,18.1,3):
        for mode in ['NE_SW','NW_SE','BILINEAR']:
            diff=interpolate(grid[:,0],grid[:,1],dx,dy,mode)-grid[:,2]
            rank.append({'dx':float(dx),'dy':float(dy),'mode':mode,'rmse_m':float(np.sqrt(np.mean(diff**2))),'max_m':float(abs(diff).max())})
rank.sort(key=lambda p:p['rmse_m'])
best=rank[0]
actual_x=2417.143+0.988364361*profile[:,0]
actual_y=6889.885-0.152104866*profile[:,0]
predicted=interpolate(actual_x,actual_y,best['dx'],best['dy'],best['mode'])
result={'grid_samples':len(grid),'profile_samples':len(profile),'best_grid_mappings':rank[:10],
 'profile_validation_max_error_m':float(abs(predicted-profile[:,3]).max()),
 'endpoint_samples':profile[np.isin(profile[:,0],[-13,-12.75,-12.5,0,12.5,12.75,13])].tolist(),
 'limits':['Mapping is an observed local comparison; no global correction applied.','SurfaceRoadY is surface-query evidence, not a player traversal test.','Profile coordinate strings rounded by Enforce; predictions use original formula.']}
(OUT/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
os.environ['MPLCONFIGDIR']=str(ROOT/'mpl-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(12,5),dpi=160)
ax.plot(profile[:,0],profile[:,3],label='Terreno: lectura de Buldozer',color='#9b612e')
ax.plot(profile[:,0],profile[:,4],label='Superficie transitable: consulta nativa',color='#123752',lw=2)
ax.plot(profile[:,0],predicted,ls=':',label=f"Exportación TB con ajuste diagnóstico ({best['dx']:.0f}, {best['dy']:.0f}) m",color='#da5795')
ax.axhline(.1,ls='--',label='Agua prevista (plano de prueba oculto)',color='#46aece')
ax.set(xlabel='Metros desde el centro, oeste → este',ylabel='Cota en el motor (m)',title='Narva · el puente está a 2 m; los accesos todavía no son continuos')
ax.legend(fontsize=8); ax.grid(alpha=.2); fig.tight_layout();fig.savefig(OUT/'perfil-nativo.png');plt.close(fig)
print(json.dumps(result,indent=2))
