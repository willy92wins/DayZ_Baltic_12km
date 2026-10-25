import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/water'))
from mesh_quality_v31 import closed_component,bidirectional_error

class MeshQuality(unittest.TestCase):
    def tetra(self):
        p=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],float)
        return p[[[0,2,1],[0,1,3],[0,3,2],[1,2,3]]]

    def test_closed_and_open_and_flipped(self):
        t=self.tetra();self.assertTrue(closed_component(t)['closed'])
        self.assertFalse(closed_component(t[:-1])['closed'])
        t[0]=t[0,::-1];self.assertFalse(closed_component(t)['closed'])

    def test_disconnected_closed_shells_fail_component(self):
        t=self.tetra();self.assertFalse(closed_component(np.concatenate([t,t+3]))['closed'])

    def test_missing_source_point_cannot_pass_one_way(self):
        source=self.tetra().reshape(-1,3);partial=source[source[:,2]==0]
        e=bidirectional_error(source,partial)
        self.assertEqual(e['compiled_to_source'],0);self.assertEqual(e['source_to_compiled'],1)
        self.assertEqual(bidirectional_error(source,source)['source_to_compiled'],0)

    def test_invalid_vertices_rejected(self):
        for v in (np.empty((0,3)),np.array([[0,0,np.nan]])):
            with self.assertRaises(ValueError):bidirectional_error(v,v)

if __name__=='__main__':unittest.main()
