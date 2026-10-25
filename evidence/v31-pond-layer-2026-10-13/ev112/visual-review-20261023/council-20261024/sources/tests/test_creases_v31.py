"""Analytic consumers for the native-mesh edge census (not fixture snapshots)."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools/terrain'))
import census_creases_v31 as c


class Creases(unittest.TestCase):
    def test_sloping_plane_has_no_creases(self):
        r,col=np.mgrid[:9,:11]
        H=3.2*col*6 - .8*r*6 + 9
        for value in c.angles(H).values(): self.assertLess(value.max(), 2e-6)

    def test_cross_cell_ridge_is_not_missed_by_diagonal_only(self):
        r,col=np.mgrid[:7,:9]
        H=np.abs(col-4)*6.
        a=c.angles(H)
        self.assertLess(a['diagonal'].max(), 2e-6)
        self.assertAlmostEqual(a['east'].max(),90.,places=8)
        self.assertLess(a['south'].max(),2e-6)

    def test_face_normals_match_independent_cross_products(self):
        H=np.array([[1.,5.,2.],[4.,9.,3.],[3.,1.,7.]])
        A,B=c.normals(H)
        points=np.array([[0,1,6],[6,5,6],[6,9,0],[0,4,0]],float)
        for tri,expected in (([0,1,2],A[0,0]),([0,2,3],B[0,0])):
            v=points[tri];n=np.cross(v[1]-v[0],v[2]-v[0]);n/=np.linalg.norm(n)
            np.testing.assert_allclose(n,expected,atol=1e-14)

    def test_pond_corner_excludes_only_incident_triangles(self):
        H=np.full((3,3),5.)
        plane=np.full((2,2),np.nan);field=np.full((2,2,4),np.nan)
        plane[0,0]=4.;field[0,0]=[4,6,4,4]
        A,B=c.tri_dry(H,plane,field)
        self.assertFalse(A[0,0]);self.assertTrue(B[0,0])
        self.assertEqual(A.sum(),3);self.assertEqual(B.sum(),4)


if __name__=='__main__':unittest.main()
