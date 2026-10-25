import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/water'))
from midpoint_stream_collision_v31 import partition_midpoint,SearchLimit
from compact_stream_collision_v31 import fit_grid,add_component,triangles
from review_compact_collision_v31 import overlay,vertices,py3d,require_eligible_packing
from mesh_quality_v31 import closed_component


def plane(n=3,m=3):
    z,x=np.mgrid[:n,:m]
    return np.stack((x,2+.1*x+.03*z,z),axis=-1).astype(float)


def consume(grid,parts):
    lod=py3d.LOD()
    for i,part in enumerate(parts,1):add_component(py3d,lod,part,i)
    for selection in lod.selections.values():
        result=closed_component(vertices(lod,list(selection.faces)))
        if not result['closed'] or result['signed_volume']>=0:raise AssertionError(result)
    roof=vertices(lod,lod.faces)
    normal=np.cross(roof[:,1]-roof[:,0],roof[:,2]-roof[:,0])
    roof=roof[normal[:,1]<-1e-10]
    return overlay(grid.reshape(-1,3)[triangles(*grid.shape[:2])],roof)


class MidpointCollision(unittest.TestCase):
    def test_ramp_single_hull_with_independent_contact(self):
        grid=plane(5,7)
        parts,info=partition_midpoint(grid,max_vertices_per_component=8,max_faces_per_component=12)
        self.assertEqual(info['cost']['components'],1)
        self.assertEqual(info['states'],1)
        self.assertTrue(all(consume(grid,parts)['checks'].values()))

    def test_tight_component_caps_split_plane_without_holes(self):
        grid=plane()
        parts,info=partition_midpoint(grid,max_vertices_per_component=6,max_faces_per_component=8)
        self.assertEqual(len(parts),8)
        self.assertEqual(info['states'],9)
        self.assertTrue(all(len(p['points'])<=6 and len(p['faces'])<=8 for p in parts))
        self.assertEqual(info['selected_splits'][0]['axis'],'row')
        self.assertTrue(all(consume(grid,parts)['checks'].values()))

    def test_valley_keeps_open_shape_and_contact(self):
        z,x=np.mgrid[:5,-4:5];grid=np.stack((x,abs(x)*.3,z),axis=-1).astype(float)
        parts,info=partition_midpoint(grid,max_vertices_per_component=20,max_faces_per_component=36)
        self.assertEqual(len(parts),2)
        self.assertEqual(info['selected_splits'][0]['axis'],'column')
        self.assertTrue(all(consume(grid,parts)['checks'].values()))

    def test_failed_or_incomplete_packing_cannot_get_geometry_pass(self):
        require_eligible_packing({'collision_packing':{'status':'CANDIDATE_GLOBAL_OVERLAY_PENDING'}})
        require_eligible_packing({'collision_trial':{'status':'legacy_overlap_candidate'}})
        for packing in ({'status':'FAIL_COST_REGRESSION'},{'status':'INCONCLUSIVE'},{'status':'PASS'}, {}, None):
            with self.assertRaisesRegex(ValueError,'not eligible'):
                require_eligible_packing({'collision_packing':packing})

    def test_state_limit_does_not_return_partial_mesh(self):
        with self.assertRaisesRegex(SearchLimit,'INCONCLUSIVE.*state limit'):
            partition_midpoint(plane(),max_vertices_per_component=6,max_faces_per_component=8,max_states=1)

    def test_timeout_checked_after_native_fit_before_return(self):
        with patch('midpoint_stream_collision_v31.time.monotonic',side_effect=[0.,0.,61.]):
            with self.assertRaisesRegex(SearchLimit,'INCONCLUSIVE.*time limit'):
                partition_midpoint(plane(),max_vertices_per_component=8,max_faces_per_component=12,timeout_s=60.)

    def test_invalid_grid_caps_budgets_and_deadline_rejected(self):
        good=dict(max_vertices_per_component=8,max_faces_per_component=12)
        for grid in (np.zeros((1,4,3)),np.full((3,3,3),np.nan),np.zeros((3,3))):
            with self.assertRaises(ValueError):partition_midpoint(grid,**good)
        for options in ({'max_vertices_per_component':5},{'max_faces_per_component':7},{'max_states':0},
                        {'max_states':True},{'timeout_s':0},{'timeout_s':float('nan')},
                        {'vertical_budget':-.1},{'vertical_budget':float('inf')},{'horizontal_budget':True}):
            with self.assertRaises(ValueError):partition_midpoint(plane(),**(good|options))

    def test_nonfinite_exact_refinement_never_becomes_zero_bound(self):
        grid=np.array([[[0.,0.,0.],[1.,1.,0.]],[[0.,1.,1.],[1.,0.,1.]]])
        self.assertIsNone(fit_grid(grid,vertical_budget=.03,horizontal_budget=.01))
        # Simulate a numerical failure returned by the external intersection
        # operation, not a duplicate author formula or malformed source grid.
        with patch('compact_stream_collision_v31.shapely.get_coordinates',return_value=(np.array([[np.nan,np.nan]]),np.array([0]))):
            with self.assertRaisesRegex(ValueError,'nonfinite exact roof refinement'):
                fit_grid(grid,vertical_budget=.03,horizontal_budget=.01)

    def test_fresh_processes_reproduce_geometry_and_tie_break(self):
        code='''import sys,json,hashlib,numpy as np
sys.path.insert(0,sys.argv[1])
from midpoint_stream_collision_v31 import partition_midpoint
z,x=np.mgrid[:3,:3];g=np.stack((x,2+.1*x+.03*z,z),axis=-1).astype(float)
p,s=partition_midpoint(g,max_vertices_per_component=6,max_faces_per_component=8)
h=hashlib.sha256()
for v in p:h.update(v['points'].tobytes());h.update(v['faces'].tobytes())
print(json.dumps(dict(sha=h.hexdigest(),splits=s['selected_splits'],cost=s['cost']),sort_keys=True))
'''
        outputs=[]
        for _ in range(2):
            r=subprocess.run([sys.executable,'-I','-c',code,str(ROOT/'tools/water')],capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stderr);outputs.append(r.stdout)
        self.assertEqual(outputs[0],outputs[1])
        self.assertEqual(json.loads(outputs[0])['splits'][0]['axis'],'row')

    def test_optimized_python_rejected(self):
        r=subprocess.run([sys.executable,'-I','-O',str(ROOT/'tools/water/midpoint_stream_collision_v31.py')],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0);self.assertIn('assertions enabled',r.stderr)


if __name__=='__main__':unittest.main()
