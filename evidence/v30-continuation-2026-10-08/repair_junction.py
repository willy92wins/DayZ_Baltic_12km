"""Fill one reproduced gap inside an already wet native triangle.

No authored placement, terrain, level, class or other water model changes. Build a
fresh source snapshot; compile just the changed model, then preserve PBO entries.
"""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import sys
import numpy as np
import shapely
from shapely.geometry import Polygon, box

ROOT=Path(__file__).resolve().parents[2]
OUT=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2')
FIT=Path('E:/DayZ-Baltic-Build/v30-v11/24')
sys.path[:0]=[str(ROOT/'tools/terrain'),str(ROOT/'tools/water'),str(ROOT/'tools/navigation')]
from verify_channel_reaches_v30 import retained_pond_faces
from water_mesh import write_water_mesh
from v30_common import tri_sample
import engine_water_model as ewm

sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest=json.loads((FIT/'water/pieces.json').read_text())
assert sha(FIT/'water/pieces.json')=='b9effd625a36cae7c7918413db2654f9b6b9997281b0d9f3135684b4d44b65e9'
axes=json.loads((FIT/'axes.json').read_text())
t=np.load('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/wave-banks-r1/terrain_wave_banks.npz')
triangle=Polygon([(2202,7086),(2208,7086),(2208,7080)])
assert all(t['cls'][r,c]>0 for r,c in [(866,367),(866,368),(867,368)])
actual=retained_pond_faces(FIT,manifest,triangle)
polys=[p[0] for p in actual]
for reach in axes.values():
    for p in reach['pieces']:
        piece=ewm.Piece(p['type'],p['matrix'])
        polys.extend(Polygon(piece.w[f][:,[0,2]]) for f in piece.faces if Polygon(piece.w[f][:,[0,2]]).area>1e-9)
missing=triangle.difference(shapely.union_all(polys))
assert 1.81<missing.area<1.82,missing.area
name='pilot_00001'
pose=next(p for p in manifest['poses'] if p['model']==f'baltic_water_v30\\{name}.p3d')
assert sum(p['model']==pose['model'] for p in manifest['poses'])==1
old_faces=retained_pond_faces(FIT,manifest,box(2201,7073,2209,7081))
own=shapely.union_all([p[0] for p in old_faces if p[2]==pose['model']])
assert abs(own.area-36)<1e-7 and abs(pose['origin'][1]-1.45)<1e-9
# A clipped buffer left the exact terrain diagonal exposed after float32 WRP
# translation. Retain its 1 cm overlap on both sides; verify every support is wet.
extension=missing.buffer(.01,join_style='mitre')
new=own.union(extension)
assert new.is_valid and 1.81<new.area-own.area<2.1 and own.difference(new).area<1e-9
coords=shapely.get_coordinates(extension)
depth=1.45-tri_sample(t['heights'].astype(float),coords[:,0],coords[:,1])
assert depth.min()>.09
OUT.mkdir(exist_ok=False)
shutil.copyfile(FIT/'axes.json',OUT/'axes.json')
src=OUT/'water/source/baltic_water_v30'
shutil.copytree(FIT/'water/source/baltic_water_v30',src)
ox,_,oz=pose['origin']
rep=write_water_mesh(new,str(src/f'{name}.p3d'),(ox,oz),uv_local=True)
a,b,c,d=new.bounds
rep.update(name=name,sha256=sha(src/f'{name}.p3d'),bounds_rel=[a-ox,b-oz,c-ox,d-oz])
before=next(p for p in manifest['model_list'] if p['name']==name)
manifest['model_list']=[rep if p['name']==name else p for p in manifest['model_list']]
pose['area_m2']=round(new.area,3)
manifest['triangles']+=rep['triangles']-before['triangles']
(OUT/'water/pieces.json').write_text(json.dumps(manifest,indent=1)+'\n')
# Isolated one-model addon for Binarize; no existing source or PBO overwritten.
compile_src=OUT/'compile/source/baltic_water_v30'
compile_src.mkdir(parents=True)
for filename in (f'{name}.p3d','config.cpp','$PBOPREFIX$'):
    shutil.copyfile(src/filename,compile_src/filename)
report=dict(status='LOCAL_WATER_FACE_CANDIDATE',source_manifest_sha256=sha(FIT/'water/pieces.json'),
            changed_model=name,old_model=before,new_model=rep,old_area_m2=own.area,
            new_area_m2=new.area,filled_gap_m2=missing.area,patch=shapely.to_geojson(extension),
            nominal_depth_min_m=float(depth.min()),terrain_changed=False,world_restaging_required=True,
            limits=['Projected coverage only until compiled and replayed in engine.',
                    'Local 1.45 m pond level retained; no assertion of maximum wave clearance.'])
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('old_model','new_model','patch')},indent=1))
