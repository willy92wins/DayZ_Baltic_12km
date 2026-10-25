from __future__ import annotations
import json, math, re, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

W = Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev')
sys.path.insert(0, str(W))
sys.path.insert(0, str(W / 'tools' / 'terrain'))
sys.path.insert(0, r'C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts')
from wrp0wzd import read as read_wrp
from odol_reader import ODOL

WRP = Path(r'E:\DayZ-Baltic-Build\v30-remaining-exact-dry-support-20261009\package\world\root\dayz_baltic_12km_dev\tb\narva_trial\baltic_trial.wrp')
MODELS = Path(r'E:\DayZ-Baltic-Build\v30-native-terminal-finish-20261009\package\water\temp\baltic_water_v30')
LOG = Path(r'E:\DayZ-Baltic-Build\v30-water-pixel-calibration-20261010\projection-final.log')
IMAGE = Path(r'E:\DayZ-Baltic-Build\v30-base-surface-runtime-20261009\capture_20261009_233431_541.jpg')
OUT = Path(__file__).resolve().parent
ROIS = {'gray': (770, 620, 860, 680), 'wavy_control': (470, 845, 575, 900)}
CAM = np.array([2417., 65., 6745.])
FWD = np.array([0., -.302244, .953231]); FWD /= np.linalg.norm(FWD)
RIGHT = np.array([1., 0., 0.])
UP = np.cross(FWD, RIGHT)

# Fit the actual perspective mapping from the 16 native GetScreenPos records.
# The exact final CAMERA id is selected to avoid mixed/early probe records.
num = lambda s: [float(v) for v in re.findall(r'[-+]?(?:\d+\.\d+|\d+)', s)]
lines = LOG.read_text(encoding='utf-8').splitlines()
pts=[]; camera=None; active=False
for line in lines:
    f=line.split(';')
    if f[0]=='CAMERA':
        active=(len(f)>1 and f[1]=='101848')
        if active: camera=f
    elif active and f[0]=='POINT':
        world=num(f[3]); pix=num(f[4])
        if len(world)>=3 and len(pix)>=2: pts.append((world[:3],pix[:2]))
if len(pts)!=16 or camera is None: raise RuntimeError(f'expected final 16 projection points, got {len(pts)}')
world=np.array([p[0] for p in pts]); observed=np.array([p[1] for p in pts])
delta=world-CAM
xcam=delta@RIGHT; ycam=delta@UP; zcam=delta@FWD
A=np.c_[np.ones(len(pts)),xcam/zcam]
cx,fx=np.linalg.lstsq(A, observed[:,0], rcond=None)[0]
A=np.c_[np.ones(len(pts)),-ycam/zcam]
cy,fy=np.linalg.lstsq(A, observed[:,1], rcond=None)[0]
res=np.c_[cx+fx*xcam/zcam, cy+fy*(-ycam/zcam)]-observed
if abs(fx-fy)>0.02 or np.max(np.abs(res))>0.01: raise RuntimeError(f'projection fit failed: fx={fx} fy={fy} max={np.max(np.abs(res))}')
focal=(fx+fy)/2

def project(points):
    d=np.asarray(points,float)-CAM
    depth=d@FWD
    good=depth>1e-4
    pixels=np.full((len(d),2),np.nan)
    pixels[good,0]=cx+focal*(d[good]@RIGHT)/depth[good]
    pixels[good,1]=cy-focal*(d[good]@UP)/depth[good]
    return pixels,depth

def roi_world(corners,y=2.):
    out=[]
    for u,v in corners:
        ray=RIGHT*((u-cx)/focal)+UP*((cy-v)/focal)+FWD
        t=(y-CAM[1])/ray[1]
        out.append(CAM+t*ray)
    return np.asarray(out)

world_rois={}
for name,(x1,y1,x2,y2) in ROIS.items():
    corners=roi_world([(x1,y1),(x2,y1),(x2,y2),(x1,y2)])
    world_rois[name]={'pixels':[x1,y1,x2,y2], 'world_y2_corners':corners.tolist(),
                      'world_xz_bbox':[float(corners[:,0].min()),float(corners[:,2].min()),float(corners[:,0].max()),float(corners[:,2].max())]}

wrp=read_wrp(WRP)
allobjs=[o for o in wrp['objects'] if o['name'].lower().startswith('baltic_water_v30\\')]
# Filter only by conservative world-space expansion; final selection is actual projected LOD0 polygon intersection.
selected=[]
for name,r in world_rois.items():
    x0,z0,x1,z1=r['world_xz_bbox']
    for o in allobjs:
        m=o['matrix']; x,z=m[9],m[11]
        if x0-80<=x<=x1+80 and z0-80<=z<=z1+80:
            selected.append(o)
selected=list({o['id']:o for o in selected}.values())

cache={}; results={k:[] for k in ROIS}; errors=[]
for obj in selected:
    model_name=obj['name'].split('\\')[-1]
    path=MODELS/model_name
    try:
        if model_name not in cache:
            odol=ODOL.from_file(str(path))
            lod=next((l for l in odol.lods if l and abs(l.resolution-1.0)<0.01),None)
            if lod is None: raise ValueError('no visible LOD res=1')
            v=np.array([[q.x,q.y,q.z] for q in lod.vertices],float)
            faces=[list(f.vertex_indices) for f in lod.faces]
            cache[model_name]=(v,faces,odol.parse_mode)
        v,faces,parse_mode=cache[model_name]
        m=np.asarray(obj['matrix'][:9],float).reshape(3,3)
        pos=np.asarray(obj['matrix'][9:],float)
        w=pos+v@m
        pix,depth=project(w)
        tri_polys=[]
        for face in faces:
            if len(face)<3: continue
            # Visible water LOD faces are triangles/quads; triangulate quads preserving the authored diagonal.
            tris=[face[:3]] if len(face)==3 else ([face[:3], [face[0],face[2],face[3]]] if len(face)==4 else [[face[0],face[i],face[i+1]] for i in range(1,len(face)-1)])
            for tri in tris:
                if not np.isfinite(pix[tri]).all(): continue
                p=Polygon(pix[tri])
                if p.is_valid and p.area>1e-9: tri_polys.append(p)
        if not tri_polys: continue
        surface=unary_union(tri_polys)
        for roi_name,(x1,y1,x2,y2) in ROIS.items():
            roi=box(x1,y1,x2,y2)
            inter=surface.intersection(roi)
            if inter.is_empty or inter.area<0.05: continue
            # Surface-vs-ROI containment distinguishes fully contained pieces, pieces crossing ROI bounds,
            # and pieces which cover the entire ROI. boundary contact is checked explicitly.
            roi_edge_through_surface=surface.intersection(roi.boundary).length
            piece_edge_inside_roi=surface.boundary.intersection(roi).length
            results[roi_name].append({'id':obj['id'],'model':model_name,'position':obj['matrix'][9:12],
                'parse_mode':parse_mode,'lod0_vertex_count':len(v),'lod0_face_count':len(faces),
                'projected_surface_area_px':float(surface.area),'overlap_area_px':float(inter.area),
                'fraction_piece_inside_roi':float(inter.area/surface.area) if surface.area else 0,
                'fraction_roi_covered':float(inter.area/roi.area), 'roi_contains_whole_piece':bool(roi.covers(surface)),
                'piece_contains_whole_roi':bool(surface.covers(roi)), 'roi_edge_through_surface_px':float(roi_edge_through_surface),
                'piece_edge_inside_roi_px':float(piece_edge_inside_roi),
                'screen_bounds':[float(q) for q in surface.bounds],
                'world_bounds_xyz':[float(w[:,i].min()) for i in range(3)]+[float(w[:,i].max()) for i in range(3)]})
    except Exception as e: errors.append({'id':obj['id'],'model':model_name,'error':f'{type(e).__name__}: {e}'})
for r in results.values(): r.sort(key=lambda q:q['overlap_area_px'],reverse=True)
summary={'source':{'wrp':str(WRP),'wrp_sha256':__import__('hashlib').sha256(WRP.read_bytes()).hexdigest(),'compiled_models':str(MODELS),
                   'projection_log':str(LOG),'capture':str(IMAGE),'capture_size':Image.open(IMAGE).size},
 'calibration':{'camera_id':camera[1],'camera_pose_fields':camera[2:],'fit_points':len(pts),'focal_px_x':float(fx),'focal_px_y':float(fy),
                'principal_px':[float(cx),float(cy)],'max_abs_residual_px':[float(np.max(np.abs(res[:,0]))),float(np.max(np.abs(res[:,1])))],
                'rmse_px':[float(np.sqrt(np.mean(res[:,0]**2))),float(np.sqrt(np.mean(res[:,1]**2)))],
                'camera_position':CAM.tolist(),'forward':FWD.tolist(),'right':RIGHT.tolist(),'up':UP.tolist()},
 'wrp':{'dimensions':wrp['dims'],'total_objects':len(wrp['objects']),'water_objects':len(allobjs),'candidate_objects_by_nearby_origins':len(selected),'unique_model_files_parsed':len(cache),'parse_errors':errors},
 'rois':world_rois,'intersections':results}
(OUT/'intersection-report.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
# Overlay polygons and ROI boxes on the exact 1920x1080 EV73 capture.
im=Image.open(IMAGE).convert('RGB'); dr=ImageDraw.Draw(im)
colors={'gray':(255,50,50),'wavy_control':(30,255,100)}
for name,(x1,y1,x2,y2) in ROIS.items():
    c=colors[name]; dr.rectangle((x1,y1,x2,y2),outline=c,width=2)
    for row in results[name]:
        b=row['screen_bounds']; dr.rectangle((b[0],b[1],b[2],b[3]),outline=c,width=1)
        # top contributors label at object origin projection
        pp,_=project([row['position']]); x,y=pp[0]
        if 0<=x<1920 and 0<=y<1080: dr.text((x,y),str(row['id']),fill=c,stroke_width=1,stroke_fill=(0,0,0))
im.save(OUT/'roi-footprints-overlay.png')
print(json.dumps({'out':str(OUT),'calibration':summary['calibration'],'wrp':summary['wrp'],'rois':{k:{'candidate_intersections':len(v),'top':v[:15]} for k,v in results.items()}},indent=2))





