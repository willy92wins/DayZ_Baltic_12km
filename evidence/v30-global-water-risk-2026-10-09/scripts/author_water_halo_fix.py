"""Repair proven 1 cm generic tile halos and five microscopic wet seam gaps; keep terrain/levels fixed."""
from pathlib import Path
import json,sys,hashlib,shutil
import numpy as np
import shapely
from shapely.geometry import Polygon,box,Point
from shapely.ops import unary_union
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09';B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
F=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2');B8=Path('E:/DayZ-Baltic-Build/v30-water-visual-fix-20261008')
B9=Path('E:/DayZ-Baltic-Build/v30-valley-smoothing-20261008')
sys.path[:0]=[str(W/'tools/navigation'),str(W/'tools/terrain')]
from water_mesh import py3d,write_water_mesh
from v30_common import cell_planes,tri_sample
from wrp0wzd import read
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((F/'water/pieces.json').read_text());flat=json.loads((W/'evidence/v30-curved-channel-pilot-2026-10-08/flat-water-authoring.json').read_text())
poses=[p for p in old['poses'] if p not in flat['removed_poses']]+flat['new_poses']
wrp=B9/'world-c1r3p/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';world=read(wrp)
objects=[o for o in world['objects'] if o['name'].startswith('baltic_water_v30')]
assert [o['name'] for o in objects]==[p['model'] for p in poses]
byid={o['id']:(o,p) for o,p in zip(objects,poses)}
discrepancies=json.loads((B/'compiled-domain-discrepancies-v2.json').read_text())
selected={r['object_id'] for r in discrepancies if r['model'].startswith(('edge_','full_'))}
micros={}
for item in json.loads((E/'compiled-water-point-audit.json').read_text())['points']:
    if item['point']['reason']!='runtime_water_missing_below_frozen_plane':continue
    # Add a 1 mm overlap from the lower neighbouring band, only inside a 2 cm disc
    # around the measured wet point. Both sides are already intended water.
    near=min(item['near'],key=lambda p:p['origin'][1]);ident=near['id'];selected.add(ident)
    micros.setdefault(ident,[]).append((float(item['point']['x']),float(item['point']['z'])))
t=dict(np.load('E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008/r3-transition-proposal/terrain_flat.npz'))
planes=cell_planes(t['cls'],t['level'],sea_cut=float(old['sea_cutoff_m']))
terrain=B9/'candidate-c1r3p/terrain_valley.npz';h=np.load(terrain)['heights']
assert sha(terrain)=='9c3011b8af5279e807630d4e91512d2e95a434463d3523a5b4074e70bc7cc8f6'
out=B/'halo-fix-v2';source=out/'compile/source/baltic_water_v30';source.mkdir(parents=True,exist_ok=False)
for name in ('config.cpp','$PBOPREFIX$'):shutil.copyfile(F/'water/source/baltic_water_v30'/name,source/name)
changes=[]
for ident in sorted(selected):
    obj,pose=byid[ident];name=pose['model'].split('\\')[-1]
    assert name.startswith(('edge_','full_')),name
    original=F/'water/source/baltic_water_v30'/name
    assert not (B8/'stitched-water/compile/source/baltic_water_v30'/name).exists(),'Do not replace stitched visible LOD'
    with original.open('rb') as stream:mdl=py3d.P3D(stream)
    lod=min(mdl.lods,key=lambda l:abs(l.resolution-3e15));v=np.array([p.coords for p in lod.points]);assert np.max(np.abs(v[:,1]))<1e-7
    v+=np.array(pose['origin']);geom=unary_union([Polygon(v[[q.point_index for q in f.vertices]][:,[0,2]]) for f in lod.faces])
    x0,z0,x1,z1=geom.bounds
    cells=[];wet=[]
    for row in range(max(0,int((12282-z1)//6)-1),min(2046,int((12282-z0)//6)+1)+1):
        for col in range(max(0,int(x0//6)-1),min(2046,int(x1//6)+1)+1):
            plane=planes[row,col]
            if not np.isfinite(plane):continue
            cell=box(col*6,12276-row*6,col*6+6,12282-row*6);wet.append(cell)
            if abs(plane-pose['origin'][1])<1e-5:cells.append(cell)
    domain=unary_union(cells);corrected=geom.intersection(domain)
    removed=geom.difference(corrected)
    # This correction only removes narrow old halo strips, never cell interiors.
    if not removed.is_empty:assert removed.difference(geom.boundary.buffer(.01001)).area<1e-7,(ident,removed.area)
    assert removed.area<2.1,(ident,removed.area)
    if corrected.is_empty:
        assert ident not in micros and geom.area<2.1
        changes.append(dict(object_id=ident,old_model=name,new_model=None,origin=pose['origin'],old_geometry=shapely.to_geojson(geom),geometry=shapely.to_geojson(corrected),
            removed_m2=removed.area,added_m2=0,closed_micro_points=[],old_source_sha256=sha(original),reason='Entire old instance was a stale halo strip'))
        continue
    for x,z in micros.get(ident,[]):
        patch=corrected.buffer(.001,join_style='mitre').intersection(Point(x,z).buffer(.02)).intersection(unary_union(wet))
        coords=shapely.get_coordinates(patch)
        assert len(coords) and np.min(pose['origin'][1]-tri_sample(h,coords[:,0],coords[:,1]))>.05
        corrected=corrected.union(patch)
        assert corrected.contains(Point(x,z)),(ident,x,z)
    added=corrected.difference(geom)
    assert added.area<.001,(ident,added.area)
    if corrected.symmetric_difference(geom).area<1e-8:continue
    newname=f'halo_{len(changes):05d}.p3d'
    rep=write_water_mesh(corrected,source/newname,(pose['origin'][0],pose['origin'][2]),uv_local=True)
    changes.append(dict(object_id=ident,old_model=name,new_model=newname,origin=pose['origin'],old_geometry=shapely.to_geojson(geom),geometry=shapely.to_geojson(corrected),
        removed_m2=removed.area,added_m2=added.area,closed_micro_points=micros.get(ident,[]),sha256=sha(source/newname),old_source_sha256=sha(original),mesh=rep))
assert sum(len(r['closed_micro_points']) for r in changes)==5
report=dict(status='HALO_FIX_AUTHORED_NOT_COMPILED',changes=changes,models=sum(r['new_model'] is not None for r in changes),removed_instances=sum(r['new_model'] is None for r in changes),
    removed_total_m2=sum(r['removed_m2'] for r in changes),added_total_m2=sum(r['added_m2'] for r in changes),
    terrain_sha256=sha(terrain),world_source_sha256=sha(wrp),old_water_sha256='542bd4e85e9f82d9ef373386371168c9b489c0794e3f4bd4773709c680c4b068',
    untouched_intentional_patch_discrepancies=sum(r['model'].startswith('patch_') for r in discrepancies),
    limits=['Only generic tile halo geometry changed; four custom patch slivers retained for separate classification.',
    'No heightfield, material, water level, stitched model or bridge edited. Full compiled/raster and historic consumer validation required.'])
(E/'halo-fix-authoring.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='changes'},indent=2))
