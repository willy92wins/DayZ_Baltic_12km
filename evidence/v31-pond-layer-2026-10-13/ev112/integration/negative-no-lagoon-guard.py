from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial import cKDTree
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');sys.path.insert(0,str(P/'tools/water'));import shore_ramp_v31 as sr
D=O/'review-terrain-r1-evidence';rep=json.loads((D/'findings.json').read_text());rep['inputs']['final']['path']=str(O/'terrain-ev112-b.npz');rep['inputs']['footprint']['path']=str(O/'fp-ev112-c/footprint.npz');hb=np.load(rep['inputs']['before_despike']['path'])['heights'];ha=np.load(rep['inputs']['final']['path'])['heights'];fb=np.load(O.parent/'ev112-ot4-20261018/frozen-six-replay-b/gate/fp-after/footprint.npz');fa=np.load(rep['inputs']['footprint']['path']);W,fp=sr.corner_water(fa['plane'],fa['field']);lag=json.loads((O.parent/'lagoons-report.json').read_text())['lagoons'];rows=[]
for d in rep['lagoon_vertices']:
 r,c=d['row'],d['col'];r0,r1,c0,c1=r-4,r+4,c-4,c+4;sets=[]
 for h in (hb,ha):
  seg=sr.extract_segments(h.astype(float),W,fp,fa['plane'],r0,r1,c0,c1);pts=seg['p'].reshape(-1,2);sets.append((seg,pts))
 s0,s1=sets[0][0],sets[1][0];same=np.array_equal(s0['key'],s1['key']);delta=float(np.max(abs(s1['p']-s0['p']),initial=0)) if same else None
 incident=[]
 for cr in (r-1,r):
  for cl in (c-1,c):
   for ti,idx in enumerate(sr.TRIS):
    rc=[(cr+sr.COFF[k][0],cl+sr.COFF[k][1]) for k in idx]
    if (r,c) in rc:
     incident.append(dict(cell=[cr,cl],triangle=ti,wet_before=[bool(hb[tr,tc]<W[cr,cl,k]) for (tr,tc),k in zip(rc,idx)],wet_after=[bool(ha[tr,tc]<W[cr,cl,k]) for (tr,tc),k in zip(rc,idx)]))
 e=min(lag,key=lambda t:(t['x']-d['x'])**2+(t['z']-d['z'])**2)
 vid=r*sr.N+c;edge_points=[]
 for sg,pts in sets:
  keys=sg['key'].ravel();hit=(keys//(sr.N*sr.N)==vid)|(keys%(sr.N*sr.N)==vid);kk=keys[hit];pp=pts[hit];order=np.argsort(kk);edge_points.append((kk[order],pp[order]))
 same_incident=np.array_equal(edge_points[0][0],edge_points[1][0]);incident_delta=float(np.max(abs(edge_points[1][1]-edge_points[0][1]),initial=0)) if same_incident else None
 rows.append(dict(x=d['x'],z=d['z'],before=float(hb[r,c]),after=float(ha[r,c]),nearest_original_lagoon=e,waterline_edge_ids_identical=same,max_waterline_endpoint_delta_in_24m_box=delta,incident_crossed_edges=len(edge_points[0][0]),incident_edge_ids_identical=same_incident,incident_waterline_delta_m=incident_delta,triangles=incident))
assert len(rows)==5 and all(v['incident_edge_ids_identical'] and v['incident_waterline_delta_m']==0 for v in rows),rows
out=dict(scope='Lagoon regression: the two shoreline vertices stay unchanged with the added lagoon shore guard. Three dry peaks may still be adjusted.',footprint_arrays_identical={k:bool(np.array_equal(fb[k],fa[k],equal_nan=fb[k].dtype.kind=='f')) for k in fb.files},vertices=rows)
(O/'review-terrain-r1-evidence-c/negative-unexpected-pass.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print(json.dumps(out),flush=True)
