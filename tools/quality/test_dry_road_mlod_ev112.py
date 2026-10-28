import importlib.util,struct,unittest
from pathlib import Path
from types import SimpleNamespace
import numpy as np
HERE=Path(__file__).resolve().parent
def module(name,file):
    s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
a=module('author','dry_road_mlod_ev112.py');c=module('consumer','verify_dry_road_mlod_ev112.py')

class MlodControls(unittest.TestCase):
    def test_unreferenced_normal_rejected(self):
        lod=SimpleNamespace(facenormals=[0,1],faces=[SimpleNamespace(vertices=[SimpleNamespace(point_index=0,normal_index=0)])])
        with self.assertRaisesRegex(ValueError,'normal_domain_incomplete'):c.normal_domains(lod)
    def test_water_cannot_reference_changed_bed_normal(self):
        lod=SimpleNamespace(facenormals=[0,1],faces=[SimpleNamespace(vertices=[SimpleNamespace(point_index=0,normal_index=0)]),SimpleNamespace(vertices=[SimpleNamespace(point_index=2,normal_index=0),SimpleNamespace(point_index=3,normal_index=1)])])
        with self.assertRaisesRegex(ValueError,'water_uses_bed_normal'):c.normal_domains(lod,1)
    def test_byte_patch_preserves_unknown_fields(self):
        blob=struct.pack('<4s6I',b'P3DM',28,256,1,1,0,0)+struct.pack('<3fI',1,2,3,19)+struct.pack('<3f',0,1,0)+b'TAGG-unknown'
        lod=SimpleNamespace(points=[0],facenormals=[0],faces=[])
        out,changes=a.patch_lod(blob,lod,{0:1.5},{0:[0,-1,0]})
        self.assertEqual(out[28:32],blob[28:32]);self.assertEqual(out[36:44],blob[36:44]);self.assertEqual(out[56:],blob[56:]);self.assertEqual(len(out),len(blob));self.assertEqual(len(changes),2)
    def test_nonrepresentable_Y_rejected(self):
        blob=struct.pack('<4s6I',b'P3DM',28,256,1,0,0,0)+bytes(16)
        with self.assertRaisesRegex(ValueError,'nonrepresentable'):a.patch_lod(blob,SimpleNamespace(points=[0],facenormals=[],faces=[]),{0:.1},{})
    def test_noop_patch_exact(self):
        blob=struct.pack('<4s6I',b'P3DM',28,256,1,0,0,0)+struct.pack('<3fI',1,2,3,19)
        out,w=a.patch_lod(blob,SimpleNamespace(points=[0],facenormals=[],faces=[]),{0:2},{})
        self.assertEqual(out,blob);self.assertEqual(w,[])
    def test_opposite_surface_normals(self):
        p=np.array([[0.,0.,0.],[1.,0.,0.],[0.,0.,1.]]);t=np.array([[0,1,2]])
        self.assertTrue(np.array_equal(a.normals(p,t),-a.normals(p,t,True)));self.assertTrue((a.normals(p,t)[:,1]==-1).all())
    def test_degenerate_rejected(self):
        with self.assertRaisesRegex(ValueError,'degenerate'):a.face_normals(np.zeros((3,3)),[[0,1,2]])
    def test_real_overlay_positive_and_bad_roof(self):
        source=np.array([[[0.,0.,0.],[1,0,0],[0,0,1]],[[1.,0.,0.],[1,0,1],[0,0,1]]])
        self.assertTrue(all(c.overlay(source,source)['checks'].values()))
        raised=source.copy();raised[:,:,1]+=.05
        self.assertFalse(c.overlay(source,raised)['checks']['vertical_contact_error'])
    def test_overlay_missing_half_rejected(self):
        source=np.array([[[0.,0.,0.],[1,0,0],[0,0,1]],[[1.,0.,0.],[1,0,1],[0,0,1]]])
        self.assertFalse(c.overlay(source,source[:1])['checks']['full_source_covered'])

if __name__=='__main__':unittest.main()
