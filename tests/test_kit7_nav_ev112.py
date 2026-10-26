"""Independent planar fixtures for the packed-roadway route consumer."""
from pathlib import Path
import sys,unittest
from shapely.geometry import box,LineString,GeometryCollection
from shapely.affinity import translate
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/navigation'))
from verify_kit7_nav_ev112 import check_route

class PackedRouteTests(unittest.TestCase):
    def setUp(self):
        self.dry={'a':box(0,2,5,8),'b':box(5,2,10,8)}
        self.water=box(0,-1,10,1)
        self.query=dict(kind='seam',required_models=['a','b'],allowed_models=['a','b'])
        self.corridor=LineString([(1,4),(9,4)]).buffer(2.1)
        self.empty=GeometryCollection()

    def run_route(self,points,dry=None,query=None,exterior=None):
        return check_route(query or self.query,points,self.corridor,self.empty if exterior is None else exterior,self.dry if dry is None else dry,self.water)

    def test_two_pieces_continuous_positive(self):
        self.assertEqual(self.run_route([[1,0,4],[9,0,4]])['status'],'PASS')

    def test_seam_gap_rejected(self):
        self.assertFalse(self.run_route([[1,0,4],[9,0,4]],{'a':self.dry['a'],'b':box(5.03,2,10,8)})['checks']['dry_continuous'])

    def test_terrain_detour_rejected(self):
        self.assertEqual(self.run_route([[1,0,4],[4,0,12],[9,0,4]])['status'],'FAIL')

    def test_water_crossing_between_waypoints_rejected(self):
        result=self.run_route([[1,0,4],[5,0,-2],[9,0,4]])
        self.assertFalse(result['checks']['no_water'])

    def test_opposite_bank_rejected(self):
        self.assertFalse(self.run_route([[1,0,-4],[9,0,-4]])['checks']['corridor_bound'])

    def test_piece_graze_rejected(self):
        self.assertFalse(self.run_route([[4.8,0,4],[9,0,4]])['checks']['required_models'])

    def test_seam_one_side_rejected(self):
        self.assertFalse(self.run_route([[1,0,4],[4,0,4]])['checks']['required_models'])

    def test_wrong_pose_rejected(self):
        self.assertEqual(self.run_route([[1,0,4],[9,0,4]],{k:translate(v,xoff=20) for k,v in self.dry.items()})['status'],'FAIL')

    def test_partial_and_nonfinite_rejected(self):
        for points in ([[1,0,4]],[[1,float('nan'),4],[9,0,4]]):
            self.assertEqual(self.run_route(points)['status'],'FAIL')

    def test_declared_cap_exterior_positive(self):
        query=dict(kind='cap_to_land',required_models=['a'],allowed_models=['a'])
        line=LineString([(-2,4),(2,4)]);corridor=line.buffer(2.1)
        result=check_route(query,[[-2,0,4],[2,0,4]],corridor,corridor.difference(self.dry['a']),self.dry,self.water)
        self.assertEqual(result['status'],'PASS')

    def test_cap_without_exterior_traversal_rejected(self):
        query=dict(kind='cap_to_land',required_models=['a'],allowed_models=['a'])
        self.assertFalse(self.run_route([[1,0,4],[4,0,4]],query=query)['checks']['exterior_transition'])

if __name__=='__main__':unittest.main()
