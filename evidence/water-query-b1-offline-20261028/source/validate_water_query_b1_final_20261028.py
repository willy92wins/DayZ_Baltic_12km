"""Final offline correction gate; never deploys or starts DayZ."""
from pathlib import Path
import hashlib,json,subprocess,sys,time,re
R=Path(__file__).resolve().parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'water-query-b1-final-offline-20261028';O.mkdir(exist_ok=False)
sys.path.insert(0,str(W/'tools/quality'))
import water_query_diag_b1_ev112 as d
import numpy as np
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
start=time.monotonic()
selected=R/'dry-road-native-discriminators-a-20261028/selected-points.json'
original=R/'dry-road-full-native-20261028/probe/result.json'
native=R/'dry-road-full-native-20261028/probe/native.log'
assert sha(selected)=='14be579b0fd5a83f821422818b227a6100f0d224af999c352c68ed9b282e30c9'
assert sha(original)=='e717a124c38ff61b4af932793541ab78b7dfb703aea946d497c246b59ee33390'
assert sha(native)=='9a312ef6206c16c60590601ba716b6e5ec5affb0eadc550c475f384f2107095d'
paths=[selected,original,native,W/'plans/ev112-water-query-discriminator-b1-20261028.md',W/'tools/quality/water_query_diag_b1_ev112.py',W/'tools/quality/test_water_query_diag_b1_ev112.py',W/'missions/BalticWaterQueryB1.BalticTrial/init.c',Path(__file__)]
pins={str(p):sha(p) for p in paths}
points=d.source_points(json.loads(selected.read_bytes()),json.loads(original.read_bytes()))
csv=d.csv_for(points);d.check_csv(csv,points)
(O/'points.csv').write_bytes(csv.encode('utf-8'))
assert sha(O/'points.csv')=='1f75d141ef905e0d1a9aed851310311642e38982104c838fc7dcefaf224ef310'
(O/'points.json').write_text(json.dumps(points,indent=2)+'\n',encoding='utf-8')
oldlog=native.read_text().splitlines()[2:-1]
native_vectors=[]
pattern=re.compile(r'<-?\d+\.\d{6}, -?\d+\.\d{6}, -?\d+\.\d{6}>')
for line in oldlog:
    fields=line.split(';')
    for index in (10,13,20,21):
        assert pattern.fullmatch(fields[index]),'native_vector_format'
        native_vectors.append(fields[index])
assert len(native_vectors)==10632
checked=0
for p in points:
    x,z=map(np.float32,(p['x'],p['z']))
    assert d.f32(float(f'{float(x):.6f}'))==float(x) and d.f32(float(f'{float(z):.6f}'))==float(z),'actual_XZ_roundtrip'
    center=np.float32(p['ground'])
    for h in (np.nextafter(center,np.float32(-np.inf)),center,np.nextafter(center,np.float32(np.inf))):
        b=np.float32(p['effective_bed']) if p['effective_bed'] is not None else h
        water=np.float32(p['water_ext']) if p['water_ext'] is not None else None
        solid=max(h,b);top=max(solid,water) if water is not None else solid
        native_y=[np.float32(h+np.float32(.01)),np.float32(solid+np.float32(.01)),np.float32(top+np.float32(.25)),np.float32(h+np.float32(100)),np.float32(solid+np.float32(2))]
        # Independent NumPy float32 arithmetic plus observed formatting; consumer
        # uses struct and the more precise logged vector H, not scalar H.
        echoed_h=float(f'{float(h):.6f}');scalar_h=float(f'{float(h):.6g}')
        assert abs(scalar_h-echoed_h)<=d.scalar_error(scalar_h)+.500001e-6
        recovered=d.f32(echoed_h);rs=max(recovered,float(b));rt=max(rs,float(water)) if water is not None else rs
        predicted=[d.f32(recovered+d.f32(.01)),d.f32(d.f32(rs)+d.f32(.01)),d.f32(d.f32(rt)+.25),d.f32(recovered+100),d.f32(d.f32(rs)+2)]
        for actual,expected in zip(native_y,predicted):
            assert d.origin_matches([float(f'{float(x):.6f}'),float(f'{float(actual):.6f}'),float(f'{float(z):.6f}')],[float(x),expected,float(z)],.500001e-6+.5*d.ulp32(recovered)),'native_Y_rounding'
            checked+=1
test=subprocess.run([sys.executable,'-I',str(W/'tools/quality/test_water_query_diag_b1_ev112.py')],cwd=W,capture_output=True,text=True,timeout=120,creationflags=0x08000000)
(O/'tests.log').write_text(test.stdout+test.stderr,encoding='utf-8')
assert test.returncode==0 and 'Ran 26 tests' in test.stderr
validator=Path('C:/Users/guill/DayZ-Modding-Knowledge-Pack/tools/dayz-script-validator/scripts/script_validator.py')
bootstrap="import runpy,sys;sys.path.insert(0,"+repr(str(validator.parent))+");sys.argv=["+repr(str(validator))+","+repr(str(W/'missions/BalticWaterQueryB1.BalticTrial'))+"];runpy.run_path(sys.argv[0],run_name='__main__')"
lint=subprocess.run([sys.executable,'-I','-c',bootstrap],cwd=W,capture_output=True,text=True,timeout=120,creationflags=0x08000000)
(O/'lint.json').write_text(lint.stdout,encoding='utf-8');(O/'lint-stderr.txt').write_text(lint.stderr,encoding='utf-8')
l=json.loads(lint.stdout);assert lint.returncode==0 and l['status']=='PASS' and l['info']['files_scanned']==1 and not l['errors'] and not l['warnings']
assert all(sha(p)==h for p,h in pins.items()) and time.monotonic()-start<120
result=dict(status='OFFLINE_CONTRACT_VALIDATED_NOT_READY_FOR_DAYZ',points=len(points),rounds=3,native_rows_expected=345,tests=26,lint_files=1,native_format_vectors_checked=len(native_vectors),actual_coordinate_roundtrips=230,independent_numpy_Y_rounding_cases=checked,seconds=time.monotonic()-start,interpreter=sys.executable,worktree=str(W),inputs=pins,csv_sha256=sha(O/'points.csv'),points_sha256=sha(O/'points.json'),limits=['No B1 engine compilation or native measurements.','No deployment, lifecycle binder or admission gate.','Original2658 FAIL and product reference INCONCLUSIVE preserved.'])
(O/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))
