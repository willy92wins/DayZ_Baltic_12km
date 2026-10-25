"""Validate temporal diagnostic completeness and report scalar semantics; no visual PASS."""
from pathlib import Path
import json,hashlib,math
import numpy as np
R=Path(__file__).parent
ref=json.loads((R/'reference.json').read_text());path=R/'snapshot.log'
lines=[s.split(';') for s in path.read_text().splitlines() if s]
assert lines[0]==['BALTIC_SCALAR_MARGIN_V1','8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b']
n=len(ref['points']);times=[v for v in lines if v[0]=='T'];points=[v for v in lines if v[0]=='P'];end=[v for v in lines if v[0]=='END']
assert len(times)==241 and len(points)==241*n and end==[['END','241',str(n)]]
assert [int(v[1]) for v in times]==list(range(241))
assert [(int(v[1]),int(v[2])) for v in points]==[(s,i) for s in range(241) for i in range(n)]
assert min(float(v[3]) for v in times)>=19.999 and max(float(v[3]) for v in times)<=20.001
assert all(int(b[2])>int(a[2]) for a,b in zip(times,times[1:]))
rows=[]
for i,q in enumerate(ref['points']):
 data=[points[s*n+i] for s in range(241)]
 vals=np.array([[float(v[j]) for j in (3,6,7,8,9)] for v in data])
 assert np.isfinite(vals).all() and np.max(np.abs(vals[:,0]-q['H']))<.001
 sea=sum(v[4]=='true' for v in data);pond=sum(v[5]=='true' for v in data)
 ground,nominal,fake,dh,db=vals.T
 rows.append({**q,'sea_samples':sea,'pond_samples':pond,
  'nominal_min_max': [float(nominal.min()),float(nominal.max())],
  'fake_above_nominal_min_max':[float((fake-nominal).min()),float((fake-nominal).max())],
  'fake_above_ground_max':float((fake-ground).max()),
  'depth_H_min_max':[float(dh.min()),float(dh.max())],
  'depth_at_old_B_query_min_max':[float(db.min()),float(db.max())],
  'depth_H_positive_over_2cm_samples':int(np.count_nonzero(dh>.02)),
  'depth_B_query_positive_over_2cm_samples':int(np.count_nonzero(db>.02)),
  'depth_matches_fake_surface_error_max':float(np.max(np.abs(dh-(fake-ground-.01)))),
  'query_height_shift_error_max':float(np.max(np.abs((dh-db)-(q['B']-ground))))})
changed=rows[:162]
summary={'observed_seconds':(int(times[-1][2])-int(times[0][2]))/1000,'changed_points':162,'controls':n-162,
 'changed_any_presence_flag':sum(q['sea_samples']+q['pond_samples']>0 for q in changed),
 'changed_positive_depth_at_H':sum(q['depth_H_positive_over_2cm_samples']>0 for q in changed),
 'changed_positive_depth_at_B_query':sum(q['depth_B_query_positive_over_2cm_samples']>0 for q in changed),
 'new_positive_at_H_not_B_query_ids':[q['id'] for q in changed if q['depth_H_positive_over_2cm_samples'] and not q['depth_B_query_positive_over_2cm_samples']],
 'max_height_shift_error_m':max(q['query_height_shift_error_max'] for q in changed),
 'max_depth_fake_surface_error_m':max(q['depth_matches_fake_surface_error_max'] for q in changed),
 'max_fake_above_nominal_m':max(q['fake_above_nominal_min_max'][1] for q in changed)}
out={'status':'COMPLETE_TEMPORAL_DIAGNOSTIC','summary':summary,'points':rows,
 'snapshot_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256((R/'reference.json').read_bytes()).hexdigest(),
 'limits':ref['limits']+['Completeness success is not terrain acceptance or a cause for gray rectangles.']}
(R/'series-review.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'summary':summary,'snapshot_sha256':out['snapshot_sha256']},indent=2))
