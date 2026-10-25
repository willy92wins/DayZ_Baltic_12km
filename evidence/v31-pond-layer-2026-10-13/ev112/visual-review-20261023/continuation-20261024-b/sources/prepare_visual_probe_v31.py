"""Create fixed server probe points from saved pilot surfaces and merged terrain.

Both original endpoints are mandatory; sampling does not shorten the accepted
reach. Tests wet centre, both dry banks, every chunk seam, native terrain and the
approved seaward Narva cut. No verdict on client walking or appearance.
"""
import argparse,hashlib,json,shutil,sys
from collections import Counter
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from streambed_kit_v31 import tri_h


def triangles(grid):
    return np.concatenate((np.stack((grid[:-1,:-1],grid[1:,:-1],grid[1:,1:]),-2).reshape(-1,3,3),
                           np.stack((grid[:-1,:-1],grid[1:,1:],grid[:-1,1:]),-2).reshape(-1,3,3)))


def height(tris,q):
    t=tris; a=t[:,0][:,[0,2]];u=t[:,1][:,[0,2]]-a;v=t[:,2][:,[0,2]]-a;r=np.asarray(q)-a
    det=u[:,0]*v[:,1]-u[:,1]*v[:,0]
    s=(r[:,0]*v[:,1]-r[:,1]*v[:,0])/det;k=(u[:,0]*r[:,1]-u[:,1]*r[:,0])/det
    inside=(s>=-1e-7)&(k>=-1e-7)&(s+k<=1+1e-7)
    values=t[:,0,1]+s*(t[:,1,1]-t[:,0,1])+k*(t[:,2,1]-t[:,0,1])
    return float(values[inside].max()) if inside.any() else None


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('build');ap.add_argument('pilot');ap.add_argument('merged');ap.add_argument('output');a=ap.parse_args()
    B=Path(a.build);P=Path(a.pilot);M=Path(a.merged);out=Path(a.output);assert not out.exists();out.mkdir(parents=True)
    H=np.load(M/'terrain-buried.npz')['heights'];base=np.load(B/'water-fix-b/terrain.npz')['heights']
    author=json.loads((P/'author-report.json').read_text());points=[];diagnostics=[]
    def add(q,kind,**kw):
        q=np.round(q,6);p=dict(id=len(points),kind=kind,x=float(q[0]),z=float(q[1]),ground=float(tri_h(H,q[0],q[1])),**kw);points.append(p);return p
    for site in author['sites']:
        sid=site['site'];z=np.load(P/(sid+'-surfaces.npz'));bed=triangles(z['bed']);wet=triangles(z['water']);axis=z['axis'];station=z['station']
        def pilot(q,kind,expect):
            by=height(bed,q);wy=height(wet,q);p=add(q,kind,site=sid,expect=expect,bed=by,water_ext=None if wy is None else wy-.25)
            assert by is not None,('outside saved bed',sid,q)
            if expect=='wet':
                assert wy is not None and wy-.25>p['ground']+.1,('endpoint or wet point buried by native ground',p)
                if by>=wy-.25:diagnostics.append(dict(id=p['id'],site=sid,issue='bed_not_below_water_road',bed=by,water_ext=wy-.25))
            else:assert wy is None,('dry control inside water',p)
            p['collision_pilot']=by>p['ground']+.03
        for q in site['original_raw_endpoints']:pilot(q,'original_endpoint','wet')
        for i in range(6,len(station)-6,4):
            centre=z['water'][i].mean(0)[[0,2]];pilot(centre,'centre','wet')
            # Named grid columns nearest +/-6m, well beyond the 2.25m water edge.
            b=z['bed'][i];d=np.linalg.norm(b[:,[0,2]]-centre,axis=1);mid=len(b)//2
            for inds in (np.arange(mid),np.arange(mid+1,len(b))):
                j=inds[np.argmin(np.abs(d[inds]-6))];pilot(b[j,[0,2]],'dry_bank','dry')
        for i in range(12,len(station)-1,12):
            for offset in (-.05,0,.05):
                st=station[i]+offset;q=np.array([np.interp(st,station,axis[:,dim]) for dim in (0,1)])
                pilot(q,'chunk_seam','wet')
    # Native relief extremes per 768m tile plus a fixed seed sample, not only attractive sites.
    globalH=np.load(B/'general-relief-20261023-c/terrain.npz');changed=globalH['v31_relief_general'];delta=np.abs(H-base)
    selected=set()
    for r in range(0,2048,128):
        for c in range(0,2048,128):
            sl=np.s_[r:r+128,c:c+128];m=changed[sl]
            if m.any():
                local=np.where(m,delta[sl],-1);rr,cc=np.unravel_index(np.argmax(local),local.shape);selected.add((r+rr,c+cc))
    candidates=np.argwhere(changed);rng=np.random.default_rng(11224)
    selected.update(map(tuple,candidates[rng.choice(len(candidates),128,replace=False)]))
    for r,c in sorted(selected):add([c*6,12282-r*6],'global_relief',expect='ground')
    for x in (2400,2415,2430,2445,2460):
        for zz in (6944.09,6945,6948,6954,6960):add([x,zz],'narva_seaward',expect='sea')
    plane=np.load(M/'bury-work/fp0/footprint.npz')['plane']
    for q in ((2400,7000),(2430,7020),(2410,7040)):
        p=add(q,'sea_reference',expect='sea');r=int((12282-q[1])//6);c=int(q[0]//6)
        assert p['ground']<-.5 and not np.isfinite(plane[r,c]),('sea control must be deep and pond-free',p)
    for q in ((2388,6942),(2468,6942),(2430,6936)):add(q,'narva_support',expect='ground')
    mission=out/'BalticVisualProbeV1.BalticTrial';mission.mkdir()
    source=HERE.parent.parent/'missions/BalticVisualProbeV1.BalticTrial/init.c';shutil.copy2(source,mission/'init.c')
    text=''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in points);(mission/'points.csv').write_text(text,encoding='ascii')
    result=dict(schema='ev112-visual-probe-v1',points=points,diagnostics=diagnostics,counts=dict(Counter(p['kind'] for p in points)),
                inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (M/'terrain-buried.npz',P/'packed/baltic_stream_pilot.pbo',mission/'points.csv',mission/'init.c')},
                scope='Dedicated-server terrain, water, roadway, RV Geometry and Bullet BUILDING queries. Client walking and appearance are separate.')
    (out/'points.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(points=len(points),counts=result['counts'],diagnostics=diagnostics),indent=2))


if __name__=='__main__':main()
