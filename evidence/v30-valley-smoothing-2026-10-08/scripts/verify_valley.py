"""Independent consumer checks and sections on a saved valley candidate."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from scipy import ndimage
from shapely.geometry import shape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008');E=W/'evidence/v30-valley-smoothing-2026-10-08'
sys.path[:0]=[str(W/'tools/terrain')]
from v30_common import cell_planes,vertex_plane_bounds,grid_xz,tri_sample
from audit_fairway_triangles_v30 import records
from verify_roads_v30 import evaluate
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
a=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
label=sys.argv[1] if len(sys.argv)>1 else 'a';b=B/f'candidate-{label}/terrain_valley.npz'
t=dict(np.load(a));u=dict(np.load(b));h=t['heights'].astype(float);v=u['heights'].astype(float);changed=h!=v
cls=t['cls'];wet=np.isin(cls,(2,3,5,6,7));dry=cls==0
planes=cell_planes(cls,t['level']);pmin,pmax=vertex_plane_bounds(planes)
paths=[Path('E:/DayZ-Baltic-Build/v30-v11/06-evidence/corridors.geojson'),W/'evidence/v30-delta-fairways-2026-10-02/axes-corridors.geojson']
corridor=np.zeros_like(wet);nc=0
for path in paths:
 for f in json.loads(path.read_text())['features']:
  if f['properties'].get('kind','corridor24m')!='corridor24m':continue
  rec=records(shape(f['geometry']),planes);ids=np.unique(rec['ids']);corridor.ravel()[ids]=True;nc+=1
new_wet=wet&np.isfinite(pmin)&(v>pmin-.02+1e-6)&~(h>pmin-.02+1e-6)
new_dry=dry&np.isfinite(pmax)&(v<pmax-1e-6)&~(h<pmax-1e-6)
badslopes=0
for dr,dc in ((0,1),(1,0)):
 def slope(q):
  mid=q[dr:dr+2047,dc:dc+2047]
  return np.degrees(np.arctan(np.hypot(mid-q[:-1,:-1],q[1:,1:]-mid)/6.))
 before,after=slope(h),slope(v)
 touch=dry[:-1,:-1]|dry[dr:dr+2047,dc:dc+2047]|dry[1:,1:]
 badslopes+=int((touch&(after>np.maximum(before,35)+1e-4)).sum())
def curve(q,mask):
 xx=(q[1:-1,:-2]-2*q[1:-1,1:-1]+q[1:-1,2:])/36.
 zz=(q[:-2,1:-1]-2*q[1:-1,1:-1]+q[2:,1:-1])/36.
 xz=(q[2:,2:]-q[2:,:-2]-q[:-2,2:]+q[:-2,:-2])/144.
 c=np.sqrt(xx*xx+zz*zz+2*xz*xz)[mask[1:-1,1:-1]]
 return dict(n=len(c),rms=float(np.sqrt(np.mean(c*c))),p95=float(np.percentile(c,95)))
x,z=grid_xz();region=(x>7170)&(x<7470)&(z>5630)&(z<5920)
groups=dict(R3_valley=region&dry,general_dry=dry&~t['reserve']&~t['platform'])
cv={}
for name,m in groups.items():
 cb,ca=curve(h,m),curve(v,m);cv[name]=dict(before=cb,after=ca,reduction=1-ca['rms']/cb['rms'])
roads=evaluate(v,t['water'].astype(bool))
checks=dict(metadata_exact=all(np.array_equal(t[k],u[k],equal_nan=True) for k in t if k!='heights'),roads_platforms_exact=not bool((changed&(t['reserve']|t['platform'])).any()),corridors_exact=not bool((changed&corridor).any()),no_bed_shallower=not bool((v[wet]>h[wet]+1e-6).any()),floor_preserved=not bool((v[wet&(h>=1)]<1).any()),no_new_dry_flood=not bool(new_dry.any()),no_new_wet_exposure=not bool(new_wet.any()),no_steeper_faces=badslopes==0,roads_pass=roads['status']=='PASS',R3_curvature_improved=cv['R3_valley']['reduction']>=.15,general_curvature_improved=cv['general_dry']['reduction']>=.1,finite=bool(np.isfinite(v).all()))
# Independent negative: a raised actual corridor support must fail both support and depth-preservation checks.
idx=tuple(np.argwhere(corridor&wet)[0]);test=v.copy();test[idx]=h[idx]+.1
neg=dict(corridor_change_rejected=bool(np.any(test[corridor]!=h[corridor])),shallower_bed_rejected=bool(np.any(test[wet]>h[wet]+1e-6)))
assert all(neg.values())
landpoints=[(2179.537858,7086.083408),(2281.835241,7203.550968),(2534.5868,7037.5396),(2210.061284,6866.549706)]
samples=[dict(x=a,z=b,before=float(tri_sample(h,a,b)),after=float(tri_sample(v,a,b))) for a,b in landpoints]
report=dict(status='PASS_OFFLINE_VALLEY' if all(checks.values()) else 'FAIL',checks=checks,curvature=cv,roads=roads,corridors=nc,corridor_vertices=int(corridor.sum()),new_dry_flood_count=int(new_dry.sum()),new_wet_exposure_count=int(new_wet.sum()),steep_faces=badslopes,changed_vertices=int(changed.sum()),regional_180m_max_change=float(np.abs(ndimage.gaussian_filter(v-h,30.)).max()),R1_land_points=samples,negative=neg,inputs={str(p):sha(p) for p in (a,b,*paths)},limits=['Heights only; actual waterline and full terrain require game views.','Regions outside the plotted R3 valley also changed; final coverage not claimed.'])
(E/f'verification-{label}.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('roads','inputs')},indent=2),flush=True)
# Native sampled profiles, no smoothing in renderer.
axes=json.loads(Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2/axes.json').read_text())['R3']
s=np.array(axes['s']);xx=np.array(axes['x']);zz=np.array(axes['z'])
fig,axs=plt.subplots(2,3,figsize=(15,8),layout='constrained')
water=np.load('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008/stitched-water/visual_vertex_levels.npy')
for k,fr in enumerate((.15,.5,.85)):
 ss=axes['s_lo']+fr*(axes['s_hi']-axes['s_lo']);cx=np.interp(ss,s,xx);cz=np.interp(ss,s,zz)
 tangent=np.array([np.interp(ss+2,s,xx)-np.interp(ss-2,s,xx),np.interp(ss+2,s,zz)-np.interp(ss-2,s,zz)])
 normal=np.array([-tangent[1],tangent[0]])/np.linalg.norm(tangent);d=np.linspace(-90,90,721)
 xs=cx+normal[0]*d;zs=cz+normal[1]*d
 ax=axs[0,k];ax.plot(d,tri_sample(h,xs,zs),color='#8b5e3c',label='Antes');ax.plot(d,tri_sample(v,xs,zs),color='#127b66',label='Candidato')
 ax.axhline(float(tri_sample(water,cx,cz)),color='#418ccd',ls=':',label='Agua visual local')
 ax.set(title=f'R3 sección {k+1}',xlabel='Distancia transversal (m)',ylabel='Altura (m)');ax.grid(alpha=.2);ax.legend()
r0,r1=1050,1120;c0,c1=1190,1255;win=np.s_[r0:r1,c0:c1]
for k,q in enumerate((h,v)):
 ax=axs[1,k];ax.contour(x[win],z[win],q[win],levels=22,linewidths=.55,colors='#817868')
 visible=np.where(np.isfinite(pmin),q-water,np.nan)
 ax.contour(x[win],z[win],visible[win],levels=[0],colors='#287aa5',linewidths=1.4)
 ax.set(title=('Antes','Candidato')[k],xlabel='X (m)',ylabel='Z (m)',aspect='equal')
im=axs[1,2].imshow((v-h)[win],extent=[c0*6,c1*6,12282-r1*6,12282-r0*6],vmin=-2,vmax=2,cmap='RdBu')
axs[1,2].set(title='Desplazamiento (m)');fig.colorbar(im,ax=axs[1,2])
fig.suptitle('Valle R3: perfiles nativos y contorno visible calculado — pendiente de motor')
fig.savefig(E/f'profiles-{label}.png',dpi=150);plt.close(fig)
