from fractions import Fraction as F
import importlib.util
from pathlib import Path
import sys
import unittest
import numpy as np
from scipy import sparse

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import certified_tangent as ct
LATTICE=Path(r'E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\G\wet-bank-pilot\postsolve-consumer\float32-component-conversion-v1\robust-f32-design\candidate-only-milp\d8-sign-fix-v1\lattice_milp.py')
spec=importlib.util.spec_from_file_location('pinned_lattice_milp',LATTICE)
lm=importlib.util.module_from_spec(spec);sys.modules[spec.name]=lm;spec.loader.exec_module(lm)

class CertifiedTangentTests(unittest.TestCase):
    def test_crossing_orientation_lower_upper_and_fixed_endpoint(self):
        base=np.array([[np.float32(0),np.float32(-1)]],dtype=np.float32)
        xrc=np.array([[0,0]],np.int32); lo=np.array([0],np.float32); hi=np.array([2],np.float32)
        crossing=lm.Crossing((0,0),(0,1),F(0),F(0),0,F(1,4),F(1,2),'fixture')
        rows=ct.build_physical_rows(base,xrc,lo,hi,crossings=[crossing])
        by={label:(row,b) for row,b,label in rows}
        self.assertEqual(by['cross_lower:0'][0],{0:F(3,4)})
        self.assertEqual(by['cross_lower:0'][1],F(1,4))
        self.assertEqual(by['cross_upper:0'][0],{0:F(-1,2)})
        self.assertEqual(by['cross_upper:0'][1],F(-1,2))
        # H_dry=1/3, H_wet=-1 gives t=1/4 and satisfies both rows.
        x=F(1,3)
        self.assertGreaterEqual(F(3,4)*x,F(1,4))
        self.assertGreaterEqual(F(-1,2)*x,F(-1,2))
        # Lower/upper reversed would reject this exact boundary witness.
        self.assertFalse(F(1,4)*x >= F(1,4))

    def test_sign_contact_and_d8_rows(self):
        base=np.array([[2,1],[0,0]],dtype=np.float32)
        xrc=np.array([[0,0]],np.int32); lo=np.array([0],np.float32); hi=np.array([3],np.float32)
        signs=[lm.Sign((0,0),F(1),1,None,'positive'),lm.Sign((0,0),F(0),0,np.float32(2),'contact')]
        rows=ct.build_physical_rows(base,xrc,lo,hi,signs=signs,d8_witnesses=[((0,0),(0,1))])
        by={label:(row,b) for row,b,label in rows}
        self.assertEqual(by['sign_above_relaxed:0'],({0:F(1)},F(1)))
        self.assertEqual(by['sign_contact_lower:1'],({0:F(1)},F(2)))
        self.assertEqual(by['sign_contact_upper:1'],({0:F(-1)},F(-2)))
        self.assertEqual(by['d8_center_ge_witness:0'],({0:F(1)},F(1)))

    def test_source_singleton_is_pinned_not_treated_as_free_box(self):
        base=np.array([[2]],dtype=np.float32); rc=np.array([[0,0]],np.int32)
        rows=ct.build_physical_rows(base,rc,np.array([1],np.float32),np.array([3],np.float32),fixed_indices=[0])
        by={label:(row,b) for row,b,label in rows}
        self.assertEqual(by['source_fixed_lower:0'],({0:F(1)},F(2)))
        self.assertEqual(by['source_fixed_upper:0'],({0:F(-1)},F(-2)))
        self.assertFalse(3 >= 2 and -3 >= -2)

    def test_analytic_dual_certifies_threshold_and_residual_correction(self):
        J,g,k=ct.objective_tangent([{0:F(1)}],[F(2)],[F(1)])
        self.assertEqual((J,g,k),(F(1,2),[F(-1)],F(3,2)))
        base=np.array([[0]],dtype=np.float32); rc=np.array([[0,0]],np.int32)
        rows=ct.build_physical_rows(base,rc,np.array([0],np.float32),np.array([1],np.float32))
        labels=[label for _,_,label in rows]
        lam=[F(1) if label=='box_upper:0' else F(0) for label in labels]
        lb=ct.dual_tangent_lower_bound(J,g,k,rows,[0],[1],lam)
        self.assertEqual(lb,F(1,2))
        self.assertTrue(ct.impossible_for_float_gate(lb,F(0),0.49))
        self.assertFalse(ct.impossible_for_float_gate(lb,F(0),0.5))
        # Inexact dual stationarity remains valid only with residual-box term.
        lam2=[F(1,2) if label=='box_upper:0' else F(0) for label in labels]
        self.assertEqual(ct.dual_tangent_lower_bound(J,g,k,rows,[0],[1],lam2),F(1,2))
        # Omitting residual correction would claim an invalid bound of 1.5.
        self.assertNotEqual(k+sum((v*b for v,(_,b,_) in zip(lam2,rows)),F(0)),F(1,2))

    def test_negative_dual_and_nonfinite_fail_closed(self):
        J,g,k=ct.objective_tangent([{0:1.0}],[2.0],[1.0])
        base=np.array([[0]],dtype=np.float32);rc=np.array([[0,0]],np.int32)
        rows=ct.build_physical_rows(base,rc,np.array([0],np.float32),np.array([1],np.float32))
        lam=[-0.01 if label=='box_upper:0' else 0.0 for _,_,label in rows]
        with self.assertRaisesRegex(ValueError,'negative dual'):
            ct.dual_tangent_lower_bound(J,g,k,rows,[0],[1],lam)
        for value in (float('nan'),float('inf'),-float('inf')):
            with self.assertRaises(ValueError): ct.Q(value)

    def test_csr_float64_error_bound_covers_actual_evaluator(self):
        dense=np.array([[0.1,-0.25],[1.0,0.0],[-0.3,0.7]],dtype=np.float64)
        A=sparse.csr_matrix(dense)
        rows=ct.csr_rows_from_arrays(A.data,A.indices,A.indptr,A.shape)
        rhs=np.array([0.7,-0.4,0.2],dtype=np.float64)
        lo=np.array([0.0,-1.0],dtype=np.float32); hi=np.array([1.0,2.0],dtype=np.float32)
        err=ct.csr_float64_eval_error_bound(rows,rhs,lo,hi)
        self.assertGreater(err,0)
        for x in (np.array([0.,-1.]),np.array([1.,2.]),np.array([.37,.91]),np.array([.125,-.25])):
            exact=F(0)
            for row,b in zip(rows,rhs):
                e=sum((a*ct.Q(x[j]) for j,a in row.items()),F(0))-ct.Q(b)
                exact+=e*e/2
            computed=0.5*float(np.sum((A@x-rhs)**2))
            self.assertLessEqual(abs(ct.Q(computed)-exact),err)
        # Exact rational conversion preserves each binary64 coefficient.
        self.assertEqual(rows[0][0],F.from_float(0.1))

if __name__=='__main__': unittest.main(verbosity=2)

