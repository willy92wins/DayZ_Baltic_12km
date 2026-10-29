"""Literal source fixtures and CLI/source-rereading integration, no historical NPZ."""
import os,sys,json,hashlib,tempfile,subprocess,unittest,copy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import numpy as np
import saved_scene_io_q03b4 as I
import saved_scene_producer_q03b4 as P
import saved_scene_consumer_q03b4 as C
D=Path(__file__).parent
O=json.loads((D/'oracle.json').read_bytes());ORIGINAL=json.loads((D/'contract.json').read_bytes())
HIST=json.loads(Path(ORIGINAL['scene']['path']).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n');return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def fixture(root,itype='<i4',ftype='<f8',ttype='<i8',wide=False,mutate=None):
    root=Path(root);root.mkdir(exist_ok=True);o=copy.deepcopy(O);b=8 if wide else 2
    grid=np.array(o['grid_2x5' if wide else 'grid_2x2'],dtype='<f8');tri=np.array(o['triangles_2x5' if wide else 'triangles_2x2'],dtype=ttype)
    bed=np.zeros((b,4,3),'<f8');bed[:,:3]=grid.reshape(-1,3)[tri]
    water=np.array([[[0,1,0],[0,1,1],[1,1,1],[1,1,0]]],'<f8')
    arrays={'prototypes':{'vertices':np.array(o['prototype_vertices'],dtype='<f8'),'meta':np.array([tuple(x) for x in o['meta']],dtype=np.dtype([tuple(x) for x in o['meta_descr']]))},'instances':{'ids':np.array(o['ids'],dtype=itype),'model_index':np.array(o['model_index'],dtype=itype),'matrix':np.array(o['matrices'],dtype=ftype),'norm':np.ones((2,3),'<f8'),'determinant':np.ones(2,'<f8'),'nonorthogonality':np.zeros(2,'<f8')}}
    arrays['selected']={k:v.copy() for k,v in arrays['instances'].items() if k in ('ids','model_index','matrix')}
    pilot={}
    faces={'bed':b,'water':1,'unknown':0,'road_bed':b,'road_water':1,'road_unknown':0}
    for g,f in faces.items():
        val=bed.copy() if g.endswith('bed') else water.copy() if g.endswith('water') else np.empty((0,4,3),'<f8');pilot[g]=val
        pilot[g+'_n']=np.full(f,3 if g.endswith('bed') else 4,'u1');pilot[g+'_flags']=np.zeros(f,'u1')
        pilot[g+'_source_ids']=np.array([[i,0] for i in range(b)] if g.endswith('bed') else [[b,1]] if f else [],dtype='<i4').reshape(f,2)
    pilot.update(source_grid=grid,source_triangles=tri,source_category=np.full(b,'BODY','<U9'),bed_source_face=np.arange(b,dtype='<i4'),npz_start=np.array(7,'<i4'),cap_before=np.array(0,'<i4'),cap_after=np.array(0,'<i4'))
    for k,v in o['extrema_2x5' if wide else 'extrema_2x2'].items():pilot[k]=np.array(v,dtype=ttype)
    arrays['pilot']=pilot
    sections=o['sections']
    if wide:
        for lod in sections[0]['lods']:lod['faces']=b+1;lod['sections'][0]['faces']=b
    expected=dict(o['expected_coverage']);expected.pop('npz_files');expected.pop('npz_members')
    spec={'model':'a/root.p3d','model_index':10,'instance_id':100,'site':'literal','station':[0.0,1.0],'file':'models/pilot.npz','faces':faces,'ambiguous_faces':{k:0 for k in faces},'unmapped_bed_faces':0,'source_regions':{'BODY':b},'checks':{}}
    source={'catalog':o['catalog'],'sections':sections,'routes':o['routes'],'epoch_pbo':'p'*64}
    if mutate:mutate(arrays,source,spec)
    archives=[]
    for kind,payload in arrays.items():
        rel='pilot-visible-surface-extraction-20261028/models/pilot.npz' if kind=='pilot' else ('geometry-payload-discovery-resolved-20261028/selected-instances.npz' if kind=='selected' else 'deployed-surface-prototypes-20261028/'+('surface-prototypes.npz' if kind=='prototypes' else 'instances.npz'))
        path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path,**payload)
        archives.append({'kind':kind,'relative':rel,'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'expanded_bound':1048576})
    by={x['kind']:x for x in archives};pins={}
    def save(label,v):pins[label]=write(root/label,v)
    for fn,v in [('model-catalog.json',source['catalog']),('model-sections.json',source['sections']),('proxy-paths.json',source['routes']),('report.json',{})]:save('deployed-surface-prototypes-20261028/'+fn,v)
    def record(a):return {'sha256':a['sha256'],'bytes':a['bytes']}
    sourcepins={str(root/'package-kit7-fc-world-20261026/compiled/narva_trial/baltic_trial.wrp'):'c'*64,str(root/'stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp'):'e'*64,'P:\\Mods\\@DayZ_Baltic_EV112_Kit7Nav8Load1\\Addons\\baltic_stream_pilot.pbo':source['epoch_pbo'],by['selected']['path']:by['selected']['sha256']}
    save('deployed-surface-prototypes-20261028/inputs.json',{'source_pins':sourcepins,'discovery_artifacts':{by['selected']['relative']:record(by['selected'])}})
    pmeta=dict(spec,sha256=by['pilot']['sha256'],sections=[{'lod':l['index'],'resolution':l['resolution'],'sections':l['sections']} for l in sections[0]['lods']],cap_rows=[])
    save('pilot-visible-surface-extraction-20261028/models.json',[pmeta]);save('pilot-visible-surface-extraction-20261028/report.json',{})
    surface=pins['deployed-surface-prototypes-20261028/inputs.json'];save('pilot-visible-surface-extraction-20261028/inputs.json',{'pins':{surface['path']:surface['sha256'],by['instances']['path']:by['instances']['sha256']}})
    pins['surface_manifest']=write(root/'surface-manifest.json',{a['relative']:record(a) for a in archives if a['kind'] in ('instances','prototypes')})
    pins['pilot_manifest']=write(root/'pilot-manifest.json',{by['pilot']['relative']:record(by['pilot'])})
    scene=copy.deepcopy(HIST);scene.update(source_root=str(root),pins=pins,arrays=archives,pilot_specs=[spec],expected=expected,epoch={'wrp_compiled':'c'*64,'wrp_editable':'e'*64,'pilot_pbo':'p'*64,'kind':'HISTORICAL_PIN_CHAIN_NOT_CURRENT_FILES'})
    contract=copy.deepcopy(ORIGINAL);contract['scene']=write(root/'scene.json',scene);cp=root/'contract.json';write(cp,contract)
    return contract,scene,sha(cp),cp
class Tests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory(dir=os.environ.get('Q03B4_TEST_ROOT'));self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def make(self,**kw):return fixture(self.root/str(len(list(self.root.iterdir()))),**kw)
    def reject(self,fn,code):
        with self.assertRaises(Exception) as x:fn()
        self.assertEqual(getattr(x.exception,'code',None),code,str(x.exception))
    def test_literal_cli_and_full_fields(self):
        c,s,h,path=self.make();out=self.root/'out';subprocess.run([sys.executable,'-I',str(D/'saved_scene_producer_q03b4.py'),str(path),h,str(out)],check=True,capture_output=True)
        report=json.loads((out/'report.json').read_bytes());self.assertEqual(report['models'],O['expected_models']);self.assertEqual(report['coverage'],O['expected_coverage']);self.assertEqual(report['proxy_routes'],O['routes'])
        static=copy.deepcopy(O['expected_pilot_static']);static['archive']='pilot-visible-surface-extraction-20261028/models/'+static['archive'];got=dict(report['pilots'][0]);got.pop('arraydigestmap');self.assertEqual(got,static)
        self.assertEqual(set(report),set(c['report_keys']));self.assertEqual(report['claims'],s['claims']);self.assertEqual(report['limitations'],c['historical_claims'])
        q=subprocess.run([sys.executable,'-I',str(D/'saved_scene_consumer_q03b4.py'),str(path),h,str(out/'report.json'),str(self.root/'consumed')],capture_output=True)
        self.assertEqual(q.returncode,0,q.stderr.decode());self.assertEqual(len(report['sources']),14)
    def test_positive_variants_N18(self):
        for i in O['positive_types']['integer']:
            for f in O['positive_types']['matrix']:
                c,s,h,_=self.make(itype=i,ftype=f,ttype='<i4' if f=='<f4' else '<i8',wide=True);r=P.produce(c,s,h);self.assertEqual(C.consume(c,s,h,r)['status'],'VERIFIED_SAVED_SCENE_INDEX_ONLY')
    def test_N01_header_then_changed_snapshot(self):
        c,s,h,_=self.make();reader=I.Reader(c);spec=s['arrays'][0]
        original=reader.session._prepare
        def changed(*args,**kw):r=original(*args,**kw);r['source_sha256']='0'*64;return r
        with patch.object(reader.session,'_prepare',changed):
            self.reject(lambda:reader.open(spec,P.names('prototypes'),lambda x:P.shape_rules(x,'prototypes',s['expected'])).__enter__(),'SOURCE_CHANGED')
    def test_N02_grid_N03_padding_N10_sourceface(self):
        mutations=[('GRID',lambda a,j,p:a['pilot']['body_col_max'].__setitem__(0,0)),('PADDING',lambda a,j,p:a['prototypes']['vertices'].__setitem__((0,3,0),-0.0)),('FACE',lambda a,j,p:a['pilot']['bed_source_ids'].__setitem__((0,0),999))]
        for code,fn in mutations:
            c,s,h,_=self.make(mutate=fn);self.reject(lambda:P.produce(c,s,h),code)
    def test_N04_proxy_N05_lod_N06_pose_N07_epoch(self):
        mutations=[('PROXY',lambda a,j,p:j['sections'][0]['proxies'][0].update(model='a/other.p3d')),('FACE',lambda a,j,p:a['prototypes']['meta']['lod'].__setitem__(0,1)),('POSE',lambda a,j,p:a['instances']['ids'].__setitem__(1,100)),('EPOCH',lambda a,j,p:j.update(epoch_pbo='wrong'))]
        for code,fn in mutations:
            c,s,h,_=self.make(mutate=fn);self.reject(lambda:P.produce(c,s,h),code)
    def test_N08_N12_N13_report_counterexamples(self):
        c,s,h,_=self.make();r=P.produce(c,s,h)
        def omit(x):x['models'][0]['runs'].pop();x['coverage']['prototype_faces']=3
        for mutate in (omit,lambda x:x['models'][0]['runs'][0].update(end=2),lambda x:x.update(contract_sha256='a'*64),lambda x:x['coverage'].update(human_resolved=False)):
            bad=copy.deepcopy(r);mutate(bad);self.reject(lambda:C.consume(c,s,h,bad),'REPORT')
        bad=copy.deepcopy(r);bad['extra']=0;self.reject(lambda:C.consume(c,s,h,bad),'SCHEMA')
    def test_N11_N16_N17_shapes_rejected_by_both(self):
        for field,val in [('ids.npy','<i2'),('source_category.npy','<U8')]:
            c,s,h,_=self.make();kind='instances' if field=='ids.npy' else 'pilot';spec=next(x for x in s['arrays'] if x['kind']==kind);reader=I.Reader(c);captured={}
            def observe(hh):captured.update(copy.deepcopy(hh))
            with reader.open(spec,P.names(kind),observe):pass
            captured[field]['dtype']=val
            self.reject(lambda:P.shape_rules(captured,kind,s['expected'],s['pilot_specs'][0]),'SCHEMA');self.reject(lambda:C.validate_headers(captured,kind,s['expected'],s['pilot_specs'][0]),'SCHEMA')
        c,s,h,_=self.make(mutate=lambda a,j,p:a['prototypes'].update(extra=np.array([1])))
        self.reject(lambda:P.produce(c,s,h),'MEMBER_SCHEMA')
    def test_N14_total_before_array_read(self):
        c,s,h,_=self.make();c['limits']['total']=1;reader=I.Reader(c)
        with patch.object(reader.archive.np.lib.format,'read_array',side_effect=AssertionError('allocated')):
            self.reject(lambda:reader.open(s['arrays'][0],P.names('prototypes'),lambda h:None).__enter__(),'TOTAL_CAP')
    def test_N15_missing_pin_file_coverage(self):
        c,s,h,_=self.make();s['arrays'].append(copy.deepcopy(s['arrays'][0]));self.reject(lambda:P.produce(c,s,h),'COVERAGE')
    def test_consumer_actually_rereads(self):
        c,s,h,_=self.make();r=P.produce(c,s,h);p=Path(s['arrays'][0]['path']);p.write_bytes(p.read_bytes()+b'X');self.reject(lambda:C.consume(c,s,h,r),'IDENTITY')
    def test_N09_permutation_equal_counts(self):
        # Negative literal category mismatch; both source and declared count can agree.
        c,s,h,_=self.make(mutate=lambda a,j,p:(a['pilot']['source_category'].__setitem__(0,'CAP_START'),p.update(source_regions={'CAP_START':1,'BODY':1})))
        self.reject(lambda:P.produce(c,s,h),'CATEGORY')
if __name__=='__main__':unittest.main(verbosity=2)
