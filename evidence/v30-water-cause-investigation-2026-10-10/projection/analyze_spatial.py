from pathlib import Path
import json, re, math, hashlib
import numpy as np

OUT = Path(r'E:\DayZ-Baltic-Build\v30-water-pixel-calibration-20261010')
LOG = OUT / 'projection-final.log'
PROBE = OUT / 'probe.json'
RUNTIME = OUT / 'runtime.json'
TERRAIN = Path(r'E:\DayZ-Baltic-Build\v30-complete-dry-surface-20261009\candidate\terrain.npz')
PLANE = Path(r'E:\DayZ-Baltic-Build\v30-complete-dry-surface-20261009\candidate\plane.npy')
IMAGE = Path(r'E:\DayZ-Baltic-Build\v30-base-surface-runtime-20261009\capture_20261009_233431_541.jpg')
EXPECTED_TERRAIN_SHA = 'b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36'
EXPECTED_PROFILE_SHA = '33ccbabd7ab0f3fab014a169d0debf23abcee5d531ac9d537ce2da0a50874703'
EXPECTED_PROBE_SHA = '57971ccfc13b09d930904978edd012cedcdb10cfe32d6f19210a1fe73bca148b'
WIDTH, HEIGHT = 1920, 1080
CELL, Z_TOP = 6.0, 12282.0

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
probe = json.loads(PROBE.read_text(encoding='utf-8'))
runtime = json.loads(RUNTIME.read_text(encoding='utf-8'))
assert probe['pbo'] and probe['sha256'] == EXPECTED_PROBE_SHA
assert probe['profile_sha256'] == EXPECTED_PROFILE_SHA
assert sha(TERRAIN) == EXPECTED_TERRAIN_SHA

# Read one complete native group at this exact position/viewport. Train/test follow EV48's even/odd split.
number = lambda text: np.array([float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', text)], dtype=float)
groups = []
lines = LOG.read_text(encoding='utf-8').splitlines()
i = 0
while i < len(lines):
    p = lines[i].split(';')
    if p[0] == 'CAMERA' and len(p) >= 8:
        pos = number(p[2]); size = (int(p[5]), int(p[6])); fov = float(p[4])
        if len(pos) == 3 and np.allclose(pos, [2417, 65, 6745], atol=1e-5) and size == (WIDTH, HEIGHT) and abs(fov-1.1)<1e-6:
            rows=[]
            for line in lines[i+1:i+17]:
                q=line.split(';')
                if q[0] != 'POINT': break
                rows.append((int(q[2]), number(q[3]), number(q[4]), number(q[5])))
            if len(rows)==16 and [r[0] for r in rows]==list(range(16)):
                groups.append((p[1], fov, float(p[7]), rows))
    i += 1
assert groups, 'No complete native 16-point group for requested camera/viewport/FOV'
tick, fov, sea_level_readback, rows = groups[-1]
ids=np.array([r[0] for r in rows], int)
world=np.stack([r[1] for r in rows]); native=np.stack([r[2] for r in rows]); relative=np.stack([r[3] for r in rows])
mat=np.array(runtime['camera']['camera']['matrix'], float).reshape(4,3)
cam=mat[3]; basis=mat[:3]
q=(world-cam)@basis.T
uv=np.c_[q[:,0]/q[:,2], -q[:,1]/q[:,2]]
center=np.array([WIDTH/2, HEIGHT/2], float)
observed=native[:,:2]-center
inside=(native[:,0]>1)&(native[:,0]<WIDTH-1)&(native[:,1]>1)&(native[:,1]<HEIGHT-1)&(native[:,2]>0)
train=inside&(ids%2==0); held=inside&~train
assert train.sum()==8 and held.sum()==8, (train.sum(),held.sum())
focal=float(np.sum(uv[train]*observed[train])/np.sum(uv[train]**2))
pred=center+focal*uv
err=np.linalg.norm(pred-native[:,:2],axis=1)
relative_error=float(np.max(np.abs(relative[:,:2]*[WIDTH,HEIGHT]-native[:,:2])))
depth_error=float(np.max(np.abs(q[:,2]-native[:,2])))
clamped=np.clip(pred,[0,0],[WIDTH,HEIGHT])
clamp_delta=np.linalg.norm(clamped-pred,axis=1)
clamp_native_error=np.linalg.norm(clamped-native[:,:2],axis=1)
assert np.isfinite(focal) and focal>0
assert float(err[held].max()) < 0.05
assert relative_error < 0.003
assert depth_error < 0.002
assert float(clamp_native_error.max()) < 0.05

calibration={
 'status':'NATIVE_PROJECTION_CALIBRATED', 'source':'EV76 projection-final.log; last complete 16-point group at exact camera/viewport/FOV',
 'run_id':runtime['launch']['run_id'], 'tick':tick, 'native_group_count':len(groups),
 'camera_position':cam.tolist(), 'camera_matrix_4x3':mat.tolist(), 'viewport':[WIDTH,HEIGHT],
 'fov_argument':runtime['camera']['fov_applied'], 'native_Camera.GetCurrentFOV':fov,
 'runtime_export_camera_fov_stub':runtime['camera']['camera']['fov'], 'sea_level_log_field':sea_level_readback,
 'focal_px':focal, 'train_ids_even':ids[train].tolist(), 'heldout_ids_odd':ids[held].tolist(),
 'all_ids':ids.tolist(), 'train_max_error_px':float(err[train].max()),
 'heldout_max_error_px':float(err[held].max()), 'heldout_rms_error_px':float(np.sqrt(np.mean(err[held]**2))),
 'max_native_depth_qz_delta':depth_error, 'max_relative_to_pixel_delta_px':relative_error,
 'clamp':{'predicted_points_clamped':int(np.count_nonzero(clamp_delta>1e-9)),
          'max_clamp_displacement_px':float(clamp_delta.max()), 'max_clamped_prediction_to_native_px':float(clamp_native_error.max()),
          'all_points_inside_native_viewport':bool(inside.all())},
 'native_points': [{'id':int(ids[j]), 'world':world[j].tolist(), 'screen_xy_depth':native[j].tolist(),
                    'camera_qz':float(q[j,2]), 'prediction_xy':pred[j].tolist(), 'error_px':float(err[j]),
                    'relative_screen_xy':relative[j,:2].tolist(), 'fit_role':'train_even' if train[j] else 'heldout_odd'} for j in range(len(ids))],
 'artifact_hashes':{'probe_pbo':probe['sha256'],'profile':probe['profile_sha256'],'terrain_npz':sha(TERRAIN),
                    'plane_npy':sha(PLANE),'EV73_capture':sha(IMAGE)},
 'limits':['Focal is fitted from 8 even-index samples and checked against 8 odd-index heldout samples.',
           'The projection is transferred to EV73 capture by same camera pose, requested/native FOV, viewport and profile; EV76 capture is invalid magenta.',
           'Projection maps rays to the approved terrain grids; it does not identify a rendered water layer, shader, or occlusion result.']}
(OUT/'calibration.json').write_text(json.dumps(calibration,indent=2,ensure_ascii=False,default=lambda o: o.item() if isinstance(o,np.generic) else str(o))+'\n',encoding='utf-8')

with np.load(TERRAIN) as t:
    h=t['heights'].astype(float); cls=t['cls'].astype(np.uint8); level=t['level'].astype(float)
    narva=t['narva'].astype(bool); reserve=t['reserve'].astype(bool); water=t['water'].astype(bool)
pgrid=np.load(PLANE).astype(float)
F_PATH=Path(r'E:\DayZ-Baltic-Build\v30-complete-dry-surface-20261009\candidate\visible-field.npy')
fgrid=np.load(F_PATH).astype(float)
assert h.shape==(2048,2048) and cls.shape==h.shape and pgrid.shape==(2047,2047) and fgrid.shape==(2047,2047,4)

# Terrain class flags are separate from F, the per-cell four-corner visible-field surface.
def cell_xy(x,z):
    return int(math.floor((Z_TOP-z)/CELL)), int(math.floor(x/CELL))
def face_info(r,c,x,z):
    u=x/CELL-c; v=(Z_TOP-z)/CELL-r
    if not (-1e-8<=u<=1+1e-8 and -1e-8<=v<=1+1e-8): return None
    if u>=v:
        ids3=((r,c),(r,c+1),(r+1,c+1)); label='NW_NE_SE'
        bary=(1-u,u-v,v)
    else:
        ids3=((r,c),(r+1,c),(r+1,c+1)); label='NW_SW_SE'
        bary=(1-v,v-u,u)
    codes=[int(cls[a,b]) for a,b in ids3]
    hs=[float(h[a,b]) for a,b in ids3]
    gs=float(sum(bary[k]*hs[k] for k in range(3)))
    ns=[bool(narva[a,b]) for a,b in ids3]; rs=[bool(reserve[a,b]) for a,b in ids3]
    ws=[bool(water[a,b]) for a,b in ids3]
    return {'triangle':label,'vertices_rc':[list(q) for q in ids3], 'barycentric':[float(vv) for vv in bary],
            'terrain_face_class_codes':codes,'terrain_face_all_wet':all(x>0 for x in codes),
            'terrain_face_all_class3':all(x==3 for x in codes),'terrain_face_class_signature':sorted(set(codes)),
            'ground_y':gs,'narva_vertices':ns,'narva_any':any(ns),'narva_all':all(ns),
            'reserve_vertices':rs,'reserve_any':any(rs),'reserve_all':all(rs),'water_vertices':ws}

# Moller-Trumbore exact ray/triangle hit. Return t and barycentric weights.
def ray_tri(o,d,verts):
    a,b,c=verts; e1=b-a; e2=c-a; pv=np.cross(d,e2); det=float(e1@pv)
    if abs(det)<1e-10: return None
    inv=1.0/det; tv=o-a; u=float(tv@pv)*inv
    if u < -1e-8 or u > 1+1e-8: return None
    qv=np.cross(tv,e1); v=float(d@qv)*inv
    if v < -1e-8 or u+v>1+1e-8: return None
    tt=float(e2@qv)*inv
    if tt<=1e-6: return None
    return tt,(1-u-v,u,v)

def ray_hits(px,py):
    qx=(px-center[0])/focal; qy=-(py-center[1])/focal
    d=basis.T@np.array([qx,qy,1.0]); o=cam.copy()
    x,z=float(o[0]),float(o[2]); dx,dz=float(d[0]),float(d[2])
    r,c=cell_xy(x,z)
    # Amanatides-Woo DDA in map X and row-coordinate w=(Z_TOP-z)/CELL.
    if dx>0: step_c=1; tmx=((c+1)*CELL-x)/dx; tdx=CELL/abs(dx)
    elif dx<0: step_c=-1; tmx=(c*CELL-x)/dx; tdx=CELL/abs(dx)
    else: step_c=0; tmx=tdx=float('inf')
    w0=(Z_TOP-z)/CELL; rowrate=-dz/CELL
    if rowrate>0: step_r=1; tmz=((r+1)-w0)/rowrate; tdz=1/abs(rowrate)
    elif rowrate<0: step_r=-1; tmz=(r-w0)/rowrate; tdz=1/abs(rowrate)
    else: step_r=0; tmz=tdz=float('inf')
    tcur=0.0; p_hit=None; f_hit=None; ground_hit=None
    for _ in range(4096):
        if r<0 or c<0 or r>=pgrid.shape[0] or c>=pgrid.shape[1]: break
        tend=min(tmx,tmz)
        if not math.isfinite(tend): break
        has_water=bool(np.any(cls[r:r+2,c:c+2]>0)) and math.isfinite(float(pgrid[r,c]))
        if has_water:
            pp=float(pgrid[r,c])
            if abs(d[1])>1e-10:
                tp=(pp-o[1])/d[1]
                if tp>=max(tcur,1e-6)-1e-6 and tp<=tend+1e-6 and p_hit is None:
                    wp=o+tp*d; ff=face_info(r,c,float(wp[0]),float(wp[2]))
                    p_hit={'t':tp,'point':wp.tolist(),'row':r,'col':c,'P':pp,'terrain_at_P':ff}
            # F is the actual four-corner visible-field surface, intersected per native face.
            for tri,indices in [('NW_NE_SE',(0,1,3)),('NW_SW_SE',(0,2,3))]:
                rcs=[(r,c),(r,c+1),(r+1,c),(r+1,c+1)]
                vals=fgrid[r,c,list(indices)]
                if not np.isfinite(vals).all(): continue
                verts=np.array([[cc*CELL,float(vals[k]),Z_TOP-rr*CELL] for k,(rr,cc) in enumerate([rcs[j] for j in indices])],float)
                hit=ray_tri(o,d,verts)
                if hit is None: continue
                tf,bary=hit
                if tf>=max(tcur,1e-6)-1e-6 and tf<=tend+1e-6 and (f_hit is None or tf<f_hit['t']):
                    fp=o+tf*d; ff=face_info(r,c,float(fp[0]),float(fp[2]))
                    codes=[int(cls[rr,cc]) for rr,cc in [rcs[j] for j in indices]]
                    ns=[bool(narva[rr,cc]) for rr,cc in [rcs[j] for j in indices]]
                    rs=[bool(reserve[rr,cc]) for rr,cc in [rcs[j] for j in indices]]
                    f_hit={'t':tf,'point':fp.tolist(),'row':r,'col':c,'triangle':tri,
                        'F_vertex_heights':[float(vv) for vv in vals], 'F_barycentric':[float(vv) for vv in bary],
                        'F_surface_y':float(fp[1]),'F_minus_P':float(fp[1])-float(pgrid[r,c]),
                        'terrain_under_F':ff,'face_class_codes':codes,'face_class_signature':sorted(set(codes)),
                        'face_narva_vertices':ns,'face_narva_any':any(ns),'face_narva_all':all(ns),
                        'face_reserve_vertices':rs,'face_reserve_any':any(rs),'face_reserve_all':all(rs)}
        # Terrain is the native NW-SE triangulated heightfield, independent of P and F.
        for tri,rcs in [('NW_NE_SE',[(r,c),(r,c+1),(r+1,c+1)]),('NW_SW_SE',[(r,c),(r+1,c),(r+1,c+1)])]:
            verts=np.array([[cc*CELL,float(h[rr,cc]),Z_TOP-rr*CELL] for rr,cc in rcs],float)
            hit=ray_tri(o,d,verts)
            if hit is None: continue
            tg,bary=hit
            if tg>=max(tcur,1e-6)-1e-6 and tg<=tend+1e-6 and (ground_hit is None or tg<ground_hit['t']):
                gp=o+tg*d; codes=[int(cls[rr,cc]) for rr,cc in rcs]
                ns=[bool(narva[rr,cc]) for rr,cc in rcs]; rs=[bool(reserve[rr,cc]) for rr,cc in rcs]
                ground_hit={'t':tg,'point':gp.tolist(),'row':r,'col':c,'triangle':tri,
                    'barycentric':[float(vv) for vv in bary],'ground_y':float(gp[1]),
                    'face_class_codes':codes,'face_class_signature':sorted(set(codes)),
                    'face_narva_vertices':ns,'face_narva_any':any(ns),'face_narva_all':all(ns),
                    'face_reserve_vertices':rs,'face_reserve_any':any(rs),'face_reserve_all':all(rs)}
        found=[v['t'] for v in (p_hit,f_hit,ground_hit) if v is not None]
        if len(found)==3 and tend>=max(found)-1e-6: break
        if ground_hit is not None and tend>=ground_hit['t']-1e-6 and p_hit is None and f_hit is None: break
        if tend>=5000: break
        tcur=tend
        if tmx<=tmz+1e-9: c+=step_c; tmx+=tdx
        if tmz<=tend+1e-9: r+=step_r; tmz+=tdz
    return p_hit,f_hit,ground_hit

# Independent calibration sanity: inverse ray center intersects the known EV72 cell P[889,402].
center_d=basis.T@np.array([0.0,0.0,1.0]); center_t=(float(pgrid[889,402])-cam[1])/center_d[1]
center_world=cam+center_t*center_d
assert cell_xy(float(center_world[0]),float(center_world[2]))==(889,402)
assert abs(float(center_world[1])-float(pgrid[889,402]))<1e-8
# Round-trip a native sample: project/unproject point 10 and verify camera-space depth.
probe_world=world[10]; probe_uv=uv[10]; probe_xy=center+focal*probe_uv
probe_d=basis.T@np.array([probe_uv[0],-probe_uv[1],1.0])
probe_t=q[10,2]; probe_roundtrip=cam+probe_t*probe_d
assert np.linalg.norm(probe_roundtrip-probe_world)<1e-3

# Positive control at optical axis: exact P/F cell and independent native ground hit.
center_p,center_f,center_ground=ray_hits(960.0,540.0)
assert center_p is not None and (center_p['row'],center_p['col'])==(889,402)
assert center_f is not None and (center_f['row'],center_f['col'])==(889,402)
assert center_ground is not None and center_ground['ground_y']<center_p['P']
geometry_sanity={'native_probe_point_id':10,'roundtrip_world_error_m':float(np.linalg.norm(probe_roundtrip-probe_world)),
  'native_probe_projected_xy_px':probe_xy.tolist(),'optical_axis_P_cell':[center_p['row'],center_p['col']],
  'optical_axis_F_cell':[center_f['row'],center_f['col']],'optical_axis_P_ground_under_m':center_p['terrain_at_P']['ground_y'],
  'optical_axis_F_ground_under_m':center_f['terrain_under_F']['ground_y'],'optical_axis_F_minus_ground_m':center_f['F_surface_y']-center_f['terrain_under_F']['ground_y'],
  'optical_axis_ground_hit':center_ground,'optical_axis_P_point':center_p['point'],'optical_axis_F_point':center_f['point']}

# ROIs were fixed from EV74; one extra ROI is manually delineated on the visible EV73 frame before geometry.
rois={
 'reported_grey_EV74':[770,620,860,680],
 'near_ripple_control_EV74':[470,845,575,900],
 'dry_control_EV74':[1280,775,1450,875],
 'visible_rect_far_center_preselected_from_EV73':[918,456,1012,500],
}
step=4
reports={}
for name,box in rois.items():
    x0,y0,x1,y1=box
    samples=[]
    for py in range(y0,y1,step):
        for px in range(x0,x1,step):
            ph,fh,gh=ray_hits(px+0.5,py+0.5)
            samples.append({'pixel':[px+0.5,py+0.5],'P':ph,'F':fh,'ground':gh})
    p_rows=[s['P'] for s in samples if s['P'] is not None]
    f_rows=[s['F'] for s in samples if s['F'] is not None]
    ground_rows=[s['ground'] for s in samples if s['ground'] is not None]
    def count_vals(rows,key):
        from collections import Counter
        return {str(k):v for k,v in sorted(Counter(str(r[key]) for r in rows).items())}
    def quant(rows,key):
        a=np.array([r[key] for r in rows],float)
        return {'min':float(a.min()),'median':float(np.median(a)),'max':float(a.max())} if len(a) else None
    reports[name]={
      'pixel_box_xyxy_half_open':box,'sampling_step_px':step,'ray_samples':len(samples),
      'first_P_plane_intersections':len(p_rows),'first_F_surface_intersections':len(f_rows),'first_terrain_face_intersections':len(ground_rows),
      'F_intersection_pct_of_all_rays':100.0*len(f_rows)/len(samples) if samples else None,
      'F_face_narva_any_pct_of_F_hits':100.0*sum(r['face_narva_any'] for r in f_rows)/len(f_rows) if f_rows else None,
      'F_face_narva_all_pct_of_F_hits':100.0*sum(r['face_narva_all'] for r in f_rows)/len(f_rows) if f_rows else None,
      'F_face_reserve_any_pct_of_F_hits':100.0*sum(r['face_reserve_any'] for r in f_rows)/len(f_rows) if f_rows else None,
      'F_face_reserve_all_pct_of_F_hits':100.0*sum(r['face_reserve_all'] for r in f_rows)/len(f_rows) if f_rows else None,
      'ground_hit_class0_pct_of_ground_hits':100.0*sum(r['face_class_signature']==[0] for r in ground_rows)/len(ground_rows) if ground_rows else None,
      'P_m':quant(p_rows,'P'),'P_minus_ground_m':quant([{'gap':r['P']-r['terrain_at_P']['ground_y']} for r in p_rows if r['terrain_at_P'] is not None],'gap'),
      'F_surface_y_m':quant(f_rows,'F_surface_y'),'F_minus_P_m':quant(f_rows,'F_minus_P'),
      'F_face_vertex_heights_m':count_vals(f_rows,'F_vertex_heights'),
      'F_face_class_signatures':count_vals(f_rows,'face_class_signature'),
      'terrain_under_F_y_m':quant([r['terrain_under_F'] for r in f_rows if r['terrain_under_F'] is not None],'ground_y'),
      'F_minus_terrain_m':quant([{'gap':r['F_surface_y']-r['terrain_under_F']['ground_y']} for r in f_rows if r['terrain_under_F'] is not None],'gap'),
      'ground_under_F_below_0_85_count':sum(r['terrain_under_F'] is not None and r['terrain_under_F']['ground_y']<0.85 for r in f_rows),
      'ground_under_F_below_0_65_count':sum(r['terrain_under_F'] is not None and r['terrain_under_F']['ground_y']<0.65 for r in f_rows),
      'F_surface_above_0_85_count':sum(r['F_surface_y']>0.85 for r in f_rows),
      'F_before_ground_hit_count':sum(s['F'] is not None and s['ground'] is not None and s['F']['t']<s['ground']['t']-1e-6 for s in samples),
      'F_behind_ground_hit_count':sum(s['F'] is not None and s['ground'] is not None and s['F']['t']>s['ground']['t']+1e-6 for s in samples),
      'P_before_ground_hit_count':sum(s['P'] is not None and s['ground'] is not None and s['P']['t']<s['ground']['t']-1e-6 for s in samples),
      'F_face_narva_any_count':sum(r['face_narva_any'] for r in f_rows),'F_face_narva_all_count':sum(r['face_narva_all'] for r in f_rows),
      'F_face_reserve_any_count':sum(r['face_reserve_any'] for r in f_rows),'F_face_reserve_all_count':sum(r['face_reserve_all'] for r in f_rows),
      'ground_hit_y_m':quant(ground_rows,'ground_y'),
      'ground_hit_face_class_signatures':count_vals(ground_rows,'face_class_signature'),
      'ground_hit_narva_any_count':sum(r['face_narva_any'] for r in ground_rows),
      'ground_hit_reserve_any_count':sum(r['face_reserve_any'] for r in ground_rows),
      'ground_hit_rows_cols':count_vals(ground_rows,'row'),
      'center_ray':next((s for s in samples if s['pixel']==[float(x0+((x1-x0)//2//step)*step)+0.5,float(y0+((y1-y0)//2//step)*step)+0.5]),None),
    }
roi_report={
 'status':'EV73_ROI_RAY_TO_TERRAIN_LINKAGE',
 'image_used':str(IMAGE),'image_sha256':sha(IMAGE),'image_size_px':[1920,1080],
 'image_is_EV73_not_EV76_magenta':True,'EV74_profile_sha256':EXPECTED_PROFILE_SHA,
 'camera_pose_fov_viewport_transfer':{'position':[2417,65,6745],'matrix':mat.tolist(),'native_fov':fov,'viewport':[WIDTH,HEIGHT],
   'match_basis':'EV76 read-only projection pose + native FOV and same EV74 profile; applied retrospectively to EV73 image.',
   'limitations':['EV76 capture itself is invalid magenta and not used as visual evidence.',
                  'EV73 screenshot transfer assumes unchanged rendered camera projection/viewport; no per-pixel native query exists for that already captured frame.',
                  'Geometric ray/terrain overlap does not identify the water shader/layer or establish occlusion/visibility.']},
 'terrain':{'path':str(TERRAIN),'sha256':sha(TERRAIN),'cell_size_m':CELL,'z_top_m':Z_TOP,
   'face_diagonal':'NW_NE_SE / NW_SW_SE; terrain heights and F field values interpolated on the actual selected face with barycentric weights.',
   'P_source':str(PLANE),'plane_sha256':sha(PLANE),'F_source':str(F_PATH),'F_sha256':sha(F_PATH),
   'F_definition':'Four corner heights in visible-field.npy order [NW,NE,SW,SE], intersected separately on the native NW_NE_SE / NW_SW_SE triangles; terrain class and Narva/reserve masks are additional face/cell flags.'},
 'geometry_sanity':geometry_sanity,'rois':reports,
 'interpretation_limits':['ROI color labels come from the EV74 report and visual EV73 boundary selection; they do not classify pixel shader.',
  'The EV74 near-ripple ROI also maps to deep Narva class-3 water; it is not an independent shallow-water control for the double-water hypothesis.',
  'P is the frozen per-cell plane. F is the four-corner visible-field mesh, intersected on each NW_NE_SE / NW_SW_SE face. Terrain is the separate native height mesh; each crossing is reported independently.',
  'Class, Narva, and reserve are face-vertex/cell-grid evidence, not engine draw-call evidence.']}
(OUT/'roi-world.json').write_text(json.dumps(roi_report,indent=2,ensure_ascii=False,default=lambda o: o.item() if isinstance(o,np.generic) else str(o))+'\n',encoding='utf-8')
print(json.dumps({'calibration':{k:calibration[k] for k in ['focal_px','train_ids_even','heldout_ids_odd','heldout_max_error_px','max_native_depth_qz_delta','max_relative_to_pixel_delta_px','clamp']},'rois':{k:{q:v for q,v in x.items() if q not in ['center_ray']} for k,x in reports.items()}},indent=2,ensure_ascii=False,default=lambda o: o.item() if isinstance(o,np.generic) else str(o)))
