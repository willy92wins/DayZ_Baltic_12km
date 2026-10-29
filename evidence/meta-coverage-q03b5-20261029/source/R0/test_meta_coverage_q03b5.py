import sys,os,json,copy,hashlib,tempfile,subprocess,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import numpy as np
import meta_coverage_io_q03b5 as I
import meta_coverage_producer_q03b5 as P
import meta_coverage_consumer_q03b5 as C
D=Path(__file__).parent;O=json.loads((D/'oracle.json').read_bytes());BASE=json.loads((D/'contract.json').read_bytes())
HISTORY=json.loads(Path(BASE['scene']['path']).read_bytes());DT=np.dtype([tuple(x) for x in BASE['schemas']['meta.npy']['dtype']])
def save(p,o):
    p.write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8');return pin(p)
def pin(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def data(equal=False):
    cat=[dict(index=i,name=n,instances=k,group=g) for i,n,k,g in O['catalog']];sections=[dict(index=i,name=n) for i,n in O['sections']]
    if equal:cat=cat[:2];sections=sections[:2]
    return cat,sections,np.array([tuple(x) for x in O['equal_meta' if equal else 'meta']],dtype=DT)
def fixture(root,equal=False):
    root.mkdir();cat,sections,meta=data(equal);n=len(meta);v=np.zeros((n,4,3),'<f8')
    np.savez_compressed(root/'prototype.npz',vertices=v,meta=meta)
    c=copy.deepcopy(BASE);c['rows']=n;c['catalog']=save(root/'catalog.json',cat);c['sections']=save(root/'sections.json',sections)
    a=copy.deepcopy(c['archive']);a.update(pin(root/'prototype.npz'));a['expanded_bound']=1048576;c['archive']=a
    c['schemas']['vertices.npy']['shape']=[n,4,3];c['schemas']['meta.npy']['shape']=[n]
    old=copy.deepcopy(HISTORY);old['expected']['prototype_faces']=n;old['arrays']=[a];old['pins']['deployed-surface-prototypes-20261028/model-catalog.json']=c['catalog'];old['pins']['deployed-surface-prototypes-20261028/model-sections.json']=c['sections'];c['scene']=save(root/'scene.json',old)
    cp=root/'contract.json';h=save(cp,c)['sha256'];return c,h,cp
class Tests(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory(dir=os.environ.get('Q03B5_TEST_ROOT'));self.root=Path(self.t.name)
    def tearDown(self):self.t.cleanup()
    def make(self,equal=False):return fixture(self.root/str(len(list(self.root.iterdir()))),equal)
    def bad(self,fn,code):
        with self.assertRaises(Exception) as ex:fn()
        self.assertEqual(getattr(ex.exception,'code',None),code,str(ex.exception))
    def test_literal_roles_groups_and_anchors(self):
        cat,s,m=data();body=P.derive(cat,s,m)
        expected={'rows':5,'roles':O['roles'],'groups':O['groups'],'catalog_map':[[0,'a','normal',0],[1,'b','normal',1],[2,'vegetation','vegetation_not_inspected',2],[4,'d','normal',3]],'sections_map':[[0,'a',0],[1,'b',1],[4,'d',2],[7,'child',3],[9,'unused',4]],'witness_anchors':[['model',1,1,1],['model',5,None,None],['source_model',4,3,2],['source_model',9,None,4]]}
        self.assertTrue(I.same(body,expected));C.verify(cat,s,m.tobytes(),expected)
    def test_equal(self):
        c,h,p=self.make(True);report=P.produce(I.load(p,h),h)
        self.assertTrue(I.same(report['roles']['model'],O['equal_roles']));self.assertTrue(I.same(report['roles']['source_model'],O['equal_roles']));self.assertEqual(C.consume(c,h,report)['status'],'VERIFIED_META_COVERAGE_DIAGNOSTIC')
    def test_cli_and_external_contract(self):
        c,h,p=self.make();out=self.root/'p';rc=subprocess.run([sys.executable,'-I',str(D/'meta_coverage_producer_q03b5.py'),str(p),h,str(out)],capture_output=True)
        self.assertEqual(rc.returncode,0,rc.stderr.decode());report=json.loads((out/'report.json').read_bytes());self.assertEqual(report['roles'],O['roles']);self.assertEqual(report['groups'],O['groups'])
        rc=subprocess.run([sys.executable,'-I',str(D/'meta_coverage_consumer_q03b5.py'),str(p),h,str(out/'report.json'),str(self.root/'c')],capture_output=True);self.assertEqual(rc.returncode,0,rc.stderr.decode())
        self.bad(lambda:C.consume(c,'0'*64,report),'REPORT')
    def test_co_mutants_and_unexpected_id_not_hidden(self):
        c,h,p=self.make();report=P.produce(c,h)
        def hidden(x):
            x['roles']['model']['unexpected']=[];x['roles']['model']['observed'].remove(5);x['roles']['model']['counts'].pop();x['roles']['model']['equal']=True
        for mutate in [hidden,lambda x:x['roles']['source_model']['missing'].pop(),lambda x:x['groups'][0].update(rows=4),lambda x:x['roles']['model']['counts'][0].__setitem__(1,4),lambda x:x['roles']['model'].update(equal=0),lambda x:x.update(rows=True),lambda x:x['witness_anchors'].pop()]:
            bad=copy.deepcopy(report);mutate(bad);self.bad(lambda:C.consume(c,h,bad),'REPORT')
        bad=copy.deepcopy(report);bad['unknown']=1;self.bad(lambda:C.consume(c,h,bad),'SCHEMA')
    def test_pins_epoch_and_source_reread(self):
        c,h,p=self.make();report=P.produce(c,h);Path(c['catalog']['path']).write_bytes(b'[]');self.bad(lambda:C.consume(c,h,report),'IDENTITY')
        c,h,p=self.make();c['epoch']['pilot_pbo']='wrong';h=save(p,c)['sha256'];self.bad(lambda:I.load(p,h),'EPOCH')
        c,h,p=self.make();c['archive']['sha256']='0'*64;self.bad(lambda:P.produce(c,h),'IDENTITY')
    def test_dtype_count_and_output_caps(self):
        c,h,p=self.make();c['schemas']['meta.npy']['dtype'][0][1]='<u4';self.bad(lambda:P.produce(c,h),'NPY_DTYPE')
        c,h,p=self.make();c['schemas']['meta.npy']['shape']=[6];self.bad(lambda:P.produce(c,h),'NPY_SHAPE')
        self.bad(lambda:I.emit(self.root/'oversize',{'x':'z'*50},20),'OUTPUT_CAP');self.assertFalse((self.root/'oversize').exists())
        cat,s,m=data();self.bad(lambda:C.verify(cat,s,m.tobytes()[:-1],{}),'SCHEMA')
    def test_integer_schema_and_duplicate_index(self):
        cat,s,m=data();cat[0]['index']=False;self.bad(lambda:P.derive(cat,s,m),'SCHEMA');self.bad(lambda:C.verify(cat,s,m.tobytes(),{}),'SCHEMA')
        cat,s,m=data();s.append(copy.deepcopy(s[0]));self.bad(lambda:P.derive(cat,s,m),'SCHEMA');self.bad(lambda:C.verify(cat,s,m.tobytes(),{}),'SCHEMA')
if __name__=='__main__':unittest.main(verbosity=2)
