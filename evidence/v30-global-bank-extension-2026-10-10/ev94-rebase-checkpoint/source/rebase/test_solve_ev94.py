"""Independent analytic KKT and malformed-input controls; never solve map data."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from scipy import sparse
import solve_ev94 as s


def fixture():
    base=np.zeros((260,260),np.float32)
    nodes=np.asarray([[5,5]],np.int32)
    fixed=np.ones(base.shape,np.uint8); fixed[5,5]=0
    A=sparse.csr_matrix([[1.]])
    C=sparse.csr_matrix([[1.]])
    p=dict(base_local=base,nodes_local=nodes,lo=np.array([0.]),hi=np.array([1.]),x0=np.array([0.]),
           fixed_mask=fixed,rhs=np.array([2.]),d=np.array([0.]),witnesses_json=np.frombuffer(b'[]',np.uint8))
    for name,m in [('A',A),('C',C)]:
        p.update({name+'_data':m.data,name+'_indices':m.indices,name+'_indptr':m.indptr,name+'_shape':np.array(m.shape)})
    return p


class Tests(unittest.TestCase):
    def test_pinned_helpers(self):
        s.check_hashes({str(k):v for k,v in s.PINS.items()})

    def test_baseline_and_negative_controls(self):
        s.unpack(fixture())
        for change in ('nan','mask','nodes','x0','bound','order','operator'):
            with self.subTest(change=change):
                p=fixture()
                if change=='nan': p['rhs'][0]=np.nan
                elif change=='mask': p['fixed_mask'][5,5]=1
                elif change=='nodes': p['nodes_local'][0,0]=0
                elif change=='x0': p['x0'][0]=.5
                elif change=='bound': p['hi'][0]=-.1
                elif change=='order': p['d'][0]=.1
                elif change=='operator': p['A_data'][0]=np.inf
                with self.assertRaises(ValueError): s.unpack(p)

    def test_analytic_constrained_optimum_and_false_multiplier(self):
        solver=s.load('test_ev94_pinned_solver',s.SOLVER)
        helper=s.load('test_ev94_pinned_kkt',s.OC)
        _,_,lo,hi,x0,_,A,rhs,C,d,_,_=s.unpack(fixture())
        x,diag,history,state=solver.solve(A,rhs,C,d,lo,hi,x0,10.,lambda _:None)
        # min .5*(x-2)^2 on [0,1] has unique optimum x=1, upper dual +1.
        self.assertEqual(diag['status'],'CONVERGED')
        self.assertLess(abs(x[0]-1.),1e-7)
        self.assertLess(abs(state['y_box'][0]-1.),1e-7)
        self.assertTrue(helper.kkt_report({'diagnostics':diag},A,rhs,C,d,lo,hi,x,state)['pass'])
        corrupted={k:v.copy() for k,v in state.items()};corrupted['y_box'][0]=0
        self.assertFalse(helper.kkt_report({'diagnostics':diag},A,rhs,C,d,lo,hi,x,corrupted)['pass'])

    def test_projection_repair_and_json(self):
        module=s.load('test_ev94_projection',s.PROJECTION)
        raw=np.array([1.0000001,1.],np.float32)
        r=module.project_order(raw,np.array([0.,0.],np.float32),np.array([2.,2.],np.float32),
                               np.array([[0,1]]),baseline=np.array([1.,1.],np.float32),fixed=np.array([False,False]))
        self.assertLessEqual(r['q'][0],r['q'][1])
        self.assertLessEqual(r['max_abs_correction'],r['a_priori_correction_bound'])
        json.dumps({k:v for k,v in r.items() if not isinstance(v,np.ndarray)},allow_nan=False)

    def test_fresh_only_and_bad_hash_never_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);pre=root/'preflight.json';pre.write_text('{}')
            out=root/'run'
            self.assertEqual(s.execute(pre,'0'*64,out),2)
            r=json.loads((out/'solve-result.json').read_text())
            self.assertEqual(r['status'],'STOP_ERROR_OR_RESOURCE_LIMIT')
            self.assertIsNone(r['candidate_path'])
            self.assertFalse((out/'candidate-local.npz').exists())
            with self.assertRaises(ValueError):s.execute(pre,'0'*64,out)


if __name__=='__main__': unittest.main()
