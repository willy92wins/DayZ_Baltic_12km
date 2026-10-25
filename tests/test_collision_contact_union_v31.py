import sys,unittest
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.strtree import STRtree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/water'))
from collision_contact_union_v31 import clip_linear_minimum,lower_coverage,coverage_certificate
from review_compact_collision_v31 import height


def contact_coverage(source,roof,minimum=-.02):
    a=np.array([Polygon(t[:,[0,2]]) for t in source]);b=np.array([Polygon(t[:,[0,2]]) for t in roof])
    bi,ai=STRtree(a).query(b,predicate='intersects');intersections=shapely.intersection(b[bi],a[ai]);regions=[[] for _ in a]
    lower_coverage(a,roof,source,bi,ai,intersections,height,minimum,regions)
    return coverage_certificate(a,regions)


class CollisionContactUnion(unittest.TestCase):
    def setUp(self):
        self.points=np.array([[0,0,0],[2,0,0],[2,0,2],[0,0,2]],float)
        self.source=self.points[[[0,1,2],[0,2,3]]]

    def test_buried_internal_roof_does_not_remove_upper_contact(self):
        roof=np.concatenate((self.source,self.source-[0,1,0]))
        self.assertTrue(contact_coverage(self.source,roof)['covered'])
        self.assertFalse(contact_coverage(self.source,roof[2:])['covered'])

    def test_two_planes_cover_each_others_low_halves(self):
        left=self.source.copy();right=self.source.copy()
        left[:,:,1]=left[:,:,0]-1-.02;right[:,:,1]=1-right[:,:,0]-.02
        self.assertTrue(contact_coverage(self.source,np.concatenate((left,right)))['covered'])
        self.assertFalse(contact_coverage(self.source,left)['covered'])

    def test_narrow_gap_between_roofs_is_not_missed(self):
        left=self.source.copy();right=self.source.copy()
        left[:,:,1]=left[:,:,0]-1-.02;right[:,:,1]=.999-right[:,:,0]-.02
        result=contact_coverage(self.source,np.concatenate((left,right)))
        self.assertFalse(result['covered']);self.assertGreater(result['uncovered_area_m2'],.0019)

    def test_clipping_and_winding(self):
        p=self.points[:,[0,2]]
        for coords,values in ((p,[-1,1,1,-1]),(p[::-1],[-1,1,1,-1][::-1])):
            polygon=clip_linear_minimum(Polygon(coords),values,0)
            self.assertAlmostEqual(polygon.area,2)

    def test_missing_source_coverage_cannot_pass(self):
        for a,b in (([],[]),([Polygon(self.points[:,[0,2]])],[])):
            with self.assertRaises(ValueError):coverage_certificate(a,b)


if __name__=='__main__':unittest.main()
