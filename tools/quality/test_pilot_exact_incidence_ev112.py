import importlib.util,unittest,numpy as np
from pathlib import Path
s=importlib.util.spec_from_file_location('i',Path(__file__).with_name('pilot_exact_incidence_ev112.py'))
i=importlib.util.module_from_spec(s);s.loader.exec_module(i)
class Exact(unittest.TestCase):
    def test_real_regression_shared_edge(self):
        a=np.array([[5189.29296875,5885.814453125],[5190.140625,5886.298828125],[5189.666015625,5885.1640625]])
        b=np.array([[5189.29296875,5885.814453125],[5187.923828125,5890.21484375],[5190.140625,5886.298828125]])
        self.assertFalse(i.positive_pair(a,b));self.assertEqual(i.rational_polygon((a,b)),[])
    def test_point_contact(self):
        a=np.array([[0.,0],[1,0],[0,1]]);b=np.array([[1.,0],[2,0],[1,1]])
        self.assertFalse(i.positive_pair(a,b))
    def test_positive_overlap(self):
        a=np.array([[0.,0],[1,0],[0,1]]);self.assertTrue(i.positive_pair(a,a))
    def test_tiny_positive_sliver_not_discarded(self):
        a=np.array([[0.,0],[1,0],[0,1]]);b=np.array([[1-1e-12,0],[2,0],[1-1e-12,1]])
        self.assertTrue(i.positive_pair(a,b))
        p,used,positive=i.guarded_intersection(a,a,b,np.empty((0,2)),0)
        self.assertTrue(used and positive);self.assertGreater(len(p),2)
    def test_native_part_contact_only(self):
        a=np.array([[0.,0],[2,0],[0,2]]);n=np.array([[0.,0],[1,0],[0,1]]);w=np.array([[1.,0],[2,0],[1,1]])
        self.assertTrue(i.positive_pair(a,w));self.assertEqual(i.rational_polygon((a,n,w)),[])
    def test_orientation_invariant(self):
        a=np.array([[0.,0],[2,0],[0,2]]);b=a*.5
        self.assertTrue(i.positive_pair(a[::-1],b));self.assertTrue(i.rational_polygon((a[::-1],b[::-1])))
    def test_large_coordinate_translation(self):
        a=np.array([[0.,0],[1,0],[0,1]])+10000;self.assertTrue(i.positive_pair(a,a))
    def test_spurious_positive_float_cut_removed_by_exact_not_threshold(self):
        a=np.array([[0.,0],[2,0],[0,2]])+10000
        n=np.array([[0.,0],[1,0],[0,1]])+10000
        w=np.array([[1.,0],[2,0],[1,1]])+10000
        fake=np.array([[10001.,10000],[10001.00000000001,10000],[10001,10000.00000000001]])
        p,used,positive=i.guarded_intersection(a,n,w,fake,1e-12)
        self.assertTrue(used);self.assertFalse(positive);self.assertEqual(len(p),0)
    def test_exact_positive_survives_float_collapse(self):
        a=np.array([[10000.,10000],[10001,10000],[10000,10001]])
        w=np.array([[10001.,10000+np.spacing(10000.)],[10001,9999],[10000,9900]])
        p,used,positive=i.guarded_intersection(a,a,w,np.empty((0,2)),0)
        self.assertTrue(used and positive)
        self.assertEqual(len(np.unique(p,axis=0)),1)
    def test_degenerate_seed_consistent(self):
        a=np.array([[0.,0],[1,0],[2,0]]);b=np.array([[0.,0],[1,0],[0,1]])
        with self.assertRaisesRegex(ValueError,'degenerate'):i.positive_pair(a,b)
        with self.assertRaisesRegex(ValueError,'degenerate'):i.rational_polygon((a,b))
if __name__=='__main__':unittest.main()
