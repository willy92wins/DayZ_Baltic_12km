"""Fault injection against independent host/MCP/census receipts; no engine claim."""
from pathlib import Path
from unittest.mock import patch
import copy
import json
import tempfile
import unittest
import collision_native_b2_binding_ev112 as b
from test_collision_native_b2_ev112 import fixture


class BindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);self.root=root
        def write(p,v):p.write_text(json.dumps(v),encoding='utf-8');return str(p)
        self.write=write
        mission=root/'mission';mission.mkdir();game=root/'game';(game/'Addons').mkdir(parents=True)
        mod=root/'mod';mod.mkdir();bridge=root/'bridge';bridge.mkdir()
        static={};packages={};report=[]
        for name in sorted(b.VANILLA|b.OWN|{'dayz_mcp.pbo'}):
            folder=game/'Addons' if name in b.VANILLA else bridge if name=='dayz_mcp.pbo' else mod
            p=folder/name;p.write_bytes(name.encode());h=b.sha(p)
            if name!='dayz_mcp.pbo':static[str(p)]=h;report.append(dict(path=str(p),sha256=h))
            if name not in b.VANILLA:packages[str(p)]=h
        frozen,original,hits,lookup,text=fixture();self.lookup=lookup;self.text=text
        paths={}
        for key,obj in [('frozen',frozen),('original',original),('hits',hits),('poses',[dict(id=1),dict(id=2)]),('report',dict(packages=report)),('config',dict(anchor={}))]:paths[key]=write(root/(key+'.json'),obj)
        for key,p,data in [('producer',mission/'init.c',b'producer'),('csv',mission/'points.csv',b.csv_for(frozen).encode()),('engine',game/'DayZDiag_x64.exe',b'engine'),('wrp',root/'world.wrp',b'wrp')]:p.write_bytes(data);paths[key]=str(p)
        d=dict(paths,mission=str(mission),mod='@test',packages=packages,static_packages=static)
        d['inputs']={p:b.sha(p) for p in [*paths.values(),*packages,*static]}
        write(root/'deployment.json',d);write(root/'accepted.json',dict(status='B2_NATIVE_READY',inputs={str(root/'deployment.json'):b.sha(root/'deployment.json')}))
        self.seal=b.sha(root/'accepted.json')
        stamp='2026-10-28T16:00:00+00:00'
        host=dict(run_id='own',pid=100,created_utc=stamp,mission_path=d['mission'],mission_sha256=b.sha(d['producer']),
            executable=d['engine'],executable_file_sha256=b.sha(d['engine']),package_hashes=copy.deepcopy(packages),vanilla_hashes={p:h for p,h in static.items() if Path(p).name in b.VANILLA},
            profiles=str(root/'profiles'),host_raw_command_line_sha256='c'*64,server_config='config',server_config_sha256='d'*64,navmesh_data_server=True,file_patching=False,server_mods=[])
        mcp=dict(run_id='own',server_run_id='own',server_binding='BOUND',version_state='ok',poll_age_s=1,
            processes=[dict(role='server',pid=100,creation_time_utc=stamp)],client_diagnostics=[dict(state='not_started')])
        capture=dict(pid=100,created_utc=stamp,last_write_utc=stamp,source=str(root/'profiles'/'baltic_collision_b2.log'),count=270,sha256='e'*64)
        cleanup=dict(close=dict(run_id='own',run_retired=True),self=dict(state='none'),own_run_present=False,pending_commands=0,cleanup_degraded=[],error=None,cleanup_error=None)
        self.args=[d,dict(status='succeeded',run_id='own'),host,copy.deepcopy(host),mcp,capture,cleanup,'e'*64]

    def test_valid_receipts(self):b.identity(*self.args)

    def test_identity_corruptions(self):
        for index,key,value in [(1,'status','failed'),(1,'run_id','other'),(2,'run_id','other'),(3,'run_id','other'),(4,'run_id','other'),(4,'server_run_id','other'),
            (3,'pid',101),(5,'pid',101),(3,'created_utc','2026-10-28T16:00:00.002001+00:00'),(5,'last_write_utc','2026-10-28T15:59:59+00:00'),
            (2,'file_patching',True),(3,'server_mods',['extra']),(2,'mission_path','wrong'),(2,'mission_sha256','x'),(3,'executable','wrong'),(3,'executable_file_sha256','wrong'),
            (4,'poll_age_s',float('nan')),(4,'poll_age_s',-1),(4,'poll_age_s',10),(4,'server_binding','UNBOUND'),(4,'client_diagnostics',[]),(4,'client_diagnostics',[dict(state='running')]),
            (2,'navmesh_data_server',False),(3,'profiles','other'),(3,'server_config_sha256','other'),(5,'source','other'),(5,'count',269),(5,'sha256','wrong'),
            (6,'close',None),(6,'self',dict(state='active')),(6,'own_run_present',True),(6,'pending_commands',1),(6,'cleanup_degraded',['error']),(6,'error','failure'),(6,'cleanup_error','failure')]:
            a=copy.deepcopy(self.args);a[index][key]=value
            with self.subTest(index=index,key=key),self.assertRaises(ValueError):b.identity(*a)

    def test_pre_and_post_vanilla_package_drift(self):
        for index in (2,3):
            for mode in ('remove','extra','change'):
                a=copy.deepcopy(self.args);m=a[index]['vanilla_hashes'];p=next(iter(m))
                if mode=='remove':m.pop(p)
                elif mode=='extra':m['other.pbo']='f'*64
                else:m[p]='f'*64
                with self.subTest(index=index,mode=mode),self.assertRaisesRegex(ValueError,'PACKAGE_DRIFT'):b.identity(*a)

    def test_census_cannot_be_rebound_by_new_deployment(self):
        a=copy.deepcopy(self.args);p=next(iter(a[0]['static_packages']));a[0]['static_packages'][p]='f'*64
        with self.assertRaisesRegex(ValueError,'PACKAGE_DRIFT'):b.identity(*a)

    def test_mod_extra_or_changed(self):
        for mode in ('change','extra','remove'):
            a=copy.deepcopy(self.args);m=a[2]['package_hashes'];p=next(iter(m))
            if mode=='change':m[p]='f'*64
            elif mode=='extra':m['extra.pbo']='f'*64
            else:m.pop(p)
            with self.subTest(mode=mode),self.assertRaises(ValueError):b.identity(*a)

    def test_official_stop_exact_run(self):
        a=copy.deepcopy(self.args);a[6]['close']['run_retired']=False
        with self.assertRaises(ValueError):b.identity(*a)
        a[6]['stop']=dict(run_id='own',status='succeeded');b.identity(*a)
        a[6]['stop']['run_id']='foreign'
        with self.assertRaises(ValueError):b.identity(*a)

    def test_file_and_seal_drift(self):
        self.assertEqual(b.gate(self.root,self.seal)['status'],'PRE_FIFO_GATE_PASS')
        for p in self.args[0]['inputs']:
            path=Path(p);old=path.read_bytes();path.write_bytes(old+b' ')
            with self.subTest(file=path.name),self.assertRaisesRegex(ValueError,'input_drift'):b.gate(self.root,self.seal)
            path.write_bytes(old)
        with self.assertRaisesRegex(ValueError,'seal_drift'):b.gate(self.root,'f'*64)

    def test_bound_consumer_mock_is_not_engine(self):
        a=copy.deepcopy(self.args);(self.root/'native.log').write_text(self.text,encoding='utf-8')
        a[1]['accepted_sha256']=self.seal;a[5]['sha256']=b.sha(self.root/'native.log')
        for name,v in zip(('launch.json','host-identity.json','host-after.json','mcp-identity.json','log-capture.json','cleanup.json'),a[1:7]):self.write(self.root/name,v)
        with patch.object(b,'SceneIndex',return_value=self.lookup):r=b.consume_bound(self.root,self.seal)
        self.assertTrue(r['identity_bound']);self.assertEqual(r['status'],'INCONCLUSIVE_DIAGNOSTIC');self.assertEqual(r['original_fail_points'],47)
        with self.assertRaisesRegex(ValueError,'unit_consumed'):b.gate(self.root,self.seal)
        self.write(self.root/'result.json',r)
        with self.assertRaisesRegex(ValueError,'result_exists'):b.consume_bound(self.root,self.seal)


if __name__ == '__main__':unittest.main()
