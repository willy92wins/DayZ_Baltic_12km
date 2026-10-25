import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/terrain'))
from repair_guarded_shapes_ev112 import crown_bounds


class GuardedReliefCaps(unittest.TestCase):
    def test_overlapping_peak_and_pit_keep_existing_neighbour_between_caps(self):
        h=np.full((9,11),2.);h[4,3]=3.;h[4,7]=1.
        lo,hi=crown_bounds(h,[(4,3,3.)],[(4,7,1.)])
        self.assertEqual(hi[4,5],3.);self.assertEqual(lo[4,5],1.)
        self.assertTrue((lo<=h).all());self.assertTrue((h<=hi).all())
        # Together with a required terrain floor, contradictory bounds reject.
        imposed_floor=lo.copy();imposed_floor[4,5]=3.1
        self.assertTrue((imposed_floor>hi).any())

    def test_nearby_non_target_extremum_prevents_a_new_crown(self):
        h=np.full((11,11),2.)
        lo,hi=crown_bounds(h,[(5,3,3.),(5,7,2.4)],[])
        self.assertEqual(hi[5,5],2.4)
        self.assertGreater(2.5,hi[5,5])
        self.assertTrue(np.isposinf(hi[0,0]))

    def test_existing_higher_or_lower_neighbours_are_preserved(self):
        h=np.full((9,9),2.);h[4,3]=4.;h[4,5]=0.
        lo,hi=crown_bounds(h,[(4,4,3.)],[(4,4,1.)])
        self.assertEqual(hi[4,3],4.);self.assertEqual(lo[4,5],0.)
        self.assertTrue((lo<=h).all());self.assertTrue((h<=hi).all())


if __name__=='__main__':unittest.main()
