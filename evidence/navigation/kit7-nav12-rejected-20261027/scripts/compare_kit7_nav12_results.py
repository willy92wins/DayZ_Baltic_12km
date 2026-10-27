"""Describe all native Nav12 outcomes; never turn a FAIL into an acceptance."""
from pathlib import Path
import hashlib,json,math
R=Path(__file__).parent;D=R/'kit7-nav12-consumer-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[R/'kit7-nav-consumer-20261026/result.json',R/'kit7-nav8-consumer-20261027/result.json',D/'result.json']
old,eight,new=map(read,paths)
assert not (D/'height-comparison.json').exists()
assert read(D/'identity-verification.json')['status']=='PASS_BOUND_NATIVE_PROBE_INPUTS'
assert sha(D/'queries.csv')=='305e808d58ac25d5fbf1a43a03eb1504600b102ebf433bca527395bfdcd6387d'
assert new['reference_sha256']==sha(D/'reference.json') and new['log_sha256']==sha(D/'runtime.log')
names=lambda value:{x['name'] for x in value['cases']}
assert names(old)==names(eight)==names(new) and len(new['cases'])==607
assert read(D/'reference.json')['max_waypoint_surface_error_m']==.801
original=['kit7_piece_124_right','kit7_piece_133_right','kit7_seam_124_right','kit7_seam_133_right']
rows=[dict(name=n,before_m=old['height_cases'][n]['max_surface_error_m'],nav8_m=eight['height_cases'][n]['max_surface_error_m'],nav12_m=new['height_cases'][n]['max_surface_error_m']) for n in original]
ordered=sorted((dict(name=n,**v) for n,v in new['height_cases'].items()),key=lambda x:x['max_surface_error_m'],reverse=True)
assert all(math.isfinite(x['max_surface_error_m']) for x in ordered)
report=dict(status=new['status'],scope='Description of exact native607 result; no RAM, actor or global acceptance',queries=607,tolerance_m=.801,original_four=rows,max_all_routes_m=ordered[0]['max_surface_error_m'],worst_routes=ordered[:20],height_issues=new['height_issues'],local_failures=new['local_failures'],case_failures=[c for c in new['cases'] if c['status']!='PASS'],inputs={str(p):sha(p) for p in paths+[D/'reference.json',D/'runtime.log',D/'queries.csv',D/'identity-verification.json']})
(D/'height-comparison.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:report[k] for k in ('status','queries','tolerance_m','original_four','max_all_routes_m','height_issues','local_failures')},indent=2))
