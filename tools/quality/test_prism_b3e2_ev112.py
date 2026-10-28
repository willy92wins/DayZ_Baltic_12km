"""Continuation acceptance: real children/readers and independent geometric fixtures."""
from pathlib import Path
import copy,hashlib,json,struct,subprocess,sys,tempfile,types,unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build_prism_b3e2_ev112 as b
import consume_prism_b3e2_ev112 as c
from test_prism_b3e_ev112 import fixture
from test_prism_b3_binary_ev112 import IDENTITY
g=b.gate

class Receipts(unittest.TestCase):
    def test_hash_before_json(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'receipt';p.write_bytes(b'not json')
            with self.assertRaisesRegex(Exception,'receipt_hash'):b.flight.pinned_json(p,'0'*64)
            with self.assertRaises(json.JSONDecodeError):b.flight.pinned_json(p,b.sha(p))
    def test_saved_receipt_and_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'receipt';p.write_bytes(b'{"n":9}');h=b.sha(p)
            self.assertEqual(b.flight.pinned_json(p,h),dict(n=9));p.write_bytes(b'{"n":8}')
            with self.assertRaisesRegex(Exception,'receipt_hash'):b.flight.pinned_json(p,h)
    def make(self,root):
        here=root/'tools/quality';here.mkdir(parents=True);(root/'plans').mkdir()
        paths=[here/n for n in ('build.py','preflight_b3e2_ev112.py','consume_prism_b3e2_ev112.py','test_prism_b3e2_ev112.py')]+[root/'plans/ev112-b3e-build-continuation-20261028.md']
        for p in paths:p.write_bytes(b'fixture')
        suite=root/'suite.json';b.dump(suite,dict(status='TESTS_PASS',tests=1,seconds=1,postimages={str(p):b.sha(p) for p in paths[:-1]}))
        review=root/'review.md';review.write_text('Adjudicated fixture')
        a=dict(schema='B3E2_EXECUTION_V1',status='REVIEW_ADJUDICATED_TESTS_PASS',output=str(root/'out'),tests=str(suite),review_adjudication=str(review),pins={str(p):b.sha(p) for p in paths+[suite,review]})
        return a,paths,here
    def run_approval(self,root,change=None):
        a,paths,here=self.make(root)
        if change:change(a,paths)
        p=root/'approval.json';b.dump(p,a)
        with mock.patch.multiple(b,__file__=str(paths[0]),HERE=here,W=root,HELPERS={}):return b.checked_approval(p,root/'out')
    def test_approval_bound_positive(self):
        with tempfile.TemporaryDirectory() as td:self.assertEqual(self.run_approval(Path(td))['schema'],'B3E2_EXECUTION_V1')
    def test_wrong_schema_or_output(self):
        for key,value in [('schema','B3E'),('output','elsewhere')]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as td,self.assertRaises(g.Inconclusive):self.run_approval(Path(td),lambda a,p:a.update({key:value}))
    def test_missing_source_pin(self):
        with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(g.Inconclusive,'approval_missing'):self.run_approval(Path(td),lambda a,p:a['pins'].pop(str(p[2])))
    def test_changed_source(self):
        with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(g.Inconclusive,'approval_changed'):self.run_approval(Path(td),lambda a,p:p[0].write_bytes(b'changed'))
    def test_missing_review_receipt(self):
        with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(g.Inconclusive,'approval_receipt'):self.run_approval(Path(td),lambda a,p:a['pins'].pop(a['review_adjudication']))
    def test_zero_tests_or_late_suite(self):
        for field,value in [('tests',0),('seconds',120.001),('status','RESOURCE_FAIL')]:
            def change(a,p):
                q=Path(a['tests']);r=json.loads(q.read_bytes());r[field]=value;b.dump(q,r);a['pins'][str(q)]=b.sha(q)
            with self.subTest(field=field),tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(g.Inconclusive,'approval_tests'):self.run_approval(Path(td),change)
    def test_stale_suite_postimage(self):
        def change(a,p):p[0].write_bytes(b'new source');a['pins'][str(p[0])]=b.sha(p[0])
        with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(g.Inconclusive,'suite_postimage'):self.run_approval(Path(td),change)
    def test_changed_helper(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);a,paths,here=self.make(root);p=root/'approval.json';b.dump(p,a);helper=root/'helper.py';helper.write_bytes(b'old');h=b.sha(helper);helper.write_bytes(b'new')
            with mock.patch.multiple(b,__file__=str(paths[0]),HERE=here,W=root,HELPERS={helper:h}),self.assertRaisesRegex(g.Inconclusive,'helper_changed'):b.checked_approval(p,root/'out')
    def test_late_zero_return_and_memory(self):
        base=dict(returncode=0,stop_reason=None,seconds=.1,peak_sampled_tree_rss_bytes=1)
        b.enforce_receipt(base,.2,1)
        for update,elapsed in [({},1.01),({'seconds':1.01},.2),({'returncode':2},.2),({'stop_reason':'timeout'},.2),({'peak_sampled_tree_rss_bytes':2*1024**3+1},.2)]:
            with self.subTest(update=update),self.assertRaises(g.Inconclusive):b.enforce_receipt({**base,**update},elapsed,1)

class GateOrder(unittest.TestCase):
    def setUp(self):
        self.od,self.ml=fixture();self.patch=mock.patch.object(g.old,'EXPECTED_COUNTS',(12,16,2));self.patch.start();self.addCleanup(self.patch.stop)
    def control(self,compiled=None):return g.gate_control(self.od,self.od if compiled is None else compiled,self.ml,IDENTITY,[0,0,0],[dict(id=700,x=.25,z=.25)],lambda row:None)
    def test_real_gate_positive_then_candidate(self):
        events=[]
        def build(side):events.append(side+'build')
        def check(side):
            if side=='control':self.assertEqual(self.control()['status'],'CONTROL_B3E_CERTIFIED')
            events.append(side+'gate')
        b.sequence(build,check);self.assertEqual(events,['controlbuild','controlgate','candidatebuild','candidategate'])
    def test_real_gate_fail_no_candidate_and_new_failure_link(self):
        bad=copy.deepcopy(self.od);bad.lods[1].faces[0].vertex_indices.reverse()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            def build(side):(root/side).mkdir()
            def check(side):
                dest=root/(side+'-gate');dest.mkdir()
                try:self.control(bad)
                except Exception as e:
                    b.dump(dest/'report.json',dict(status=g.failure_status(e)));raise
            with self.assertRaises(g.Inconclusive) as caught:b.sequence(build,check)
            b.linked_failure(root,caught.exception,'control-gate');r=json.loads((root/'execution-failure.json').read_bytes())
            self.assertEqual(r['gate_or_preflight']['status'],'INCONCLUSIVE_BINARY');self.assertEqual(r['gate_or_preflight']['sha256'],b.sha(root/'control-gate/report.json'));self.assertFalse((root/'candidate').exists())
    def test_geometry_rejection_link_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'candidate-gate').mkdir();b.dump(root/'candidate-gate/report.json',dict(status='REJECTED_BINARY'))
            b.linked_failure(root,RuntimeError('child nonzero'),'candidate-gate');self.assertEqual(json.loads((root/'execution-failure.json').read_bytes())['gate_or_preflight']['status'],'REJECTED_BINARY')
    def test_missing_report_does_not_become_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);b.linked_failure(root,RuntimeError('terminated'),'control-gate');r=json.loads((root/'execution-failure.json').read_bytes());self.assertIsNone(r['gate_or_preflight']);self.assertEqual(r['status'],'INCONCLUSIVE_EXECUTION')
    def test_config_mutation_between_phases_prevents_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'config.cpp';p.write_bytes(b'original');pins={str(p):b.sha(p)}
            def build(side):g.check_pins(dict(pins=pins));(root/side).mkdir()
            def check(side):self.control();p.write_bytes(b'mutated')
            with self.assertRaises(g.Inconclusive):b.sequence(build,check)
            self.assertFalse((root/'candidate').exists())

class ReaderAndChildren(unittest.TestCase):
    def test_reader_missing_pin(self):
        with self.assertRaisesRegex(g.Inconclusive,'reader_pin'):c.bind_reader(Path('missing'),{})
    def test_loaded_shadow_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'odol_reader.py';p.write_bytes(b'#fixture');pins={str(p):b.sha(p)}
            with mock.patch.object(c,'READER_PINS',{'odol_reader.py':b.sha(p)}),mock.patch.dict(sys.modules,{'odol_reader':types.SimpleNamespace(__file__=str(root/'shadow.py'))}),self.assertRaisesRegex(g.Inconclusive,'loaded_reader_path'):c.bind_reader(root,pins)
    def test_loaded_matching_module(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'odol_reader.py';p.write_bytes(b'#fixture');pins={str(p):b.sha(p)}
            with mock.patch.object(c,'READER_PINS',{'odol_reader.py':b.sha(p)}),mock.patch.dict(sys.modules,{'odol_reader':types.SimpleNamespace(__file__=str(p))}):c.bind_reader(root,pins)
    def test_real_child_writes_independent_pbo_fixture(self):
        # Plain PBO layout from the format: header, entry, terminator, body.
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'x.pbo';payload=b'ODOL'+bytes(12)
            raw=b'\0'+struct.pack('<5I',0x56657273,0,0,0,0)+b'prefix\0fixture\0\0'+b'model.p3d\0'+struct.pack('<5I',0,len(payload),0,0,len(payload))+b'\0'+bytes(20)+payload
            cmd=[str(b.reads.interpreter_image()),'-I','-S','-c','from pathlib import Path;import sys;Path(sys.argv[1]).write_bytes(bytes.fromhex(sys.argv[2]))',str(p),raw.hex()]
            r=b.run_process(cmd,root/'child.log',10);_,props,entries=g.old.read_pbo(p)
            self.assertEqual(props['prefix'],'fixture');self.assertEqual(entries,{'model.p3d':payload});self.assertEqual(r['returncode'],0)
            identity=json.loads((root/'child.running.json').read_bytes());self.assertTrue(any(k.startswith(str(identity['pid'])+'@') for k in r['observed_processes']))
    def test_actual_stdlib_child_imports_preflight_without_running_it(self):
        command=[str(b.reads.interpreter_image()),'-I','-S','-c','import sys;sys.path.insert(0,sys.argv[1]);import preflight_b3e2_ev112;print("IMPORT_ONLY_OK")',str(b.HERE)]
        r=subprocess.run(command,capture_output=True,timeout=10);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),b'IMPORT_ONLY_OK')
    def test_actual_reader_import_binds_all_five_modules(self):
        command=[sys.executable,'-I','-c','import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import consume_prism_b3e2_ev112 as c;r=Path(sys.argv[2]);c.bind_reader(r,{str(r/n):h for n,h in c.READER_PINS.items()});print("BOUND_FIVE")',str(b.HERE),str(b.READER)]
        r=subprocess.run(command,capture_output=True,timeout=15);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),b'BOUND_FIVE')
    def test_observed_descendant_prevents_early_success_and_is_retired(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);childfile=root/'child.json'
            code="import subprocess,sys,time,json;from pathlib import Path;p=subprocess.Popen([sys.executable,'-I','-S','-c','import time;time.sleep(20)']);Path(sys.argv[1]).write_text(json.dumps({'pid':p.pid}));time.sleep(.7)"
            with self.assertRaises(RuntimeError):b.run_process([str(b.reads.interpreter_image()),'-I','-S','-c',code,str(childfile)],root/'tree.log',2)
            r=json.loads((root/'tree.receipt.json').read_bytes());pid=json.loads(childfile.read_bytes())['pid'];matching=[x for k,x in r['observed_processes'].items() if k.startswith(str(pid)+'@')]
            self.assertEqual(r['stop_reason'],'timeout');self.assertEqual(len(matching),1)
            try:p=b.base.psutil.Process(pid);self.assertTrue(p.create_time()!=matching[0]['create_time'] or not p.is_running())
            except b.base.psutil.NoSuchProcess:pass
    def test_consumer_cli_invalid_and_output_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/'bad.json';p.write_bytes(b'{bad');dest=root/'out'
            command=[sys.executable,'-I',str(Path(c.__file__)),'control',str(p),str(root/'pair'),str(root/'reader'),str(dest)]
            r=subprocess.run(command,capture_output=True,timeout=15);self.assertEqual(r.returncode,2);report=dest/'report.json';self.assertEqual(json.loads(report.read_bytes())['status'],'INCONCLUSIVE_BINARY');raw=report.read_bytes()
            r=subprocess.run(command,capture_output=True,timeout=15);self.assertNotEqual(r.returncode,0);self.assertEqual(report.read_bytes(),raw)

if __name__=='__main__':unittest.main()
