import importlib.util
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np

SRC = Path(__file__).with_name("real_energy_bound.py")
spec = importlib.util.spec_from_file_location("real_energy_bound_fixture", SRC)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
v2 = mod._fraction_api()

class DriverFixtures(unittest.TestCase):
    def test_exact_physical_rows_use_local_rc_and_no_fixed_raw_indices(self):
        base=np.zeros((3,3),dtype=np.float32); base[1,1]=1.0; base[1,2]=-1.0
        crossing=SimpleNamespace(local_a=(1,1),local_b=(1,2),level_a=Fraction(0),level_b=Fraction(0),
            dry_endpoint=0,t_lower=Fraction(2,5),t_upper=Fraction(3,5))
        sign=SimpleNamespace(local_rc=(1,1),sign=1,level=Fraction(0),baseline=np.float32(1))
        rows,lo,hi=mod.physical_rows_from_specs(base,np.array([[1,1]],np.int32),
            np.array([-2.],np.float64),np.array([2.],np.float64),[crossing],[sign],
            np.array([[1,1,1,0]],np.int32),v2)
        ok,bad=mod.evaluate_exact_rows(rows,[1.0])
        self.assertTrue(ok,bad)
        self.assertEqual(len(rows),1+4+1)
        self.assertFalse(any(label.startswith("source_fixed_") or label.startswith("box_") for _,_,label in rows))
        self.assertEqual(float(lo[0]),-2.0); self.assertEqual(float(hi[0]),2.0)

    def test_superset_allows_boundary_and_rejects_wrong_crossing_side(self):
        base=np.zeros((3,3),dtype=np.float32); base[1,1]=1.0; base[1,2]=-1.0
        cross=SimpleNamespace(local_a=(1,1),local_b=(1,2),level_a=Fraction(0),level_b=Fraction(0),
            dry_endpoint=0,t_lower=Fraction(2,5),t_upper=Fraction(3,5))
        rows,_,_=mod.physical_rows_from_specs(base,np.array([[1,1]],np.int32),
            np.array([-2.]),np.array([2.]),[cross],[],np.empty((0,4),np.int32),v2)
        self.assertTrue(mod.evaluate_exact_rows(rows,[1.0])[0])
        ok,bad=mod.evaluate_exact_rows(rows,[-0.25])
        self.assertFalse(ok); self.assertIn("cross_dry_sign",bad["label"])

    def test_crossing_with_dry_endpoint_one(self):
        base=np.zeros((3,3),dtype=np.float32); base[1,1]=-1.0; base[1,2]=1.0
        cross=SimpleNamespace(local_a=(1,1),local_b=(1,2),level_a=Fraction(0),level_b=Fraction(0),
            dry_endpoint=1,t_lower=Fraction(2,5),t_upper=Fraction(3,5))
        rows,_,_=mod.physical_rows_from_specs(base,np.array([[1,2]],np.int32),
            np.array([-2.]),np.array([2.]),[cross],[],np.empty((0,4),np.int32),v2)
        self.assertTrue(mod.evaluate_exact_rows(rows,[1.0])[0])
        ok,bad=mod.evaluate_exact_rows(rows,[-0.25])
        self.assertFalse(ok); self.assertIn("cross_dry_sign",bad["label"])

    def test_dual_residual_box_support_and_negative_lambda(self):
        rows=[({0:Fraction(1)},Fraction(1,4),"x_ge_quarter")]
        out=mod.dual_certificate(Fraction(0),[Fraction(1)],Fraction(-1,2),rows,
                                 [Fraction(0)],[Fraction(1)],[Fraction(1)],Fraction(0),0.0,0.0)
        self.assertEqual(Fraction(out["tangent_lower_bound_exact"]),Fraction(-1,4))
        with self.assertRaisesRegex(ValueError,"negative dual"):
            mod.dual_certificate(Fraction(0),[1],Fraction(0),rows,[0],[1],[-1],0,0,0)

    def test_gate_threshold_rounding_is_conservative(self):
        raw=155.94405102975674; allowance=1.5594405102975674e-5
        t=mod.gate_threshold_exact(raw,allowance)
        self.assertGreater(t,Fraction.from_float(raw)+Fraction.from_float(allowance))
        self.assertEqual(float(t),mod.PHYSICAL_GATE_THRESHOLD)

    def test_square_guard_catches_pre_square_overflow_case(self):
        # 1e200 is below max_float/4 but its square is outside binary64 range.
        with self.assertRaisesRegex(OverflowError,"square"):
            mod.safe_csr_float64_eval_error_bound([{0:1.0e200}],[0.0],[0.0],[1.0])

    def test_accumulator_guard_catches_sum_margin(self):
        # Each ~9e306 term is below max/16; their sum is above the safety margin.
        with self.assertRaisesRegex(OverflowError,"accumulation"):
            mod.safe_csr_float64_eval_error_bound([{0:3.0e153},{0:3.0e153}],[0.0,0.0],[0.0],[1.0])

    def test_nonfinite_inputs_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"non-finite"):
            mod.safe_csr_float64_eval_error_bound([{0:float('nan')}],[0.0],[0.0],[1.0])

    def test_global_to_local_rc_roundtrip_and_shape_guard(self):
        global_rc=np.array([[856,1180],[859,1193]],dtype=np.int32)
        local=mod.global_rc_to_local(global_rc,(855,1179))
        np.testing.assert_array_equal(local,[[1,1],[4,14]])
        with self.assertRaisesRegex(ValueError,"coordinates"):
            mod.global_rc_to_local(np.array([[856,1180,1]]),(855,1179))

    def test_real_lp_entrypoint_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,"disabled"):
            mod.obtain_dual_from_linprog({},allow_real_lp=True)

if __name__=="__main__": unittest.main(verbosity=2)

