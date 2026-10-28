import importlib.util,unittest,math
from pathlib import Path
import numpy as np
from shapely import STRtree,Point
spec=importlib.util.spec_from_file_location('e',Path(__file__).with_name('pilot_visible_exposure_ev112.py'))
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
class Corridor(unittest.TestCase):
    def test_rectangle_area(self):self.assertAlmostEqual(e.rect(np.array([0,0]),np.array([10,0])).area,80)
    def test_disc_bounds(self):
        inner,outer=e.disc_bounds(np.zeros(2))
        self.assertLess(inner.area,math.pi*16);self.assertGreater(outer.area,math.pi*16)
        angle=math.pi/64
        p=Point(4*np.cos(angle),4*np.sin(angle))
        self.assertFalse(inner.covers(p));self.assertTrue(outer.buffer(1e-12).covers(p))
    def face(self,water=None,road_z=6):
        h=np.zeros((3,3));wp=np.full((2,2),np.nan);wf=np.full((2,2,4),np.nan)
        tri=np.array([[0.,1,0],[12,1,0],[0,1,12]])
        if water is None:water=np.empty((0,3,3))
        polygons=[e.polygon(t[:,(0,2)]) for t in water]
        xy=np.array([[0.,road_z],[12,road_z]]);edges=np.array([[0,1,12]])
        rects,inners,outers,_=e.corridor(xy,edges)
        return e.regions_for_face(tri,h,wp,wf,water,STRtree(polygons),rects,STRtree(rects),inners,outers,STRtree(outers))[0]
    def test_exact_continuous_corridor_area(self):
        m=self.face()
        self.assertAlmostEqual(m['above_H_area'],72)
        self.assertAlmostEqual(m['corridor_rectangle_above_H_area'],48)
    def test_near_road_no_rectangle_overlap(self):
        m=self.face(road_z=17)
        self.assertEqual(m['corridor_rectangle_above_H_area'],0)
        self.assertEqual(m['corridor_disc_inner_above_H_area'],0)
        self.assertEqual(m['corridor_disc_uncertain_above_H_area'],0)
    def test_submerged_is_not_absent(self):
        w=np.array([[[0.,2,0],[12,2,0],[0,2,12]]])
        m=self.face(w)
        self.assertAlmostEqual(m['above_H_at_or_below_visual_W_area'],72)
        self.assertAlmostEqual(m['above_H_area'],72)
        self.assertEqual(m['above_H_without_visual_W_footprint_area'],0)
    def test_layers_not_double_counted(self):
        w=np.array([[[0.,2,0],[12,2,0],[0,2,12]],[[0.,3,0],[12,3,0],[0,3,12]]])
        m=self.face(w)
        self.assertAlmostEqual(m['above_H_at_or_below_visual_W_area'],72)
        self.assertEqual(m['intersecting_visual_water_faces'],2)
        self.assertEqual(m['nominal_visual_water_min_delta'],1.25)
        self.assertEqual(m['nominal_visual_water_max_delta'],2.25)
    def test_water_contact_explicit(self):
        w=np.array([[[0.,1,0],[12,1,0],[0,1,12]]]);m=self.face(w)
        self.assertAlmostEqual(m['above_H_at_or_below_visual_W_area'],72)
    def test_nominal_not_substituted_for_real_water(self):
        w=np.array([[[0.,2,0],[12,2,0],[0,2,12]]]);m=self.face(w)
        self.assertEqual(m['above_H_at_or_below_nominal_W_area'],0)
        self.assertEqual(m['above_H_at_or_below_visual_W_area'],72)
    def test_zero_road_edge_rejected(self):
        with self.assertRaisesRegex(ValueError,'zero_length'):e.rect(np.zeros(2),np.zeros(2))
    def test_visual_water_below_bed(self):
        w=np.array([[[0.,.5,0],[12,.5,0],[0,.5,12]]]);m=self.face(w)
        self.assertEqual(m['above_H_at_or_below_visual_W_area'],0)
        self.assertEqual(m['intersecting_visual_water_faces'],1)
        self.assertEqual(m['above_H_without_visual_W_footprint_area'],0)
    def test_half_footprint(self):
        w=np.array([[[0.,2,0],[12,2,0],[0,2,6]]]);m=self.face(w)
        self.assertAlmostEqual(m['above_H_at_or_below_visual_W_area'],36)
        self.assertAlmostEqual(m['above_H_without_visual_W_footprint_area'],36)
    def test_categories_aggregation(self):
        m=np.zeros((3,len(e.NAMES)));m[:,1]=[1,2,3];m[:,11]=[-3,-2,-1];m[:,12]=[4,5,6]
        r=e.summarize_regions(m,np.array(['BODY','CAP_START','CAP_START']))
        self.assertEqual(r['BODY']['above_H_area'],1)
        self.assertEqual(r['CAP_START']['above_H_area'],5)
        self.assertEqual(r['CAP_START']['min_B_H'],-2)
        self.assertEqual(r['CAP_START']['max_B_H'],6)
    def test_only_endpoint_disc_overlap(self):
        # Small triangle beyond flat end, entirely inside the circular end addition.
        tri=np.array([[7.,1,2.8],[8.,1,2.8],[7.,1,3.2]])
        xy=np.array([[3.,3],[6,3]]);edges=np.array([[0,1,3]])
        rects,ins,outs,_=e.corridor(xy,edges);empty=STRtree([])
        m=e.regions_for_face(tri,np.zeros((3,3)),np.full((2,2),np.nan),np.full((2,2,4),np.nan),np.empty((0,3,3)),empty,rects,STRtree(rects),ins,outs,STRtree(outs))[0]
        self.assertEqual(m['corridor_rectangle_above_H_area'],0)
        self.assertAlmostEqual(m['corridor_disc_inner_above_H_area'],.2)
    def test_near_degenerate_water_propagates(self):
        w=np.array([[[0.,2,0],[1,2,0],[1,2,1e-14]]])
        with self.assertRaisesRegex(ValueError,'NEAR_DEGENERATE'):self.face(w)
    def test_disc_ring_retained_as_uncertain(self):
        tri=np.array([[0.,1,0],[12,1,0],[0,1,12]])
        xy=np.array([[3.,3],[6,3]]);edges=np.array([[0,1,3]])
        rects,ins,outs,_=e.corridor(xy,edges);empty=STRtree([])
        m=e.regions_for_face(tri,np.zeros((3,3)),np.full((2,2),np.nan),np.full((2,2,4),np.nan),np.empty((0,3,3)),empty,rects,STRtree(rects),ins,outs,STRtree(outs))[0]
        self.assertGreater(m['corridor_disc_uncertain_above_H_area'],0)
        self.assertLessEqual(sum(m[k] for k in ('corridor_rectangle_above_H_area','corridor_disc_inner_above_H_area','corridor_disc_uncertain_above_H_area')),72+1e-12)
if __name__=='__main__':unittest.main()
