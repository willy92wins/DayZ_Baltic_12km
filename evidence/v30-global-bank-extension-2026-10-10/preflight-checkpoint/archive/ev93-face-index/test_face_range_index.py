"""Synthetic query/geometry fixtures; never reads or writes a global cache."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

import numpy as np

import build_face_index as index


def load_ev87():
    spec=importlib.util.spec_from_file_location('ev87_fixture',index.EV87_PATH)
    if spec is None or spec.loader is None:raise ImportError(index.EV87_PATH)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


class FaceRangeIndexFixtures(unittest.TestCase):
    def test_source_pins_and_wrong_pin_fail_closed(self):
        index.verify_source_pins()
        old=index.EXPECTED_EV87_SHA
        try:
            index.EXPECTED_EV87_SHA='0'*64
            with self.assertRaises(AssertionError):index.verify_source_pins()
        finally:index.EXPECTED_EV87_SHA=old

    def test_output_must_be_the_new_EV93_directory(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):index.build(Path(td))
            self.assertEqual(list(Path(td).iterdir()),[])

    def test_large_face_crosses_window_and_kind_filter(self):
        z0=12282.0
        xyz=np.asarray([[1.0,2.0,z0-1.0],[25.0,8.0,z0-2.0],[2.0,4.0,z0-25.0]],dtype=np.float64)
        r=index.conservative_cell_range(xyz)
        self.assertTrue(np.array_equal(r,np.asarray([0,4,0,4],dtype=np.int32)))
        ranges=np.asarray([r,[-1,-1,-1,-1]],dtype=np.int32)
        kinds=np.asarray([index.KIND['physical'],index.KIND['visible']],dtype=np.uint8)
        self.assertEqual(index.query_mask(ranges,(2,2,2,2)).tolist(),[True,False])
        self.assertEqual(index.query_mask(ranges,(2,2,2,2),kinds,'visible').tolist(),[False,False])
        self.assertEqual(index.query_mask(ranges,(2,2,2,2),kinds,'physical').tolist(),[True,False])

    def test_direct_bbox_exposure_catches_omitted_face_and_excluding_range(self):
        z0=12282.0
        faces=[
            np.asarray([[1,0,z0-1],[25,2,z0-2],[2,1,z0-25]],dtype=np.float64),
            np.asarray([[13,0,z0-13],[17,1,z0-13],[13,2,z0-17]],dtype=np.float64),
            np.asarray([[70,0,z0-70],[72,1,z0-70],[70,2,z0-72]],dtype=np.float64),
        ]
        ranges=np.asarray([index.conservative_cell_range(x) for x in faces],dtype=np.int32)
        window=(0,3,0,3)
        r0,r1,c0,c1=window
        wx0,wx1=c0*6.0,(c1+1)*6.0
        wz1,wz0=z0-r0*6.0,z0-(r1+1)*6.0
        direct=[]
        for face_id,xyz in enumerate(faces):
            x0,x1=float(xyz[:,0].min()),float(xyz[:,0].max())
            z0f,z1f=float(xyz[:,2].min()),float(xyz[:,2].max())
            if x1>=wx0 and x0<=wx1 and z1f>=wz0 and z0f<=wz1:direct.append(face_id)
        mask=index.query_mask(ranges,window)
        indexed=set(np.flatnonzero(mask).tolist())
        self.assertTrue(set(direct).issubset(indexed))
        self.assertGreater(len(direct),0)
        # Negative oracle: dropping a face or corrupting its stored range must
        # be observable as a direct-bbox candidate missing from the index.
        omitted=indexed-{direct[0]}
        self.assertTrue(set(direct)-omitted)
        corrupted=ranges.copy();corrupted[direct[0]]=-1
        excluded=set(np.flatnonzero(index.query_mask(corrupted,window)).tolist())
        self.assertTrue(set(direct)-excluded)

    def test_closed_exact_boundary_range_is_conservative(self):
        z0=12282.0
        # The triangle touches x=6 and z=z0-6 exactly; closed bbox contact
        # includes every adjoining cell, even where overlap has zero area.
        xyz=np.asarray([[6.0,0.0,z0-6.0],[12.0,0.0,z0-6.0],[6.0,0.0,z0-12.0]],dtype=np.float64)
        got=index.conservative_cell_range(xyz)
        self.assertTrue(np.array_equal(got,np.asarray([0,2,0,2],dtype=np.int32)))
        self.assertTrue(index.query_mask(got.reshape(1,4),(0,0,0,0))[0])
        self.assertTrue(index.query_mask(got.reshape(1,4),(2,2,2,2))[0])

    def test_off_grid_and_empty_queries(self):
        xyz=np.asarray([[20000,0,20000],[20001,0,20000],[20000,0,20001]],dtype=np.float64)
        r=index.conservative_cell_range(xyz)
        self.assertEqual(r.tolist(),[-1,-1,-1,-1])
        self.assertFalse(index.query_mask(r.reshape(1,4),(0,10,0,10))[0])
        self.assertEqual(index.query_mask(np.empty((0,4),dtype=np.int32),(0,10,0,10)).size,0)

    def test_degenerate_and_tiny_positive_ranges_remain_queryable(self):
        # Index ranges do not apply EV87's downstream area cutoff. Collinear
        # triangles remain query candidates and are tagged by their producer.
        z0=12282.0
        line=np.asarray([[6,0,z0-6],[12,1,z0-6],[18,2,z0-6]],dtype=np.float64)
        r=index.conservative_cell_range(line)
        self.assertFalse(np.all(r==-1))
        self.assertTrue(index.query_mask(r.reshape(1,4),(0,3,0,3))[0])
        tiny=np.asarray([[1,0,1],[2,0,1],[1,0,1.00000000001]],dtype=np.float64)
        self.assertGreater(float(load_ev87().Polygon(tiny[:,[0,2]]).area),0.0)
        self.assertFalse(np.all(index.conservative_cell_range(tiny)==-1))

    def test_record_lod_arrays_retains_collinear_and_duplicate_vertex_faces(self):
        ev87=load_ev87()
        vertices=[SimpleNamespace(x=x,y=y,z=z) for x,y,z in (
            (6.0,10.0,12276.0),(12.0,11.0,12276.0),(18.0,12.0,12276.0))]
        lod=SimpleNamespace(vertices=vertices,faces=[
            SimpleNamespace(vertex_indices=[0,1,2]),
            SimpleNamespace(vertex_indices=[0,0,1])])
        arrays=index._record_lod_arrays(None,ev87,'fixture.p3d',lod,'physical',17,2,
            0.0,0.0,0.0,6.0,12282.0,2048)
        self.assertEqual(arrays['face_id'].tolist(),[0,1])
        self.assertEqual(arrays['degenerate'].tolist(),[1,1])
        self.assertEqual(arrays['area_xz'].tolist(),[0.0,0.0])
        self.assertTrue(np.all(arrays['plane_y_xz']==0.0))
        self.assertTrue(np.all(arrays['cell_range_rc'][:,0]>=0))

    def test_native_nw_se_split_matches_frozen_ev87(self):
        ev87=load_ev87()
        self.assertEqual(tuple(tuple(x) for x in ev87.TRIS),((0,1,3),(0,2,3)))
        xy=ev87.cell_xy(0,0)
        self.assertAlmostEqual(float(ev87.Polygon(xy[list(ev87.TRIS[0])]).area),18.0)
        self.assertAlmostEqual(float(ev87.Polygon(xy[list(ev87.TRIS[1])]).area),18.0)

    def test_query_api_returns_identity_and_geometry_arrays(self):
        arrays={'kind':np.asarray([0,1],dtype=np.uint8),
            'object_id':np.asarray([17,18],dtype=np.int32),
            'model_id':np.asarray([2,2],dtype=np.uint32),
            'face_id':np.asarray([8,9],dtype=np.uint32),
            'xyz':np.zeros((2,3,3),dtype=np.float64),
            'plane_y_xz':np.zeros((2,3),dtype=np.float64),
            'area_xz':np.asarray([1.0,0.0],dtype=np.float64),
            'cell_range_rc':np.asarray([[0,2,0,2],[-1,-1,-1,-1]],dtype=np.int32),
            'degenerate':np.asarray([0,1],dtype=np.uint8)}
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'shards').mkdir()
            path=root/'shards'/'faces-000000.npz'
            np.savez(path,**arrays)
            sha=index.sha(path)
            manifest={'schema':index.SCHEMA,'status':'COMPLETE',
                'models':[{'model_id':2,'basename':'fixture.p3d','sha256':'0'*64}],
                'shards':[{'path':'shards/faces-000000.npz','sha256':sha,'records':2}]}
            (root/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            api=index.FaceRangeIndex(root)
            got=api.query_window(1,1,1,1,'physical')
            self.assertEqual(got['object_id'].tolist(),[17])
            self.assertEqual(got['face_id'].tolist(),[8])
            self.assertEqual(got['xyz'].shape,(1,3,3))
            self.assertEqual(api.query_cell(1,1,'visible')['object_id'].size,0)
            self.assertTrue(api.reverify())
            with path.open('ab') as f:f.write(b'changed')
            with self.assertRaises(AssertionError):api.reverify()


if __name__=='__main__':unittest.main(verbosity=2)
