from pathlib import Path
import importlib.util,unittest,tempfile,hashlib
import numpy as np
R=Path(__file__).parent;s=importlib.util.spec_from_file_location('pilot',R/'pilot_dry_apron.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_wrong_input_identity_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'input.txt';p.write_bytes(b'fixture');m.check_expected({p:hashlib.sha256(b'fixture').hexdigest()})
   with self.assertRaises(ValueError):m.check_expected({p:'0'*64})
 def test_pre_rounding_floor_ramp(self):
  H=np.array([[0.,1.08],[0.,1.08]]);x=np.array([3.]);z=np.array([12279.]);g=np.array([.54]);lower=m.support_rounding_lower_bound(H,x,z,g)
  self.assertAlmostEqual(lower[0],.54-.18/1024)
 def test_pre_rounding_floor_diagonal_valley(self):
  # y=abs(x-row) in one NW-SE cell: the box can straddle the valley.
  H=np.array([[0.,6.],[6.,0.]]);x=np.array([3.0003]);z=np.array([12279.]);g=np.array([.0003]);lower=m.support_rounding_lower_bound(H,x,z,g)
  self.assertLessEqual(lower[0],0.)
 def test_protected_high_floor_stays_exact(self):
  out,valid=m.quantize_bounded(np.array([0.,0.]),np.array([4.,4.]),np.array([False,True]),np.array([3.,3.]),np.array([4.,4.]))
  self.assertTrue(np.array_equal(out,[4.,3.]))
 def test_empty_quantized_interval_keeps_original(self):
  out,valid=m.quantize_bounded(np.array([1.0002]),np.array([1.]),np.array([True]),np.array([1.0001]),np.array([1.0003]))
  self.assertFalse(valid[0]);self.assertEqual(out[0],1.)
 def test_directed_rounding_respects_both_bounds(self):
  out,valid=m.quantize_bounded(np.array([.9,1.1]),np.array([2.,2.]),np.ones(2,bool),np.array([1.0001,1.]),np.array([2.,1.003]))
  self.assertGreaterEqual(out[0],1.0001);self.assertLessEqual(out[1],1.003);self.assertTrue(np.array_equal(out,np.rint(out*512)/512))
 def test_noop_mask(self):
  old=np.array([1.,2.,3.]);out,valid=m.quantize_bounded(old-1,old,np.zeros(3,bool),old,old)
  self.assertTrue(np.array_equal(out,old));self.assertFalse(valid.any())
 def test_nonfinite_rejected(self):
  with self.assertRaises(ValueError):m.quantize_bounded(np.array([np.nan]),np.array([1.]),np.array([True]),np.array([0.]),np.array([1.]))
 def test_physical_slope_not_parameter_index(self):
  bed=np.array([[[0.,0.,0.],[.5,1.,0.]],[[0.,0.,3.],[.5,1.,3.]]]);faces=np.array([[0,2,3],[0,3,1]])
  r=m.slope_metrics(bed,faces);self.assertEqual(r['transverse_max'],2.);self.assertEqual(r['face_max'],2.);self.assertEqual(r['longitudinal_max'],0.)
 def test_collapsed_face_rejected(self):
  bed=np.zeros((2,2,3));faces=np.array([[0,2,3],[0,3,1]])
  with self.assertRaises(ValueError):m.slope_metrics(bed,faces)
if __name__=='__main__':unittest.main()
