"""One bounded P11 road candidate. No mutation of the integrated visual terrain."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation,distance_transform_edt,minimum_filter
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import repair_roads_v30 as repair
import verify_roads_v30 as judge
import despike_v31 as guard
import census_creases_v31 as crease

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('build');ap.add_argument('out');ap.add_argument('--collar-m',type=float,default=0);ap.add_argument('--allow-proven-dry-legacy',action='store_true');a=ap.parse_args();B=Path(a.build);out=Path(a.out);assert not out.exists()
    terrain=B/'visual-merged-20261024-b/terrain-buried.npz';fp=B/'visual-merged-20261024-b/bury-work/fp0/footprint.npz'
    prior=json.loads((B/'roads-visual-review-20261024-c/review.json').read_text());assert sha(terrain)==prior['terrain_sha256']
    data=dict(np.load(terrain));h0=data['heights'].astype(float);h=h0.copy();f=np.load(fp)
    shore=guard.shoreline_vertices(h0,fp,np.ones_like(h0,bool));pond=guard.env_vertex_plane(f['plane'])[0]
    records=guard.records_mask([str(B/'records-nonforest.json')])[0]
    fixed=data['narva']|pond|shore|(h0<.9)|records
    for key in ('v31_kit','v31_bridge_cut','v31_bridge_fill','v31_dam','v31_shore_ramp','v31_causeway','v31_continuous_pilot'):
        fixed|=binary_dilation(data[key],iterations=2)
    rr,cc=np.mgrid[:2048,:2048];fixed|=np.hypot(6*cc-10397.4,12282-6*rr-9421.9)<=60
    s,q,n,length=repair.stations(repair.road_chains()[49]);idx=np.flatnonzero((s>1640)&(s<1702))
    pts=q[idx][None,:,:]+repair.OFFSETS[:,None,None]*n[idx][None,:,:]
    ra,ca,wa=repair.bary(pts[...,0].ravel(),pts[...,1].ravel());allowed=np.zeros_like(fixed);allowed[ra,ca]=True
    dry_legacy=np.zeros_like(fixed)
    if a.allow_proven_dry_legacy:
        trial=allowed.copy()
        if a.collar_m:trial|=(distance_transform_edt(~allowed)*6<=a.collar_m)&~data['reserve']&~data['platform']
        dry_legacy=trial&data['water']&~fixed
        assert int((dry_legacy&allowed).sum())==5
        wet=np.load(B/'forest-visual-consumers-20261024-a/water1m.npy',mmap_mode='r')
        local_min=minimum_filter(h0,size=3)
        for r,c in np.argwhere(dry_legacy):
            # The whole native star: no pond cell, all 3x3 vertices above high
            # sea, and no staged kit/custom water in the enclosing 12m square.
            x,z=int(c*6),int(12282-r*6)
            dry_legacy[r,c]=not np.isfinite(f['plane'][r-1:r+1,c-1:c+1]).any() and local_min[r,c]>.9 and not wet[12288-z-6:12288-z+6,x-6:x+6].any()
        assert int((dry_legacy&allowed).sum())==5
    fixed|=data['water']&~dry_legacy
    verts,x,dmax=repair.solve_group(h,s,q,n,idx,fixed);h.ravel()[verts]=x
    collar=np.zeros_like(fixed)
    if a.collar_m:
        assert a.collar_m==36,'Only the declared 36m feasibility trial is authorized by this producer'
        # Extend only into unreserved dry terrain. Other road platforms stay
        # exact; the original 46 road vertices remain Dirichlet conditions.
        collar=(distance_transform_edt(~allowed)*6<=a.collar_m)&~allowed&~fixed&~data['reserve']&~data['platform']
        coords=np.argwhere(collar);lookup=np.full(h.shape,-1,int);lookup[collar]=np.arange(len(coords))
        rows=[];cols=[];vals=[];rhs=np.zeros(len(coords));delta=h-h0
        for i,(r,c) in enumerate(coords):
            rows.append(i);cols.append(i);vals.append(4.)
            for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                nr,nc=r+dr,c+dc;j=lookup[nr,nc]
                if j>=0:rows.append(i);cols.append(j);vals.append(-1.)
                else:rhs[i]+=delta[nr,nc]
        if len(coords):h[collar]+=spsolve(coo_matrix((vals,(rows,cols)),shape=(len(coords),len(coords))).tocsr(),rhs)
    h=h.astype(np.float32).astype(float);changed=h!=h0
    water=np.load(B/'roads-visual-review-20261024-c/water-vertices.npz')['wet'];road=judge.evaluate(h,water)
    a0=crease.angles(h0);a1=crease.angles(h);regressed={k:int((a1[k]>np.maximum(20,a0[k])+1e-4).sum()) for k in a0}
    checks=dict(outside_window_exact=not bool((changed&~(allowed|collar)).any()),protected_exact=not bool((changed&fixed).any()),
                sea_classification_exact=bool(np.array_equal(h<.75,h0<.75)),pond_corners_exact=not bool((changed&pond).any()),
                proven_legacy_stars_stay_dry=bool((minimum_filter(h,size=3)[dry_legacy]>.9).all()),
                no_regressed_sharp_edges=not any(regressed.values()),road_gate=road['status']=='PASS')
    out.mkdir(parents=True);data['heights']=h.astype(np.float32);data['v31_road_repair']=changed;np.savez_compressed(out/'terrain.npz',**data)
    report=dict(status='OFFLINE_CANDIDATE_PASS' if all(checks.values()) else 'REJECTED_NOT_INTEGRATED',checks=checks,
                changed_vertices=int(changed.sum()),allowed_vertices=int(allowed.sum()),collar_m=a.collar_m,collar_vertices=int(collar.sum()),fixed_in_window=int((allowed&fixed).sum()),
                proven_dry_legacy_vertices=int(dry_legacy.sum()),
                delta_range_m=[float((h-h0).min()),float((h-h0).max())],regressed_sharp_edges=regressed,road=road,
                terrain_input_sha256=sha(terrain),terrain_output_sha256=sha(out/'terrain.npz'),
                changes=[dict(row=int(r),col=int(c),x=int(c*6),z=int(12282-r*6),before=float(h0[r,c]),after=float(h[r,c])) for r,c in np.argwhere(changed)],
                sources={str(p):sha(p) for p in (Path(__file__),Path(repair.__file__),Path(judge.__file__),fp)},
                limits=['A bounded local feasibility trial; not integrated, rebuilt, walked or driven.',
                        'Road reserve/platform may change by P11; actual water and all listed guards remain fixed.',
                        'Only an explicit proof permits editing five legacy water-labelled vertices that are dry in the current native and staged water surfaces.'])
    (out/'review.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ('changes','sources','road')},indent=2));print(json.dumps({k:v for k,v in road.items() if k!='fail_list'}))

if __name__=='__main__':main()
