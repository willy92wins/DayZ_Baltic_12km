"""Analytical geometry controls; no runtime acceptance."""
from pathlib import Path
import sys
import unittest
from shapely.geometry import LineString

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/navigation'))
from prepare_full_river_consumer import shortest_trace


class TraceTests(unittest.TestCase):
    def test_retraced_branch_removed_using_existing_edges(self):
        source=LineString([(0,0),(1,0),(1,2),(1,0),(3,0)])
        actual=shortest_trace([source],(0,0),(3,0))
        self.assertEqual(list(actual.coords),[(0.,0.),(1.,0.),(3.,0.)])
        self.assertEqual(actual.length,3.)
        self.assertEqual(actual.difference(source).length,0.)

    def test_interior_intersection_is_a_connection(self):
        a=LineString([(0,0),(4,0)])
        b=LineString([(2,-2),(2,2)])
        actual=shortest_trace([a,b],(0,0),(2,2))
        self.assertEqual(list(actual.coords),[(0.,0.),(2.,0.),(2.,2.)])
        self.assertEqual(actual.length,4.)

    def test_disconnected_sources_rejected(self):
        with self.assertRaisesRegex(ValueError,'Disconnected'):
            shortest_trace([LineString([(0,0),(1,0)]),LineString([(2,0),(3,0)])],(0,0),(3,0))


if __name__=='__main__':unittest.main()
