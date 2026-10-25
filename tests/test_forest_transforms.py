import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/vegetation'))
from review_visual_forest_support_v31 import transform_failures,outside_measured_domain

class ForestTransforms(unittest.TestCase):
    def test_uniform_rotation_and_mirror_shear_scale(self):
        A=np.array([np.eye(3),np.diag([-1,1,1]),np.eye(3),np.eye(3)*2])
        A[2,0,1]=.1;bad=transform_failures(A,np.tile([.8,1.2],(4,1)))
        self.assertFalse(any(v[0] for v in bad.values()))
        self.assertTrue(bad['determinant'][1]);self.assertTrue(bad['orthonormal_scale'][2]);self.assertTrue(bad['scale_range'][3])

    def test_nan_is_not_a_pass(self):
        A=np.eye(3)[None];A[0,0,0]=np.nan
        with self.assertRaises(ValueError):transform_failures(A,[[.8,1.2]])

    def test_boundary_coverage_includes_whole_support_disc(self):
        self.assertEqual(outside_measured_domain([[100,5,100],[12284,5,100],[12281,5,100]],[1,1,2]).tolist(),[False,True,True])
        with self.assertRaises(ValueError):outside_measured_domain([[100,5,100]],[float('nan')])

if __name__=='__main__':unittest.main()
