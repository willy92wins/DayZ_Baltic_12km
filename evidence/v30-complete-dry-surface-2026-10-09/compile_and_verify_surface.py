"""Consumer of saved PNG/PAA: independently interpolate native triangle heights over the whole map."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,subprocess,time
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

B=Path(__file__).parent
T=Path('E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009/candidate/terrain.npz')
P=Path('E:/DayZ-Baltic-Build/v30-remaining-exact-dry-support-20261009/candidate/plane.npy')
OLD=Path('E:/DayZ-Baltic-Build/v30-current-satellite-20261009/surface/layers')
MASK=OLD
TOOL=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZ Tools/Bin/ImageToPAA/ImageToPAA.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def barycentric(nw,ne,sw,se,u,v):
    return np.where(u>=v,(1-u)*nw+(u-v)*ne+v*se,(1-v)*nw+(v-u)*sw+u*se)

def process(ab):
    a,b=ab;layers=B/'surface/layers';decoded=B/'decoded';images={};identities={}
    for prefix,suffix,channels in [('s','lco','RGB'),('m','lca','RGBA')]:
        name=f'{prefix}_{a:03d}_{b:03d}_{suffix}'
        png=layers/(name+'.png');paa=layers/(name+'.paa');dest=decoded/(name+'.png')
        original=np.array(Image.open(png).convert(channels));assert original.shape[:2]==(512,512)
        for source,target in [(png,paa),(paa,dest)]:
            call=subprocess.run([str(TOOL),str(source),str(target)],capture_output=True,text=True)
            assert call.returncode==0 and target.is_file(),(name,call.stdout,call.stderr)
        saved=np.array(Image.open(dest).convert(channels));assert saved.shape==original.shape
        images[prefix]=(original,saved)
        identities[prefix]={'png_sha256':sha(png),'paa_sha256':sha(paa),'decoded_sha256':sha(dest)}
    uv=np.arange(512)-64+.5
    xx,zz=np.meshgrid(a*384+uv,12288-b*384-uv)
    fc=np.clip(xx/6,0,2047-1e-6);fr=np.clip((12282-zz)/6,0,2047-1e-6)
    cc=np.floor(fc).astype(int);rr=np.floor(fr).astype(int);u=fc-cc;v=fr-rr
    ground=barycentric(H[rr,cc],H[rr,cc+1],H[rr+1,cc],H[rr+1,cc+1],u,v)
    nominal=np.fmax(F[rr,cc],.75);depth=nominal-ground;wet=depth>1e-6
    core=np.zeros(wet.shape,bool);core[64:448,64:448]=True
    core&=(xx>0)&(xx<12282)&(zz>0)&(zz<12282)
    mask,decoded_mask=images['m'];sat,decoded_sat=images['s']
    source_bad=core&wet&(mask[:,:,:3].max(axis=2)>0)
    interior=core&wet&(distance_transform_edt(wet)>=4)
    compiled_bad=interior&(decoded_mask[:,:,:3].max(axis=2)>8)
    all_bad=core&wet&(decoded_mask[:,:,:3].max(axis=2)>8)
    colors=np.unique(mask[:,:,:3].reshape(-1,3),axis=0)
    valid_colors=all(tuple(c) in {(0,0,0),(255,0,0),(0,255,0),(0,0,255)} for c in colors)
    oldsat=np.array(Image.open(OLD/f's_{a:03d}_{b:03d}_lco.png').convert('RGB'))
    oldmask=np.array(Image.open(MASK/f'm_{a:03d}_{b:03d}_lca.png').convert('RGBA'))
    changes=core&np.any(sat!=oldsat,axis=2);maskchanges=core&np.any(mask!=oldmask,axis=2)
    error=abs(decoded_sat.astype(int)-sat.astype(int))[core]
    control=None
    if interior.any():
        r,c=np.argwhere(interior)[0];mutant=decoded_mask.copy();mutant[r,c,:3]=[255,0,0]
        control=bool((interior&(mutant[:,:,:3].max(axis=2)>8)).sum()==compiled_bad.sum()+1)
    return dict(tile=[a,b],pixels=int(core.sum()),wet_pixels=int((core&wet).sum()),source_wet_not_gravel=int(source_bad.sum()),
        compiled_interior_pixels=int(interior.sum()),compiled_interior_non_gravel=int(compiled_bad.sum()),compiled_wet_non_gravel=int(all_bad.sum()),
        source_alpha_exact=bool(np.all(mask[:,:,3]==255)),valid_mask_palette=bool(valid_colors),
        satellite_changed_pixels=int(changes.sum()),mask_changed_pixels=int(maskchanges.sum()),dry_mask_changed_pixels=int((maskchanges&~wet).sum()),
        satellite_quantization_max=int(error.max()),satellite_quantization_abs_sum=int(error.sum()),
        negative_control=control,files=identities)

if __name__=='__main__':
    started=time.monotonic();spec=json.loads((B/'surface/surface.json').read_text())
    assert spec['terrain_sha256']==sha(T)=='b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36'
    assert spec['water_field']['sha256']==sha(P)=='768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
    assert spec['tiles']==1024 and spec['bed_surface']=='gravel'
    assert np.array_equal(barycentric(0,6,12,24,np.array([.75,.25]),np.array([.25,.75])),[9,12])
    assert np.array_equal(10-barycentric(0,6,12,24,np.array([.75,.25]),np.array([.25,.75]))>0,[True,False])
    H=np.load(T)['heights'].astype(float);F=np.load(P)
    (B/'decoded').mkdir(exist_ok=False)
    reports=[]
    with ThreadPoolExecutor(max_workers=4) as ex:
        for i,result in enumerate(ex.map(process,[(a,b) for b in range(32) for a in range(32)])):
            reports.append(result)
            if i%128==127:print(f'{i+1}/1024 tiles compiled and independently classified',flush=True)
    overlaps=0;bad_overlaps=[]
    for prefix,suffix in [('s','lco'),('m','lca')]:
        for a in range(32):
            for b in range(32):
                tile=np.array(Image.open(B/'surface/layers'/f'{prefix}_{a:03d}_{b:03d}_{suffix}.png'))
                for da,db in [(1,0),(0,1)]:
                    if a+da>=32 or b+db>=32:continue
                    other=np.array(Image.open(B/'surface/layers'/f'{prefix}_{a+da:03d}_{b+db:03d}_{suffix}.png'))
                    old,new=(tile[:,384:],other[:,:128]) if da else (tile[384:],other[:128])
                    if not np.array_equal(old,new):bad_overlaps.append([prefix,a,b,da,db,int(np.count_nonzero(old!=new))])
                    overlaps+=1
    names=['pixels','wet_pixels','source_wet_not_gravel','compiled_interior_pixels','compiled_interior_non_gravel','compiled_wet_non_gravel',
           'satellite_changed_pixels','mask_changed_pixels','dry_mask_changed_pixels','satellite_quantization_abs_sum']
    totals={key:sum(r[key] for r in reports) for key in names}
    gates=dict(all_map_pixels=totals['pixels']==12282**2,all_tiles=len(reports)==1024,
        source_wet_gravel=totals['source_wet_not_gravel']==0,compiled_interior_gravel=totals['compiled_interior_non_gravel']==0,
        mask_alpha=all(r['source_alpha_exact'] for r in reports),palette=all(r['valid_mask_palette'] for r in reports),
        all_overlaps=overlaps==3968 and not bad_overlaps,
        negative_controls=any(r['negative_control'] for r in reports) and all(r['negative_control'] is not False for r in reports))
    result=dict(status='PASS_COMPLETE_SURFACE_SOURCE_COMPILED' if all(gates.values()) else 'FAIL_COMPLETE_SURFACE',gates=gates,counts=totals,
        satellite_quantization_mean=totals['satellite_quantization_abs_sum']/(totals['pixels']*3),satellite_quantization_max=max(r['satellite_quantization_max'] for r in reports),
        overlaps=overlaps,bad_overlaps=bad_overlaps,inputs={str(p):sha(p) for p in [T,P,TOOL]},
        controls=['independent_nonplanar_triangle_heights','nonplanar_wet_dry_classification','compiled_real_interior_pixel_mutations'],
        tiles=reports,seconds=time.monotonic()-started,
        limits=['Full nominal physical pixel classification; does not detect native ocean shader artifacts.',
                'DXT border mixing inventoried, not zero at all water edges. Satellite compression error measured, not identical to PNG.',
                'Same palette and design classes; near-water shore proximity outside finite cells retains legacy heuristic.'])
    (B/'surface-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='tiles'},indent=2));assert all(gates.values())
