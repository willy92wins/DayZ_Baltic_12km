from __future__ import annotations
import hashlib, json, time
from pathlib import Path
import numpy as np
from shapely.geometry import box, shape
from shapely.ops import unary_union

G = Path(r'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010')
AUDIT = G/'unknown-p-audit'/'unknown-p-audit.json'
CORRIDORS = Path(r'E:\DayZ-Baltic-Build\v30-v11\06-evidence\corridors.geojson')
WATER = Path(r'E:\DayZ-Baltic-Build\v30-v11\design\water_v3.geojson')
CLASS_NPZ = G/'build-focal'/'candidate'/'terrain.npz'
BUILD_09 = Path(r'E:\DayZ-Baltic-Build\v30-v11\09\build.json')
BUILD_13 = Path(r'E:\DayZ-Baltic-Build\v30-v11\13\build.json')
NATIVE = G/'build-selected'/'native-snapshot.log'
W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\codex-handoff-review-74f290')
COMMON = W/'tools'/'terrain'/'v30_common.py'
WATER_BUILDER = W/'tools'/'terrain'/'build_v30_water.py'
PIECE_BUILDER = W/'tools'/'water'/'build_water_pieces_v30.py'
MISSION_INIT = G/'build-focal'/'missions'/'BalticEV94FocalBankV1.BalticTrial'/'init.c'
STAGE = G/'build-focal'/'stage.json'
DEPLOY = G/'build-focal'/'deploy.json'
OPRW = G/'build-focal'/'op_rw_verification.json'
WATER_PBO = Path(r'P:\Mods\@DayZ_Baltic_EV94_FocalBankPreviewV1\Addons\baltic_water_v30.pbo')
CONTEXT = G/'unknown-p-audit'/'corridor-domain-context.json'
OUT = G/'unknown-p-audit'/'current-water-polygon-context.json'
SCRIPT = Path(__file__).resolve()
CELL=6.0; Z0=12282.0
TARGETS=('Narva_23','Luga_0')

def sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()

def read_features(path: Path, key: str):
    d=json.loads(path.read_text(encoding='utf-8'))
    return d, {f['properties'].get(key):f for f in d['features']}

def make_cell_patch(r:int,c:int,corridor):
    # Grid X increases with column; geographic Z decreases with row.
    return corridor.intersection(box(c*CELL, Z0-(r+1)*CELL, (c+1)*CELL, Z0-r*CELL))

def main():
    t0=time.perf_counter()
    paths=[SCRIPT,AUDIT,CORRIDORS,WATER,CLASS_NPZ,BUILD_09,BUILD_13,NATIVE,COMMON,WATER_BUILDER,PIECE_BUILDER,MISSION_INIT,STAGE,DEPLOY,OPRW,WATER_PBO,CONTEXT]
    start={str(p):sha(p) for p in paths}
    audit=json.loads(AUDIT.read_text(encoding='utf-8'))
    context=json.loads(CONTEXT.read_text(encoding='utf-8'))
    _,corridor_features=read_features(CORRIDORS,'river')
    _,water_features=read_features(WATER,'id')
    with np.load(CLASS_NPZ) as d:
        cls=d['cls'].copy(); level=d['level'].copy(); heights=d['heights'].copy()
    sea_lines=[line.strip() for line in NATIVE.read_text(encoding='utf-8').splitlines() if line.startswith('SEA;')]
    if len(sea_lines)!=1: raise RuntimeError(f'expected one native SEA line, got {len(sea_lines)}')
    sea=[float(x) for x in sea_lines[0].split(';')[1:]]
    build09=json.loads(BUILD_09.read_text(encoding='utf-8'))
    build13=json.loads(BUILD_13.read_text(encoding='utf-8'))
    stage=json.loads(STAGE.read_text(encoding='utf-8'))
    deploy=json.loads(DEPLOY.read_text(encoding='utf-8'))
    oprw=json.loads(OPRW.read_text(encoding='utf-8'))
    if stage.get('terrain_sha256')!=sha(CLASS_NPZ) or not stage.get('objects_and_materials_exact'):
        raise RuntimeError('EV94 terrain/stage identity does not match current candidate NPZ')
    if deploy.get('files',{}).get('baltic_water_v30.pbo')!=sha(WATER_PBO) or not deploy.get('water_pbo_exact') or not oprw.get('water_pbo_exact_to_baseline'):
        raise RuntimeError('EV94 water PBO is not proven exact to staged baseline')
    outputs={}
    for name in TARGETS:
        corridor=shape(corridor_features[name]['geometry'])
        water_feature=water_features[name]
        water=shape(water_feature['geometry'])
        records=audit['results'][name]['physical']['cells']
        patches=[]; cells=[]
        for raw in records.values():
            r,c=int(raw['row']),int(raw['col'])
            unknown=sum(float(t['unknown_area_m2']) for t in raw['triangles'].values())
            if unknown<=0: continue
            patch=make_cell_patch(r,c,corridor)
            if abs(patch.area-unknown)>2e-7:
                raise RuntimeError(f'corridor patch/census area mismatch {name} {(r,c)} {patch.area} vs {unknown}')
            inside=patch.intersection(water)
            outside=patch.difference(water)
            inside_bands={str(d):inside.intersection(water.buffer(-d)).area for d in (0.0,3.0,6.0,12.0,20.0)}
            # Exterior distances characterize whether the P-unknown patch is central to, near an edge of,
            # or outside the current authoritative water polygon. These are geometric bands only.
            outside_bands={str(d):outside.intersection(water.buffer(d)).area for d in (0.0,3.0,6.0,12.0,20.0)}
            corners=[(r,c),(r,c+1),(r+1,c),(r+1,c+1)]
            classes=[int(cls[y,x]) for y,x in corners]
            levels=[float(level[y,x]) for y,x in corners]
            ground=[float(heights[y,x]) for y,x in corners]
            cells.append({'rc':[r,c],'unknown_area_m2':unknown,'water_polygon_inside_m2':inside.area,
                          'outside_current_water_polygon_m2':outside.area,
                          'centroid_xy_m':[patch.centroid.x,patch.centroid.y],
                          'centroid_to_water_polygon_boundary_m':patch.centroid.distance(water.boundary),
                          'inside_area_at_least_distance_from_boundary_m2':inside_bands,
                          'outside_area_within_distance_of_water_polygon_m2':outside_bands,
                          'corner_class_1_to_3':classes,'corner_levels_m':levels,
                          'corner_ground_heights_EV94_m':ground,
                          'class_1_corner_count':classes.count(1),'class_3_corner_count':classes.count(3),
                          'minimum_nominal_surface_minus_ground_m':min(levels[i]-ground[i] for i in range(4))})
            patches.append(patch)
        unknown_geom=unary_union(patches)
        inside=unknown_geom.intersection(water); outside=unknown_geom.difference(water)
        in_bands={str(d):inside.intersection(water.buffer(-d)).area for d in (0.0,3.0,6.0,12.0,20.0)}
        out_bands={str(d):outside.intersection(water.buffer(d)).area for d in (0.0,3.0,6.0,12.0,20.0)}
        area=sum(c['unknown_area_m2'] for c in cells)
        width=water_feature['properties']
        outputs[name]={
            'corridor_feature_id':corridor_features[name]['properties'].get('id',corridor_features[name]['properties'].get('river')),
            'water_design_feature_properties':width,
            'unknown_cell_count':len(cells),'unknown_area_m2':area,
            'current_EV94_ground_height_range_m':[min(y for c in cells for y in c['corner_ground_heights_EV94_m']),max(y for c in cells for y in c['corner_ground_heights_EV94_m'])],
            'current_EV94_level_range_m':[min(y for c in cells for y in c['corner_levels_m']),max(y for c in cells for y in c['corner_levels_m'])],
            'corner_class_counts':{'class_1_sea':sum(c['class_1_corner_count'] for c in cells),'class_3_navigable':sum(c['class_3_corner_count'] for c in cells)},
            'minimum_level_minus_ground_m_across_cell_corners':min(c['minimum_nominal_surface_minus_ground_m'] for c in cells),
            'current_water_design_polygon_area_m2':water.area,
            'unknown_inside_current_water_polygon_m2':inside.area,
            'unknown_outside_current_water_polygon_m2':outside.area,
            'inside_area_at_least_distance_from_polygon_boundary_m2':in_bands,
            'outside_area_within_distance_of_polygon_m2':out_bands,
            'inside_area_fraction':inside.area/area if area else None,
            'distance_method':'exact Shapely polygon intersections; buffer(-d) is inward distance band; no raster-center approximation',
            'cells':cells,
        }
    end={str(p):sha(p) for p in paths}
    if start!=end: raise RuntimeError('readset changed during water-polygon context pass')
    report={
      'schema':'ev94.current-water-design-polygon-context.v1','status':'COMPLETE_CONTEXT_ONLY',
      'readset_start':start,'readset_end':end,'readset_unchanged':start==end,
      'source_provenance':{
        'analysis_script_path':str(SCRIPT),'analysis_script_sha256':sha(SCRIPT),
        'water_design_geojson_sha256':sha(WATER),
        'build09_input_water_design_sha256':build09.get('inputs',{}).get(str(WATER)),
        'build13_input_water_design_sha256':build13.get('inputs',{}).get(str(WATER)),
        'water_design_hash_pinned_by_both_build_records':build09.get('inputs',{}).get(str(WATER))==sha(WATER)==build13.get('inputs',{}).get(str(WATER)),
        'corridor_geojson_sha256':sha(CORRIDORS),'unknown_face_audit_sha256':sha(AUDIT),
        'current_EV94_candidate_terrain_npz_path':str(CLASS_NPZ),'current_EV94_candidate_terrain_npz_sha256':sha(CLASS_NPZ),
        'native_sea_record_from_EV93_selected_snapshot':{'raw':sea_lines[0],'min_m':sea[0],'max_m':sea[1],'nominal_m':sea[2],'wave_max_m':sea[3]},
        'native_snapshot_sha256':sha(NATIVE),
        'ev94_stage_json_sha256':sha(STAGE),'ev94_deploy_json_sha256':sha(DEPLOY),'ev94_oprw_verification_sha256':sha(OPRW),
        'ev94_water_pbo_path':str(WATER_PBO),'ev94_water_pbo_sha256':sha(WATER_PBO),
        'mission_init_path':str(MISSION_INIT),'mission_init_sha256':sha(MISSION_INIT),
        'water_source_builder_sha256':sha(WATER_BUILDER),'water_piece_builder_sha256':sha(PIECE_BUILDER),'v30_common_sha256':sha(COMMON),
        'native_scope_note':'Native sea tuple is an observed EV93-selected baseline snapshot; the EV94 focal mission contains the same SEA sampling calls, but no fresh EV94 runtime reading at these corridors was made.'
      },
      'interpretation_limits':[
        'The water_v3 polygons are the current source design features pinned by the v30-v11 builds, not a runtime water readback.',
        'Unknown P remains unknown: geometric overlap with a design water polygon and class-1/3 terrain metadata do not populate P or establish engine-visible coverage/depth.',
        'Inside/outside and distance bands classify corridor cells relative to current water polygon boundaries; they do not define a legal shoreline or exact river centerline.',
        'Sea level values are reported from an existing native snapshot; no live engine/process was launched for this audit.'
      ],
      'results':outputs,'elapsed_seconds':time.perf_counter()-t0
    }
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'output':str(OUT),'output_sha256':sha(OUT),'water_polygon_pinned':report['source_provenance']['water_design_hash_pinned_by_both_build_records'],'native_sea':report['source_provenance']['native_sea_record_from_EV93_selected_snapshot'],'results':{k:{'unknown_area_m2':v['unknown_area_m2'],'inside_water_polygon_m2':v['unknown_inside_current_water_polygon_m2'],'outside_water_polygon_m2':v['unknown_outside_current_water_polygon_m2'],'inside_fraction':v['inside_area_fraction'],'inside_distances_m2':v['inside_area_at_least_distance_from_polygon_boundary_m2'],'outside_distances_m2':v['outside_area_within_distance_of_polygon_m2']} for k,v in outputs.items()},'elapsed_seconds':report['elapsed_seconds']},indent=2))

if __name__=='__main__': main()
