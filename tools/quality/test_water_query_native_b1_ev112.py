"""Fault injection against independent receipts and the B1 analytic producer fixture."""
from pathlib import Path
import copy,json,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import water_query_native_b1_ev112 as b
from test_water_query_diag_b1_ev112 import inputs,log_fixture
from water_query_diag_b1_ev112 import csv_for

def receipts():
    stamp='2026-10-28T13:00:00+00:00'
    packages={f'C:\\mod{i}\\Addons\\{i}.pbo':str(i)*64 for i in range(4)}
    d=dict(mission='C:\\missions\\B1.World',producer='C:\\missions\\B1.World\\init.c',
           engine='C:\\game\\DayZDiag_x64.exe',packages=packages)
    d['inputs']={d['producer']:'a'*64,d['engine']:'b'*64}
    h=dict(run_id='own-run',pid=100,created_utc=stamp,mission_path=d['mission'],mission_sha256='a'*64,
           executable=d['engine'],executable_file_sha256='b'*64,package_hashes=copy.deepcopy(packages),
           profiles='C:\\profiles\\own',host_raw_command_line_sha256='c'*64,server_config='C:\\server.cfg',
           server_config_sha256='d'*64,navmesh_data_server=True,file_patching=False,server_mods=[])
    m=dict(run_id='own-run',server_run_id='own-run',server_binding='BOUND',version_state='ok',poll_age_s=1,
           processes=[dict(role='server',pid=100,creation_time_utc=stamp)],client_diagnostics=[dict(state='not_started')])
    c=dict(pid=100,created_utc=stamp,last_write_utc=stamp,source='C:\\profiles\\own\\baltic_water_query_b1.log',count=345,sha256='e'*64)
    end=dict(close=dict(run_id='own-run',run_retired=True),self=dict(state='none'),own_run_present=False,pending_commands=0,cleanup_degraded=[],error=None,cleanup_error=None)
    return d,dict(status='succeeded',run_id='own-run'),h,copy.deepcopy(h),m,c,end,'e'*64

class NativeBindingTests(unittest.TestCase):
    def test_valid_receipts(self):
        b.identity(*receipts())

    def bad(self,index,key,value,match=None):
        r=list(receipts());r[index][key]=value
        with self.assertRaisesRegex(ValueError,match or '.'):b.identity(*r)

    def test_run_mismatch_all_receipts(self):
        for index,key in ((1,'run_id'),(2,'run_id'),(3,'run_id'),(4,'run_id'),(4,'server_run_id')):
            with self.subTest(index=index,key=key):self.bad(index,key,'foreign','run_binding')

    def test_pid_changed(self):self.bad(3,'pid',101,'process_binding')
    def test_creation_changed(self):self.bad(5,'created_utc','2026-10-28T13:00:01+00:00','creation_binding')
    def test_creation_format_rounding(self):
        r=list(receipts());r[4]['processes'][0]['creation_time_utc']='2026-10-28T13:00:00.000001+00:00'
        r[5]['last_write_utc']='2026-10-28T13:00:01+00:00'
        r[2]['created_utc']='2026-10-28T13:00:00.0000006+00:00';b.identity(*r)
        self.bad(3,'created_utc','2026-10-28T13:00:00.002001+00:00','creation_binding')
    def test_external_source_mode(self):
        for i in (2,3):
            self.bad(i,'file_patching',True,'external_source_mode')
            self.bad(i,'file_patching',None,'external_source_mode')
            self.bad(i,'server_mods',['C:\\foreign'],'external_source_mode')
    def test_close_absent(self):self.bad(6,'close',None,'lifecycle_not_closed')
    def test_official_stop(self):
        r=list(receipts());r[6]['close']['run_retired']=False
        r[6]['stop']=dict(run_id='own-run',status='succeeded');b.identity(*r)
        r[6]['stop']['run_id']='foreign'
        with self.assertRaisesRegex(ValueError,'lifecycle_not_closed'):b.identity(*r)
    def test_old_log(self):self.bad(5,'last_write_utc','2026-10-28T12:59:59+00:00','stale_log')
    def test_foreign_profile(self):self.bad(5,'source','C:\\other\\baltic_water_query_b1.log','profile_log_binding')
    def test_wrong_log_digest(self):self.bad(5,'sha256','f'*64,'log_binding')
    def test_bad_count(self):self.bad(5,'count',344,'log_binding')
    def test_bridge(self):
        for k,v in (('poll_age_s',11),('poll_age_s',float('nan')),('poll_age_s',-1),('server_binding','UNBOUND'),('version_state','stale')):
            with self.subTest(k=k,v=v):self.bad(4,k,v,'bridge_binding')
    def test_client(self):self.bad(4,'client_diagnostics',[dict(state='running')],'runtime_mode')
    def test_extra_server(self):
        r=list(receipts());r[4]['processes']*=2
        with self.assertRaisesRegex(ValueError,'process_count'):b.identity(*r)
    def test_wrong_mission(self):self.bad(2,'mission_path','C:\\missions\\Other.World','mission_binding')
    def test_engine(self):self.bad(2,'executable_file_sha256','z'*64,'engine_binding')
    def test_packages(self):
        for mutation in ('extra','missing','hash','same_basename'):
            r=list(receipts());p=r[2]['package_hashes'];key=next(iter(p))
            if mutation=='extra':p['C:\\extra.pbo']='1'*64
            elif mutation=='missing':p.pop(key)
            elif mutation=='hash':p[key]='f'*64
            else:p['C:\\elsewhere\\0.pbo']=p.pop(key)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):b.identity(*r)
    def test_host_drift(self):self.bad(3,'server_config_sha256','f'*64,'runtime_changed')
    def test_incomplete_close(self):
        for key,val in (('close',dict(run_id='own-run',run_retired=False)),('self',dict(state='active')),('own_run_present',True),('pending_commands',1),('cleanup_degraded',['failed']),('error','capture failed'),('cleanup_error','failed')):
            with self.subTest(key=key):self.bad(6,key,val,'lifecycle_not_closed')

    def test_files_gate_and_full_consumer(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);mission=root/'mission';mission.mkdir()
            def write(p,v):
                p.write_text(json.dumps(v),encoding='utf-8')
                return str(p)
            selected,orig=inputs()
            sp=write(root/'selected.json',selected);op=write(root/'original.json',orig)
            csv=mission/'points.csv';csv.write_text(csv_for(b.source_points(selected,orig)),encoding='ascii')
            init=mission/'init.c';init.write_bytes(b'producer')
            exe=root/'engine.exe';exe.write_bytes(b'engine')
            packages={}
            for i in range(4):
                p=root/f'{i}.pbo';p.write_bytes(str(i).encode());packages[str(p)]=b.sha(p)
            paths=[Path(sp),Path(op),csv,init,exe,*map(Path,packages)]
            d=dict(mission=str(mission),mod='@fixture',producer=str(init),csv=str(csv),selected=sp,original=op,engine=str(exe),packages=packages,inputs={str(p):b.sha(p) for p in paths})
            write(root/'deployment.json',d)
            write(root/'accepted.json',dict(status='B1_NATIVE_READY',inputs={str(root/'deployment.json'):b.sha(root/'deployment.json')}))
            seal=b.sha(root/'accepted.json')
            self.assertEqual(b.gate(root,seal)['status'],'PRE_FIFO_GATE_PASS')
            for target in paths:
                original=target.read_bytes();target.write_bytes(original+b' ')
                with self.subTest(target=target.name),self.assertRaisesRegex(ValueError,'input_drift'):b.gate(root,seal)
                target.write_bytes(original)
            with self.assertRaisesRegex(ValueError,'seal_drift'):b.gate(root,'f'*64)
            rr=list(receipts());rr[0]=d
            for h in (rr[2],rr[3]):
                h.update(mission_path=str(mission),mission_sha256=b.sha(init),executable=str(exe),executable_file_sha256=b.sha(exe),package_hashes=packages)
            native=root/'native.log';native.write_text(log_fixture(),encoding='utf-8')
            rr[1]['accepted_sha256']=seal;rr[5]['sha256']=b.sha(native)
            for name,value in zip(('launch.json','host-identity.json','host-after.json','mcp-identity.json','log-capture.json','cleanup.json'),rr[1:7]):write(root/name,value)
            result=b.consume_bound(root,seal)
            self.assertTrue(result['identity_bound']);self.assertEqual(result['original_native_verdict'],'FAIL')
            self.assertEqual(result['rows'],345);self.assertEqual(result['product_reference'],'INCONCLUSIVE_PRODUCT_REFERENCE')
            with self.assertRaisesRegex(ValueError,'unit_consumed'):b.gate(root,seal)
            write(root/'result.json',result)
            with self.assertRaisesRegex(ValueError,'result_exists'):b.consume_bound(root,seal)

if __name__=='__main__':unittest.main()
