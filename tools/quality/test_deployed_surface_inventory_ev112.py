"""Independent geometric and malformed-input controls for prototype extraction."""
import hashlib, importlib.util, io, json, struct, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace as S
import numpy as np
from shapely.geometry import Polygon
P=Path(__file__).with_name('deployed_surface_inventory_ev112.py')
spec=importlib.util.spec_from_file_location('surfaces',P);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def section(indices, texture=0, material=0, name=''):
    return S(texture_index=texture,material_index=material,mat_name=name,get_face_indices=lambda faces:indices)


def lod(resolution=0., material='DZ\\Water\\Streams\\Data\\Water_Streambed.rvmat'):
    return S(resolution=resolution,lod_end_ok=True,
             vertices=[S(x=x,y=2.,z=z) for x,z in ((0,0),(5,0),(5,3),(0,3))],
             faces=[S(vertex_indices=[0,1,2,3])],sections=[section([0])],
             textures=['DZ\\Data\\SURFACES\\water_ext.paa'],materials=[S(material_name=material)],proxies=[])


def odol(lods):
    return S(lods=lods,resolutions=[l.resolution for l in lods],lod_errors={},model_info=S(bounding_center=S(x=0.,y=0.,z=0.)))


class Geometry(unittest.TestCase):
    def test_root_matrix_orientation_and_scale(self):
        # Column axes map local X -> world +Z, local Z -> world -X; scale is 2.
        pose=[0,0,2, 0,2,0, -2,0,0, 100,7,200]
        np.testing.assert_array_equal(m.transform([[3,4,5]],pose),[[90,15,206]])

    def test_proxy_center_and_rotation(self):
        pose=[0,0,1, 0,1,0, -1,0,0, 20,30,40]
        # Stored [1,2,3] plus center [4,5,6] => author [5,7,9].
        np.testing.assert_array_equal(m.proxy_transform([[1,2,3]],[4,5,6],pose),[[11,37,45]])

    def test_projection_matches_independent_polygon(self):
        p=np.array([[0,0,0],[7,0,0],[6,0,3],[0,0,2.]])
        self.assertEqual(m.face_flag(p),0)
        poly=Polygon(p[:,[0,2]])
        fan=Polygon(p[[0,1,2]][:,[0,2]]).union(Polygon(p[[0,2,3]][:,[0,2]]))
        self.assertEqual(poly.symmetric_difference(fan).area,0)

    def test_ambiguous_quad_and_concave(self):
        a=np.array([[0,0,0],[7,0,0],[6,0,3],[0,1,2.]])
        self.assertEqual(m.face_flag(a),m.AMBIGUOUS_FACE)
        self.assertEqual(m.face_flag([[0,0,0],[5,0,0],[1,0,1],[0,0,4]]),m.AMBIGUOUS_FACE)

    def test_degenerate_and_nonfinite(self):
        self.assertEqual(m.face_flag([[0,0,0],[1,1,1],[2,2,2]]),m.DEGENERATE_FACE)
        with self.assertRaisesRegex(ValueError,'face_input'):m.face_flag([[0,0,0],[1,0,0],[0,np.nan,0]])

    def test_vertical_face_retained(self):
        self.assertEqual(m.face_flag([[0,0,0],[0,3,0],[0,3,4],[0,0,4]]),0)

    def test_matrix_diagnostics(self):
        row=[2,0,0,1,3,0,0,0,4,10,20,30];r=m.matrix_inventory([row])
        self.assertAlmostEqual(r['determinant'][0],24);self.assertEqual(r['nonorthogonality'][0],2)

    def test_proxy_dependency_and_cycle(self):
        v=np.array([[[1,2,3],[4,2,3],[1,2,6],[0,0,0]]],float)
        meta=np.array([(1,1,2,0,0,1,3,0,-1,0.)],m.META)
        info=dict(center=[4,5,6],proxies=[])
        parent=dict(center=[0,0,0],proxies=[dict(model='b',matrix=[0,0,1,0,1,0,-1,0,0,20,30,40])])
        empty=(np.empty((0,4,3)),np.empty(0,m.META))
        ps={'a':(*empty,parent),'b':(v,meta,info)}
        out,ids=m.expand_proxies('a',ps,{'a':0,'b':1})
        np.testing.assert_array_equal(out[0,0],[11,37,45]);self.assertEqual(ids['kind'][0],2)
        self.assertTrue(ids['flags'][0]&m.PROXY_CONDITIONAL);self.assertEqual(ids['source_model'][0],1)
        ps['b'][2]['proxies']=[dict(model='a',matrix=[1,0,0,0,1,0,0,0,1,0,0,0])]
        with self.assertRaisesRegex(ValueError,'proxy_cycle'):m.expand_proxies('a',ps,{'a':0,'b':1})
        del ps['b']
        with self.assertRaisesRegex(ValueError,'missing_proxy'):m.expand_proxies('a',ps,{'a':0,'b':1})

    def test_nested_and_repeated_proxies_keep_full_path(self):
        v=np.array([[[0,0,0],[1,0,0],[0,0,1],[0,0,0]]],float)
        # Child includes Roadway and water. Only one face must travel up each path.
        meta=np.array([(2,2,0,0,0,0,3,0,-1,0.),(2,2,0,0,0,1,3,0,-1,0.)],m.META)
        empty=(np.empty((0,4,3)),np.empty(0,m.META));I=[1,0,0,0,1,0,0,0,1]
        ps={'root':(*empty,dict(center=[100,0,0],proxies=[dict(model='mid',matrix=I+[10,0,0]),dict(model='mid',matrix=I+[20,0,0])])),
            'mid':(*empty,dict(center=[2,0,0],proxies=[dict(model='leaf',matrix=I+[3,0,0])])),
            'leaf':(np.repeat(v,2,axis=0),meta,dict(center=[4,0,0],proxies=[]))}
        paths=[];out,ids=m.expand_proxies('root',ps,{'root':0,'mid':1,'leaf':2},paths=paths)
        self.assertEqual(len(out),2);np.testing.assert_array_equal(out[:,0,0],[19,29])
        np.testing.assert_array_equal(ids['kind'],[2,2]);self.assertNotEqual(ids['proxy'][0],ids['proxy'][1])
        self.assertEqual(paths[0]['slots'],[[0,0],[1,0]]);self.assertEqual(paths[1]['slots'],[[0,1],[1,0]])

    def test_planarity_magnitude_retained(self):
        flag,res=m.face_diagnostics([[0,0,0],[1,0,0],[1,0,1],[0,.000001,1]])
        self.assertEqual(flag,m.AMBIGUOUS_FACE);self.assertAlmostEqual(res,.000001)


class Consumer(unittest.TestCase):
    def test_windows_water_and_roadway_separate(self):
        v,ids,e=m.extract(odol([lod(),lod(m.ROADWAY)]),5)
        self.assertEqual(len(v),2);self.assertEqual(sorted(ids['kind']),[0,1])
        self.assertEqual(e['lods'][0]['sections'][0]['material'],'dz/water/streams/data/water_streambed.rvmat')
        self.assertIn('\\',e['lods'][0]['sections'][0]['material_raw'])

    def test_unknown_material_is_not_water(self):
        v,ids,e=m.extract(odol([lod(material='x/water_streambed.rvmat')]),0)
        self.assertEqual(len(ids),0);self.assertEqual(e['lods'][0]['sections'][0]['faces'],1)

    def test_empty_texture_not_omitted(self):
        a=lod(m.ROADWAY,material='');a.sections=[section([0],texture=-1,material=-1)]
        v,ids,e=m.extract(odol([lod(material='x'),a]),0)
        self.assertEqual(len(ids),1);self.assertEqual(ids['kind'][0],0)
        self.assertEqual(e['lods'][1]['sections'][0]['texture'],'')

    def test_lod_exact_not_nearest(self):
        self.assertEqual(m.select_lods([0.,m.ROADWAY+1e8]),(0,None))
        with self.assertRaisesRegex(ValueError,'duplicate_roadway'):m.select_lods([0.,m.ROADWAY,m.ROADWAY])
        with self.assertRaisesRegex(ValueError,'duplicate_visual'):m.select_lods([0.,0.])
        with self.assertRaisesRegex(ValueError,'missing_visual'):m.select_lods([m.ROADWAY])

    def test_section_omission_and_overlap(self):
        a=lod();a.sections=[]
        with self.assertRaisesRegex(ValueError,'unassigned_face'):m.sections(a)
        a.sections=[section([0]),section([0])]
        with self.assertRaisesRegex(ValueError,'overlapping_sections'):m.sections(a)
        a.sections=[section([0],material=4)]
        with self.assertRaisesRegex(ValueError,'section_index'):m.sections(a)

    def test_bad_face_or_incomplete_decode(self):
        a=lod();a.faces[0].vertex_indices=[0,1,8]
        with self.assertRaisesRegex(ValueError,'face_vertex_indices'):m.extract(odol([a]),0)
        o=odol([lod()]);o.lod_errors={1:'bad'}
        with self.assertRaisesRegex(ValueError,'incomplete_odol'):m.extract(o,0)

    def test_multiple_faces_including_degenerate_are_retained(self):
        a=lod(m.ROADWAY,material='');a.faces=[S(vertex_indices=[0,1,2]),S(vertex_indices=[0,1,2,3]),S(vertex_indices=[0,0,0])]
        a.sections=[section([0,1,2])]
        v,ids,e=m.extract(odol([lod(material='x'),a]),0)
        self.assertEqual(len(ids),3);np.testing.assert_array_equal(ids['face'],[0,1,2])
        np.testing.assert_array_equal(ids['flags'],[0,0,m.DEGENERATE_FACE]);self.assertEqual(ids['vertices'][1],4)


class Provenance(unittest.TestCase):
    def test_real_manifest_keys(self):
        p=P.parents[2]/'evidence/deployed-geometry-discovery-20261028/artifact-hashes.json'
        values=m.manifest_keys(json.loads(p.read_text(encoding='utf-8')))
        for name in ('all-models.json','payload-bindings.json','inputs.json','selected-instances.npz'):
            self.assertIn('geometry-payload-discovery-resolved-20261028/'+name,values)
        with self.assertRaisesRegex(ValueError,'ambiguous_artifact'):
            m.manifest_keys({'a/b':{},'A\\B':{}})

    def test_sealed_snapshot_and_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'a.json';p.write_bytes(b'old')
            manifest=m.manifest_keys({'a.json':dict(sha256=hashlib.sha256(b'old').hexdigest())})
            data=m.sealed_bytes(p,root,manifest);p.write_bytes(b'new')
            self.assertEqual(data,b'old')
            with self.assertRaisesRegex(ValueError,'discovery_changed'):m.sealed_bytes(p,root,manifest)

    def test_instance_coverage_and_mutation(self):
        catalog=[dict(index=0,instances=2,group='bridge'),dict(index=1,instances=5,group='vegetation_not_inspected')]
        ids=np.array([12,19]);mi=np.array([0,0]);matrix=np.tile([1,0,0,0,1,0,0,0,1,0,0,0],(2,1))
        self.assertEqual(len(m.instance_guard(ids,mi,matrix,catalog)['norm']),2)
        with self.assertRaisesRegex(ValueError,'instance_identity'):m.instance_guard(np.array([12,12]),mi,matrix,catalog)
        with self.assertRaisesRegex(ValueError,'instance_coverage'):m.instance_guard(ids,np.array([0,1]),matrix,catalog)
        with self.assertRaisesRegex(ValueError,'instance_shape'):m.instance_guard(ids,mi,matrix[:1],catalog)


class PBO(unittest.TestCase):
    @staticmethod
    def archive(names):
        return b''.join(n.encode()+b'\0'+struct.pack('<5I',0,0,0,0,len(data)) for n,data in names)+bytes(21)+b''.join(data for n,data in names)

    def test_reader_and_hash_mutation(self):
        b=self.archive([('a.p3d',b'first'),('b.p3d',b'last')]);f=io.BytesIO(b);_,entries=m.pbo_table(f,len(b))
        self.assertEqual(m.read_payload(f,entries[1],hashlib.sha256(b'last').hexdigest()),b'last')
        with self.assertRaisesRegex(ValueError,'payload_hash'):m.read_payload(f,entries[1],'0'*64)

    def test_archive_ambiguity_truncation_compression(self):
        b=self.archive([('a',b'data')])
        for blob in (self.archive([('a',b'x'),('A',b'y')]),self.archive([('../a',b'x')]),b[:-1],b[:4]):
            with self.assertRaises(ValueError):m.pbo_table(io.BytesIO(blob),len(blob))
        with self.assertRaisesRegex(ValueError,'compressed'):m.read_payload(io.BytesIO(b),dict(mime=1),'')

    def test_properties_and_mixed_path(self):
        prop=b'\0'+struct.pack('<5I',0x56657273,0,0,0,0)+b'prefix\0DZ\\Water\0\0'
        b=prop+self.archive([('A\\B.P3D',b'payload')]);p,e=m.pbo_table(io.BytesIO(b),len(b))
        self.assertEqual(m.norm(p['prefix']),'dz/water');self.assertEqual(e[0]['name'],'a/b.p3d')


if __name__=='__main__':unittest.main(verbosity=2)
