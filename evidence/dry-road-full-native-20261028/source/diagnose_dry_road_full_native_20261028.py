"""Single bounded classification of saved native measurements; no verdict rewrites."""
from pathlib import Path
import hashlib,json,math,collections,time
R=Path(__file__).resolve().parent;O=R/'dry-road-full-native-diagnosis-20261028'
O.mkdir(exist_ok=False);started=time.monotonic()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
S=R/'dry-road-full-native-20261028';result=read(S/'probe/result.json');cal=read(S/'calibration/result.json')
assert result['identity_bound'] and result['status']=='FAIL' and result['points']==2658
rows=result['rows'];table=collections.Counter();failwater=[];collision=[];unique=set()
margin=cal['calibration']['margin_m']
for row in rows:
    p=row['expected'];m=row['measured'];b=p['effective_bed'];w=p['water_ext']
    relation='no_waterway' if w is None else 'bed_above_water' if b is not None and b>w else 'water_at_or_above_bed'
    table[(p['expect'],relation,m['pond'],row['states']['water'])]+=1
    bad=[k for k,v in row['states'].items() if v=='FAIL']
    if bad:unique.add(row['id'])
    if row['states']['water']=='FAIL':
        failwater.append(dict(id=row['id'],expect=p['expect'],x=p['x'],z=p['z'],bed_minus_water=None if b is None or w is None else b-w,water_minus_ground=None if w is None else w-p['ground'],pond=m['pond'],sea=m['sea'],depth=m['depth'],surface_delta=None if w is None else m['surface']-w,sources=p['sources']))
    if row['states']['rv']=='FAIL' or row['states']['bullet']=='FAIL':
        length=math.sqrt(sum(v*v for v in m['bullet_normal']))
        projected=None if not length or b is None else sum((c-a)*n/length for c,a,n in zip(m['bullet_pos'],(p['x'],b,p['z']),m['bullet_normal']))
        collision.append(dict(id=row['id'],x=p['x'],z=p['z'],states=row['states'],ground=p['ground'],bed=b,rv_shape=m['rv_shapes'],rv_height=m['rv_pos'][1],rv_delta_to_expected=None if b is None else m['rv_pos'][1]-max(b,p['ground']),bullet_shape=m['bullet_shape'],bullet_margin_error=None if projected is None else projected-margin,sources=p['sources']))
    assert time.monotonic()-started<120
report=dict(status='NATIVE_FAILURE_CLASSIFICATION_ONLY',source_verdict=result['status'],points=2658,failed_unique_points=len(unique),failure_channels=result['failure_count'],uncertain_unique_points=len({p['id'] for p in result['inconclusive']}),uncertain_channels=result['inconclusive_count'],
water_cross_tab=[dict(expect=a,bed_water_relation=b,pond=c,water_verdict=d,count=n) for (a,b,c,d),n in table.items()],
water_failures=failwater,collision_failures=collision,
limits=['No consumer or map mutation; original FAIL remains authoritative.','Correlations with bed-water height do not prove opaque engine semantics.','Tree identity is directly reported by both native ray consumers; the reason for the two other RV misses remains unproven.'],
inputs={str(p):sha(p) for p in [S/'probe/result.json',S/'probe/native.log',S/'calibration/result.json',Path(__file__)]})
(O/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('water_failures','inputs')},indent=2))

