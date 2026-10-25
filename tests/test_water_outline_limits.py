"""Regression checks for real shoreline failure modes, independent of ring displacement stats."""
from pathlib import Path
import sys
import unittest
import numpy as np
from shapely.geometry import Point, Polygon, box

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/water'))
from smooth_water_outlines_v30 import strict_smooth_feature


class WaterOutlineLimits(unittest.TestCase):
    def assert_outline(self, original, candidate):
        self.assertTrue(candidate.is_valid)
        self.assertLessEqual(abs(candidate.area/original.area-1),.02+1e-9)
        self.assertTrue(original.boundary.buffer(4,quad_segs=128).covers(candidate.boundary))
        self.assertTrue(candidate.boundary.buffer(4,quad_segs=128).covers(original.boundary))

    def test_smooths_wavy_shore_inside_final_envelope(self):
        a=np.linspace(0,2*np.pi,901)
        r=200+2*np.sin(40*a)
        original=Polygon(np.column_stack([r*np.cos(a),r*np.sin(a)]))
        candidate,_,_=strict_smooth_feature(original,18,4,None,2)
        self.assert_outline(original,candidate)
        self.assertFalse(original.equals(candidate))
        self.assertLess(candidate.length,original.length*.99)

    def test_keeps_sub_cell_islands(self):
        islands=[box(12,12,12.3,12.3),box(280,140,290,145)]
        original=Polygon(box(0,0,600,300).exterior.coords,[i.exterior.coords for i in islands])
        candidate,_,_=strict_smooth_feature(original,24,4,None,2)
        self.assert_outline(original,candidate)
        self.assertEqual(len(candidate.interiors),2)
        for island in islands:
            self.assertTrue(any(island.equals(Polygon(r)) for r in candidate.interiors))

    def test_two_touching_bodies_stay_connected(self):
        a=box(0,0,200,100);b=box(200,0,400,100)
        ca,_,_=strict_smooth_feature(a,18,4,b,2)
        cb,_,_=strict_smooth_feature(b,18,4,a,2)
        self.assert_outline(a,ca);self.assert_outline(b,cb)
        self.assertEqual(ca.distance(cb),0)
        self.assertTrue(ca.intersection(cb).covers(a.intersection(b)))

    def test_island_and_shift_checks_reject_bad_results(self):
        original=Point(0,0).buffer(40).difference(Point(0,0).buffer(2))
        filled=Polygon(original.exterior)
        self.assertNotEqual(len(original.interiors),len(filled.interiors))
        self.assertFalse(original.boundary.buffer(4).covers(Point(0,0).buffer(46).boundary))


if __name__=='__main__':unittest.main()
