import copy,hashlib,importlib.util,json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
D=Path(__file__).parent
def module(name):
    s=importlib.util.spec_from_file_location(name,D/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
P=module('prepare_pair_c1c2a');C=module('consume_pair_c1c2a')
DRIVER=module('run_pair_c1c2a')
O=json.loads((D/'oracles.json').read_bytes());REAL=json.loads((D/'contract.json').read_bytes())
EXT=json.loads((D/'oracle-extension.json').read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(v,sort_keys=True)+'\n').encode())
def row(p):
    s=p.stat();return {'bytes':s.st_size,'sha256':sha(p.read_bytes()),'identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]}
class Suite(unittest.TestCase):
    def setUp(self):
        base=D/'tests-temp';base.mkdir(exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=base);self.base=Path(self.tmp.name);self.c=copy.deepcopy(REAL);self.c.update(root=str(self.base/'prepared'),source_stage=str(self.base/'source'),profile_roots=[],evidence=copy.deepcopy([r for r in REAL['evidence'] if r['path']==sys.executable]))
        self.pins=[]
        for i,literal in enumerate(O['payloads']):
            p=self.base/'inputs'/str(i);p.parent.mkdir(exist_ok=True);p.write_bytes(bytes.fromhex(literal['hex']));self.assertEqual(row(p)['sha256'],literal['sha256']);self.pins.append({'path':str(p),'bytes':literal['bytes'],'sha256':literal['sha256']})
        entries=[{'dest':'data/data.bin','scope':'common',**{k:self.pins[0][k] for k in ['bytes','sha256']}},{'dest':'empty','scope':'common',**{k:self.pins[2][k] for k in ['bytes','sha256']}},{'dest':'scene.wrp','scope':'control',**{k:self.pins[0][k] for k in ['bytes','sha256']}},{'dest':'scene.wrp','scope':'candidate',**{k:self.pins[1][k] for k in ['bytes','sha256']}}]
        manifest=self.base/'manifest.json';put(manifest,{'files':entries});self.c['c1b']={'path':str(manifest),**row(manifest)};self.c['c1b_consumer']=self.pins[0]
        for arm in ['control','candidate']:
            for e in entries:
                if e['scope'] in ['common',arm]:
                    p=Path(self.c['source_stage'])/arm/'root'/e['dest'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(next(bytes.fromhex(x['hex']) for x in O['payloads'] if x['sha256']==e['sha256']))
        self.c['tool_files']=[{'dest':'tool.exe',**self.pins[1]},{'dest':'logger.xml',**self.pins[0]}];self.c['tools']={'dummy':self.pins[1]};self.c['include']=self.pins[0];self.c['exclude']=self.pins[2];self.c['preflight']=self.pins[1]
        self.cp=self.base/'contract.json';put(self.cp,self.c);self.pin=sha(self.cp.read_bytes());self.root=Path(self.c['root']);self.cmd=[sys.executable,'-I','-X','utf8',str(D/'prepare_pair_c1c2a.py'),'--contract',str(self.cp),'--sha',self.pin]
    def tearDown(self):self.tmp.cleanup()
    def produce(self):
        start=time.monotonic();r=subprocess.run(self.cmd,capture_output=True,timeout=20);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.stdout=self.base/'stdout';self.stderr=self.base/'stderr';self.stdout.write_bytes(r.stdout);self.stderr.write_bytes(r.stderr);self.elapsed=time.monotonic()-start;return r
    def observe(self,rc=0):
        return {'schema':'c1c2a-external-observation.v1','contract_sha256':self.pin,'contract_path':str(self.cp),'producer_code':{'path':str(D/'prepare_pair_c1c2a.py'),**row(D/'prepare_pair_c1c2a.py')},'command':self.cmd,'owned_retired':True,'completion':{'root_pid':12345,'root_birth':1.0,'rc':rc,'reason':None,'seconds':self.elapsed,'peak_rss':0,'observed_disk_peak':0,'stdout':{'path':str(self.stdout),**row(self.stdout)},'stderr':{'path':str(self.stderr),**row(self.stderr)}},'meta':{p.name:row(p) for p in (self.root/'meta').iterdir() if p.is_file()}}
    def consume(self,obs=None):
        if obs is None:obs=self.observe()
        op=self.base/('observation-'+str(time.time_ns())+'.json');put(op,obs);out=self.base/('result-'+str(time.time_ns())+'.json');cmd=[sys.executable,'-I','-X','utf8',str(D/'consume_pair_c1c2a.py'),'--contract',str(self.cp),'--sha',self.pin,'--observation',str(op),'--observation-sha',sha(op.read_bytes()),'--output',str(out)]
        r=subprocess.run(cmd,capture_output=True,timeout=20);self.assertTrue(out.exists(),r.stdout+r.stderr);return r.returncode,json.loads(out.read_bytes())
    def bad(self,code,obs=None):
        rc,r=self.consume(obs);self.assertEqual(rc,1,r);self.assertEqual(r['status'],'REJECTED');self.assertEqual(r['reason'],code,r)
    def test_complete_literal_cli(self):
        self.produce();rc,r=self.consume();self.assertEqual(rc,0,r);self.assertEqual(r,{'status':O['complete_status'],'contract_sha256':self.pin,'files':O['file_count'],'claims':self.c['claims']})
        self.assertEqual(sorted(p.name for p in (self.root/'meta').iterdir()),sorted(O['meta_names']))
    def test_N01_source_byte(self):
        self.produce();(Path(self.c['source_stage'])/'control/root/data/data.bin').write_bytes(b'xyz');self.bad('PIN')
    def test_N02_extra_file(self):
        self.produce();(self.root/'fixed/extra').write_bytes(b'x');self.bad('INVENTORY')
    def test_N03_extra_directory(self):
        self.produce();(self.root/'work/control/root/extra').mkdir();self.bad('INVENTORY')
    def test_N04_reparse_simulated(self):
        original=Path.lstat
        def fake(path):
            s=original(path)
            if path==self.base:
                class R:st_mode=s.st_mode;st_file_attributes=1024
                return R()
            return s
        with patch.object(Path,'lstat',fake):
            with self.assertRaisesRegex(P.Stop,'REPARSE'):P.guard(self.base)
            with self.assertRaisesRegex(C.Reject,'REPARSE'):C.pathcheck(self.base)
    def test_N05_existing_root(self):
        self.root.mkdir()
        with self.assertRaisesRegex(P.Stop,'EXISTS'):P.prepare(self.c,self.pin)
    def test_N06_read_mutation(self):
        p=Path(self.pins[0]['path']);original=Path.open;mutated=False
        class Wrapper:
            def __init__(self,f):self.f=f
            def __enter__(self):return self
            def __exit__(self,*args):self.f.close()
            def fileno(self):return self.f.fileno()
            def read(self,n):
                nonlocal mutated
                b=self.f.read(n)
                if not mutated:
                    mutated=True
                    with original(p,'ab') as out:out.write(b'x')
                return b
        def opening(path,*args,**kw):
            f=original(path,*args,**kw);return Wrapper(f) if path==p and args and args[0]=='rb' else f
        with patch.object(Path,'open',opening):
            with self.assertRaisesRegex(P.Stop,'IDENTITY'):P.read_hash(p,64)
    def test_N07_truncated_copy(self):
        self.produce();(self.root/'work/candidate/root/scene.wrp').write_bytes(b'hel');self.bad('PIN')
    def test_N08_missing_fixed(self):
        self.produce();(self.root/'fixed/include.lst').unlink();self.bad('INVENTORY')
    def test_N09_done_without_started(self):
        self.produce();(self.root/'meta/source.started.json').unlink();self.bad('JOURNAL')
    def test_N10_report_comutation(self):
        self.produce();obs=self.observe();p=self.root/'meta/report.json';r=json.loads(p.read_bytes());r['reason']='changed';put(p,r);self.bad(O['negative_codes']['N10'],obs)
    def test_N11_hash_self_claim(self):
        self.produce();p=self.root/'work/control/root/scene.wrp';p.write_bytes(b'xyz');rp=self.root/'meta/report.json';r=json.loads(rp.read_bytes());r['rows']['work']['control']['scene.wrp']=row(p);put(rp,r);self.bad('PIN')
    def test_N12_partial(self):
        self.produce();rp=self.root/'meta/report.json';r=json.loads(rp.read_bytes());r['status']='PREPARATION_STOPPED';r['reason']='BUDGET';r['phase']='fixed';r['journals'].pop('fixed.done.json');(self.root/'meta/fixed.done.json').unlink();put(rp,r)
        rc,result=self.consume(self.observe(2));self.assertEqual(rc,2,result);self.assertEqual(result['status'],'INCONCLUSIVE_PREPARATION')
    def test_N13_root_empty_sibling(self):
        self.produce();(self.root/'output').mkdir();self.bad('INVENTORY')
    def test_N14_false_prepared(self):
        self.produce();(self.root/'meta/fixed.done.json').unlink();self.bad('JOURNAL')
    def test_N15_journal_comutation(self):
        self.produce();obs=self.observe();p=self.root/'meta/copy.done.json';r=json.loads(p.read_bytes());r['elapsed_ns']+=100;put(p,r);self.bad(O['negative_codes']['N15'],obs)
    def test_negative_sequence_even_repinned(self):
        self.produce();p=self.root/'meta/copy.done.json';r=json.loads(p.read_bytes());r['sequence']=True;put(p,r);rp=self.root/'meta/report.json';q=json.loads(rp.read_bytes());q['journals']['copy.done.json']=row(p);put(rp,q);self.bad('JOURNAL')
    def test_wrong_contract_before_cli(self):
        r=subprocess.run([*self.cmd[:-1],'0'*64],capture_output=True,timeout=10);self.assertEqual(r.returncode,1);self.assertFalse(self.root.exists())
    def test_N16_report_elapsed_bool(self):
        self.produce();p=self.root/'meta/report.json';r=json.loads(p.read_bytes());r['elapsed_ns']=True;put(p,r);self.bad(EXT['negatives']['report_elapsed_bool'])
    def test_N17_finalize_20_seconds(self):
        self.produce();p=self.root/'meta/report.json';r=json.loads(p.read_bytes());r['elapsed_ns']=json.loads((self.root/'meta/fixed.done.json').read_bytes())['elapsed_ns']+20000000000;put(p,r);self.bad(EXT['negatives']['finalize_plus20s'])
    def test_rc_bool(self):
        self.produce();obs=self.observe();obs['completion']['rc']=False;self.bad(EXT['negatives']['rc_bool'],obs)
    def test_report_and_row_extra(self):
        self.produce();p=self.root/'meta/report.json';r=json.loads(p.read_bytes());q=copy.deepcopy(r);q['extra']=0;put(p,q);self.bad(EXT['negatives']['report_extra']);r['rows']['extra']=0;put(p,r);self.bad(EXT['negatives']['row_extra'])
    def test_manifest_pin_code(self):
        self.produce();Path(self.c['c1b']['path']).write_bytes(b'{}');self.bad(EXT['negatives']['manifest_pin'])
    def test_interpreter_pin(self):
        self.produce();self.c['evidence'][0]['sha256']='0'*64
        with self.assertRaisesRegex(C.Reject,'PIN'):C.current_inputs(self.c,time.monotonic()+10)
    def test_complete_driver(self):
        cfg={'out':str(self.base/'run'),'contract':str(self.cp),'contract_sha256':self.pin,'producer':{'path':str(D/'prepare_pair_c1c2a.py'),**row(D/'prepare_pair_c1c2a.py')},'consumer':{'path':str(D/'consume_pair_c1c2a.py'),**row(D/'consume_pair_c1c2a.py')}};p=self.base/'driver.json';put(p,cfg)
        r=subprocess.run([sys.executable,'-I','-X','utf8',str(D/'run_pair_c1c2a.py'),str(p)],capture_output=True,timeout=20);self.assertEqual(r.returncode,0,r.stdout+r.stderr);result=json.loads((self.base/'run/consumer.json').read_bytes());self.assertEqual(result['status'],EXT['driver_positive'])
    def test_monitor_error_stops_fail_closed(self):
        # Inject only disk enumeration failure; never reinterpret an unreadable file as zero.
        with patch.object(Path,'rglob',side_effect=PermissionError('synthetic')):
            r=DRIVER.run([sys.executable,'-I','-c','import time;time.sleep(20)'],str(self.base),self.base/'monitor-fail',5,268435456,self.base)
        self.assertTrue(r['reason'].startswith('SUPERVISOR:PermissionError'));self.assertTrue(r['owned_retired']);self.assertNotEqual(r['rc'],0)
if __name__=='__main__':unittest.main()
