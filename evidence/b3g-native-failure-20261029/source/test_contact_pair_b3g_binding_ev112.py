"""Host/run/package mutation checks, distinct from synthetic surface checks."""
import copy,unittest
import test_collision_native_b2_binding_ev112 as old_fixture
import contact_pair_b3g_binding_ev112 as b
from test_contact_pair_b3g_ev112 import fixture
from contact_pair_b3g_ev112 import consume

class NativeBindingTests(unittest.TestCase):
    def setUp(self):
        # Reuse only receipt fixture construction, never the old CLI or tests.
        f=old_fixture.BindingTests();f.setUp();self.addCleanup(f.doCleanups);self.args=copy.deepcopy(f.args)
        d,launch,host,after,mcp,capture,cleanup,h=self.args
        d['vanilla']=dict(host['vanilla_hashes']);d['scripts_sha256']='f'*64
        for x in (host,after):x.update(scripts_sha256='f'*64,mods=['own','bridge'])
        launch.update(request=dict(mode='server',build=False,clean=False,pack_only=False,preflight=False,no_base_mods=True,no_file_patching=True,navmesh_data_server=True,takeover=False,on_busy='queue',wait_for_box_s=600.0,mission=d['mission'],extra_mods=[d['mod']]),readiness_budget_s=300,capture_budget_s=180)
        capture['source']=capture['source'].replace('baltic_collision_b2.log','baltic_contact_b3g.log')
    def test_complete_receipts(self):b.identity(*self.args)
    def test_wrong_run_process_and_mode(self):
        for ix,key,value in ((1,'run_id','other'),(2,'pid',101),(3,'created_utc','2026-10-28T16:00:00.003+00:00'),(4,'server_binding','UNBOUND'),(4,'poll_age_s',99),(4,'client_diagnostics',[]),(2,'file_patching',True),(2,'server_mods',['x']),(2,'navmesh_data_server',False)):
            a=copy.deepcopy(self.args);a[ix][key]=value
            with self.subTest(ix=ix,key=key),self.assertRaises(ValueError):b.identity(*a)
    def test_script_or_effective_mods_changed(self):
        for ix,key,value in ((2,'scripts_sha256','changed'),(3,'scripts_sha256','changed'),(3,'mods',['other','bridge']), (2,'mods',['own'])):
            a=copy.deepcopy(self.args);a[ix][key]=value
            with self.assertRaises(ValueError):b.identity(*a)
    def test_launch_flags_and_capture_budget(self):
        for k,v in (('takeover',True),('on_busy','fail'),('mode','all'),('wait_for_box_s',599.0),('build',True),('extra_mods',['other'])):
            a=copy.deepcopy(self.args);a[1]['request'][k]=v
            with self.assertRaises(ValueError):b.identity(*a)
        a=copy.deepcopy(self.args);a[1]['capture_budget_s']=300
        with self.assertRaises(ValueError):b.identity(*a)
    def test_static_package_changed(self):
        for ix,field in ((2,'package_hashes'),(3,'package_hashes'),(2,'vanilla_hashes'),(3,'vanilla_hashes')):
            a=copy.deepcopy(self.args);a[ix][field][next(iter(a[ix][field]))]='changed'
            with self.assertRaises(ValueError):b.identity(*a)
    def test_stale_capture(self):
        for key,value in (('source','wrong'),('count',269),('sha256','wrong'),('last_write_utc','2026-10-28T15:59:59+00:00')):
            a=copy.deepcopy(self.args);a[5][key]=value
            with self.assertRaises(ValueError):b.identity(*a)
    def test_cleanup_required(self):
        for key,value in (('self',dict(state='active')),('own_run_present',True),('pending_commands',1),('error','error')):
            a=copy.deepcopy(self.args);a[6][key]=value
            with self.assertRaises(ValueError):b.identity(*a)
        a=copy.deepcopy(self.args);a[6]['close']['run_retired']=False
        with self.assertRaises(ValueError):b.identity(*a)

class PairTests(unittest.TestCase):
    def setUp(self):
        pts,orig,csv,text=fixture();a=consume(text,csv,pts,orig);a.update(identity_bound=True,arm='control',run_id='run-control')
        z=copy.deepcopy(a);z.update(arm='candidate',run_id='run-candidate')
        d={k:k for k in ('original','frozen','wrp','engine','scripts','producer','csv')};d['inputs']={v:'h'+v for v in d.values()}
        d.update(vanilla={'plants':'same'},packages={name:'h'+name for name in b.OWN});d['packages']['baltic_stream_pilot.pbo']=b.CONTROL
        e=copy.deepcopy(d);e['packages']['baltic_stream_pilot.pbo']=b.CANDIDATE
        self.args=[a,z,d,e]
    def test_bound_pair_still_not_causality(self):self.assertEqual(b.pair_bound(*self.args)['causality'],'UNPROVEN')
    def test_same_run_rejected(self):
        self.args[1]['run_id']=self.args[0]['run_id']
        with self.assertRaises(ValueError):b.pair_bound(*self.args)
    def test_swapped_arm_rejected(self):
        self.args[1]['arm']='control'
        with self.assertRaises(ValueError):b.pair_bound(*self.args)
    def test_changed_source_or_world_rejected(self):
        for k in ('scripts','original','wrp','producer','csv'):
            a=copy.deepcopy(self.args);a[3]['inputs'][k]='changed'
            with self.assertRaises(ValueError):b.pair_bound(*a)
        a=copy.deepcopy(self.args);a[3]['packages']['narva_trial.pbo']='changed'
        with self.assertRaises(ValueError):b.pair_bound(*a)
    def test_wrong_candidate_rejected(self):
        self.args[3]['packages']['baltic_stream_pilot.pbo']=b.CONTROL
        with self.assertRaises(ValueError):b.pair_bound(*self.args)

if __name__=='__main__':unittest.main()
