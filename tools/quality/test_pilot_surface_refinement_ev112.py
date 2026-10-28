import importlib.util,unittest
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('r',Path(__file__).with_name('pilot_surface_refinement_ev112.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class Refine(unittest.TestCase):
    def args(self,h=1.):
        return np.full((3,3),h),np.full((2,2),np.nan),np.full((2,2,4),np.nan)
    def tri(self,y=0.):return np.array([[0,y,0],[12,y,0],[0,y,12]],float)
    def test_covered_plane(self):
        parts=r.refine(self.tri(),*self.args())
        self.assertAlmostEqual(sum(p['area'] for p in parts),72.)
        self.assertEqual(max(r.sign_regions(p,'terrain')['maximum'] for p in parts),-1.)
    def test_protrusion_between_original_vertices(self):
        h,p,f=self.args();h[1,1]=-1.
        parts=r.refine(self.tri(),h,p,f)
        # Original bed vertices are all below H=1; common-refinement finds H=-1.
        self.assertEqual(max(r.sign_regions(z,'terrain')['maximum'] for z in parts),1.)
        self.assertGreater(sum(r.sign_regions(z,'terrain')['above_area'] for z in parts),0.)
    def test_contact_plane_not_double_counted(self):
        parts=r.refine(self.tri(),*self.args(0))
        regions=[r.sign_regions(p,'terrain') for p in parts]
        self.assertEqual(sum(z['above_area']+z['below_area'] for z in regions),0.)
        self.assertAlmostEqual(sum(z['contact_area'] for z in regions),72.)
    def test_water_sea_and_pond_separate(self):
        h,p,f=self.args();p[1,0]=2;f[1,0]=2
        parts=r.refine(self.tri(1),h,p,f)
        self.assertEqual({z['water_kind'] for z in parts},{'SEA','POND'})
        self.assertGreater(sum(r.sign_regions(z,'water')['below_area'] for z in parts),0.)
        self.assertGreater(sum(r.sign_regions(z,'water')['above_area'] for z in parts),0.)
    def test_sign_area_partition(self):
        tri=self.tri();tri[1,1]=2
        regions=[r.sign_regions(p,'terrain') for p in r.refine(tri,*self.args())]
        self.assertAlmostEqual(sum(z['above_area']+z['below_area']+z['contact_area'] for z in regions),72.)
        self.assertAlmostEqual(sum(z['above_area'] for z in regions),18.)
    def test_reverse_winding(self):
        self.assertAlmostEqual(sum(p['area'] for p in r.refine(self.tri()[::-1],*self.args())),72.)
    def test_near_degenerate_inconclusive(self):
        with self.assertRaisesRegex(ValueError,'NEAR_DEGENERATE'):
            r.plane(np.array([[0.,0],[1,0],[1,1e-14]]),np.array([0.,0,1]))
    def test_outside_domain(self):
        t=self.tri();t[0,0]=-1
        with self.assertRaisesRegex(ValueError,'outside_native'):r.refine(t,*self.args())
    def test_wet_dry_linear_split(self):
        p=np.array([[0.,0],[4,0],[4,4],[0,4]])
        self.assertEqual(r.area(r.clip(p,p[:,0]-1)),12)
        self.assertEqual(r.area(r.clip(p,p[:,0]-1,False)),4)
    def test_close_vertices_not_welded(self):
        p=np.array([[0.,0],[1,0],[1,1e-8],[0,1e-8]])
        self.assertEqual(len(r.clip(p,np.ones(4))),4)
    def test_duplicate_boundary_vertices(self):
        p=np.array([[0.,0],[1,0],[0,1]])
        self.assertEqual(len(r.clip(p,p[:,0])),3)
    def test_layer_values_retained(self):
        p1=r.refine(self.tri(0.),*self.args())
        p2=r.refine(self.tri(2.),*self.args())
        self.assertEqual(max(r.sign_regions(p,'terrain')['maximum'] for p in p1),-1)
        self.assertEqual(max(r.sign_regions(p,'terrain')['maximum'] for p in p2),1)
if __name__=='__main__':unittest.main()
