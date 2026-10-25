import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/water'))
from audit_stream_visibility_ev112 import visibility,route_metrics,wet_span
from stream_reference_v31 import require_original_endpoints

class Streams(unittest.TestCase):
    def test_occluded_and_missing_water_fail(self):
        self.assertTrue(visibility(0,.3,1))
        self.assertFalse(visibility(.8,.3,1));self.assertFalse(visibility(0,.8,1));self.assertFalse(visibility(0,.3,None))

    def test_straight_and_square_route_are_distinguished(self):
        self.assertEqual(route_metrics([[0,0],[1,0],[2,0]])['turn_max_deg'],0)
        self.assertEqual(route_metrics([[0,0],[1,0],[1,1]])['turn_max_deg'],90)

    def test_original_ends_do_not_require_dry_aprons_to_be_water(self):
        mask,span=wet_span([[0,0],[1,0],[2,0],[3,0]],[[.5,0],[2.5,0]])
        self.assertEqual(mask.tolist(),[False,True,True,False]);self.assertEqual(span,[.5,2.5])
        require_original_endpoints([[0,0],[3,0]],[[0,0],[3,0]])
        with self.assertRaises(ValueError):require_original_endpoints([[1,0],[2,0]],[[0,0],[3,0]])

if __name__=='__main__':unittest.main()
