"""Independent constraints and finite differences for the support author."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/water'))
from continuous_stream_pilot_v31 import fair_energy,fair_support


class Support(unittest.TestCase):
    def test_energy_gradient_against_central_difference(self):
        h=np.random.default_rng(23).normal(size=(7,8));p=np.zeros_like(h);_,g=fair_energy(h,p)
        for r,c in ((0,0),(2,3),(6,7),(0,4)):
            a=h.copy();b=h.copy();a[r,c]+=1e-5;b[r,c]-=1e-5
            fd=(fair_energy(a,p)[0]-fair_energy(b,p)[0])/2e-5
            self.assertAlmostEqual(fd,g[r,c],places=6)

    def test_sloping_plane_preserved_and_fixed_boundary_exact(self):
        r,c=np.mgrid[:9,:10];h=5+.1*r+.2*c;free=np.ones_like(h,bool)
        actual,rep=fair_support(h,h,free,np.zeros_like(h),np.full_like(h,np.inf))
        np.testing.assert_allclose(actual,h,atol=1e-10);self.assertTrue(rep['success'])

    def test_spike_smoothed_with_low_cap_and_frozen_vertex(self):
        h=np.full((11,12),4.);h[5,5]=12.;free=np.ones_like(h,bool);free[3,3]=False
        upper=np.full_like(h,np.inf);upper[5,5]=3
        actual,rep=fair_support(h,np.full_like(h,4.),free,np.ones_like(h),upper)
        self.assertLessEqual(actual[5,5],3);self.assertEqual(actual[3,3],h[3,3])
        np.testing.assert_array_equal(actual[0],h[0]);self.assertLess(rep['energy_after'],rep['energy_before'])


if __name__=='__main__':unittest.main()
