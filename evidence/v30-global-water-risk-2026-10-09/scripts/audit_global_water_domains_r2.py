"""Audit every compiled pond footprint against frozen native-cell planes, including tile halos."""
from pathlib import Path
from collections import Counter
import json,hashlib,sys,time
import argparse
import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.affinity import translate
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09';B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
B8=Path('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008');B9=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
F=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water'),str(W/'tools/playtest')]
from wrp0wzd import read
from attach_navmesh import read_pbo
from engine_water_model import ODOL
from v30_common import cell_planes
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('--halo-fix',action='store_true');args=ap.parse_args()
H=B/'halo-fix-v3'
water=Path('P:/Mods/@DayZ_Baltic_HaloFixV2/Addons/baltic_water_v30.pbo') if args.halo_fix else Path('P:/Mods/@DayZ_Baltic_ValleySmoothC1R3P/Addons/baltic_water_v30.pbo')
expected=json.loads((E/'halo-r2-deploy.json').read_text())['files']['baltic_water_v30.pbo'] if args.halo_fix else '542bd4e85e9f82d9ef373386371168c9b489c0794e3f4bd4773709c680c4b068'
assert sha(water)==expected
_,_,packed=read_pbo(water)
worldpath=B9/'world-c1r3p/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
world=read(worldpath)
old=json.loads((F/'water/pieces.json').read_text());author=json.loads((W/'evidence/v30-curved-channel-pilot-2026-10-08/flat-water-authoring.json').read_text())
poses=[p for p in old['poses'] if p not in author['removed_poses']]+author['new_poses']
objects=[o for o in world['objects'] if o['name'].startswith('baltic_water_v30')]
assert [o['name'] for o in objects]==[p['model'] for p in poses]
if args.halo_fix:
    previous={o['id']:p for o,p in zip(objects,poses)}
    changes={r['object_id']:r for r in json.loads((E/'halo-fix-r2-authoring.json').read_text())['changes']}
    worldpath=H/'world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
    objects=[o for o in read(worldpath)['objects'] if o['name'].startswith('baltic_water_v30')]
    poses=[dict(previous[o['id']],model=o['name']) for o in objects]
active_models={p['model'].split('\\')[-1] for p in poses}
src=Path('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz')
t=dict(np.load(src));sea_cut=float(old['sea_cutoff_m'])
planes=cell_planes(t['cls'],t['level'],sea_cut=sea_cut);bands=np.where(np.isfinite(planes),np.rint(np.nan_to_num(planes)/.025),-1).astype(int)
cache={}
cachepath=B/'compiled-model-domains.json'
if cachepath.exists():
    for name,entry in json.loads(cachepath.read_text()).items():
        if name not in active_models:continue
        assert hashlib.sha256(packed[name]).hexdigest()==entry['sha256']
        cache[name]=dict(entry,geom=shapely.from_wkb(entry['wkb']))
rows=[];tiny_area=0.;tiny_count=0;count=0;start=time.time()
for obj,pose in zip(objects,poses):
    name=pose['model'].split('\\')[-1]
    if name not in cache:
        p=(H/'water/temp/baltic_water_v30' if args.halo_fix else B8/'stitched-water/water/temp/baltic_water_v30')/name
        assert p.read_bytes()==packed[name]
        od=ODOL.from_file(str(p));lod=min(od.lods,key=lambda l:abs(l.resolution-3e15))
        assert abs(lod.resolution-3e15)/3e15<1e-6
        v=np.array([(q.x,q.y,q.z) for q in lod.vertices]);assert np.ptp(v[:,1])<1e-6
        geom=shapely.union_all([Polygon(v[f.vertex_indices][:,[0,2]]) for f in lod.faces])
        cache[name]=dict(wkb=shapely.to_wkb(geom,hex=True),y=float(v[0,1]),sha256=sha(p),geom=geom)
    model=cache[name];mat=np.array(obj['matrix']);assert np.max(np.abs(mat[:9].reshape(3,3)-np.eye(3)))<1e-6
    geom=translate(model['geom'],xoff=mat[9],yoff=mat[11]);level=model['y']+mat[10]
    band=int(round(level/.025));assert abs(level-band*.025)<1e-5
    xmin,zmin,xmax,zmax=geom.bounds
    cs=np.arange(max(0,int(np.floor(xmin/6))),min(2046,int(np.floor(xmax/6)))+1)
    rs=np.arange(max(0,int(np.floor((12282-zmax)/6))),min(2046,int(np.floor((12282-zmin)/6)))+1)
    cc,rr=np.meshgrid(cs,rs);cc=cc.ravel();rr=rr.ravel();bad=bands[rr,cc]!=band
    cc=cc[bad];rr=rr[bad]
    if len(cc):
        boxes=shapely.box(cc*6,12276-rr*6,cc*6+6,12282-rr*6)
        intersections=shapely.intersection(geom,boxes);areas=shapely.area(intersections)
        tiny=(areas>1e-9)&(areas<=.005);tiny_area+=float(areas[tiny].sum());tiny_count+=int(tiny.sum())
        for r,c,intersection,area in zip(rr[areas>.005],cc[areas>.005],intersections[areas>.005],areas[areas>.005]):
            b=int(bands[r,c]);rows.append(dict(object_id=obj['id'],model=name,origin=pose['origin'],row=int(r),col=int(c),level=float(level),expected_level=None if b<0 else b*.025,
                area_m2=float(area),geometry=shapely.to_geojson(intersection),cell_classes=[int(t['cls'][r,c]),int(t['cls'][r,c+1]),int(t['cls'][r+1,c]),int(t['cls'][r+1,c+1])]))
    count+=1
    if count%2000==0:print(json.dumps(dict(instances=count,models=len(cache),nontrivial_mismatched_cells=len(rows),seconds=round(time.time()-start,1))),flush=True)
suffix='halo-r2' if args.halo_fix else 'v2'
if not args.halo_fix:(B/'compiled-model-domains.json').write_text(json.dumps({k:{key:value for key,value in v.items() if key!='geom'} for k,v in cache.items()})+'\n')
(B/f'compiled-domain-discrepancies-{suffix}.json').write_text(json.dumps(rows)+'\n')
summary=dict(status='COMPLETE_COMPILED_DOMAIN_INVENTORY_NOT_RENDER_ACCEPTANCE',instances=len(objects),models=len(cache),cell_intersections=len(rows),affected_objects=len(set(r['object_id'] for r in rows)),
    total_mismatch_area_m2=sum(r['area_m2'] for r in rows),maximum_cell_mismatch_area_m2=max([r['area_m2'] for r in rows],default=0),
    no_expected_pond_cells=sum(r['expected_level'] is None for r in rows),tiny_intersections=tiny_count,tiny_area_m2=tiny_area,
    water_sha256=sha(water),world_source_sha256=sha(worldpath),frozen_terrain_sha256=sha(src),sea_cutoff_m=sea_cut,elapsed_s=time.time()-start,
    limits=['Mismatch means compiled roadway outside a frozen level cell, not automatically a defect. Local deliberate junction/flat replacements must be classified.',
    'Intersections <=0.005 m2 are inventoried separately as numerical/sliver cases, not accepted as correct.',
    'Area is summed per object and cell; overlapping objects can count the same ground more than once.'])
(E/f'compiled-domain-inventory-{suffix}.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
