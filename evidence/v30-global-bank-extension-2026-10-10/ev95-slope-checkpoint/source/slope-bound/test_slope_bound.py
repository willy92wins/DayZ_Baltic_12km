import importlib.util, pathlib, unittest, math
import numpy as np

p = pathlib.Path(__file__).with_name('prepare_slope_bound.py')
s = importlib.util.spec_from_file_location('scalar_bound_tested',p)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)

class ScalarBound(unittest.TestCase):
    def test_whole_interval_against_independent_triangle_normal(self):
        nw,ne,se,hi = 7.2344970703125,3.1139774322509766,2.2943551540374756,2.7943551540374756
        lower,proof = m.scalar_interval(nw,ne,se,1.8000000715255737,hi)
        def angle(h):
            normal = np.cross([6.,ne-nw,0.],[6.,h-nw,-6.])
            return math.degrees(math.atan2(math.hypot(normal[0],normal[2]),abs(normal[1])))
        cap = angle(se)
        self.assertEqual(lower,se)
        for h in np.linspace(lower,hi,101):
            self.assertLessEqual(angle(h),cap+1e-12)
        self.assertGreater(angle(2.2569596767425537),cap+1e-4)
        self.assertFalse(proof['angular_tolerance_consumed'])

    def test_invalid_support_and_intervals(self):
        cases = [(7.,3.,2.,1.,2.5,(False,True)),
                 (7.,3.,2.,1.,3.5,(True,True)),
                 (7.,3.,2.,2.1,2.5,(True,True)),
                 (7.,3.,float('nan'),1.,2.5,(True,True)),
                 (7.,3.,2.,1.,1.5,(True,True))]
        for args in cases:
            with self.subTest(args=args),self.assertRaises(ValueError):
                m.scalar_interval(*args)

if __name__ == '__main__': unittest.main()
