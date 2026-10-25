from __future__ import annotations
import hashlib, importlib.util, json, math, sys
from pathlib import Path

import numpy as np
from shapely.geometry import Point, Polygon, shape
from shapely.ops import nearest_points, unary_union

ROOT = Path(r'E:/DayZ-Baltic-Build/v30-global-bank-extension-20261010')
OUT = ROOT / 'G/wet-bank-pilot/selection.json'
SCRIPT = ROOT / 'G/wet-bank-pilot/select_wet_bank.py'
GIS = Path(r'C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe')
W = Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
R = Path(r'E:/DayZ-Baltic-Build')
EV87_PATH = R/'v30-global-strict-bank-relief-20261010/review-independent/verify_ev87.py'
INDEX_RUN = ROOT/'ev93-face-index/runs/20261010T092417Z-63d4cec3'
INDEX_BUILDER = ROOT/'ev93-face-index/build_face_index.py'
TERRAIN = ROOT/'global-operator-prototype/real-sector-preflight/focus-unit/author-run-01/candidate-terrain.npz'
EV93_BASE_TERRAIN = ROOT/'compound-selection/run-02/candidate-terrain.npz'
EV82_B_TERRAIN = R/'v30-mixed-bank-incremental-fixed-20261010/candidate/terrain.npz'
EV95_TERRAIN = ROOT/'global-operator-prototype/real-sector-preflight/ev94-rebase/slope-bound/composition-run-01/terrain.npz'
P_PATH = ROOT/'build-focal/candidate/plane.npy'
F_PATH = ROOT/'build-focal/candidate/visible-field.npy'
EV79_CONSTRAINTS = R/'v30-narva-dry-bank-relief-20261010/constraints.npz'
PRIOR_CONSTRAINTS = R/'v30-remaining-exact-dry-support-20261009/constraints.npz'
SELECTION = ROOT/'compound-selection/run-02/selection.json'
WATER_GEOJSON = R/'v30-v11/design/water_v3.geojson'
CORRIDORS = R/'v30-v11/06-evidence/corridors.geojson'
ROAD_REFERENCE = Path(r'P:/DayZ_Baltic_12km_dev/tests/regional_foundation_roads_v6/reference.npz')
BASE_WRP = R/'v30-mixed-bank-incremental-fixed-20261010/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
STAGED_WRP = ROOT/'build-focal/package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'
STAGE_JSON = ROOT/'build-focal/stage.json'

R0, C0 = 862, 1186
CELL, Z0 = 6.0, 12282.0
RIVER_ID = 'river_041'
EXPECTED = {
    TERRAIN: '30d0ed33e477846297a17e758e34a51490d54ee809e8b63ec9d69229170d15a1',
    EV93_BASE_TERRAIN: '6e27557315eb65ecc69052e1ec387304a19f37eaa4f5167ab82fb607f095461d',
    EV82_B_TERRAIN: 'f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0',
    EV95_TERRAIN: '40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a',
    P_PATH: '768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0',
    F_PATH: 'f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c',
    EV79_CONSTRAINTS: 'ad0cffd5f26fc942e17fc959236494287650b1528b728a15f4b1100da72f319c',
    PRIOR_CONSTRAINTS: '18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370',
    SELECTION: '3b22dcc381b34b8d7c3e6641d3c919658f0fe7377594a859e3d5c064cf92ba0b',
    WATER_GEOJSON: 'caa333e365c2a4511f839937a9d76a5aa157a0ef925d6ee4b5efcc4ebb38f8a9',
    CORRIDORS: '28866a8cf6ff57f2f825228046164ef939bc22bca9948eb96fe2463da46af343',
    ROAD_REFERENCE: '94ecbca61bd5ba9ba61f89b765b043676a4a65703729a0b69009ae233984a1c2',
    BASE_WRP: '3071395e2d1830f1c5c28bd84346761b5c517710e9d5f1f4ac19cd3fc1eff1f6',
    STAGED_WRP: '8bf57d622fb2f01aa491f280f9dcb8cdc9dd8a603ac18995e3e50d21e83e4cb3',
    STAGE_JSON: 'cc394869cf45f60315eea5b13a99b2f79d80135bee5ee32879b3900ecaa86610',
    INDEX_RUN/'manifest.json': 'c81bfeb9e271b35add6644ad0d66cad1093b8cf08b665d2253ba62fbfad7372c',
    INDEX_BUILDER: 'd1d3d1106bfdff7fd63f201ae042fdbd181bce92a96dddf1afc3182f694d288e',
    EV87_PATH: '964206b98f4c30c04abcb070d0e05f08a6e41edb31a24400574de2ad208fee27',
}

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024), b''): h.update(b)
    return h.hexdigest()

def load_module(name, path):
    spec=importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None: raise ImportError(path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

def jsonread(path):
    return json.loads(path.read_text(encoding='utf-8'))

def fnum(x):
    x=float(x)
    return x if math.isfinite(x) else None

def p_rc(r,c):
    return [float(c*CELL), float(Z0-r*CELL)]

def bbox_gap(q, win):
    r,c=q; r0,r1,c0,c1=win
    dr = r0-r if r<r0 else (r-(r1-1) if r>=r1 else 0)
    dc = c0-c if c<c0 else (c-(c1-1) if c>=c1 else 0)
    return int(max(dr,dc)), int(dr), int(dc)

def face_record_summary(index, kind, cell, cell_poly, model_names):
    arr=index.query_cell(*cell,kind=kind)
    rows=[]; polys=[]
    for i in range(len(arr['object_id'])):
        if arr['degenerate'][i]: continue
        tri=arr['xyz'][i]
        poly=Polygon(tri[:,[0,2]])
        if not poly.is_valid or poly.area<=0: continue
        inter=poly.intersection(cell_poly)
        area=float(inter.area)
        if area<=1e-10: continue
        polys.append(inter)
        rows.append({'object_id':int(arr['object_id'][i]),'model_id':int(arr['model_id'][i]),
          'model':model_names.get(int(arr['model_id'][i])),'face_id':int(arr['face_id'][i]),
          'overlap_area_xz_m2':area,'native_face_area_xz_m2':float(arr['area_xz'][i]),
          'plane_y_xz':arr['plane_y_xz'][i].astype(float).tolist(),
          'vertices_xyz':tri.astype(float).tolist()})
    union=unary_union(polys) if polys else Polygon()
    rows.sort(key=lambda x:(-x['overlap_area_xz_m2'],x['object_id'],x['face_id']))
    return {'bbox_candidates':int(len(arr['object_id'])),'positive_intersecting_faces':len(rows),
      'union_overlap_area_xz_m2':float(union.intersection(cell_poly).area) if not union.is_empty else 0.0,
      'face_examples_largest_first':rows[:8]}

def tri_coords(r,c,which):
    # NW, NE, SW, SE grid vertices; source split is NW-SE.
    nw=(r,c); ne=(r,c+1); sw=(r+1,c); se=(r+1,c+1)
    return (nw,ne,se) if which=='A' else (nw,se,sw)

def hinge_vertices(kind,r,c):
    if kind=='diag':
        return {'triangle_1':tri_coords(r,c,'A'),'triangle_2':tri_coords(r,c,'B'),
                'cells':[[r,c],[r,c]],'shared_edge_nodes':[[r,c],[r+1,c+1]]}
    if kind=='vertical':
        return {'triangle_1':tri_coords(r,c,'A'),'triangle_2':tri_coords(r,c+1,'B'),
                'cells':[[r,c],[r,c+1]],'shared_edge_nodes':[[r,c+1],[r+1,c+1]]}
    return {'triangle_1':tri_coords(r,c,'B'),'triangle_2':tri_coords(r+1,c,'A'),
            'cells':[[r,c],[r+1,c]],'shared_edge_nodes':[[r+1,c],[r+1,c+1]]}

def main():
    expected_inputs=[TERRAIN,EV93_BASE_TERRAIN,EV82_B_TERRAIN,EV95_TERRAIN,P_PATH,F_PATH,EV79_CONSTRAINTS,PRIOR_CONSTRAINTS,SELECTION,
      WATER_GEOJSON,CORRIDORS,ROAD_REFERENCE,BASE_WRP,STAGED_WRP,STAGE_JSON,
      INDEX_RUN/'manifest.json', INDEX_BUILDER,EV87_PATH]
    read_start={str(p):sha(p) for p in expected_inputs}
    for p,want in EXPECTED.items():
        got=read_start[str(p)]
        if got!=want: raise AssertionError(f'pin drift: {p}: {got} != {want}')

    ev87=load_module('ev87_wet_bank',EV87_PATH)
    idxmod=load_module('ev93_face_index_wet_bank',INDEX_BUILDER)
    terrain=np.load(TERRAIN,allow_pickle=False)
    h=terrain['heights']; cls=terrain['cls']; flags={k:terrain[k] for k in ('water','beach','reserve','platform','narva')}
    with np.load(EV93_BASE_TERRAIN,allow_pickle=False) as bz: hb=bz['heights']
    with np.load(EV82_B_TERRAIN,allow_pickle=False) as b2: hb82=b2['heights']
    with np.load(EV95_TERRAIN,allow_pickle=False) as ez: h95=ez['heights']
    p=np.load(P_PATH, mmap_mode='r', allow_pickle=False)
    f=np.load(F_PATH, mmap_mode='r', allow_pickle=False)
    with np.load(EV79_CONSTRAINTS,allow_pickle=False) as z:
        constraints={k:z[k] for k in ('wet_support','engineering_halo','other_fixed','fixed','allowed','narva')}
    with np.load(PRIOR_CONSTRAINTS,allow_pickle=False) as z:
        large_lake_banks=z['large_lake_banks']

    # Exact coordinate convention from EV87: N=2048, CELL=6, Z0=12282.
    x,z=p_rc(R0,C0)
    assert x==7116.0 and z==7110.0
    H3=h[R0-1:R0+2,C0:C0+3].astype(float)
    B3=hb[R0-1:R0+2,C0:C0+3].astype(float)
    B82_3=hb82[R0-1:R0+2,C0:C0+3].astype(float)
    if not np.array_equal(H3,B3) or not np.array_equal(H3,B82_3): raise AssertionError('EV94/EV93-base/EV82-B heights differ at pilot 3x3')
    P2=np.asarray(p[R0-1:R0+1,C0:C0+2],dtype=float)
    F2=np.asarray(f[R0-1:R0+1,C0:C0+2,:],dtype=float)
    h_dry=float(h[R0,C0]); h_wet=float(h[R0,C0+1])
    p_cell=float(p[R0,C0]); f_dry=float(f[R0,C0,0]); f_wet=float(f[R0,C0,1])
    dd=h_dry-f_dry; dw=h_wet-f_wet
    if not (dd>0 and dw<0): raise AssertionError(f'not an actual dry/wet edge crossing: {dd=}, {dw=}')
    t=dd/(dd-dw)
    assert abs(p_cell-5.525)<1e-6 and abs(f_dry-5.525)<1e-6 and abs(f_wet-5.525)<1e-6

    # Published design contour/source name; use geometry itself for nearest contour distance.
    water_fc=jsonread(WATER_GEOJSON)
    matches=[feat for feat in water_fc['features'] if feat.get('properties',{}).get('id')==RIVER_ID]
    if len(matches)!=1: raise AssertionError(f'expected one source feature {RIVER_ID}, found {len(matches)}')
    water_feature=matches[0]; water_geom=shape(water_feature['geometry'])
    point=Point(x,z); nearest=nearest_points(point,water_geom.boundary)[1]

    # Distances to the signed corridor geometry and nearest sampled road reference.
    corridor_doc=jsonread(CORRIDORS)
    corridor_geoms=[shape(feat['geometry']) for feat in corridor_doc['features'] if feat.get('geometry')]
    corridor_union=unary_union(corridor_geoms)
    corridor_dist=float(point.distance(corridor_union))
    with np.load(ROAD_REFERENCE,allow_pickle=False) as road:
        road_xy=road['xy']; road_delta=road_xy-np.asarray([x,z],dtype=float)
        road_d=np.linalg.norm(road_delta,axis=1); road_i=int(np.argmin(road_d))
        road_nearest={'distance_m':float(road_d[road_i]),'xy':road_xy[road_i].astype(float).tolist(),'sample_index':road_i}

    # Verify this is outside all retained selection windows; derive each window from its real source result.
    sel=jsonread(SELECTION); retained=set(sel['retained_unit_ids']); units=[u for u in sel['units'] if u['unit_id'] in retained]
    if len(units)!=499: raise AssertionError(f'retained-unit count drift: {len(units)}')
    best=None; overlaps=[]; all_windows=[]; window_result_hashes={}
    for u in units:
        artifact=Path(u['source_artifact_path'])
        if sha(artifact)!=u['source_artifact_sha256']: raise AssertionError(f'selection artifact hash drift: {artifact}')
        rec=jsonread(artifact)
        if u['origin']=='crest':
            source_result=Path(rec['source_result_path'])
            got_source=sha(source_result)
            if got_source!=rec['source_result_sha256']: raise AssertionError(f'crest source result hash drift: {source_result}')
            window_result_hashes[str(source_result)]=got_source
            qrec=jsonread(source_result)
        else:
            window_result_hashes[str(artifact)]=sha(artifact)
            qrec=rec
        win=[int(v) for v in qrec['window_rc']]
        gap,dr,dc=bbox_gap((R0,C0),win)
        item={'unit_id':u['unit_id'],'window_rc_half_open':win,'linf_gap_nodes':gap,'row_gap':dr,'col_gap':dc}
        all_windows.append(item)
        if gap==0: overlaps.append(item)
        if best is None or gap<best['linf_gap_nodes']: best=item
    if overlaps: raise AssertionError(f'hotspot overlaps retained windows: {overlaps[:3]}')

    # Compiled ODOL face index coverage of the actual shoreline cell.
    index=idxmod.FaceRangeIndex(INDEX_RUN)
    model_names={int(m['model_id']):m['basename'] for m in index.manifest['models']}
    cell=(R0,C0)
    cell_poly=Polygon([(C0*CELL,Z0-R0*CELL),((C0+1)*CELL,Z0-R0*CELL),
      ((C0+1)*CELL,Z0-(R0+1)*CELL),(C0*CELL,Z0-(R0+1)*CELL)])
    face_physical=face_record_summary(index,'physical',cell,cell_poly,model_names)
    face_visible=face_record_summary(index,'visible',cell,cell_poly,model_names)
    if face_visible['positive_intersecting_faces']==0 or face_physical['positive_intersecting_faces']==0:
        raise AssertionError('compiled ODOL faces do not cover proposed shoreline cell')

    # Find the measured maximum hinge in a small crop around the contact+edge, then list its exact triangles/nodes.
    rr0,cc0=R0-2,C0-2
    crop=h[rr0:R0+3,cc0:C0+4].astype(np.float64)
    edge_arrays=dict(ev87.edge_angles(crop))
    maxima=[]
    for kind,a in edge_arrays.items():
        ij=np.unravel_index(int(np.argmax(a)),a.shape)
        r,c=rr0+int(ij[0]),cc0+int(ij[1])
        maxima.append({'kind':kind,'angle_deg':float(a[ij]),'index_rc':[r,c],**hinge_vertices(kind,r,c)})
    hinge=max(maxima,key=lambda e:e['angle_deg'])
    # For this site, report gradient profile in core plus a one-node collar around exact crossing+hinge footprint.
    feature_nodes=list(hinge['triangle_1'])+list(hinge['triangle_2'])+[(R0,C0),(R0,C0+1),(R0+1,C0),(R0+1,C0+1)]
    core_rc=[min(q[0] for q in feature_nodes),max(q[0] for q in feature_nodes)+1,min(q[1] for q in feature_nodes),max(q[1] for q in feature_nodes)+1]
    domain_rc=[core_rc[0]-1,core_rc[1]+1,core_rc[2]-1,core_rc[3]+1]
    r0,r1,c0,c1=domain_rc
    local=h[r0:r1,c0:c1].astype(float)
    ev95_local=h95[r0:r1,c0:c1].astype(float)
    if not np.array_equal(local,ev95_local): raise AssertionError('EV95 rebase differs from selected EV94 terrain in pilot domain')
    horizontal=np.abs(np.diff(local,axis=1)); vertical=np.abs(np.diff(local,axis=0))
    # Local slope rings around exact feature-node core; statistics justify extent without an invented cutoff.
    pr0,pr1,pc0,pc1=R0-7,R0+8,C0-7,C0+8
    patch=h[pr0:pr1,pc0:pc1].astype(float)
    def ring_distance(r,c):
        dr=max(core_rc[0]-r,0,r-(core_rc[1]-1)); dc=max(core_rc[2]-c,0,c-(core_rc[3]-1))
        return max(dr,dc)
    buckets={k:[] for k in range(7)}
    for rr in range(pr0,pr1):
        for cc in range(pc0,pc1-1):
            k=min(ring_distance(rr,cc),ring_distance(rr,cc+1))
            if k<7: buckets[k].append(abs(float(h[rr,cc])-float(h[rr,cc+1])))
    for rr in range(pr0,pr1-1):
        for cc in range(pc0,pc1):
            k=min(ring_distance(rr,cc),ring_distance(rr+1,cc))
            if k<7: buckets[k].append(abs(float(h[rr,cc])-float(h[rr+1,cc])))
    ring_stats={str(k):{'edge_count':len(v),'max_abs_delta_m':max(v) if v else None,
       'median_abs_delta_m':float(np.median(v)) if v else None} for k,v in buckets.items()}
    # Profile/extent records are raw, not an optimizer radius or a chosen smoothing threshold.
    local_profile={'window_rc_half_open':domain_rc,'height_m':local.tolist(),
       'slope_ring_source_window_rc_half_open':[pr0,pr1,pc0,pc1],
       'slope_ring_distance_definition':'Chebyshev node distance from the exact union of crossing-cell and maximum-hinge triangle vertices; orthogonal neighboring-height differences are binned by the smaller endpoint distance.',
       'slope_ring_abs_neighbor_delta_m':ring_stats,
       'center_row_profile_rc_start':[R0,C0-7],'center_row_heights_m':h[R0,C0-7:C0+8].astype(float).tolist(),
       'center_column_profile_rc_start':[R0-7,C0],'center_column_heights_m':h[R0-7:R0+8,C0].astype(float).tolist(),
       'extended_profile_is_measurement_not_smoothing_extent':True,
       'EV95_equal_to_EV94_in_domain':bool(np.array_equal(local,ev95_local)),
       'max_adjacent_horizontal_delta_m':float(horizontal.max()),
       'max_adjacent_vertical_delta_m':float(vertical.max()),
       'core_feature_union_rc_half_open':core_rc,
       'domain_reason':'Exact union of crossing cell and maximum-hinge triangles, plus one 6 m nodal collar as a minimum stencil/boundary diagnostic. This is not asserted as a sufficient smoothing extent; measured neighboring deltas remain large.'}

    # Water WRP identity: all exact water instances are unchanged between B and staged EV94.
    sys.path.insert(0,str(W/'tools/terrain'))
    import wrp0wzd
    bwrp=wrp0wzd.read(str(BASE_WRP)); swrp=wrp0wzd.read(str(STAGED_WRP))
    def water_map(wrp):
        return {int(o['id']):(o['name'].replace('\\','/').lower(),np.asarray(o['matrix'],dtype=np.float64))
          for o in wrp['objects'] if 'baltic_water_v30' in o['name'].replace('\\','/').lower()}
    bm,sm=water_map(bwrp),water_map(swrp)
    if set(bm)!=set(sm) or any(bm[i][0]!=sm[i][0] or not np.array_equal(bm[i][1],sm[i][1]) for i in bm):
        raise AssertionError('EV94 staged WRP water object identity differs from B')
    # Local WRP proximity diagnostic, based on serialized object origins only (not mesh bounds).
    objects=swrp['objects']; nonwater=[]; bridge_named=[]
    for o in objects:
        name=o['name'].replace('\\','/').lower()
        if 'baltic_water_v30' in name: continue
        m=np.asarray(o['matrix'],dtype=float); d=math.hypot(float(m[9])-x,float(m[11])-z)
        item={'id':int(o['id']),'name':o['name'],'origin_distance_m':d,'origin_xz':[float(m[9]),float(m[11])]}
        nonwater.append(item)
        if 'bridge' in name: bridge_named.append(item)
    nonwater.sort(key=lambda a:a['origin_distance_m']); bridge_named.sort(key=lambda a:a['origin_distance_m'])

    constraints_at={'water_support':bool(constraints['wet_support'][R0,C0]),
      'engineering_halo':bool(constraints['engineering_halo'][R0,C0]),
      'other_fixed':bool(constraints['other_fixed'][R0,C0]),'fixed':bool(constraints['fixed'][R0,C0]),
      'allowed':bool(constraints['allowed'][R0,C0]),'EV79_narva':bool(constraints['narva'][R0,C0]),
      'large_lake_banks':bool(large_lake_banks[R0,C0]),
      'terrain_cls':int(cls[R0,C0]),**{k:bool(a[R0,C0]) for k,a in flags.items()}}

    def node_masks_at(r,c):
        return {'terrain_cls':int(cls[r,c]),**{k:bool(a[r,c]) for k,a in flags.items()},
          'water_support':bool(constraints['wet_support'][r,c]),'engineering_halo':bool(constraints['engineering_halo'][r,c]),
          'other_fixed':bool(constraints['other_fixed'][r,c]),'fixed':bool(constraints['fixed'][r,c]),
          'allowed':bool(constraints['allowed'][r,c]),'EV79_narva':bool(constraints['narva'][r,c]),
          'large_lake_banks':bool(large_lake_banks[r,c])}

    stage=jsonread(STAGE_JSON)
    if not stage.get('objects_and_materials_exact') or stage.get('source_wrp_sha256')!=sha(BASE_WRP):
        raise AssertionError('EV94 stage does not bind unchanged base WRP objects/materials')
    if len(bm)!=18024 or stage.get('objects')!=18033: raise AssertionError('water object inventory mismatch')

    # Rehash inputs and all read selection artifacts after calculations; index reverify covers every shard.
    if not index.reverify(): raise AssertionError('EV93 index reverify failed')
    read_end={str(p):sha(p) for p in expected_inputs}
    for u in units:
        a=Path(u['source_artifact_path'])
        if sha(a)!=u['source_artifact_sha256']: raise AssertionError(f'selection artifact changed while reading: {a}')
    for name,want in window_result_hashes.items():
        if sha(Path(name))!=want: raise AssertionError(f'window result changed while reading: {name}')
    if read_start!=read_end: raise AssertionError('source readset changed during selection')

    max_m=0.95; nominal_bed=1.0
    result={
      'schema':'ev94.wet-bank-pilot-selection.v1','status':'SELECTED_GEOMETRY_ONLY_NO_TERRAIN_CHANGE',
      'selection_reason':'Selected Oredezh as the high-water verified fallback to Msta: this location has a measured P/F dry-to-wet crossing on a real compiled visible face, with head sufficient for a 1.0 m bed plus 0.95 m draft at the wet endpoint.',
      'site':{'water_feature_id':RIVER_ID,'water_feature_properties':water_feature['properties'],
        'water_feature_index':84,'source':str(WATER_GEOJSON),'feature_geometry_type':water_feature['geometry']['type'],
        'point_rc':[R0,C0],'world_xz_m':[x,z],'cell_rc':[R0,C0],
        'cell_corner_order':'NW,NE,SW,SE; triangulation NW-SE: [NW,NE,SE] + [NW,SE,SW]',
        'dry_corner_rc':[R0,C0],'wet_corner_rc':[R0,C0+1],
        'crossing_edge':'cell top edge NW→NE; F sample indices 0→1'},
      'terrain_and_surface':{'H_3x3_rc_start':[R0-1,C0],'H_candidate_EV94_m':H3.tolist(),
        'H_base_EV93_selected_m':B3.tolist(),'H_base_EV82_B_m':B82_3.tolist(),'H_EV95_rebase_domain_equal':True,'EV95_rebase_path':str(EV95_TERRAIN),'EV95_rebase_sha256':read_start[str(EV95_TERRAIN)],'P_cells_2x2_rc_start':[R0-1,C0],'P_plane_m':P2.tolist(),'crossing_cell_offset_in_P_F_arrays_rc':[1,0],
        'F_cells_2x2_corner_order_NW_NE_SW_SE_m':F2.tolist(),
        'crossing':{'P_cell_m':p_cell,'F_dry_m':f_dry,'F_wet_m':f_wet,
          'H_dry_m':h_dry,'H_wet_m':h_wet,'H_minus_F_dry_m':dd,'H_minus_F_wet_m':dw,
          'linear_zero_fraction_dry_to_wet':t,'linear_zero_distance_from_dry_m':CELL*t,
          'wet_clearance_F_minus_H_m':f_wet-h_wet,
          'max_bed_raise_while_retaining_0_95m_draft_m':f_wet-h_wet-max_m,
          'nominal_1m_bed_elevation_F_minus_1m_m':f_wet-nominal_bed,
          'wet_H_minus_1m_m':h_wet-1.0,
          'draft_0_95_contract_applies_here':False,
          'note':'The .95 m contract is a navigable-corridor requirement; this point is outside the signed corridor. Clearance is reported as geometry, not an added requirement.'}},
      'compiled_faces':{'index_manifest_path':str(INDEX_RUN/'manifest.json'),
         'manifest_sha256':read_start[str(INDEX_RUN/'manifest.json')],
         'cell_polygon_xz_m':list(cell_poly.exterior.coords),
         'physical':face_physical,'visible':face_visible,
         'meaning':'EV93 compiled ODOL XZ faces intersect this cell; face planes are static source geometry, not runtime water/depth proof.'},
      'slope_hinge':{'measurement_source':str(EV87_PATH),'measurement_source_sha256':read_start[str(EV87_PATH)],
         'max_incident_hinge_in_crop':hinge,'hinge_vertex_xyz_h':{str(q):{'xz_m':p_rc(*q),'H_m':float(h[q[0],q[1]])} for q in sorted(set(feature_nodes))},'all_kind_maxima_in_crop':maxima,
         'local_profile_domain':local_profile,
         'interpretation':'The 47.95° hinge is the maximum in this bounded crop; the reported triangle vertex lists let the profile include the neighboring facet pair and actual shoreline cell together.'},
      'design_contour':{'nearest_boundary_distance_m':float(point.distance(water_geom.boundary)),
         'nearest_boundary_xz_m':[float(nearest.x),float(nearest.y)],
         'minimum_area_pilot_domain_recommendation':{'feature_core_rc_half_open':core_rc,'first_fixed_collar_probe_rc_half_open':domain_rc,'profile_probe_rc_half_open':local_profile['slope_ring_source_window_rc_half_open'],'profile_probe_span_m':[84.0,84.0],
           'boundary_test':'The 6 m collar is only the topological minimum. The measured max orthogonal height delta is 3.65 m at ring 1 and remains 2.69 m at ring 6 (~36 m from the feature core); no fixed smoothing radius is justified by these measurements.',
           'recommended_profile':'Use the exact dry-to-wet cross-shore line through row 862 together with the 47.95 degree NW-SE hinge pair, then extend the movable band only until the measured fixed-side shoulder becomes suitable. The 15x15 probe is evidence of slope persistence, not a selected edit radius.'}},
      'protection_and_separation':{'node_masks':constraints_at,'dry_endpoint_masks':node_masks_at(R0,C0),'wet_endpoint_masks':node_masks_at(R0,C0+1),
         'selection_windows':{'retained_units':len(units),'overlap_count':len(overlaps),'nearest':best,
           'window_source':'selection units; all retained source result files re-read and SHA-checked before/after window_rc extraction','window_result_count':len(window_result_hashes),'window_result_readset_sha256':hashlib.sha256(json.dumps(window_result_hashes,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()},
         'signed_corridor_distance_m':corridor_dist,'signed_corridor_path':str(CORRIDORS),
         'nearest_road_sample':road_nearest,'road_reference_path':str(ROAD_REFERENCE),
         'nearest_nonwater_WRP_origins':nonwater[:5],'nonwater_WRP_origin_count_within_500m':sum(o['origin_distance_m']<=500 for o in nonwater),'bridge_named_WRP_origins':bridge_named[:5],'bridge_named_WRP_origin_count_within_500m':sum(o['origin_distance_m']<=500 for o in bridge_named),
         'origin_distance_limit':'WRP transform-origin distances only; not a compiled object-bounds clearance test.',
         'why_dry_pass_froze_node':'EV79 wet_support is true at the dry corner; the point is not in any retained selection window. Other listed local exclusion masks are false.'},
      'water_object_identity':{'base_wrp_path':str(BASE_WRP),'base_wrp_sha256':read_start[str(BASE_WRP)],
        'EV94_staged_wrp_path':str(STAGED_WRP),'staged_wrp_sha256':read_start[str(STAGED_WRP)],
        'stage_json_path':str(STAGE_JSON),'stage_json_sha256':read_start[str(STAGE_JSON)],
        'stage_status':stage['status'],'objects_and_materials_exact':stage['objects_and_materials_exact'],
        'water_object_count_base_and_EV94':len(bm),'water_ids_names_and_12-float_matrices_equal':True,
        'EV94_water_pbo_sha256':stage.get('baseline_water_pbo_sha256')},
      'source_readset':{'start':read_start,'end':read_end,'unchanged':read_start==read_end,
        'script_sha256':sha(SCRIPT) if SCRIPT.exists() else None},
      'scope_limits':['Selection only; no candidate geometry was authored or changed.','P/F and static face intersections establish geometry, not game runtime wave level or appearance.','WRP non-water proximity is by object origin only.','Local domain is a measured geometric footprint, not a tuned smoothing radius.']}
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'out':str(OUT),'sha256':sha(OUT),
      'point_rc':[R0,C0],'world_xz_m':[x,z],'crossing_fraction':t,
      'hinge':{'kind':hinge['kind'],'angle_deg':hinge['angle_deg'],'index_rc':[hinge['index_rc'][0],hinge['index_rc'][1]]},
      'nearest_selected_window':best,'corridor_distance_m':corridor_dist,'nearest_road_m':road_nearest['distance_m'],
      'physical_faces':face_physical['positive_intersecting_faces'],'visible_faces':face_visible['positive_intersecting_faces'],
      'readset_unchanged':True},indent=2))

if __name__=='__main__': main()


















