from pathlib import Path
import copy,hashlib,json,subprocess,sys,tempfile,unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import preflight_read_discovery_ev112 as d

class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.out=self.root/'out';self.out.mkdir()
        self.sources=[self.root/'original.py',self.root/'archived.py'];self.config=self.root/'config.cpp';self.tools=self.root/'Tools';self.dirs=[self.root/'DZ'];self.dirs[0].mkdir();self.events=[]
        paths=self.sources+[self.config]+[self.tools/n for n in d.TOOLS]+[self.tools/'Bin/Binarize/Binarize.exe']
        for p in paths:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'abc')
        self.h='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
        self.old=dict(tools_root=str(self.tools),original_source=str(self.sources[0]),original_sha256=self.h,local_sha256=self.h,tools_sha256={str(self.tools/n):self.h for n in d.TOOLS})
        self.prior=dict(pins={str(self.tools/'Bin/Binarize/Binarize.exe'):self.h,str(self.config):self.h})
        self.receipts=self.save_receipts()
    def save_receipts(self):
        result=[]
        for name,v in [('old',self.old),('prior',self.prior)]:
            p=self.root/(name+'.json');p.write_text(json.dumps(v),encoding='utf-8');result.append((name,p,hashlib.sha256(p.read_bytes()).hexdigest()))
        return result
    def emit(self,phase,**kw):self.events.append(dict(phase=phase,**kw))
    def run_discovery(self):return d.discover(self.receipts,self.out,self.sources,self.config,self.dirs,self.emit)
    def test_positive_exact_multiplicity_and_unchanged_inputs(self):
        original={p:p.read_bytes() for _,p,_ in self.receipts};r=self.run_discovery();self.assertEqual(r['status'],'HASHES_MATCH');self.assertEqual(r['readings_count'],9);self.assertEqual(r['distinct_paths'],7)
        self.assertEqual(sum(row['path']==str(self.config) for row in r['readings']),2)
        self.assertEqual(sum(row['path'].endswith('Binarize.exe') for row in r['readings']),2)
        self.assertTrue(all(p.read_bytes()==data for p,data in original.items()));self.assertTrue(any(e['phase']=='directory_done' for e in self.events))
    def test_modified_tool_fails_with_expected_observed(self):
        (self.tools/d.TOOLS[1]).write_bytes(b'changed')
        with self.assertRaises(d.HashMismatch):self.run_discovery()
        row=self.events[-1];self.assertEqual(row['phase'],'hash_mismatch');self.assertEqual(row['expected_sha256'],self.h);self.assertNotEqual(row['sha256'],self.h)
    def test_missing_path_is_io_error(self):
        self.config.unlink()
        with self.assertRaises(FileNotFoundError):self.run_discovery()
        self.assertEqual(self.events[-1]['phase'],'read_start')
    def test_unexpected_path_rejected_before_tools_read(self):
        self.old['tools_sha256'][str(self.root/'unapproved.exe')]=self.old['tools_sha256'].pop(str(self.tools/d.TOOLS[0]));self.receipts=self.save_receipts()
        with self.assertRaisesRegex(d.ContractError,'unexpected_tool_path'):self.run_discovery()
        self.assertTrue(all(e.get('label','').startswith('receipt_') for e in self.events))
    def test_receipt_hash_format_and_schema_fail_closed(self):
        bad=list(self.receipts);bad[0]=('old',bad[0][1],'0'*64)
        with self.assertRaisesRegex(d.ContractError,'receipt_hash'):d.load_receipts(bad,self.out,self.emit)
        self.old['tools_sha256']=[];self.receipts=self.save_receipts()
        with self.assertRaisesRegex(d.ContractError,'receipt_maps'):self.run_discovery()
        self.old['tools_sha256']={str(self.tools/n):'invalid' for n in d.TOOLS};self.receipts=self.save_receipts()
        with self.assertRaisesRegex(d.ContractError,'job_hashes'):self.run_discovery()
    def test_malformed_receipt_is_contract_error(self):
        p=self.receipts[0][1];p.write_bytes(b'{broken');self.receipts[0]=('old',p,hashlib.sha256(p.read_bytes()).hexdigest())
        with self.assertRaisesRegex(d.ContractError,'receipt_json'):self.run_discovery()
    def test_permission_failure_not_a_mismatch(self):
        op=Path.open
        def denied(p,*a,**kw):
            if p==self.config:raise PermissionError('fixture')
            return op(p,*a,**kw)
        with mock.patch.object(Path,'open',denied),self.assertRaises(PermissionError):self.run_discovery()
        self.assertFalse(any(e['phase']=='hash_mismatch' for e in self.events))
    def test_changed_receipt_after_read_is_inconclusive(self):
        def mutate(phase,**kw):
            self.emit(phase,**kw)
            if phase=='read_done' and kw['label']=='config.cpp:2':self.receipts[0][1].write_bytes(b'{}')
        with self.assertRaisesRegex(d.ContractError,'receipt_changed'):d.discover(self.receipts,self.out,self.sources,self.config,self.dirs,mutate)
    def test_hash_chunk_boundary(self):
        p=self.root/'blocks';data=b'a'*((4<<20)+7);p.write_bytes(data);r,_=d.read_hash(p,'blocks',self.emit)
        self.assertEqual(r['sha256'],hashlib.sha256(data).hexdigest());self.assertEqual(r['bytes'],len(data));self.assertEqual(self.events[1]['bytes'],4<<20)
    def test_durable_events(self):
        path=self.root/'events';event=d.Events(path)
        with mock.patch.object(d.os,'fsync',wraps=d.os.fsync) as sync:event('first');event('last')
        self.assertEqual(sync.call_count,2);self.assertEqual([json.loads(s)['phase'] for s in path.read_text().splitlines()],['first','last'])
    def test_timeout_owned_child_and_persisted_event(self):
        code="import os,time; f=open('"+str(self.out/'slow.txt').replace('\\','/')+"','w');f.write(str(os.getpid()));f.flush();os.fsync(f.fileno());time.sleep(20)"
        r=d.launch([d.interpreter_image(),'-I','-S','-c',code],self.out,2)
        self.assertEqual(r['status'],'INCONCLUSIVE_TIMEOUT');self.assertNotEqual(r['returncode'],0);self.assertGreater(r['identity']['creation_filetime'],0);self.assertEqual(int((self.out/'slow.txt').read_text()),r['identity']['pid'])
    def test_timeout_upper_bound_and_finished_child(self):
        with self.assertRaisesRegex(d.ContractError,'timeout_range'):d.launch([],self.out,61)
        r=d.launch([d.interpreter_image(),'-I','-S','-c','pass'],self.out,5);self.assertEqual(r['status'],'CHILD_FINISHED');self.assertEqual(r['returncode'],0)

if __name__=='__main__':unittest.main()
