from pathlib import Path
import sys,unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/terrain'))
from audit_road_mesh_edges_ev112 import segment_breaks,native,native_slopes

class MeshEdges(unittest.TestCase):
    def test_breaks_include_grid_and_diagonal(self):
        t,q=segment_breaks([1.,12281.],[11.,12271.])
        self.assertTrue(np.all(np.diff(t)>0));self.assertEqual(t[0],0.);self.assertEqual(t[-1],1.)
        self.assertTrue(any(np.allclose(p,[6,12276]) for p in q))
        _,diagonal=segment_breaks([1.,12281.],[11.,12281.])
        self.assertTrue(any(np.allclose(p,[7,12281]) for p in diagonal))

    def test_native_diagonal_saddle_distinguishes_opposite_split(self):
        H=np.array([[0.,1.],[1.,0.]])
        self.assertEqual(float(native(H,np.array([[3.,12279.]]))[0]),0.)

    def test_plane_exact_at_all_crossings(self):
        r,c=np.mgrid[:10,:10];H=2+(.03*c*6)+.02*(12282-r*6)
        t,q=segment_breaks([1.,12281.],[43.,12242.])
        np.testing.assert_allclose(native(H,q),2+.03*q[:,0]+.02*q[:,1],atol=1e-12)

    def test_between_samples_ridge_is_detected(self):
        r,c=np.mgrid[:10,:10];H=.5-abs(c*6-6)*.1
        # A narrow peak at x=6 lies between the half-metre samples at5.8/6.3.
        a=np.array([5.3,12275.]);b=np.array([6.8,12275.])
        _,q=segment_breaks(a,b)
        samples=a+np.arange(0,1.51,.5)[:,None]*[1.,0.]
        self.assertAlmostEqual(native(H,q).max(),.5)
        self.assertLess(native(H,samples).max(),.5)

    def test_derivative_is_stable_at_near_zero_edge_interval(self):
        r,c=np.mgrid[:10,:10];H=90+.03*c*6+.02*(12282-r*6)
        a=np.array([6-1e-12,12276-1e-12]);b=np.array([19.,12258.])
        _,q=segment_breaks(a,b);want=abs(np.dot([.03,.02],b-a)/np.linalg.norm(b-a))
        np.testing.assert_allclose(native_slopes(H,q),want,atol=1e-12)
        _,reverse=segment_breaks(b,a)
        np.testing.assert_allclose(native_slopes(H,reverse),want,atol=1e-12)

if __name__=='__main__':unittest.main()
