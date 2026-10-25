"""Check the centring used by actual ODOLs, plus a false removal negative."""
from pathlib import Path
import copy,hashlib,json,sys
import numpy as np
import shapely
from shapely.geometry import Polygon,box
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'tools/terrain'),str(ROOT/'tools/water')]
from verify_channel_reaches_v30 import retained_pond_faces,actual_reach_geometry
import engine_water_model as ewm
FIT=Path('E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2')
m=json.loads((FIT/'water/pieces.json').read_text());axes=json.loads((FIT/'axes.json').read_text())
removed={tuple(rc) for reach in axes.values() for rc in reach['removed_cells']}
domain=shapely.union_all([box(c*6,12282-(r+1)*6,(c+1)*6,12282-r*6) for r,c in removed])
actual=retained_pond_faces(FIT,m,domain);names=sorted({p[2] for p in actual});reports=[]
models={x['name']:x for x in m['model_list']}
for path in names:
    name=Path(path.replace('\\','/')).stem
    p=FIT/'water/temp/baltic_water_v30'/f'{name}.p3d';o=ewm.ODOL.from_file(str(p))
    lod=next(l for l in o.lods if 2.9e15<l.resolution<3.1e15)
    center=o.model_info.bounding_center;cv=np.array([center.x,center.y,center.z])
    v=np.array([(p.x,p.y,p.z) for p in lod.vertices])+cv
    poly=shapely.union_all([Polygon(v[f.vertex_indices][:,[0,2]]) for f in lod.faces])
    poses=[p for p in m['poses'] if p['model']==path]
    errors=[]
    for pose in poses:
        ox,oy,oz=pose['origin'];b=models[name]['bounds_rel']
        if not box(ox+b[0],oz+b[1],ox+b[2],oz+b[3]).intersects(domain):continue
        source=shapely.union_all([p[0] for p in retained_pond_faces(FIT,dict(m,poses=[pose]),box(ox+b[0],oz+b[1],ox+b[2],oz+b[3]))])
        native=shapely.transform(poly,lambda a:a+np.array([ox,oz]))
        errors.append(native.hausdorff_distance(source))
    assert errors and max(errors)<1e-5 and np.max(np.abs(v[:,1]))<1e-6
    reports.append(dict(model=name,compiled_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),max_geometry_error_m=max(errors),poses=len(errors)))
# Reinsert an actual retained model over one declared removed cell.
wrong=copy.deepcopy(m)
pose=next(p for p in wrong['poses'] if p['model']=='baltic_water_v30\\pilot_00001.p3d')
pose['origin'][2]=7086
pieces=[ewm.Piece(p['type'],p['matrix']) for reach in axes.values() for p in reach['pieces']]
t=np.load('E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/wave-banks-r1/terrain_wave_banks.npz')
negative=actual_reach_geometry(t,FIT,wrong,axes,pieces)
assert negative['removed_centers_still_under_pond']>0
stage=json.loads((FIT/'package-stage.json').read_text())
o=ewm.ODOL.from_file(str(FIT/'water/temp/baltic_water_v30/pilot_00001.p3d'))
lod=next(l for l in o.lods if 2.9e15<l.resolution<3.1e15)
world=np.asarray([(p.x,p.y,p.z) for p in lod.vertices])+np.asarray(stage['new_wrp_matrix'][9:])
native=shapely.union_all([Polygon(world[f.vertex_indices][:,[0,2]]) for f in lod.faces])
native_gap_points=[dict(x=x,z=z,covered=bool(native.covers(shapely.Point(x,z))))
                   for x,z in [(2207.64988128585,7080.7002374283),(2207.5,7080.5)]]
assert all(p['covered'] for p in native_gap_points)
report=dict(status='PASS_COMPILED_RETAINED_FACES',models=reports,native_gap_points=native_gap_points,
            undeleted_pond_negative_rejected=True,negative_centers=negative['remaining_pond_centers'],
            limits=['ODOL centre corrected against authored origins; WRP float translations have separate sub-mm rounding.',
                    'Only retained models touching removed cells; no global visual or wave assertion.'])
(OUT/'compiled-face-verification-r2.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],models=len(reports),max_error_m=max(p['max_geometry_error_m'] for p in reports),negative_centers=len(negative['remaining_pond_centers'])),indent=1))
