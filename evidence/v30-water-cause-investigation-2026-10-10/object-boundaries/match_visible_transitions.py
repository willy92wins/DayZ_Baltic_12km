import json,sys,collections,math
from pathlib import Path
import numpy as np
from shapely.geometry import LineString,box
from shapely.ops import unary_union
W=Path(r'C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev');sys.path.insert(0,str(W));sys.path.insert(0,str(W/'tools'/'terrain'));sys.path.insert(0,r'C:\Users\guill\.claude\skills\dayz-p3d-debinarizer\scripts')
from wrp0wzd import read as read_wrp
from odol_reader import ODOL
WRP=Path(r'E:\DayZ-Baltic-Build\v30-remaining-exact-dry-support-20261009\package\world\root\dayz_baltic_12km_dev\tb\narva_trial\baltic_trial.wrp');MODELS=Path(r'E:\DayZ-Baltic-Build\v30-native-terminal-finish-20261009\package\water\temp\baltic_water_v30');OUT=Path(__file__).parent
CAM=np.array([2417.,65.,6745.]);F=np.array([0.,-.302244,.953231]);F/=np.linalg.norm(F);R=np.array([1.,0.,0.]);U=np.cross(F,R);f=654.5454758096084;cx,cy=960.,540.
def project(w):
 d=w-CAM;z=d@F
 return np.array([cx+f*(d@R)/z,cy-f*(d@U)/z]),z
# Visual estimates from exact EV73 capture; lines are approximate pixel selections, not semantic masks.
targets={'smooth-to-ripple':{'line':LineString([(635,707),(780,707)]),'tolerance_px':2.0},
         'far-patch-top-edge':{'line':LineString([(890,660),(936,660)]),'tolerance_px':2.0}}
# Conservative broad world box around both projected transition neighborhoods.
wrp=read_wrp(WRP);objs=[o for o in wrp['objects'] if o['name'].lower().startswith('baltic_water_v30\\') and 2290<=o['matrix'][9]<=2480 and 6780<=o['matrix'][11]<=6930]
results={k:[] for k in targets}; parse_errors=[]
for obj in objs:
 name=obj['name'].split('\\')[-1];path=MODELS/name
 try:
  p=ODOL.from_file(str(path));lod=next((l for l in p.lods if l and abs(l.resolution-1)<.01),None)
  if lod is None:continue
  v=np.array([[x.x,x.y,x.z] for x in lod.vertices]);m=np.array(obj['matrix'][:9]).reshape(3,3);pos=np.array(obj['matrix'][9:]);world=pos+v@m
  pix=np.full((len(v),2),np.nan);depth=np.zeros(len(v))
  for i,q in enumerate(world):pix[i],depth[i]=project(q)
  edges=collections.Counter()
  for face in lod.faces:
   ix=face.vertex_indices
   for i in range(len(ix)):edges[tuple(sorted((ix[i],ix[(i+1)%len(ix)])))]+=1
  bound=[]
  for (a,b),n in edges.items():
   if n==1 and depth[a]>0 and depth[b]>0:
    line=LineString([pix[a],pix[b]])
    if line.length:bound.append((line,a,b))
  for label,t in targets.items():
   tol=t['tolerance_px']; target=t['line']; matches=[]
   (t0,t1)=target.coords; p0=np.array(t0,float); axis=(np.array(t1,float)-p0); target_len=float(np.linalg.norm(axis)); axis/=target_len
   for line,a,b in bound:
    e0=np.array(pix[a],float); e1=np.array(pix[b],float); ev=e1-e0; el=float(np.linalg.norm(ev))
    if el<1e-8:continue
    angle=math.degrees(math.acos(min(1.,abs(float((ev/el)@axis)))))
    if angle>5.0:continue
    d0=abs(float(axis[0]*(e0-p0)[1]-axis[1]*(e0-p0)[0])); d1=abs(float(axis[0]*(e1-p0)[1]-axis[1]*(e1-p0)[0]))
    if max(d0,d1)>tol:continue
    s0=float((e0-p0)@axis); s1=float((e1-p0)@axis)
    overlap=max(0.,min(max(s0,s1),target_len)-max(min(s0,s1),0.))
    if overlap<2.0:continue
    matches.append({'mean_pixel_offset_px':float((d0+d1)/2),'max_endpoint_offset_px':float(max(d0,d1)),
      'parallel_angle_deg':float(angle),'projected_overlap_px':float(overlap),'world_edge_xyz':[world[a].tolist(),world[b].tolist()],
      'screen_edge_xy':[pix[a].tolist(),pix[b].tolist()],'id':obj['id'],'model':name,'parse_mode':p.parse_mode})
   if matches:results[label].extend(matches)
 except Exception as e:parse_errors.append({'id':obj['id'],'model':name,'error':f'{type(e).__name__}: {e}'})
for k in results:results[k].sort(key=lambda r:(r['mean_pixel_offset_px'],-r['projected_overlap_px']))
report={'image':r'E:\DayZ-Baltic-Build\v30-base-surface-runtime-20261009\capture_20261009_233431_541.jpg','targets':{k:{'pixel_endpoints':list(v['line'].coords),'tolerance_px':v['tolerance_px']} for k,v in targets.items()},'search_objects':len(objs),'parse_errors':parse_errors,'matches':{k:v[:40] for k,v in results.items()}}
(OUT/'visible-transition-matches.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'search_objects':len(objs),'errors':parse_errors,'matches':{k:v[:12] for k,v in results.items()}},indent=2))



