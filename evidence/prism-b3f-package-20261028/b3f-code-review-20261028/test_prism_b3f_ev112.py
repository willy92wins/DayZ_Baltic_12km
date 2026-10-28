"""PBO fixtures written independently of the shared reader and composition code."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,tempfile,unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prism_b3f_package_ev112 as p
import compiled_dry_road_gate_ev112 as legacy

PROPS=[('prefix','baltic_stream_pilot'),('product','dayz ugc')]
def sample():
    files={p.NAME:b'ODOL control'}
    files.update({f'cs_other_{i:04d}.p3d':b'ODOL'+bytes([i]) for i in range(200)})
    files['config.bin']=b'\0raP201 configuration';return files
def writer(path,props,files):
    out=b'\0'+struct.pack('<5I',0x56657273,0,0,0,0)
    for k,v in props:out+=k.encode()+b'\0'+v.encode()+b'\0'
    out+=b'\0'
    for n,v in files.items():out+=n.encode()+b'\0'+struct.pack('<5I',0,len(v),0,123,len(v))
    out+=b'\0'+bytes(20)+b''.join(files.values());path.write_bytes(out)

class PboFixtures(unittest.TestCase):
    def setUp(self):self.before=sample();self.candidate=b'ODOL approved candidate';self.after={**self.before,p.NAME:self.candidate}
    def test_saved_pbo_positive_preserves_201_and_config(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);writer(root/'before.pbo',PROPS,self.before);writer(root/'after.pbo',PROPS,self.after)
            bp,b=p.read_package(root/'before.pbo');ap,a=p.read_package(root/'after.pbo');r=p.compare(bp,b,ap,a,self.candidate)
            self.assertEqual(r['unchanged_model_entries'],200);self.assertTrue(r['config_exact']);self.assertEqual(r['changed_entries'],[p.NAME])
    def test_wrong_config_extra_missing_and_control_payload(self):
        variants=[{**self.after,'config.bin':b'one model config'},{**self.after,'extra.p3d':b'ODOL'},dict(list(self.after.items())[1:]),self.before]
        for actual in variants:
            with self.subTest(keys=len(actual)),self.assertRaises(p.Rejected):p.compare(PROPS,self.before,PROPS,actual,self.candidate)
    def test_entry_order_is_physical(self):
        actual=dict(reversed(list(self.after.items())))
        with self.assertRaisesRegex(p.Rejected,'PBO_entry_order'):p.compare(PROPS,self.before,PROPS,actual,self.candidate)
    def test_extra_or_reordered_properties(self):
        for props in [PROPS+[('extra','x')],list(reversed(PROPS)),[('prefix','wrong'),PROPS[1]]]:
            with self.subTest(props=props),self.assertRaisesRegex(p.Rejected,'property_sequence'):p.compare(PROPS,self.before,props,self.after,self.candidate)
    def test_duplicate_property_rejected_before_dict(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'x.pbo';writer(f,PROPS+[PROPS[0]],self.before)
            with self.assertRaisesRegex(p.Rejected,'duplicate_property'):p.read_package(f)
    def test_duplicate_casefold_entry_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'x.pbo';writer(f,PROPS,{'a.p3d':b'x','A.p3d':b'y'})
            with self.assertRaisesRegex(p.Rejected,'duplicate_entry'):p.read_package(f)
    def test_unsafe_name(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'x.pbo';writer(f,PROPS,{'../escape':b'x'})
            with self.assertRaisesRegex(p.Rejected,'unsafe_name'):p.read_package(f)
    def test_truncated_body_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'x.pbo';writer(f,PROPS,self.before);f.write_bytes(f.read_bytes()[:-1])
            with self.assertRaisesRegex(p.Rejected,'truncated'):p.read_package(f)
    def test_old_candidate_and_anchors_do_not_control_new_identity(self):
        with mock.patch.multiple(legacy,CANDIDATE_SHA='unrelated',ANCHORS={'alien':'wrong'}):
            self.assertEqual(p.compare(PROPS,self.before,PROPS,self.after,self.candidate)['unchanged_model_entries'],200)
    def test_all_copied_files_and_mutated_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for n,v in self.after.items():(root/n).write_bytes(v)
            p.source_check(root,self.after);(root/p.NAME).write_bytes(self.before[p.NAME])
            with self.assertRaisesRegex(p.Rejected,'source_bytes'):p.source_check(root,self.after)
    def test_unexpected_source_file(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'a').write_bytes(b'x');(root/'extra').write_bytes(b'y')
            with self.assertRaisesRegex(p.Rejected,'source_bytes'):p.source_check(root,{'a':b'x'})

class Bindings(unittest.TestCase):
    def test_census_positive_and_missing_failed_component(self):
        row=dict(status='EXACT_CENSUS',compared_components=1520,visited_components=1520,expected_components=1520,observed_components=1520,global_errors=[],geometric_failures=[],structural_failures=0);p.census_check(row)
        for key,value in [('status','INCONCLUSIVE'),('compared_components',1519),('visited_components',1519),('observed_components',1521),('global_errors',['missing']),('geometric_failures',['c1335']),('structural_failures',1)]:
            with self.subTest(key=key),self.assertRaises(p.Inconclusive):p.census_check({**row,key:value})
    def test_output_extra_file_or_folder_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);target=root/'baltic_stream_pilot.pbo';target.write_bytes(b'package');p.output_universe(root);(root/'extra').write_bytes(b'other')
            with self.assertRaises(p.Rejected):p.output_universe(root)
            (root/'extra').unlink();target.unlink();target.mkdir()
            with self.assertRaises(p.Rejected):p.output_universe(root)
    def test_late_zero_exit_and_rss_limit(self):
        r=dict(returncode=0,stop_reason=None,seconds=.1,peak_sampled_tree_rss_bytes=1);p.runtime.enforce_receipt(r,.1,120)
        with self.assertRaises(p.gate.Inconclusive):p.runtime.enforce_receipt(r,120.001,120)
        with self.assertRaises(p.gate.Inconclusive):p.runtime.enforce_receipt({**r,'peak_sampled_tree_rss_bytes':2*1024**3+1},.1,120)
    def test_real_saved_chain_matches_published_witness(self):
        pins,props,before,candidate=p.context();self.assertEqual(p.digest(candidate),p.CANDIDATE_SHA);self.assertEqual(p.digest(before[p.NAME]),p.CONTROL_SHA);self.assertEqual(len(before),202)
        self.assertEqual(pins[str(p.PAIR/'contract.json')],'c3709a1929214e1372fb2026b8d84c8ae83466aa83e033da968fa196a598f8e4')
    def test_foreign_receipt_hash_fails_before_fields(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'proof.json';f.write_bytes(b'{"status":"COMPILED_B3E_CONDITIONAL"}')
            with self.assertRaisesRegex(p.Inconclusive,'pin_changed'):p.pins_check({str(f):p.ANCHORS[p.PAIR/'candidate-gate/report.json']})
    def test_unknown_inherited_pin_change(self):
        with tempfile.TemporaryDirectory() as td:
            f=Path(td)/'source';f.write_bytes(b'old');pins={str(f):p.sha(f)};f.write_bytes(b'new')
            with self.assertRaises(p.Inconclusive):p.pins_check(pins)
    def test_tool_inventory_detects_added_removed_and_changed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);f=root/'a.dll';f.write_bytes(b'old');a=p.flight.inventory(root);f.write_bytes(b'new');self.assertNotEqual(a,p.flight.inventory(root));f.write_bytes(b'old');(root/'x.dll').write_bytes(b'extra');self.assertNotEqual(a,p.flight.inventory(root));f.unlink();self.assertNotEqual(a,p.flight.inventory(root))
    def test_empty_tool_inventory(self):
        with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(ValueError,'empty_tools'):p.flight.inventory(Path(td))
    def test_child_imports_preflight_in_isolated_image(self):
        code='import sys;sys.path.insert(0,sys.argv[1]);import preflight_b3f_ev112;print("IMPORT_ONLY")'
        r=subprocess.run([str(p.runtime.reads.interpreter_image()),'-I','-S','-c',code,str(p.HERE)],capture_output=True,timeout=10);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(r.stdout.strip(),b'IMPORT_ONLY')
    def approval_fixture(self,root):
        here=root/'tools/quality';here.mkdir(parents=True);(root/'plans').mkdir()
        files=[here/'package.py',here/'preflight_b3f_ev112.py',here/'test_prism_b3f_ev112.py',root/'plans/ev112-b3f-package-composition-20261028.md']
        for f in files:f.write_bytes(b'fixture')
        review=root/'review.md';review.write_bytes(b'adjudicated');suite=root/'tests.json';p.dump(suite,dict(status='TESTS_PASS',tests=5,seconds=1,postimages={str(f):p.sha(f) for f in files[:-1]}))
        a=dict(schema='B3F_EXECUTION_V1',status='REVIEW_ADJUDICATED_TESTS_PASS',output=str(root/'out'),pins={str(f):p.sha(f) for f in files+[review,suite]},review_adjudication=str(review),tests=str(suite));return a,files,here
    def check_approval(self,root,mutate=None):
        a,files,here=self.approval_fixture(root)
        if mutate:mutate(a,files)
        f=root/'approval.json';p.dump(f,a)
        with mock.patch.multiple(p,HERE=here,W=root,__file__=str(files[0]),HELPERS={}):return p.approval(f,root/'out')
    def test_new_approval_positive(self):
        with tempfile.TemporaryDirectory() as td:self.assertEqual(self.check_approval(Path(td))['schema'],'B3F_EXECUTION_V1')
    def test_foreign_or_missing_approval(self):
        for mutate in [lambda a,f:a.update(schema='B3E2_EXECUTION_V1'),lambda a,f:a.update(output='other'),lambda a,f:a['pins'].pop(str(f[1]))]:
            with tempfile.TemporaryDirectory() as td,self.assertRaises(p.Inconclusive):self.check_approval(Path(td),mutate)
    def test_approval_cannot_rebind_untested_source(self):
        def mutate(a,files):files[0].write_bytes(b'changed');a['pins'][str(files[0])]=p.sha(files[0])
        with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(p.Inconclusive,'suite'):self.check_approval(Path(td),mutate)
    def test_zero_tests_not_pass(self):
        def mutate(a,files):s=Path(a['tests']);r=json.loads(s.read_bytes());r['tests']=0;p.dump(s,r);a['pins'][str(s)]=p.sha(s)
        with tempfile.TemporaryDirectory() as td,self.assertRaisesRegex(p.Inconclusive,'suite'):self.check_approval(Path(td),mutate)
    def test_cli_missing_manifest_is_inconclusive_and_cannot_clobber(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);out=root/'out';cmd=[sys.executable,'-I',str(Path(p.__file__)),'consume',str(root),str(out)]
            r=subprocess.run(cmd,capture_output=True,timeout=15);self.assertEqual(r.returncode,2,r.stderr);f=out/'report.json';raw=f.read_bytes();self.assertEqual(json.loads(raw)['status'],'INCONCLUSIVE_PACKAGE')
            r=subprocess.run(cmd,capture_output=True,timeout=15);self.assertNotEqual(r.returncode,0);self.assertEqual(f.read_bytes(),raw)

if __name__=='__main__':unittest.main()
