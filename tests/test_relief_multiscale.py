import unittest,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/terrain'))
from audit_relief_multiscale_ev112 import scale_fields

class Relief(unittest.TestCase):
    def test_planar_ramp_is_not_curvature(self):
        r,c=np.mgrid[:40,:40];H=5+.31*r-.22*c
        for lag in (1,2,4,8):
            self.assertLess(scale_fields(H,lag)['chord_residual_m'].max(),1e-12)

    def test_broad_ridge_and_terrace_not_strict_peaks(self):
        r,c=np.mgrid[:40,:40];H=np.minimum(.08*c,1.6)
        fields=scale_fields(H,4)
        self.assertAlmostEqual(fields['chord_residual_m'].max(),.16)
        self.assertEqual(fields['ring_peak_m'].max(),0)

    def test_spike_and_pit_and_nan(self):
        H=np.zeros((21,21));H[10,10]=.35
        self.assertEqual(scale_fields(H,1)['ring_peak_m'].max(),.35)
        self.assertEqual(scale_fields(-H,1)['ring_pit_m'].max(),.35)
        H[0,0]=np.nan
        with self.assertRaises(ValueError):scale_fields(H,1)

if __name__=='__main__':unittest.main()
