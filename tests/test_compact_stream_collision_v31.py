import sys,unittest,subprocess
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/water'))
from compact_stream_collision_v31 import partition,fit_grid,add_component,triangles
from review_compact_collision_v31 import overlay,vertices,py3d
from mesh_quality_v31 import closed_component


class CompactCollision(unittest.TestCase):
    def test_plane_packs_to_one_closed_component(self):
        z,x=np.mgrid[:7,:9];grid=np.stack((x,2+.1*x+.03*z,z),axis=-1).astype(float)
        parts=partition(grid);self.assertEqual(len(parts),1)
        lod=py3d.LOD();add_component(py3d,lod,parts[0],1)
        self.assertTrue(closed_component(vertices(lod,lod.faces))['closed'])
        roof=vertices(lod,lod.faces);normal=np.cross(roof[:,1]-roof[:,0],roof[:,2]-roof[:,0]);roof=roof[normal[:,1]<-1e-10]
        self.assertTrue(all(overlay(grid.reshape(-1,3)[triangles(*grid.shape[:2])],roof)['checks'].values()))

    def test_valley_cannot_be_closed_by_one_roof(self):
        z,x=np.mgrid[:5,-4:5];grid=np.stack((x,abs(x)*.3,z),axis=-1).astype(float)
        self.assertIsNone(fit_grid(grid))
        parts=partition(grid);self.assertGreater(len(parts),1)

    def test_overlay_finds_interior_error_with_identical_corners(self):
        p=np.array([[0,0,0],[2,0,0],[2,0,2],[0,0,2]],float);source=p[[[0,1,2],[0,2,3]]]
        for error in (-.03,.03):
            roof=np.array([[p[i],p[(i+1)%4],[1,error,1]] for i in range(4)])
            result=overlay(source,roof)
            self.assertFalse(result['checks']['vertical_contact_error'])
            self.assertTrue(result['checks']['full_source_covered'])

    def test_hole_and_lateral_extension_fail_separately(self):
        p=np.array([[0,0,0],[2,0,0],[2,0,2],[0,0,2]],float);source=p[[[0,1,2],[0,2,3]]]
        self.assertFalse(overlay(source,source[:1])['checks']['full_source_covered'])
        larger=source.copy();larger[larger[:,:,0]==0,0]=-.1
        self.assertFalse(overlay(source,larger)['checks']['no_excessive_horizontal_extension'])

    def test_invalid_grid_never_produces_empty_success(self):
        for grid in (np.zeros((1,4,3)),np.full((3,3,3),np.nan),np.zeros((3,3))):
            with self.assertRaises(ValueError):partition(grid)

    def test_buried_internal_roof_requires_complete_upper_contact(self):
        source=np.array([[[0,0,0],[2,0,0],[0,0,2]]],float)
        buried=source.copy();buried[:,:,1]-=.2
        self.assertFalse(overlay(source,buried)['checks']['vertical_contact_error'])
        complete=overlay(source,np.concatenate((buried,source)))
        self.assertTrue(all(complete['checks'].values()))
        self.assertAlmostEqual(complete['minimum_pair_height_error_m'],-.2)
        upper=source.copy();upper[:,:,1]+=.03
        self.assertFalse(overlay(source,np.concatenate((buried,upper)))['checks']['vertical_contact_error'])

    def test_invalid_overlay_never_produces_empty_success(self):
        triangle=np.array([[[0,0,0],[2,0,0],[0,0,2]]],float)
        for other in (np.empty((0,3,3)),np.full((1,3,3),np.nan),np.zeros((1,3,3))):
            with self.assertRaises(ValueError):overlay(triangle,other)

    def test_optimized_python_cannot_disable_safety_checks(self):
        root=Path(__file__).resolve().parents[1]/'tools/water'
        for name in ('compact_stream_collision_v31.py','review_compact_collision_v31.py'):
            run=subprocess.run([sys.executable,'-I','-O',str(root/name)],capture_output=True,text=True)
            self.assertNotEqual(run.returncode,0)
            self.assertIn('assertions enabled',run.stderr)


if __name__=='__main__':unittest.main()
