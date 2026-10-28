"""Exercise the exact launch gate on isolated synthetic filesystem fixtures."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile
R=Path(__file__).resolve().parent;source=R/'check_dry_road_full_gate_20261028.py';cases=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v),encoding='utf-8')
for case in ('calibration_ok','probe_ok','missing_calibration_hash','wrong_calibration_hash','engine_drift','log_drift','deployment_drift','already_launched'):
    with tempfile.TemporaryDirectory(prefix='baltic-gate-test-') as temp:
        root=Path(temp);out=root/'dry-road-full-native-20261028';out.mkdir();(out/'probe').mkdir();(out/'calibration').mkdir()
        runner=root/source.name;runner.write_bytes(source.read_bytes())
        payloads={}
        for name in ('engine.exe','bridge.pbo','world.pbo','water.pbo','pilot.pbo','calibration.log'):
            p=root/name;p.write_bytes(('FIXTURE ONLY '+name).encode());payloads[name]=p
        deployed={str(payloads[n]):sha(payloads[n]) for n in ('world.pbo','water.pbo','pilot.pbo')}
        pre=dict(executable=str(payloads['engine.exe']),executable_sha256=sha(payloads['engine.exe']),bridge_pbo=str(payloads['bridge.pbo']),bridge_sha256=sha(payloads['bridge.pbo']))
        dep=dict(mod='@fixture',units={m:dict(mission='fixture') for m in ('calibration','probe')},inputs={},deployed=deployed)
        dump(out/'deployment.json',dep);dump(out/'prelaunch.json',pre);dump(out/'points.json',{})
        accept=dict(status='REVIEWED_FULL_NATIVE_READY',inputs={str(out/n):sha(out/n) for n in ('deployment.json','prelaunch.json','points.json')});dump(out/'accepted.json',accept);seal=sha(out/'accepted.json')
        ref=dict(status='CALIBRATION_PASS',identity_bound=True,packages={**deployed,pre['bridge_pbo']:pre['bridge_sha256']},engine_sha256=pre['executable_sha256'],inputs={str(payloads['calibration.log']):sha(payloads['calibration.log'])})
        dump(out/'calibration/result.json',ref);calhash=sha(out/'calibration/result.json');mode='calibration' if case=='calibration_ok' else 'probe'
        args=[sys.executable,'-I',str(runner),mode,seal]
        if mode=='probe' and case!='missing_calibration_hash':args.append('0'*64 if case=='wrong_calibration_hash' else calhash)
        if case=='engine_drift':payloads['engine.exe'].write_bytes(b'changed')
        elif case=='log_drift':payloads['calibration.log'].write_bytes(b'changed')
        elif case=='deployment_drift':dump(out/'deployment.json',{})
        elif case=='already_launched':dump(out/'probe/launch.json',dict(run_id='fixture'))
        q=subprocess.run(args,capture_output=True,text=True,timeout=20,creationflags=0x08000000)
        if q.returncode==0:
            parsed=json.loads(q.stdout);assert parsed['mode']==mode and parsed['accepted_sha256']==seal and parsed['calibration_sha256']==(calhash if mode=='probe' else None)
        expected=case.endswith('_ok');assert (q.returncode==0)==expected,(case,q.stderr)
        cases.append(dict(case=case,expected_pass=expected,returncode=q.returncode,verified=True))
result=dict(status='EIGHT_PRE_FIFO_GATE_CONTROLS_PASS',script_sha256=sha(source),cases=cases,limits=['Synthetic filesystem binding controls only; no MCP request or DayZ run.'])
dest=R/'dry-road-full-gate-tests-r2-20261028.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
