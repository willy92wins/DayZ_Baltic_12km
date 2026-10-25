import json,sys,collections
from pathlib import Path
import numpy as np
from shapely.geometry import LineString,box
from shapely.ops import unary_union
W=Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev');sys.path.insert(0,str(W));sys.path.insert(0,str(W/'tools'/'terrain'));sys.path.insert(0,r'C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts')
from wrp0wzd import read as read_wrp
from odol_reader import ODOL
WRP=Path(r'E:\DayZ-Baltic-Build\v30-remaining-exact-dry-support-20261009\package\world\root\dayz_baltic_12km_dev\tb\narva_trial\baltic_trial.wrp');MODELS=Path(r'E:\DayZ-Baltic-Build\v30-native-terminal-finish-20261009\package\water\temp\baltic_water_v30');REPORT=Path(__file__).with_name('intersection-report.json')
CAM=np.array([2417.,65.,6745.]);F=np.array([0.,-.302244,.953231]);F/=np.linalg.norm(F);R=np.array([1.,0.,0.]);U=np.cross(F,R);f=654.5454758096084;cx,cy=960.,540.
def proj(w):
 d=w-CAM;z=d@F
 return np.array([cx+f*(d@R)/z,cy-f*(d@U)/z]),z
def line_parts(g):
 if g.is_empty:return []
 if g.geom_type=='Point':return [g]
 if g.geom_type=='LineString':return [LineString([g.coords[0],g.coords[-1]]).centroid]
 if g.geom_type in ('MultiPoint','GeometryCollection','MultiLineString'):
  out=[]
  for h in (g.geoms if hasattr(g,'geoms') else [g]):out.extend(line_parts(h))
  return out
 return []
def param_from_screen(a,b,pix,z0,z1):
 seg=np.array(b)-np.array(a); den=float(seg@seg); s=0 if den==0 else float((np.array(pix)-np.array(a))@seg/den);s=min(1,max(0,s));return s*z0/(s*z0+(1-s)*z1)
summary=json.load(open(REPORT));w=read_wrp(WRP);lookup={o['id']:o for o in w['objects']};out={}
for roiname,ids in {'gray':[16800157,16800158,16812769,16812770],'wavy_control':[16812763,16812764]}.items():
 x1,y1,x2,y2=summary['rois'][roiname]['pixels'];roi=box(x1,y1,x2,y2);items=[]
 for oid in ids:
  obj=lookup[oid];name=obj['name'].split('\\')[-1];p=ODOL.from_file(str(MODELS/name));lod=next(l for l in p.lods if l and abs(l.resolution-1)<.01);v=np.array([[a.x,a.y,a.z] for a in lod.vertices]);m=np.array(obj['matrix'][:9]).reshape(3,3);pos=np.array(obj['matrix'][9:]);world=pos+v@m;pix=[];depth=[]
  for q in world:
   a,b=proj(q);pix.append(a);depth.append(b)
  pix=np.array(pix);depth=np.array(depth);counts=collections.Counter()
  for face in lod.faces:
   fidx=face.vertex_indices
   for i in range(len(fidx)):
    a,b=sorted((fidx[i],fidx[(i+1)%len(fidx)]));counts[(a,b)]+=1
  boundaries=[]
  for (a,b),n in counts.items():
   if n!=1 or depth[a]<=0 or depth[b]<=0:continue
   ls=LineString([pix[a],pix[b]]);inside=ls.intersection(roi);cut=ls.intersection(roi.boundary)
   if inside.length<.03 and cut.is_empty:continue
   row={'vertex_ids':[a,b],'world_xyz':[world[a].tolist(),world[b].tolist()],'screen_xy':[pix[a].tolist(),pix[b].tolist()], 'piece_edge_inside_roi_px':float(inside.length),'roi_boundary_intersection_px':[]}
   for g in line_parts(cut):
    if g.geom_type=='Point':points=[(g.x,g.y)]
    else:points=[(g.coords[0][0],g.coords[0][1]),(g.coords[-1][0],g.coords[-1][1])]
    for xy in points:
     t=param_from_screen(pix[a],pix[b],xy,depth[a],depth[b]);wxyz=world[a]+t*(world[b]-world[a]);row['roi_boundary_intersection_px'].append({'pixel':[float(xy[0]),float(xy[1])],'world_xyz':wxyz.tolist()})
   boundaries.append(row)
  items.append({'id':oid,'model':name,'unique_boundary_edges':len(boundaries),'edges_inside_roi':sum(e['piece_edge_inside_roi_px']>.03 for e in boundaries),'edge_length_inside_roi_px':sum(e['piece_edge_inside_roi_px'] for e in boundaries),'edge_examples':boundaries[:20]})
 out[roiname]={'roi_pixels':[x1,y1,x2,y2],'objects':items}
(OUT:=Path(__file__).parent/'edge-crossings.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))


