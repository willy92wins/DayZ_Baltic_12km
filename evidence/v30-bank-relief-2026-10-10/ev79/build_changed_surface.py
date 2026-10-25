from pathlib import Path
import sys,json,hashlib,subprocess,importlib.util,time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
B=Path(__file__).parent;R=B.parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OLD=R/'v30-complete-dry-surface-20261009'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    started=time.monotonic()
    assert json.loads((B/'review-luna/report.json').read_text())['status']=='PASS_EV79_CONSUMER'
    generator=W/'tools/terrain/build_surface_v30.py'
    assert sha(generator)==json.loads((OLD/'inputs.json').read_text())['generator_sha256']
    assert sha(OLD/'candidate/terrain.npz')=='b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36'
    assert sha(B/'candidate/terrain.npz')=='dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c'
    assert sha(B/'candidate/plane.npy')==sha(OLD/'candidate/plane.npy')=='768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0'
    h=np.load(B/'candidate/terrain.npz')['heights'];base=np.load(OLD/'candidate/terrain.npz')['heights']
    changed=h!=base;cells=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]
    tiles=[]
    for b in range(32):
        for a in range(32):
            # Includes generator's 8 px filter padding and all overlapping native cells.
            xmin,xmax=384*a-72,384*a+456
            zmax,zmin=12288-384*b+72,12288-384*b-456
            c0,c1=max(0,int(np.floor(xmin/6))),min(2047,int(np.ceil(xmax/6)))
            r0,r1=max(0,int(np.floor((12282-zmax)/6))),min(2047,int(np.ceil((12282-zmin)/6)))
            if cells[r0:r1,c0:c1].any():tiles.append((a,b))
    assert tiles and len(tiles)<1024 and not (B/'surface').exists()
    args=[sys.executable,str(generator),str(B/'candidate/terrain.npz'),str(B/'surface'),'--tiles',';'.join(f'{a},{b}' for a,b in tiles),'--workers','4','--bed-tone','depth-all','--bed-surface','gravel','--shore-ring','flowing','--landcover','smooth','--landcover-sigma','1.0','--water-plane',str(B/'candidate/plane.npy'),'--water-plane-sha256',sha(B/'candidate/plane.npy')]
    with (B/'surface-generation.log').open('w') as log:
        result=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT)
    assert result.returncode==0
    spec=importlib.util.spec_from_file_location('surface_consumer',OLD/'compile_and_verify_surface.py');consumer=importlib.util.module_from_spec(spec);spec.loader.exec_module(consumer)
    consumer.B=B;consumer.T=B/'candidate/terrain.npz';consumer.P=B/'candidate/plane.npy';consumer.OLD=OLD/'surface/layers';consumer.MASK=consumer.OLD;consumer.H=h.astype(float);consumer.F=np.load(consumer.P)
    (B/'decoded').mkdir(exist_ok=False)
    with ThreadPoolExecutor(max_workers=4) as ex:reports=list(ex.map(consumer.process,tiles))
    overlap_count=0;bad=[]
    selected=set(tiles)
    for prefix,suffix in [('s','lco'),('m','lca')]:
        for b in range(32):
            for a in range(32):
                for da,db in [(1,0),(0,1)]:
                    other=(a+da,b+db)
                    if other[0]>=32 or other[1]>=32 or ((a,b) not in selected and other not in selected):continue
                    def load(ab):
                        aa,bb=ab;folder=B/'surface/layers' if ab in selected else OLD/'surface/layers'
                        return np.array(Image.open(folder/f'{prefix}_{aa:03d}_{bb:03d}_{suffix}.png'))
                    one,two=load((a,b)),load(other)
                    left,right=(one[:,384:],two[:,:128]) if da else (one[384:],two[:128])
                    if not np.array_equal(left,right):bad.append([prefix,a,b,da,db,int(np.count_nonzero(left!=right))])
                    overlap_count+=1
    totals={k:sum(q[k] for q in reports) for k in ('pixels','wet_pixels','source_wet_not_gravel','compiled_interior_non_gravel','compiled_wet_non_gravel','satellite_changed_pixels','mask_changed_pixels')}
    gates=dict(all_selected_tiles=len(reports)==len(tiles),source_wet_gravel=totals['source_wet_not_gravel']==0,compiled_interior_gravel=totals['compiled_interior_non_gravel']==0,alpha=all(q['source_alpha_exact'] for q in reports),palette=all(q['valid_mask_palette'] for q in reports),overlap_exact=not bad,negative=any(q['negative_control'] for q in reports) and all(q['negative_control'] is not False for q in reports))
    out=dict(status='PASS_AFFECTED_SURFACE' if all(gates.values()) else 'FAIL_AFFECTED_SURFACE',gates=gates,tiles=tiles,counts=totals,overlaps=overlap_count,bad_overlaps=bad,files=reports,terrain_sha256=sha(consumer.T),generator_sha256=sha(generator),baseline_surface_report_sha256=sha(OLD/'surface-verification.json'),unchanged_tile_proof='All four vertices of every native cell in each excluded padded tile are unchanged; semantic metadata, P/F, generator and options identical.',seconds=time.monotonic()-started)
    (B/'surface-verification.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='files'},indent=2));assert all(gates.values())
if __name__=='__main__':main()
