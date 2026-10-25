"""Global geometric risk inventory; does not claim to reproduce the native renderer."""
from pathlib import Path
import csv,json,hashlib,sys
import numpy as np
from scipy import ndimage
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
E=W/'evidence/v30-global-water-risk-2026-10-09'
B9=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
sys.path.insert(0,str(W/'tools/terrain'))
from v30_common import tri_sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
SOURCE=B9/'candidate-c1r3p/terrain_valley.npz'
EMPIRICAL=1.8
SEA_MEASURED=.85
B.mkdir(parents=True,exist_ok=True);E.mkdir(parents=True,exist_ok=True)
def coarse_surface(h,factor):
    n=h.shape[0]
    nodes=np.unique(np.r_[np.arange(0,n,factor),n-1])
    base=np.minimum(np.searchsorted(nodes,np.arange(n),side='right')-1,len(nodes)-2)
    frac=(np.arange(n)-nodes[base])/(nodes[base+1]-nodes[base])
    r=nodes[base,None];c=nodes[base][None,:]
    rr=nodes[base+1,None];cc=nodes[base+1][None,:]
    fr=frac[:,None];fc=frac[None,:]
    nw,ne,sw,se=h[r,c],h[r,cc],h[rr,c],h[rr,cc]
    return np.where(fc>=fr,nw+fc*(ne-nw)+fr*(se-ne),nw+fr*(sw-nw)+fc*(se-sw))
def screening(h,dry):
    return dry&(h<EMPIRICAL-1e-5),dry&(h<SEA_MEASURED-1e-5)
def independent_controls():
    r,c=np.mgrid[:33,:33]
    plane=3+2*c+4*r
    assert all(np.allclose(coarse_surface(plane,f),plane) for f in (2,4,8,16))
    flat=np.full((33,33),2.)
    assert not any(m.any() for m in screening(flat,np.ones_like(flat,bool)))
    low=flat.copy();low[7,12]=1.4
    risk,flood=screening(low,np.ones_like(low,bool))
    assert risk.sum()==1 and risk[7,12] and not flood.any()
    low[7,12]=.5
    risk,flood=screening(low,np.ones_like(low,bool));assert flood[7,12]
    dry=np.ones_like(low,bool);dry[7,12]=False
    assert not any(m.any() for m in screening(low,dry))
    # Independent analytical example: a 2 m native vertex lies halfway between -2 and +2 coarse supports.
    h=np.full((33,33),2.);h[:,16]=-2.
    q=coarse_surface(h,4)
    assert h[8,14]==2 and q[8,14]==0
    return dict(affine_planes_exact=True,high_dry_negative=True,low_dry_positive=True,
        physical_subsea_positive=True,intentional_water_excluded=True,coarse_depression_analytic=True)
t=dict(np.load(SOURCE));h=t['heights'].astype(float);dry=t['cls']==0;wet=~dry
low,subsea=screening(h,dry)
dist_water=ndimage.distance_transform_edt(dry,sampling=6)
dist_struct=ndimage.distance_transform_edt(~(t['reserve']|t['platform']),sampling=6)
physical_support=np.zeros_like(dry)
touch=wet[:-1,:-1]|wet[1:,:-1]|wet[:-1,1:]|wet[1:,1:]
for dr,dc in ((0,0),(0,1),(1,0),(1,1)):physical_support[dr:dr+2047,dc:dc+2047]|=touch
coarse_min=h.copy();coarse_rows=[];coarse_masks={}
for factor in (2,4,8,16):
    v=coarse_surface(h,factor);coarse_min=np.minimum(coarse_min,v)
    flag=dry&(h>=EMPIRICAL-1e-5)&(v<SEA_MEASURED)
    coarse_masks['coarse_'+str(factor)]=flag
    coarse_rows.append(dict(spacing_m=factor*6,native_dry_points_below_measured_sea=int(flag.sum()),maximum_drop_m=float(np.max((h-v)[dry]))))
    print('coarse',factor,flush=True)
coarse_risk=dry&(h>=EMPIRICAL-1e-5)&(coarse_min<SEA_MEASURED)
counts=dict(dry_vertices=int(dry.sum()),low_vertices=int(low.sum()),native_subsea_vertices=int(subsea.sum()),
    low_reserve=int((low&t['reserve']).sum()),low_platform=int((low&t['platform']).sum()),
    low_beach=int((low&t['beach']).sum()),low_water_face_support=int((low&physical_support).sum()),
    low_beyond_18m_water=int((low&(dist_water>18)).sum()),coarse_only=int(coarse_risk.sum()))
structure=np.array([[1,1,0],[1,1,1],[0,1,1]],bool)
labels,n=ndimage.label(low,structure)
components=[]
for ident,sl in enumerate(ndimage.find_objects(labels),1):
    if sl is None:continue
    local=labels[sl]==ident;rr,cc=np.nonzero(local);rr+=sl[0].start;cc+=sl[1].start
    k=int(np.argmin(h[rr,cc]));r,c=int(rr[k]),int(cc[k])
    components.append(dict(id=ident,vertices=len(rr),x=float(c*6),z=float(12282-r*6),min_ground_m=float(h[r,c]),
        x_min=int(cc.min()*6),x_max=int(cc.max()*6),z_min=int(12282-rr.max()*6),z_max=int(12282-rr.min()*6),
        reserve_vertices=int(t['reserve'][rr,cc].sum()),platform_vertices=int(t['platform'][rr,cc].sum()),
        water_face_support_vertices=int(physical_support[rr,cc].sum()),beyond_18m_water=int((dist_water[rr,cc]>18).sum())))
tiles=[]
for r0 in range(0,2048,8):
    for c0 in range(0,2048,8):
        sl=np.s_[r0:min(2048,r0+8),c0:min(2048,c0+8)]
        count=int(low[sl].sum());cm=int(coarse_risk[sl].sum())
        if not count and not cm:continue
        pts=np.argwhere(low[sl]|coarse_risk[sl]);pts[:,0]+=r0;pts[:,1]+=c0
        vals=h[pts[:,0],pts[:,1]];i=int(np.argmin(vals));r,c=pts[i]
        tiles.append(dict(tile_row=r0//8,tile_col=c0//8,x=int(c*6),z=int(12282-r*6),low_vertices=count,
            coarse_only_vertices=cm,min_ground_m=float(vals[i]),reserve_vertices=int((low[sl]&t['reserve'][sl]).sum()),
            platform_vertices=int((low[sl]&t['platform'][sl]).sum()),water_face_support=int((low[sl]&physical_support[sl]).sum())))
for name,rows in [('lowland-components',components),('risk-tiles',tiles)]:
    with (E/(name+'.csv')).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ['id']);writer.writeheader();writer.writerows(rows)
historic=json.loads((W/'evidence/v30-water-visual-fix-2026-10-08/geometry-diagnostic.json').read_text())
controls=[]
for p in historic['R1_projected_locations']:
    x,_,z=p['world'];r=int(round((12282-z)/6));c=int(round(x/6));sl=np.s_[r-3:r+4,c-3:c+4]
    controls.append(dict(name=p['name'],x=x,z=z,source_projection='approximate FOV, not exact native registration',
        current_ground=float(tri_sample(h,x,z)),lowland_risk_near_18m=bool(low[sl].any()),
        coarse_risk_near_18m=bool(coarse_risk[sl].any()),nearest_water_m=float(dist_water[r,c])))
np.savez_compressed(B/'global-risk-masks.npz',lowland=low,native_subsea=subsea,coarse_only=coarse_risk,
    coarse_min=coarse_min.astype(np.float32),labels=labels,**coarse_masks)
out=dict(status='GLOBAL_RISK_INVENTORY_NOT_RENDER_CERTIFICATION',terrain_sha256=sha(SOURCE),
    grid=dict(vertices=2048**2,native_faces=2*2047**2,cell_size_m=6),
    thresholds=dict(measured_sea_max_m=SEA_MEASURED,empirical_screening_m=EMPIRICAL),
    counts=counts,components=n,risk_tiles=len(tiles),coarse_models=coarse_rows,known_locations=controls,
    analytical_controls=independent_controls(),
    limits=['Empirical threshold is a screening bound, not native visual sea height.',
    'Coarse surfaces are hypotheses, not decoded renderer LODs.',
    'Full native vertex coverage; subcell physical pond coverage and global shader behavior remain separate.',
    'New user residual must be located and tested; do not close 016 from this inventory.'])
(E/'global-risk-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
if __name__=='__main__':pass
