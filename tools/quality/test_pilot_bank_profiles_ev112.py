import importlib.util,unittest
from pathlib import Path
import numpy as np
s=importlib.util.spec_from_file_location('p',Path(__file__).with_name('pilot_bank_profiles_ev112.py'));g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
class Profiles(unittest.TestCase):
    def fixture(self,height=1):
        return np.array([[1.,height,6.],[6.,height,6.],[11.,height,6.]]),np.array([[4.,0.,6.],[8.,0.,6.]])
    def test_flat_exposed(self):
        row,w=self.fixture();v=g.row_profile(row,w,np.zeros((3,3)))['metrics']
        self.assertEqual(v['left_dry_above_H_length'],5);self.assertEqual(v['right_outer_reach'],3);self.assertEqual(v['max_B_section_W'],1)
    def test_flat_hidden(self):
        row,w=self.fixture(-1);v=g.row_profile(row,w,np.zeros((3,3)))['metrics'];self.assertEqual(v['left_above_H_length'],0)
    def test_interior_native_valley_not_endpoints(self):
        h=np.ones((3,3))*2;h[1,1]=0
        row=np.array([[0.,1,6],[3.,1,6],[12.,1,6]]);w=np.array([[2.,0,6],[4.,0,6]])
        v=g.row_profile(row,w,h)['metrics'];self.assertAlmostEqual(v['right_above_H_length'],6);self.assertEqual(v['max_B_H'],1)
    def test_native_diagonal(self):
        h=np.array([[0.,0],[0.,12.]])
        self.assertEqual(float(g.native(h,[3.,4.])),4)
        self.assertEqual(float(g.native(h,[2.,3.])),4)
        np.testing.assert_array_equal(g.cuts([0,6],[6,6],6),[0,1])
        np.testing.assert_array_equal(g.cuts([0,3],[6,3],6),[0,.5,1])
    def test_real_water_not_level(self):
        row,w=self.fixture(.01);w[:,1]=.02;v=g.row_profile(row,w,np.zeros((3,3)))['metrics']
        self.assertEqual(v['left_dry_above_H_length'],0);self.assertEqual(v['left_above_H_length'],5)
    def test_cap_reference_extrapolated(self):
        row,w=self.fixture();row[:,2]=9
        v=g.row_profile(row,w,np.zeros((3,3)),extrapolated=True)['metrics'];self.assertEqual(v['left_outer_reach'],3)
    def test_actual_water_midpoint_offset(self):
        row,w=self.fixture();w[:,0]+=.5
        p=g.row_profile(row,w,np.zeros((3,3)));self.assertEqual(p['metrics']['left_outer_reach'],3.5);self.assertEqual(p['metrics']['right_outer_reach'],2.5)
        self.assertEqual(p['water_midpoint_minus_bed_centre'],[.5,0.])
        e=g.row_profile(row,w,np.zeros((3,3)),extrapolated=True);self.assertEqual(e['metrics']['left_outer_reach'],3)
    def test_nonfinite_native_rejected(self):
        row,w=self.fixture();h=np.zeros((3,3));h[1,1]=np.nan
        with self.assertRaisesRegex(ValueError,'nonfinite'):g.row_profile(row,w,h)
    def test_zero_and_inverted(self):
        row,w=self.fixture();row[1]=row[0]
        with self.assertRaisesRegex(ValueError,'inverted'):g.row_profile(row,w,np.zeros((3,3)))
        row,w=self.fixture()
        with self.assertRaisesRegex(ValueError,'inverted'):g.row_profile(row[::-1],w,np.zeros((3,3)))
    def test_tiny_positive_interval(self):
        r=g.positive_interval(-1,1e-12);self.assertGreater(r[1]-r[0],0)
        self.assertIsNone(g.positive_interval(0,0))
    def test_shared_rows(self):
        target=np.zeros((3,2,3));seen=np.zeros(3,bool);a=np.ones((2,2,3))
        g.attach_grid(target,seen,0,a);g.attach_grid(target,seen,1,a);self.assertTrue(seen.all())
        with self.assertRaisesRegex(ValueError,'discordant'):g.attach_grid(target,seen,1,a*2)
    def test_candidate_mutants(self):
        source=dict(bed=np.zeros((2,39,3)),water=np.zeros((2,2,3)))
        g.candidate_guard(source,source,'kit-7')
        for k,ix in [('water',(0,0,1)),('bed',(0,0,0))]:
            candidate={k:v.copy() for k,v in source.items()};candidate[k][ix]=1
            with self.assertRaisesRegex(ValueError,'changed'):g.candidate_guard(source,candidate,'kit-7')
        with self.assertRaisesRegex(ValueError,'wrong_site'):g.candidate_guard(source,source,'kit-118')
    def test_face_classes(self):
        np.testing.assert_array_equal(g.face_classes([1,1,1,0,0,0],[[0,1,2],[1,2,3],[3,4,5]]),[0,1,2])
    def test_dry_mask_and_inner_domain(self):
        qs=np.unique(np.r_[np.arange(-18,19,dtype=float),-2.25,2.25]);bed=np.zeros((3,39,3));bed[:,:,1]=1
        touch=np.zeros((3,39),bool);touch[1,30]=True
        ex,reasons,floor=g.dry_contract(bed,np.zeros(3),np.array([0.,10.,20.]),np.zeros((3,39)),touch,np.zeros(3,bool))
        q3=int(np.flatnonzero(qs==3)[0]);self.assertFalse(ex[1,q3]);self.assertTrue(ex[1,30]);self.assertTrue(ex[0].all())
        self.assertTrue(abs(qs[q3])<=4) # Original v31 fixed domain differs from dry-pilot free domain.
    def test_floor_and_quantization(self):
        bed=np.zeros((3,39,3));bed[:,:,1]=.026;touch=np.zeros((3,39),bool)
        ex,reasons,floor=g.dry_contract(bed,np.zeros(3),np.array([0.,10.,20.]),np.full((3,39),.0059),touch,np.zeros(3,bool))
        self.assertTrue(reasons['no_quantized_value'][1].all());self.assertFalse(reasons['floor_above_original'][1].any())
    def test_water_mismatch(self):
        row,w=self.fixture();w[0,1]=1
        with self.assertRaisesRegex(ValueError,'water_row'):g.row_profile(row,w,np.zeros((3,3)))
if __name__=='__main__':unittest.main()
