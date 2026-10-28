import importlib.util,unittest
from pathlib import Path
import numpy as np
s=importlib.util.spec_from_file_location('solver',Path(__file__).with_name('dry_bed_road_solver_ev112.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)

class SolverTests(unittest.TestCase):
    def setUp(self):
        self.p=np.array([[0.,1.,0.],[1.,1.,0.],[0.,1.,1.]]);self.t=np.array([[0,1,2]])
    def test_plane_burial(self):
        out,r=g.solve(self.p,self.t,np.ones(3,bool),[0]*3,np.eye(3),np.ones(3))
        self.assertEqual(r['status'],'NUMERIC_CANDIDATE_PENDING_CONSUMER');self.assertTrue((out[:,1]<=-.03).all());self.assertTrue(np.array_equal(out[:,[0,2]],self.p[:,[0,2]]))
    def test_fixed_wet_support_is_infeasible(self):
        out,r=g.solve(self.p,self.t,np.zeros(3,bool),[0],[[1,0,0]],[1])
        self.assertIsNone(out);self.assertEqual(r['status'],'INFEASIBLE_FIXED_SUPPORT')
    def test_native_valley_between_vertices(self):
        out,r=g.solve(self.p,self.t,np.ones(3,bool),[0]*4,np.r_[np.eye(3),[[.5,.5,0]]],[0,0,0,1])
        self.assertLessEqual((out[0,1]+out[1,1])/2,0)
    def test_outer_chord_fixed_failure_and_dry_repair(self):
        weights=[[.3930197268583471,.606980273141653,0]]
        out,r=g.solve(self.p,self.t,[False,False,True],[0],weights,[.044270951063846375])
        self.assertIsNone(out);self.assertEqual(r['status'],'INFEASIBLE_FIXED_SUPPORT')
        out,r=g.solve(self.p,self.t,[True,True,True],[0],weights,[.044270951063846375])
        self.assertLessEqual(.044270951063846375-np.dot(weights[0],self.p[:,1]-out[:,1]),0)
    def test_fixed_dry_vertex_exact(self):
        p=self.p.copy();p[0,1]=-1
        out,r=g.solve(p,self.t,[False,True,True],[0]*3,np.eye(3),[-1,1,1]);self.assertTrue(np.array_equal(out[0],p[0]))
    def test_joint_is_single_vertex(self):
        p=np.r_[self.p,[[1.,1.,1.]]];t=np.array([[0,1,2],[1,3,2]])
        out,r=g.solve(p,t,[1,1,1,1],[0,1],[[0,.5,.5],[.5,0,.5]],[1,1])
        self.assertLessEqual((out[1,1]+out[2,1])/2,0);self.assertEqual(len(out),4)
    def test_domain_radius(self):
        free,dist=g.local_domain(self.p,self.t,[True],12);self.assertTrue(free.all());self.assertTrue((dist==0).all())
    def test_empty_seed_rejected(self):
        with self.assertRaisesRegex(ValueError,'empty_seed'):g.local_domain(self.p,self.t,[False])
    def test_nonfinite_rejected(self):
        with self.assertRaisesRegex(ValueError,'nonfinite'):g.solve(self.p,self.t,[1,1,1],[0],[[1,0,0]],[float('nan')])
    def test_near_fixed_does_not_bury_millions(self):
        for weight in (1e-8,1e-10):
            out,r=g.solve(self.p,self.t,[False,True,True],[0],[[1-weight,weight,0]],[.1])
            self.assertIsNone(out);self.assertEqual(r['status'],'INFEASIBLE_DESCENT_ENVELOPE')
    def test_unchanged_offgrid_points_not_quantized(self):
        p=self.p.copy();p[:,1]=1.001
        out,r=g.solve(p,self.t,[True]*3,[0]*3,np.eye(3),[-1]*3)
        self.assertTrue(np.array_equal(out,p));self.assertEqual(r['changed_vertices'],0)
    def test_negative_weights_rejected(self):
        with self.assertRaisesRegex(ValueError,'weights'):g.solve(self.p,self.t,[1,1,1],[0],[[-.1,.5,.6]],[1])
    def test_barycentric_interior(self):
        np.testing.assert_allclose(g.barycentric(self.p,[[.25,.25]]),[[.5,.25,.25]])
    def test_barycentric_outside_rejected(self):
        with self.assertRaisesRegex(ValueError,'outside_triangle'):g.barycentric(self.p,[[2,2]])

if __name__=='__main__':unittest.main()
