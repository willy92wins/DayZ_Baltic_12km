from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/water'))
from eval_visual_road_probe_ev112 import sections


class RoadEvidence(unittest.TestCase):
    def fixture(self):
        doc={'road_sections':[dict(station_m=100+j,ids=list(range(j*17,(j+1)*17))) for j in range(11)]}
        rows={i:dict(ground=10+(.027 if i%17==0 else 0)) for i in range(187)}
        return doc,rows

    def test_measured_crossfall(self):
        d,r=self.fixture();self.assertEqual(sections(d,r)['status'],'PASS')
        # Each individual point is within 1 cm of its reference, but the
        # measured range violates 3 cm. The additional consumer must fail.
        r[0]['ground']+=.009;r[1]['ground']-=.009
        self.assertEqual(sections(d,r)['status'],'FAIL')

    def test_missing_and_duplicate(self):
        d,r=self.fixture();d['road_sections'][0]['ids'][-1]=0
        with self.assertRaises(AssertionError):sections(d,r)
        d,r=self.fixture();r.pop(7)
        with self.assertRaises(KeyError):sections(d,r)


if __name__=='__main__':unittest.main()
