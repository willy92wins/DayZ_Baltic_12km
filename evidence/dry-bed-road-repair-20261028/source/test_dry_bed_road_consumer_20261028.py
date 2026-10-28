from pathlib import Path
import importlib.util,unittest
import numpy as np
R=Path(__file__).parent
sp=importlib.util.spec_from_file_location('consumer',R/'verify_dry_bed_road_candidate_20261028.py');c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sp=importlib.util.spec_from_file_location('producer',W/'tools/quality/dry_bed_road_candidate_ev112.py');p=importlib.util.module_from_spec(sp);sp.loader.exec_module(p)

class Controls(unittest.TestCase):
    def test_native_valley_continuous_not_vertex_only(self):
        h=np.zeros((3,3));h[1,1]=-1;plane=np.full((2,2),np.nan);field=np.zeros((2,2,4));tri=np.array([[0.,0.,0.],[12.,0.,0.],[0.,0.,12.]])
        maximum=-np.inf;total=0
        for cut,base,hh,water in c.native_parts(tri,h,plane,field):
            xy=np.array(cut.exterior.coords)[:-1];maximum=max(maximum,float((-c.interp(base,hh,xy)).max()));total+=cut.area
        self.assertEqual(maximum,1.);self.assertEqual(total,72.)
    def test_road_cap_outer_bound(self):
        shape=c.perimeter_corridor(np.array([[0.,0.],[10.,0.]]),np.array([[0,1,10.]]),np.array([-5,-5]),np.array([15,5]))
        self.assertTrue(shape.covers(c.Point(-4,0)));self.assertTrue(shape.covers(c.Point(5,4)));self.assertFalse(shape.covers(c.Point(5,4.1)))
    def test_sign_area(self):
        points=np.array([[0.,0.],[2.,0.],[0.,2.]])
        self.assertAlmostEqual(c.clip_sign(points,np.array([-1.,1.,1.])).area,1.5)
    def test_raised_conditional_water_kept(self):
        v=np.array([[[0.,10.,0.],[2.,10.,0.],[0.,10.,2.],[0.,0.,0.]]]);m=np.zeros(1,dtype=[('model','i4'),('kind','i4'),('vertices','i4'),('flags','i4')]);m['kind']=2;m['vertices']=3;m['flags']=1
        ins=dict(ids=np.array([3]),model_index=np.array([0]),matrix=np.array([[1,0,0,0,1,0,0,0,1,0,0,0]],float))
        shapes,world,refs,count=p.local_water((v,m,ins,[]),np.array([0,0]),np.array([2,2]))
        self.assertEqual(len(shapes),1);self.assertEqual(refs[0,3],1);self.assertTrue(shapes[0].intersects(c.Polygon([[0,0],[2,0],[0,2]])))
    def test_boundary_water_contact_kept(self):
        water=c.Polygon([[0,0],[1,0],[0,1]]);dry=c.Polygon([[1,0],[2,0],[1,1]])
        self.assertEqual(water.intersection(dry).area,0);self.assertTrue(water.intersects(dry))

if __name__=='__main__':unittest.main()
