from pathlib import Path
import json,hashlib,shutil
import numpy as np
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
ref=json.loads((E/'anomaly-temporal-reference.json').read_text());points=ref['points'];n=len(points)
profile=Path('P:/DayZ_MCP_dev/_server/profiles')
log=profile/'baltic_v30_water_anomaly_temporal_v1.log';orderlog=profile/'baltic_v30_water_anomaly_order_v1.log'
text=log.read_text();order=orderlog.read_text()
def judge(text):
    rows=[s.split(';') for s in text.splitlines()];errors=[]
    if any(r[0]=='FAIL' for r in rows):errors.append('runtime_FAIL')
    if sum(r==['END','62',str(n)] for r in rows)!=1:errors.append('END')
    rr=[r for r in rows if r[0]=='T']
    if len(rr)!=62*n or any(len(r)!=17 for r in rr):return ['schema_or_count'],None
    a=np.array([[float(v) if v not in ('true','false') else int(v=='true') for v in r[1:]] for r in rr]).reshape(62,n,16)
    if not np.isfinite(a).all():errors.append('nonfinite')
    if not np.array_equal(a[:,:,0],np.repeat(np.arange(62)[:,None],n,axis=1)):errors.append('sample_order')
    if not np.array_equal(a[:,:,1],np.repeat(np.arange(n)[None,:],62,axis=0)):errors.append('point_order')
    if np.max(np.abs(a[:,:,3]-np.array([p['expected_ground'] for p in points])))>.001:errors.append('ground_reference')
    if (np.diff(a[:,:,2],axis=0)<2000).any():errors.append('sample_cadence')
    if np.max(np.abs(a[:31,:,14]-.1))>.01 or np.min(a[31:,:,14])<19.9:errors.append('wind_phase')
    return errors,a
errors,a=judge(text);assert a is not None
negatives={}
negatives['missing_END']=bool(judge('\n'.join(s for s in text.splitlines() if not s.startswith('END;')))[0])
negatives['missing_point']=bool(judge('\n'.join(s for s in text.splitlines() if not s.startswith('T;3;2;')))[0])
first=next(s for s in text.splitlines() if s.startswith('T;0;0;'));parts=first.split(';');parts[4]=str(float(parts[4])+1)
negatives['wrong_ground']=bool(judge(text.replace(first,';'.join(parts),1))[0]);assert all(negatives.values())
orows=[r.split(';') for r in order.splitlines() if r.startswith('O;')]
assert len(orows)==62*n and all(len(r)==7 for r in orows)
oa=np.array([[float(v) for v in r[1:]] for r in orows]).reshape(62,n,6)
assert np.array_equal(oa[:,:,:2],a[:,:,:2])
point_reports=[]
for i,p in enumerate(points):
    v=a[:,i,:]
    point_reports.append(dict(point=p,ground=float(v[0,3]),presence_count=int(np.count_nonzero(v[:,4]+v[:,5])),
        no_fake_range=[float(v[:,6].min()),float(v[:,6].max())],with_fake_range=[float(v[:,7].min()),float(v[:,7].max())],
        with_fake_above_ground_max_m=float(np.max(v[:,7]-v[:,3])),depth_range=[float(v[:,8].min()),float(v[:,8].max())],
        query_order_max_delta_m=float(np.max(np.ptp(oa[:,i,3:6],axis=1)))))
report=dict(status='PASS_BOUNDED_NATIVE_TEMPORAL_READBACK' if not errors else 'FAIL',errors=errors,negatives=negatives,points=n,samples=62,
    max_ground_error_m=float(np.max(np.abs(a[:,:,3]-np.array([p['expected_ground'] for p in points])))),
    query_order_max_delta_m=float(np.max(np.ptp(oa[:,:,3:6],axis=2))),
    results=point_reports,terrain_sha256=ref['terrain_sha256'],pbo=ref['pbo'],
    limits=ref['limits']+['One minute per calm/storm phase, not all tide dates or a shader acceptance.'])
(E/'anomaly-temporal-verification.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(log,E/'anomaly-temporal-runtime.log');shutil.copyfile(orderlog,E/'anomaly-temporal-order.log')
print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2))
for r in point_reports:
    if r['point']['role'].startswith('calibrated'):print(json.dumps(r))
