import itertools
import unittest
from fractions import Fraction

import numpy as np
from scipy import sparse
from shapely.geometry import LineString, MultiLineString

import executor as e


class ExecutorFixtures(unittest.TestCase):
    def test_assignment_space_is_exactly_59049_and_ordered(self):
        combos = list(itertools.islice(itertools.product((-1, 0, 1), repeat=10), 2))
        self.assertEqual(e.TOTAL_ASSIGNMENTS, 59049)
        self.assertEqual(combos, [(-1,) * 10, (-1,) * 9 + (0,)])
        self.assertEqual(next(itertools.islice(itertools.product((-1,0,1), repeat=10), 59048, None)), (1,) * 10)

    def test_material_target_is_derived_from_failed_rows_and_csr(self):
        data=[];indices=[];indptr=[0];meta=[];groups=[]
        for group in range(5):
            edge=(e.EXPECTED_NODES_RC[2*group],e.EXPECTED_NODES_RC[2*group+1])
            cells=((855+group,1179),(856+group,1179))
            group_rows=[]
            row_specs=((cells[0],"P"),(cells[0],"F"),(cells[1],"P"),(cells[1],"F"))
            for row_index,(cell,surface) in enumerate(row_specs):
                col=2*group+(row_index//2)
                row=len(meta);group_rows.append(row)
                data.append(1.0);indices.append(col);indptr.append(len(data))
                meta.append({"type":"cross_lower","edge_rc":[list(edge[0]),list(edge[1])],
                             "cell_rc":list(cell),"surface":surface})
            groups.append({"edge_rc":[list(edge[0]),list(edge[1])],"cells":[list(c) for c in cells],
                           "surfaces":["P","F"],"rows":group_rows})
        for _ in range(528-len(meta)):
            meta.append({"type":"cross_lower","edge_rc":[[0,0],[0,1]]})
        indptr.extend([len(data)]*(529-len(indptr)))
        # Include the 32 non-row summary records to prove alignment filters them.
        metadata=meta+[{"type":"sign_only"} for _ in range(32)]
        matrix=sparse.csr_matrix((data,indices,indptr),shape=(528,10))
        diag={"schema":"ev94.wet-bank-crossing-geometry-fraction.v2",
              "physical_crossing":{"candidate_direct_failures":20,"candidate_failed_native_edges":groups}}
        derived,row_ids,edges=e.derive_material_target(diag,metadata,matrix,np.asarray(e.EXPECTED_NODES_RC))
        self.assertEqual(derived,e.EXPECTED_NODES_RC)
        self.assertEqual(row_ids,tuple(range(20)))
        self.assertEqual(len(edges),5)
        bad=list(metadata)
        bad[0]={"type":"cross_lower","edge_rc":[[1,1],[2,2]]}
        with self.assertRaises(ValueError):
            e.derive_material_target(diag,bad,matrix,np.asarray(e.EXPECTED_NODES_RC))

    def test_options_keep_out_of_bounds_neighbor_for_all_gates(self):
        x = np.float32(1.0)
        down = e.f32_next(x, False)
        up = e.f32_next(x, True)
        options = e.build_neighbor_options([x], [x], [x])
        self.assertEqual(options, ((down, x, up),))
        selected = e.offsets_for((1,), options)
        self.assertEqual(selected.view(np.uint32)[0], up.view(np.uint32))
        self.assertGreater(selected[0], x)  # bounds gate, not enumeration, rejects it

    def test_out_of_bounds_assignment_still_evaluates_independent_gates(self):
        rc=np.asarray([(855,1179)],dtype=np.int32)
        grid=np.zeros((15,15),dtype=np.float32);grid[0,0]=1.0
        data={"vars_rc":rc,"lo":np.asarray([1.0]),"hi":np.asarray([1.0]),
              "cross_specs":(),"sign_specs":(),"witnesses":np.empty((0,4),dtype=np.int32),
              "G":sparse.csr_matrix(np.asarray([[1.0],[0.0]])),"k":np.zeros(2),"radii":np.asarray([1.0]),
              "A":sparse.csr_matrix([[1.0]]),"rhs":np.asarray([0.0]),"raw_x":np.asarray([1.0]),"x0":np.asarray([1.0])}
        candidate=grid.copy();candidate[0,0]=e.f32_next(np.float32(1),True)
        gates=e.eval_gates(data,candidate)
        self.assertFalse(gates["bounds"])
        self.assertTrue(gates["PF_signs"])
        self.assertTrue(gates["all_116_direct_crossings"])
        self.assertTrue(gates["D8_direct"])
        self.assertFalse(gates["face_cones"])
        self.assertFalse(gates["closure_energy_and_improvement"])

    def test_only_target_values_change(self):
        grid = np.arange(225, dtype=np.float32).reshape(15, 15)
        data = {"target_rc": np.asarray([(855,1179),(862,1186)], dtype=np.int32)}
        vals = np.asarray([11.5, 12.5], dtype=np.float32)
        out = e.set_ten_values(grid, data, vals)
        self.assertEqual(out[0,0], vals[0])
        self.assertEqual(out[7,7], vals[1])
        mask = np.ones(grid.shape, dtype=bool)
        mask[(data["target_rc"] - np.asarray(e.ORIGIN)).T[0], (data["target_rc"] - np.asarray(e.ORIGIN)).T[1]] = False
        self.assertTrue(np.array_equal(out[mask].view(np.uint32), grid[mask].view(np.uint32)))

    def test_direct_crossing_and_strict_sign_controls(self):
        edge = ((e.ORIGIN[0], e.ORIGIN[1]), (e.ORIGIN[0], e.ORIGIN[1] + 1))
        spec = e.CrossSpec(
            key=((855,1179), edge, "P"), surface="P", cell_rc=(855,1179), edge_rc=edge,
            local_a=(0,0), local_b=(0,1), level_a=Fraction(0), level_b=Fraction(0),
            dry_endpoint=0, t_lower=Fraction(49,100), t_upper=Fraction(51,100),
            dry_level=Fraction(0), wet_level=Fraction(0), dry_rc=edge[0], wet_rc=edge[1])
        grid = np.zeros((2,2), dtype=np.float32)
        grid[0,0] = 1.0
        grid[0,1] = -1.0
        self.assertTrue(e.direct_crossings_pass(grid, (spec,)))
        self.assertTrue(e.direct_signs_pass(grid, (spec,), ()))
        grid[0,1] = -0.5
        self.assertFalse(e.direct_crossings_pass(grid, (spec,)))
        self.assertTrue(e.direct_signs_pass(grid, (spec,), ()))

    def test_design_edge_intersection_deduplicates_exact_points_only(self):
        edge=((855,1179),(855,1180))
        one=LineString([(7077.0,7151.0),(7077.0,7153.0)])
        self.assertEqual(e.design_t_ab(edge,one),Fraction(1,2))
        two_close=MultiLineString([
            [(7075.0,7151.0),(7075.0,7153.0)],
            [(7075.0000000001,7151.0),(7075.0000000001,7153.0)]])
        with self.assertRaises(ValueError):
            e.design_t_ab(edge,two_close)

    def test_same_sign_and_baseline_contact(self):
        strict = e.SignSpec((855,1179),(0,0),Fraction(0),1,np.float32(1),"F")
        contact = e.SignSpec((855,1180),(0,1),Fraction(1),0,np.float32(1),"P")
        grid = np.ones((2,2), dtype=np.float32)
        self.assertTrue(e.direct_signs_pass(grid, (), (strict, contact)))
        grid[0,0] = np.float32(0)
        self.assertFalse(e.direct_signs_pass(grid, (), (strict,)))
        grid[0,0] = np.float32(1)
        grid[0,1] = e.f32_next(np.float32(1), True)
        self.assertFalse(e.direct_signs_pass(grid, (), (contact,)))

    def test_exact_binary64_surface_sign_does_not_require_extra_ulp(self):
        level = Fraction.from_float(0.1)
        spec = e.SignSpec((855,1179),(0,0),level,1,np.float32(0.1),"P")
        grid = np.asarray([[np.float32(0.1)]], dtype=np.float32)
        self.assertGreater(Fraction.from_float(float(grid[0,0])), level)
        self.assertTrue(e.direct_signs_pass(grid, (), (spec,)))

    def test_d8_direction(self):
        grid = np.asarray([[2.0, 1.0], [3.0, 1.0]], dtype=np.float32)
        self.assertTrue(e.d8_pass(grid, [(0,0,0,1), (1,0,1,1)]))
        self.assertFalse(e.d8_pass(grid, [(0,1,0,0)]))

    def test_face_cone_boundary_and_outside(self):
        G = sparse.eye(2, format="csr")
        ok, excess = e.cone_metrics(np.asarray([0.6,0.8]), G, np.zeros(2), np.asarray([1.0]))
        self.assertTrue(ok)
        self.assertLessEqual(excess, 0.0)
        bad, excess = e.cone_metrics(np.asarray([0.6,0.81]), G, np.zeros(2), np.asarray([1.0]))
        self.assertFalse(bad)
        self.assertGreater(excess, 0.0)

    def test_energy_inherited_allowance_and_strict_improvement(self):
        passed, allowance = e.closure_energy_pass(10.0, 10.0 + 5e-7, 11.0)
        self.assertTrue(passed)
        self.assertAlmostEqual(allowance, 1e-6)
        failed, _ = e.closure_energy_pass(10.0, 10.0 + 2e-6, 11.0)
        self.assertFalse(failed)
        no_improvement, _ = e.closure_energy_pass(10.0, 10.0, 10.0)
        self.assertFalse(no_improvement)

    def test_rank_uses_ulp_count_then_distance_then_row_major_tuple(self):
        rc = np.asarray([(862,1186),(862,1187)], dtype=np.int32)
        x64 = np.asarray([1.0,1.0])
        a = e.rank_candidate((0,1), rc, np.asarray([1.0,1.0]), x64)
        b = e.rank_candidate((1,0), rc, np.asarray([1.0,1.0]), x64)
        self.assertEqual(a[0], b[0])
        self.assertEqual(a[1], b[1])
        self.assertLess(a[2], b[2])
        c = e.rank_candidate((0,0), rc, np.asarray([1.0,1.0]), x64)
        self.assertLess(c, a)


if __name__ == "__main__":
    unittest.main(verbosity=2)
