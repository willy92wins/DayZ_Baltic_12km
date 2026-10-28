import io,math,struct,tempfile,unittest,sys
from pathlib import Path
from types import SimpleNamespace as N
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parent))
import road_asset_catalog_ev112 as c

def vec(x,y,z):return N(x=x,y=y,z=z)
def model(roadway=False):
    vertices=[vec(-6,0,-12.5),vec(6,0,-12.5),vec(6,0,12.5)]
    section=N(texture_index=0,material_index=-1,mat_name='',get_face_indices=lambda faces:[0])
    lod=N(resolution=c.f32(3e15) if roadway else 0.,lod_end_ok=True,vertices=vertices,
          vertex_raw=b''.join(struct.pack('<fff',p.x,p.y,p.z) for p in vertices),faces=[N(vertex_indices=[0,1,2])],
          sections=[section],materials=[],textures=['road.paa'],named_selections=[],named_properties=[('class','road')],
          b_min=vec(-6,0,-12.5),b_max=vec(6,0,12.5),b_center=vec(0,0,0),proxies=[],frames=[])
    return N(lods=[lod],lod_errors={},n_lods=1,resolutions=[lod.resolution],version=54,
             model_info=N(bbox_min=vec(-6,0,-12.5),bbox_max=vec(6,0,12.5),bounding_center=vec(0,0,0),animated=False))

def pbo(names=('parts/ASf1.p3d','bridges/a.p3d','config.bin'),prefix='dz\\structures\\roads',mime=0,trailer=b''):
    header=b'\0'+struct.pack('<5I',0x56657273,0,0,0,0)+b'prefix\0'+prefix.encode()+b'\0\0'
    payloads={n:b'ODOL' if n.lower().endswith('.p3d') else b'cfg' for n in names}
    for n in names:header+=n.encode()+b'\0'+struct.pack('<5I',mime,0,0,0,len(payloads[n]))
    return header+b'\0'+bytes(20)+b''.join(payloads[n] for n in names)+trailer

def parse(data):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'test.pbo';p.write_bytes(data);raw,props,entries=c.read_pbo(p)
        return c.check_table(raw,props,entries),entries

class CatalogTests(unittest.TestCase):
    def test_complete_table_case_and_payload(self):
        (rows,tail),entries=parse(pbo());self.assertEqual(len(rows),3);self.assertEqual(rows[0]['name'],'parts/ASf1.p3d')
        self.assertEqual(rows[0]['category'],'road_part_by_path');self.assertEqual(tail['payload_end'],tail['file_bytes'])
    def test_optional_trailer_shape(self):
        self.assertEqual(len(parse(pbo(trailer=b'\0'+b'x'*20))[0][1]['trailer_hex']),42)
        with self.assertRaisesRegex(ValueError,'trailer'):parse(pbo(trailer=b'junk'))
    def test_duplicate_case(self):
        with self.assertRaisesRegex(ValueError,'Duplicate'):parse(pbo(names=('parts/A.p3d','parts/a.p3d')))
    def test_prefix_and_truncation(self):
        with self.assertRaisesRegex(ValueError,'prefix'):parse(pbo(prefix='wrong'))
        with self.assertRaises(ValueError):parse(pbo()[:-1])
    def test_compressed_not_green(self):
        with self.assertRaisesRegex(ValueError,'Compressed'):parse(pbo(mime=0x43707273))
    def test_omitted_payload_not_green(self):
        data=pbo();props,table=c.pbo_table(io.BytesIO(data),len(data))
        with self.assertRaisesRegex(ValueError,'coverage'):c.check_table(data,props,{'config.bin':b'cfg'})
    def test_analytic_bbox_raw_and_no_roadway(self):
        out=c.model_metadata(model());self.assertEqual(out['lods'][0]['bbox'],dict(min=[-6,0,-12.5],max=[6,0,12.5]))
        self.assertFalse(out['roadway_present']);self.assertEqual(out['usable_width'],'UNDETERMINED')
        self.assertNotIn('vertex_raw',out['lods'][0]);self.assertIsInstance(out['lods'][0]['vertices'],int)
    def test_roadway_not_usable_width(self):
        out=c.model_metadata(model(True));self.assertTrue(out['roadway_present']);self.assertEqual(out['usable_width'],'UNDETERMINED')
    def test_incomplete_lod_and_model(self):
        m=model();m.lods[0].lod_end_ok=False
        with self.assertRaisesRegex(ValueError,'incomplete_lod'):c.model_metadata(m)
        m=model();m.n_lods=2
        with self.assertRaisesRegex(ValueError,'incomplete_model'):c.model_metadata(m)
    def test_nan_and_scale(self):
        m=model();m.lods[0].vertices[0].x=math.nan
        with self.assertRaisesRegex(ValueError,'nonfinite'):c.model_metadata(m)
        with self.assertRaisesRegex(ValueError,'nonunit'):c.model_metadata(model(),2)
    def test_raw_disagreement(self):
        m=model();m.lods[0].vertices[0].x=-5
        with self.assertRaisesRegex(ValueError,'disagreement'):c.model_metadata(m)
    def test_bad_face_or_section_not_green(self):
        m=model();m.lods[0].faces[0].vertex_indices=[0,1,9]
        with self.assertRaisesRegex(ValueError,'face_indices'):c.model_metadata(m)
        m=model();m.lods[0].sections=[]
        with self.assertRaisesRegex(ValueError,'unassigned'):c.model_metadata(m)
    def test_denominator_retains_errors(self):
        (rows,_),entries=parse(pbo());calls=[];emitted=[]
        def decoder(b,strict):
            calls.append(strict)
            if len(calls)==1:raise ValueError('unsupported fixture')
            return model(True)
        records=c.collect(rows,entries,decoder,emitted.append)
        self.assertEqual(len(records),2);self.assertEqual(calls,[True,True]);self.assertEqual(len(emitted),2)
        self.assertEqual(c.verify_coverage(rows,records),'INCONCLUSIVE_CATALOG')
    def test_missing_duplicate_or_mutated_model(self):
        (rows,_),entries=parse(pbo());records=c.collect(rows,entries,lambda b,strict:model(),lambda row:None)
        self.assertEqual(c.verify_coverage(rows,records),'CATALOG_COMPLETE_NOT_PLACEMENT_ACCEPTANCE')
        for bad in (records[:-1],records+[records[0]],records[::-1]):
            with self.assertRaisesRegex(ValueError,'coverage'):c.verify_coverage(rows,bad)
        records[0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'coverage'):c.verify_coverage(rows,records)
    def test_false_width(self):
        (rows,_),entries=parse(pbo());records=c.collect(rows,entries,lambda b,strict:model(),lambda row:None)
        records[0]['measurement']['usable_width']=12
        with self.assertRaisesRegex(ValueError,'false_width'):c.verify_coverage(rows,records)
    def test_unknown_category_is_retained(self):
        (rows,_),entries=parse(pbo(names=('ODD.P3D','notes.txt')))
        self.assertEqual(rows[0]['category'],'other_model');self.assertEqual(rows[1]['category'],'non_model')
    def test_nonfinite_resolution_and_selections(self):
        m=model();m.lods[0].resolution=math.nan
        with self.assertRaisesRegex(ValueError,'resolution'):c.model_metadata(m)
        m=model();m.lods[0].named_selections=[N(name='bad',selected_vertices=[9],selected_faces=[],is_sectional=False,sections=[])]
        with self.assertRaisesRegex(ValueError,'selection'):c.model_metadata(m)
    def test_serialization_failure_keeps_full_denominator(self):
        (rows,_),entries=parse(pbo());calls=[]
        def decoder(b,strict):
            m=model();calls.append(1)
            if len(calls)==1:m.lods[0].named_properties=[('bad',b'not-json')]
            return m
        records=c.collect(rows,entries,decoder,lambda row:__import__('json').dumps(row,allow_nan=False))
        self.assertEqual(len(records),2);self.assertEqual(records[0]['status'],'INCONCLUSIVE_PARSE')
        self.assertEqual(records[1]['status'],'READ_STRICT');self.assertEqual(c.verify_coverage(rows,records),'INCONCLUSIVE_CATALOG')
    def test_loaded_reader_shadow(self):
        modules={Path(n).stem:N(__file__=str(c.READER/n)) for n in c.READER_PINS}
        with mock.patch.dict(sys.modules,modules):
            c.loaded_reader_binding()
            sys.modules['bis_reader']=N(__file__=str(Path.cwd()/'bis_reader.py'))
            with self.assertRaisesRegex(ValueError,'shadowed'):c.loaded_reader_binding()
    def test_missing_error_record(self):
        (rows,_),entries=parse(pbo());records=c.collect(rows,entries,lambda b,strict:model(),lambda row:None)
        records[0]={'name':records[0]['name'],'sha256':records[0]['sha256'],'status':'INCONCLUSIVE_PARSE'}
        with self.assertRaisesRegex(ValueError,'model_record'):c.verify_coverage(rows,records)

if __name__=='__main__':unittest.main()
