"""Filesystem identity regressions; fixture identities are synthetic, never runs."""
from pathlib import Path
import copy,hashlib,json,subprocess,sys,tempfile
R=Path(__file__).resolve().parent;source=R/'consume_dry_road_full_native_20261028.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v),encoding='utf-8')
def read(p):return json.loads(p.read_bytes())
native=R/'buried-roadway-semantics-20261028';small=read(native/'points.json')['points'];rows=[]
for s in small:rows.append(dict(id=s['id'],x=s['x'],z=s['z'],ground=s['ground'],effective_bed=s['bed'],water_ext=None,roadway=max(s['ground'],s['bed']),expect='dry',uncertain=[],bed_shapes=['baltic_stream_pilot/cs_kit_118_0000.p3d']))
results=[]
for case in ('positive','stale_log','pid_creation','mission','packages','cleanup','calibration_order','calibration_value_drift','accepted_value_drift'):
    with tempfile.TemporaryDirectory(prefix='baltic-binding-test-') as temp:
        root=Path(temp);o=root/'dry-road-full-native-20261028';o.mkdir();runner=root/source.name;runner.write_bytes(source.read_bytes())
        assets={}
        for name in ('engine.exe','bridge.pbo','world.pbo','water.pbo','pilot.pbo'):
            p=root/name;p.write_bytes(('FIXTURE ONLY '+name).encode());assets[name]=p
        pre=dict(executable=str(assets['engine.exe']),executable_sha256=sha(assets['engine.exe']),bridge_pbo=str(assets['bridge.pbo']),bridge_sha256=sha(assets['bridge.pbo']))
        packages={str(p):sha(p) for n,p in assets.items() if n.endswith('.pbo')};deployed={p:h for p,h in packages.items() if p!=pre['bridge_pbo']};inputs={};units={}
        for mode in ('calibration','probe'):
            d=o/mode;d.mkdir();mission=root/(mode+'.BalticTrial');mission.mkdir();(mission/'init.c').write_bytes(b'// fixture only');inputs[str(mission/'init.c')]=sha(mission/'init.c')
            units[mode]=dict(mission=str(mission),producer_sha256=sha(mission/'init.c'),count=289 if mode=='calibration' else 16)
            created='2026-10-28T09:00:00+00:00' if mode=='calibration' else '2026-10-28T10:00:00+00:00';run='fixture-'+mode
            log=(R/'kit7-overlap-native-20261026/calibration/native.log') if mode=='calibration' else native/'run/native.log';(d/'native.log').write_bytes(log.read_bytes())
            host=dict(run_id=run,pid=42,created_utc=created,navmesh_data_server=True,mission_path=str(mission),mission_sha256=units[mode]['producer_sha256'],executable_file_sha256=pre['executable_sha256'],executable=str(assets['engine.exe']),package_hashes=packages)
            m=dict(run_id=run,server_run_id=run,server_binding='BOUND',version_state='ok',poll_age_s=1,processes=[dict(role='server',pid=42,creation_time_utc=created)],client_diagnostics=[dict(state='not_started')])
            capture=dict(pid=42,created_utc=created,last_write_utc='2026-10-28T10:01:00+00:00',sha256=sha(d/'native.log'),count=units[mode]['count'])
            cleanup=dict(close=dict(run_id=run,run_retired=True),self=dict(state='none'),own_run_present=False,pending_commands=0,cleanup_degraded=[],error=None,cleanup_error=None)
            for name,value in [('host-identity.json',host),('mcp-identity.json',m),('log-capture.json',capture),('cleanup.json',cleanup),('launch.json',dict(run_id=run,status='succeeded'))]:dump(d/name,value)
        csv=''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in rows);(Path(units['probe']['mission'])/'points.csv').write_text(csv,encoding='ascii',newline='\n')
        dump(o/'points.json',dict(points=rows));dump(o/'prelaunch.json',pre);dump(o/'deployment.json',dict(units=units,deployed=deployed,inputs=inputs));dump(o/'accepted.json',dict(status='REVIEWED_FULL_NATIVE_READY',inputs={str(o/n):sha(o/n) for n in ('points.json','prelaunch.json','deployment.json')}))
        for unit in ('calibration','probe'):
            path=o/unit/'launch.json';launch=read(path);launch.update(mode=unit,accepted_sha256=sha(o/'accepted.json'));dump(path,launch)
        q=subprocess.run([sys.executable,'-I',str(runner),'calibration'],capture_output=True,text=True,timeout=30,creationflags=0x08000000);assert q.returncode==0,q.stderr
        d=o/'probe'
        launch=read(d/'launch.json');launch['calibration_sha256']=sha(o/'calibration/result.json');dump(d/'launch.json',launch)
        if case in ('stale_log','pid_creation'):
            p=d/'log-capture.json';x=read(p);x['last_write_utc' if case=='stale_log' else 'created_utc']='2026-10-27T10:01:00+00:00';dump(p,x)
        elif case in ('mission','packages'):
            p=d/'host-identity.json';x=read(p)
            if case=='mission':x['mission_sha256']='0'*64
            else:x['package_hashes'][pre['bridge_pbo']]='0'*64
            dump(p,x)
        elif case=='accepted_value_drift':
            p=o/'accepted.json';x=read(p);x['changed_after_launch']=True;dump(p,x)
        elif case=='cleanup':
            p=d/'cleanup.json';x=read(p);x['close']['run_retired']=False;dump(p,x)
        elif case in ('calibration_order','calibration_value_drift','accepted_value_drift'):
            p=o/'calibration/result.json';x=read(p)
            if case=='calibration_order':x['created_utc']='2026-10-29T10:00:00+00:00'
            else:x['calibration']['margin_m']+=.0005
            dump(p,x)
        q=subprocess.run([sys.executable,'-I',str(runner),'probe'],capture_output=True,text=True,timeout=30,creationflags=0x08000000);expected_pass=case=='positive'
        results.append(dict(case=case,returncode=q.returncode,expected_pass=expected_pass,verified=(q.returncode==0)==expected_pass,diagnostic=q.stderr[-600:]))
doc=dict(status='BINDER_CONTROLS_PASS' if all(x['verified'] for x in results) else 'BINDER_CONTROLS_FOUND_GAP',source_sha256=sha(source),tests=results,limits=['Synthetic process/mission identities around recorded logs. No new native run or calibration.'])
out=R/'dry-road-full-binding-tests-r2-20261028.json';assert not out.exists();dump(out,doc);print(json.dumps(doc))
