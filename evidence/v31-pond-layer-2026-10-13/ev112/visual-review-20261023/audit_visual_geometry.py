"""Read-only diagnosis of the EV112 visual feedback. Not an acceptance gate."""
import csv
import hashlib
import json
import sys
from pathlib import Path
from collections import Counter

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

OUT = Path(__file__).resolve().parent
B = Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
WT = Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.dont_write_bytecode = True
sys.path.insert(0, str(WT / 'tools/water'))
import streambed_kit_v31 as kit

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for data in iter(lambda: f.read(1024*1024), b''):
            h.update(data)
    return h.hexdigest()

tp = B / 'water-fix-b/terrain.npz'
fp = B / 'water-fix-b/bury-work/fp0/footprint.npz'
assert sha(tp) == '07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62'
assert sha(fp) == '49ee2a69db85f047425f8e1d31a964f92771ceb19b203c42570b04c3c6207de5'
with np.load(tp) as z:
    H = z['heights'].astype(float)
    narva = z['narva']
with np.load(fp) as z:
    plane = z['plane']
base_t = B.parent/'bridges/terrain-ev107.npz'
base_fp = B.parent/'bridges/fp-ev107/footprint.npz'
with np.load(base_t) as z:
    Hbase=z['heights'].astype(float)
with np.load(base_fp) as z:
    Pbase=z['plane']
report = json.loads((B/'water-fix-b/kit/kit-report.json').read_text())
records = json.loads((B/'water-fix-b/kit/kit-records.json').read_text())
models = kit.load_models()
target = next(s for s in report['sites'] if s['site'] == 'kit-118')
target_records = [r for r in records if r['site']=='kit-118' and r['piece']!='stones']
surface = kit.KitSurface(target_records, models)
V = np.asarray(target['lattice'])
cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(V,axis=0),axis=1))]

def along(st):
    q = np.column_stack([np.interp(st,cum,V[:,i]) for i in (0,1)])
    u0 = (V[1]-V[0])/np.linalg.norm(V[1]-V[0])
    u1 = (V[-1]-V[-2])/np.linalg.norm(V[-1]-V[-2])
    q = np.where((st<0)[:,None], V[0]+st[:,None]*u0, q)
    return np.where((st>cum[-1])[:,None], V[-1]+(st-cum[-1])[:,None]*u1,q)

def ground_and_pond(q):
    g = kit.tri_h(H,q[:,0],q[:,1])
    r = np.clip(np.floor((12282-q[:,1])/6).astype(int),0,2046)
    c = np.clip(np.floor(q[:,0]/6).astype(int),0,2046)
    p = plane[r,c]
    return g,np.where(np.isfinite(p),p,-np.inf)

ends=[]
samples=[]
for name,station in [('south_start',0.0),('north_end',cum[-1])]:
    st=np.arange(station-36,station+36.001,.25)
    q=along(st); g,p=ground_and_pond(q)
    w=surface.max_height(q,'water')
    wet=(np.maximum(w,p)>g)
    idx=np.flatnonzero(~wet)
    runs=[]
    for group in np.split(idx,np.where(np.diff(idx)>1)[0]+1):
        if not len(group): continue
        a,b=group[0],group[-1]
        runs.append(dict(start_xz=q[a].round(3).tolist(),end_xz=q[b].round(3).tolist(),sampled_length_m=round(float((b-a+1)*.25),3),station_start=float(st[a]),station_end=float(st[b])))
    ends.append(dict(end=name,lattice_endpoint_xz=along(np.array([station]))[0].tolist(),dry_runs=runs))
    for i in range(len(st)):
        samples.append(dict(end=name,station=float(st[i]),x=float(q[i,0]),z=float(q[i,1]),ground=float(g[i]),pond=None if not np.isfinite(p[i]) else float(p[i]),kit_visual=None if not np.isfinite(w[i]) else float(w[i]),wet=bool(wet[i])))
with open(OUT/'kit118-end-samples.csv','w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(samples[0])); writer.writeheader(); writer.writerows(samples)

site_rows=[]
skipped_sites=[]
for s in report['sites']:
    if 'lattice' not in s:
        assert s.get('skipped'), s['site']
        skipped_sites.append(dict(site=s['site'],reason=s['skipped']))
        continue
    v=np.asarray(s['lattice'],float)
    d=np.diff(v,axis=0); lens=np.linalg.norm(d,axis=1)
    dirs=np.round(d/lens[:,None],8)
    breaks=np.r_[0,np.flatnonzero(np.any(dirs[1:]!=dirs[:-1],axis=1))+1,len(lens)]
    runs=[float(lens[a:b].sum()) for a,b in zip(breaks[:-1],breaks[1:])]
    site_rows.append(dict(site=s['site'],length_m=float(lens.sum()),turns=len(s['corners']),
                          elbows=sum(c['type']=='elbow' for c in s['corners']),longest_straight_m=max(runs),
                          start_xz=v[0].tolist(),end_xz=v[-1].tolist(),mode=s.get('mode')))

peaks=list(csv.DictReader(open(OUT/'pyramids/pyramids.csv')))
near=[p for p in peaks if p['kind']=='peak' and p['land']=='True' and np.hypot(float(p['x'])-2428,float(p['z'])-6942)<=500]
near.sort(key=lambda p:float(p['prom']),reverse=True)

# A crease is not a strict local maximum. Measure the angle between the two native triangles in each grid cell.
nw,ne,sw,se=H[:-1,:-1],H[:-1,1:],H[1:,:-1],H[1:,1:]
n0=np.stack([-(ne-nw)/6,np.ones_like(nw),(se-ne)/6],axis=-1)
n1=np.stack([-(se-sw)/6,np.ones_like(nw),(sw-nw)/6],axis=-1)
dot=np.einsum('ijk,ijk->ij',n0,n1)/(np.linalg.norm(n0,axis=-1)*np.linalg.norm(n1,axis=-1))
fold=np.degrees(np.arccos(np.clip(dot,-1,1)))
cell_min=np.minimum.reduce([nw,ne,sw,se])
land_cells=(cell_min>=.8)&(~np.isfinite(plane)|(cell_min>=plane))
r0,r1,c0,c1=842,942,354,454
local_fold=fold[r0:r1,c0:c1]
local_land=land_cells[r0:r1,c0:c1]
fold_stats=dict(domain='600 x 600 m centred approximately on Narva dam; all corners >=0.8m and no corner below the footprint plane',
                land_cells=int(local_land.sum()),
                internal_diagonal_angle_p50_p90_max=np.percentile(local_fold[local_land],[50,90,100]).tolist(),
                cells_above_20deg=int((local_land&(local_fold>20)).sum()),
                note='20 degrees is a descriptive inventory bin, not an approved acceptance threshold; edge folds between different cells are not included.')

# Exact terrain interpolation and actual kit water-proxy faces at 1m pixel centres.
xs=np.arange(8130.5,8352,1.0); zs=np.arange(8874.5,9264,1.0)
X,Z=np.meshgrid(xs,zs); Q=np.column_stack([X.ravel(),Z.ravel()]); g,p=ground_and_pond(Q)
w=surface.max_height(Q,'water')
pond=(p>g).reshape(X.shape); kw=(w>g).reshape(X.shape)
rb=np.floor((12282-Q[:,1])/6).astype(int);cb=np.floor(Q[:,0]/6).astype(int)
gb=kit.tri_h(Hbase,Q[:,0],Q[:,1]);pb=Pbase[rb,cb]
oldwater=(np.isfinite(pb)&(pb>gb)).reshape(X.shape)
terminal_areas=[]
for label,zlo,zhi in [('north',9189,9222),('south',8928,8943)]:
    sel=(Z>=zlo)&(Z<zhi)
    terminal_areas.append(dict(region=label,z_range=[zlo,zhi],x_range=[float(xs[0]-.5),float(xs[-1]+.5)],
                               reference_pond_m2_at_1m_sampling=int((sel&oldwater).sum()),
                               final_pond_or_kit118_m2_at_1m_sampling=int((sel&(pond|kw)).sum())))
gh=g.reshape(X.shape); dz,dx=np.gradient(gh)
shade=np.clip(.65+(.22*dx-.22*dz)/np.sqrt(1+dx*dx+dz*dz),.15,.95)
fig,(ax0,ax,ax2)=plt.subplots(1,3,figsize=(16,8),gridspec_kw={'width_ratios':[1,1,1.3]})
ext=[xs[0]-.5,xs[-1]+.5,zs[0]-.5,zs[-1]+.5]
oldgh=gb.reshape(X.shape);bz,bx=np.gradient(oldgh)
oldshade=np.clip(.65+(.22*bx-.22*bz)/np.sqrt(1+bx*bx+bz*bz),.15,.95)
ax0.imshow(oldshade,origin='lower',extent=ext,cmap='gray',vmin=0,vmax=1)
oldrgba=np.zeros((*X.shape,4));oldrgba[oldwater]=[.1,.35,.8,.9]
ax0.imshow(oldrgba,origin='lower',extent=ext,interpolation='nearest')
for label,pt in [('S',V[0]),('N',V[-1])]:
    ax0.plot(*pt,'o',color='red',ms=6);ax0.annotate(label,pt,xytext=(7,6),textcoords='offset points',color='red',weight='bold')
ax0.set_title('Referencia EV107 antes del kit\nMisma ventana y escala; agua a 1 m')
ax0.set_xlabel('X (m)');ax0.set_ylabel('Z (m)');ax0.set_aspect('equal')
ax.imshow(shade,origin='lower',extent=ext,cmap='gray',vmin=0,vmax=1)
rgba=np.zeros((*X.shape,4));rgba[pond]=[.1,.35,.8,.9];rgba[kw]=[0,.85,.85,1]
ax.imshow(rgba,origin='lower',extent=ext,interpolation='nearest')
ax.plot(V[:,0],V[:,1],color='orange',lw=.6,alpha=.6)
for label,pt in [('S',V[0]),('N',V[-1])]:
    ax.plot(*pt,'o',color='red',ms=6);ax.annotate(label,pt,xytext=(7,6),textcoords='offset points',color='red',weight='bold')
ax.set_title('Kit-118: terreno y agua final\nMuestreo a 1 m; eje del trazado en naranja')
ax.legend(handles=[Patch(color='#1959cc',label='Charca visible'),Patch(color='#00d9d9',label='Agua visible del kit')],loc='lower left',fontsize=8)
ax.set_xlabel('X (m)');ax.set_ylabel('Z (m)');ax.set_aspect('equal')
ext2=[6*c0,6*c1,12282-6*r1,12282-6*r0]
im=ax2.imshow(np.where(local_land,local_fold,np.nan),extent=ext2,vmin=0,vmax=45,cmap='magma',interpolation='nearest')
ax2.plot([2388,2468],[6942,6942],color='cyan',lw=3,label='Presa')
for q in near[:6]:
    ax2.plot(float(q['x']),float(q['z']),'o',mfc='none',mec='lime',ms=8)
ax2.set_xlim(ext2[:2]);ax2.set_ylim(ext2[2:]);ax2.set_aspect('equal')
ax2.set_title('Narva: arista entre triángulos de cada celda\nCírculos: picos aislados del censo, no todos los pliegues')
ax2.set_xlabel('X (m)');ax2.set_ylabel('Z (m)');ax2.legend(loc='upper right')
fig.colorbar(im,ax=ax2,label='Cambio de normal (grados)',shrink=.65)
fig.suptitle('Diagnóstico EV112 — geometría offline; no sustituye la vista en juego',fontsize=12)
fig.tight_layout();fig.savefig(OUT/'kit118-narva-diagnostic.png',dpi=150);plt.close(fig)

result=dict(schema='ev112-general-visual-review-v1',terrain_sha256=sha(tp),footprint_sha256=sha(fp),skipped_sites=skipped_sites,
            reference_terrain_sha256=sha(base_t),reference_footprint_sha256=sha(base_fp),
            sites=len(site_rows),total_turns=sum(s['turns'] for s in site_rows),
            total_elbows=sum(s['elbows'] for s in site_rows),
            kit118=next(s for s in site_rows if s['site']=='kit-118'),
            kit118_wet_span=target['wet_span'],kit118_trim_log=target['trim_log'],
            terminal_band_areas=terminal_areas,
            terminal_axis_diagnostics=ends,narva_peak_candidates_within_500m=near[:10],narva_fold=fold_stats,
            scope_gap='G3 only measures wet_span, not both original endpoints. G11 junctions skips sites whose mode is not reach; kit-118 is component mode.',
            limitations=['End samples follow straight continuation of the lattice axis; absence there is not proof of missing intended water without comparison to original water and lateral receptor.',
                         'KitSurface is shared with the builder; results diagnose its geometry, not independent acceptance.',
                         'A sharp lattice corner is not the same as a rendered sharp curve: physical kit pieces round the turns.',
                         'Source censo labels the current baseline Baltic EV110 land even when passed EV112; the terrain hash, not that legacy label, identifies this run.',
                         'Existing census free-domain label omits later shore guards; do not use it as mutation eligibility.'],
            sites_inventory=site_rows)
(OUT/'geometry-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('sites_inventory','narva_peak_candidates_within_500m')},indent=2))
