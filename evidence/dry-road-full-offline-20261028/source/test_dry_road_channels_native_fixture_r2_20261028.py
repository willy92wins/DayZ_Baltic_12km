"""Consumer regression on a real frozen log, NOT a fresh calibrated native pass."""
from pathlib import Path
import copy,json,sys,hashlib
R=Path(__file__).resolve().parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');sys.path.insert(0,str(W/'tools/quality'))
from dry_road_native_consumer_ev112 import evaluate,calibrate,require
O=R/'dry-road-channels-native-fixture-r2-20261028';O.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
native=R/'buried-roadway-semantics-20261028/run/result.json';oldcal=R/'kit7-overlap-native-20261026/calibration/native.log'
doc=json.loads(native.read_bytes());require(doc['status']=='SEMANTICS_OBSERVED_AT_SAMPLES' and doc['identity_bound'],'fixture_not_bound')
cal=calibrate(oldcal.read_text(encoding='utf-8-sig'));points=[];rows={}
for v in doc['rows']:
    i=v['id'];m=v['measured'];points.append(dict(id=i,x=m['rv_pos'][0],z=m['rv_pos'][2],ground=v['expected_ground'],effective_bed=v['expected_bed'],water_ext=None,roadway=max(v['expected_ground'],v['expected_bed']),expect='dry',uncertain=[],bed_shapes=['baltic_stream_pilot\\cs_kit_118_0000.p3d']));rows[i]=m
# Expected XZ comes from the frozen source points, never from measured ray hits.
sources=json.loads((R/'buried-roadway-semantics-20261028/points.json').read_bytes())['points']
for p,s in zip(points,sources):require(p['id']==s['id'],'fixture_id');p['x']=s['x'];p['z']=s['z']
base=evaluate(points,rows,cal);require(base['status']=='SERVER_PROBE_PASS','real_fixture_positive')
out=[]
for kind in ('ground','roadway','water','rv','bullet','missing_id','boundary_does_not_mask_failure'):
    p=copy.deepcopy(points);m=copy.deepcopy(rows)
    if kind=='ground':m[0]['ground']+=.02
    elif kind=='roadway':m[0]['road']+=.04
    elif kind=='water':m[0]['pond']=True;m[0]['depth']=.2
    elif kind=='rv':m[0]['rv_pos'][1]+=.04
    elif kind=='bullet':m[0]['bullet_pos'][1]+=.04
    elif kind=='missing_id':del m[0]
    else:p[0]['uncertain']=['water_boundary_numeric'];m[0]['ground']+=.02
    try:
        q=evaluate(p,m,cal);rejected=q['status']=='FAIL'
    except ValueError:rejected=True
    require(rejected,'negative_not_rejected:'+kind);out.append(dict(kind=kind,rejected=True))
paths=[native,oldcal,R/'buried-roadway-semantics-20261028/points.json',W/'tools/quality/dry_road_native_consumer_ev112.py',Path(__file__).resolve()]
result=dict(status='CONSUMER_REAL_FIXTURE_REGRESSION_PASS',positive_samples=16,negatives=out,calibration_source='Historical2026-10-26; NOT a fresh runtime calibration',new_native_run=False,inputs={str(p):sha(p) for p in paths},limits=['Regression of code on recorded native measurements only.','Full2658 probe and fresh calibration remain unexecuted.'])
(O/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))
