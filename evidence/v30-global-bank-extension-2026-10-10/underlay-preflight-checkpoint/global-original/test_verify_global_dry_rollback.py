from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
SOURCE=HERE/"verify_global_dry_rollback.py"
spec=importlib.util.spec_from_file_location("global_dry_rollback_consumer_test",SOURCE)
consumer=importlib.util.module_from_spec(spec);sys.modules[spec.name]=consumer;spec.loader.exec_module(consumer)


class ConsumerFixtures(unittest.TestCase):
    def test_domain_passes_only_exact_mutable_nodes(self):
        base=np.ones((5,5),np.float32);h=base.copy();h[2,2]=1.25
        rc=np.asarray([[2,2]],np.int32)
        result=consumer.exact_domain_identity(base,h,rc,{"fixed":np.zeros((5,5),bool)},1,None)
        self.assertTrue(result["pass"]);self.assertEqual(result["changed_vertices"],1)

    def test_domain_rejects_fixed_and_protected_changes(self):
        base=np.ones((5,5),np.float32);h=base.copy();h[2,2]=1.25;h[1,1]=0.75
        rc=np.asarray([[2,2]],np.int32);protect=np.zeros((5,5),bool);protect[2,2]=True
        result=consumer.exact_domain_identity(base,h,rc,{"fixed_guard":protect},1,None)
        self.assertFalse(result["pass"]);self.assertEqual(result["fixed_changes"],1)
        self.assertEqual(result["protected_changes"]["fixed_guard"],1)

    def test_domain_rejects_duplicate_and_out_of_range_coordinates(self):
        base=np.ones((5,5),np.float32)
        with self.assertRaises(ValueError):
            consumer.exact_domain_identity(base,base,np.asarray([[1,1],[1,1]],np.int32),{},2,None)
        with self.assertRaises(ValueError):
            consumer.exact_domain_identity(base,base,np.asarray([[5,0]],np.int32),{},1,None)

    def test_inward_float32_rounding_never_crosses_real_bound(self):
        raw=np.asarray([1.00000003,-2.00000007,4.0],np.float64)
        lo=consumer.inward_float32(raw,True);hi=consumer.inward_float32(raw,False)
        self.assertTrue(np.all(lo.astype(np.float64)>=raw))
        self.assertTrue(np.all(hi.astype(np.float64)<=raw))
        self.assertTrue(np.all(np.nextafter(lo,np.float32(-np.inf)).astype(np.float64)<raw))
        self.assertTrue(np.all(np.nextafter(hi,np.float32(np.inf)).astype(np.float64)>raw))

    def test_d8_detects_new_strict_minimum_and_witness_order_loss(self):
        b=np.full((7,7),2.0,np.float32);h=b.copy();h[3,3]=1.0
        self.assertFalse(consumer.check_d8_no_new_strict_minima(b,h)["pass"])
        b=np.full((7,7),2.0,np.float32);b[3,3]=1.0;b[3,2]=1.0
        h=b.copy();h[3,3]=0.5
        self.assertFalse(consumer.check_d8_witness_order(b,h)["pass"])

    def test_rectangle_union_uses_inclusive_cell_bounds(self):
        ranges=np.asarray([[0,0,0,0],[1,3,2,4],[2,4,3,5],[5,5,0,5]],np.int32)
        actual=consumer.rectangle_union(ranges,6);expected=np.zeros((6,6),bool)
        for r0,r1,c0,c1 in ranges:expected[r0:r1+1,c0:c1+1]=True
        self.assertTrue(np.array_equal(actual,expected))
        with self.assertRaises(ValueError):consumer.rectangle_union(np.asarray([[0,6,0,1]],np.int32),6)

    def test_face_identity_rejects_wrong_ids_and_deploy_binding(self):
        manifest={"schema":"ev93.face-range-index.v1","status":"COMPLETE",
          "water_object_ids_sha256":consumer.EXPECTED_FACE_IDS,"object_count":18024,"counts":{"faces":883308},
          "base_identity":{"terrain_sha256":consumer.EXPECTED_BASE_TERRAIN,
            "wrp_source_sha256":consumer.PINNED[str(consumer.B_WRP)],
            "world_pbo_sha256":consumer.EXPECTED_WORLD_PBO,"water_pbo_sha256":consumer.EXPECTED_WATER_PBO}}
        deploy={"baseline_world_pbo_sha256":consumer.EXPECTED_WORLD_PBO,
          "baseline_water_pbo_sha256":consumer.EXPECTED_WATER_PBO,
          "baseline_terrain_sha256":consumer.EXPECTED_BASE_TERRAIN}
        consumer.validate_face_identity(manifest,deploy)
        bad={**manifest,"water_object_ids_sha256":"0"*64}
        with self.assertRaises(ValueError):consumer.validate_face_identity(bad,deploy)
        bad_deploy={**deploy,"baseline_water_pbo_sha256":"0"*64}
        with self.assertRaises(ValueError):consumer.validate_face_identity(manifest,bad_deploy)

    def test_edge_angle_chunks_equal_independent_ev87_generator(self):
        ev87=consumer.load_module("ev87_fixture_consumer",consumer.EV87,consumer.PINNED[str(consumer.EV87)])
        rng=np.random.default_rng(12282);h=rng.normal(2.0,0.2,size=(23,23)).astype(np.float64)
        actual=consumer.collect_edge_angles(ev87,h,chunk_rows=4)
        expected=dict(ev87.edge_angles(h))
        for key in expected:self.assertTrue(np.array_equal(actual[key],expected[key]),key)

    def test_face_failure_is_json_serializable_python_bool(self):
        ev87=consumer.load_module("ev87_face_failure_fixture",consumer.EV87,consumer.PINNED[str(consumer.EV87)])
        class PopulationStub:
            triangle_normals=staticmethod(ev87.triangle_normals)
            edge_vertex_slices=staticmethod(ev87.edge_vertex_slices)
            summaries=staticmethod(ev87.summaries)
            @staticmethod
            def _ev87_populations(base, constraints):return {"fixture":np.ones(base["heights"].shape,dtype=bool)}
            @staticmethod
            def _ev87_thresholds(values):return {"q0":-1.0,"q1":-0.5}
        base=np.full((8,8),2.0,np.float32);candidate=base.copy();candidate[3,3]=20.0
        radii=np.zeros((7,7,2),np.float64)
        result=consumer.check_face_fields(PopulationStub,base,candidate,radii,{"heights":base}, {})
        self.assertFalse(result["pass"])
        self.assertGreater(result["face_cone_violations"],0)
        self.assertGreater(result["slope_violations"],0)
        self.assertGreater(result["new_hinges_over_30"],0)
        self.assertFalse(result["sector_max_nonregression"])
        self.assertIs(type(result["pass"]),bool)
        json.dumps(result)

    def test_water_clearance_rejects_zero_or_negative_touch(self):
        b=np.full((4,4),1.5,np.float32);h=b.copy();h[1,1]=1.0
        levels=np.full((4,4),1.0,np.float64)
        ok=consumer.direct_changed_water_clearance(b,b,np.asarray([[1,1]],np.int32),levels)
        bad=consumer.direct_changed_water_clearance(b,h,np.asarray([[1,1]],np.int32),levels)
        self.assertTrue(ok["pass"]);self.assertFalse(bad["pass"])

    def test_water_topology_checks_independent_p_f_and_sea_faces(self):
        n=5;base=np.full((n,n),2.0,np.float32);p=np.full((n-1,n-1),np.nan,np.float64)
        f=np.full((n-1,n-1,4),np.nan,np.float64)
        same=consumer.compare_water_topology(base,base,p,f,((0,0),(0,1),(1,0),(1,1)),((0,1,3),(0,3,2)),2)
        self.assertTrue(same["pass"])
        p[1,1]=1.5;changed=base.copy();changed[1,1]=1.0
        bad=consumer.compare_water_topology(base,changed,p,f,((0,0),(0,1),(1,0),(1,1)),((0,1,3),(0,3,2)),2)
        self.assertFalse(bad["pass"]);self.assertGreater(bad["sign_changed_samples_by_surface"]["P"],0)
        self.assertGreater(bad["native_triangle_mask_changes_by_surface"]["P"],0)

    def test_radius_and_bound_rebuild_use_ev79_binary64_formula(self):
        b=np.full((4,4),2.0,np.float32);ev79=np.full((4,4),2.0,np.float32)
        p=np.full((3,3),np.nan,np.float64);f=np.full((3,3,4),np.nan,np.float64)
        rc=np.asarray([[1,1],[2,2]],np.int32)
        result=consumer.rebuild_bounds(b,ev79,ev79,p,f,rc,
            consumer.inward_float32(np.asarray([1.8,1.8],np.float64),True),
            consumer.inward_float32(np.asarray([4.0,4.0],np.float64),False))
        self.assertTrue(result["formula_matches_prepared"])
        self.assertTrue(result["candidate_within_bounds"])


if __name__=="__main__":
    unittest.main(verbosity=2)
