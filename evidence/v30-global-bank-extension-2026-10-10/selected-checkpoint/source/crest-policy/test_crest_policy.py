import importlib.util
from fractions import Fraction
from pathlib import Path
import sys
import unittest

import numpy as np

spec = importlib.util.spec_from_file_location("crest_policy_under_test", Path(__file__).with_name("crest_policy.py"))
policy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = policy
spec.loader.exec_module(policy)


def provenance(center=(2, 2)):
    return policy.Provenance(
        queue_id=7, center_rc=center,
        baseline_sha256=policy.EXPECTED_PINS["baseline_sha256"],
        prepared_sha256="1" * 64, result_sha256="2" * 64, solution_sha256="3" * 64,
        policy_plan_sha256=policy.EXPECTED_PINS["policy_plan_sha256"],
        ev92_sha256=policy.EXPECTED_PINS["ev92_sha256"],
        shape_contract_sha256=policy.EXPECTED_PINS["shape_contract_sha256"],
        policy_module_sha256="4" * 64,
        source_rejection_reason=policy.EXPECTED_SOURCE_REASON,
    )


class CrestPolicyTests(unittest.TestCase):
    def test_union_component_connected_and_disconnected(self):
        component = policy._component_reaching_one
        self.assertEqual(component([(Fraction(0), Fraction(1, 3)), (Fraction(2, 3), Fraction(1))]),
                         (Fraction(2, 3), Fraction(1)))
        self.assertEqual(component([(Fraction(0), Fraction(2, 3)), (Fraction(2, 3), Fraction(1))]),
                         (Fraction(0), Fraction(1)))
        self.assertIsNone(component([(Fraction(0), Fraction(1, 2)), None]))

    def test_both_axes_active_and_energy_midpoint(self):
        b = np.zeros((5, 5), dtype=np.float32); h = b.copy()
        b[2, 2] = 3
        legacy = {"alpha": 0.6769237551186755, "energy_lower": 0.4,
                  "focus_lower_by_axis": {"EW": 0.2, "NS": 0.3}, "rule": "unchanged EV92"}
        result = policy.derive_scalar_rule(b, h, focus_rc=(2, 2), alpha_energy=0.4,
                                           provenance=provenance(), legacy_rule=legacy)
        self.assertTrue(result["axes"]["EW"]["active"] and result["axes"]["NS"]["active"])
        self.assertEqual(result["alpha"], legacy["alpha"])
        self.assertEqual(result["alpha_midpoint"], legacy["alpha"])
        self.assertEqual(result["rule"], legacy["rule"])
        self.assertEqual(result["policy_mode"], "legacy_both_axes_bit_exact")

    def test_both_axes_legacy_rule_is_not_gated_by_new_alpha_one_tail(self):
        b = np.zeros((5, 5), dtype=np.float32); h = b.copy()
        b[2, 2] = 4
        b[2, 1] = b[2, 3] = b[1, 2] = b[3, 2] = 3
        h[2, 2] = 10  # Both new-policy endpoint constraints fail at alpha=1.
        legacy = {"alpha": 0.5, "energy_lower": 0.4,
                  "focus_lower_by_axis": {"EW": 0.1, "NS": 0.1}, "rule": "unchanged EV92"}
        result = policy.derive_scalar_rule(b, h, focus_rc=(2, 2), alpha_energy=0.4,
                                           provenance=provenance(), legacy_rule=legacy)
        self.assertEqual(result["alpha"], 0.5)
        self.assertEqual(result["alpha_midpoint"], 0.5)
        self.assertEqual(result["rule"], "unchanged EV92")

    def test_one_axis_active_and_inactive_axis_remains_zero(self):
        b = np.zeros((5, 5), dtype=np.float32); h = b.copy()
        b[2, 2] = 2; b[1, 2] = b[3, 2] = 3; h[2, 2] = 0
        rule = policy.derive_scalar_rule(b, h, focus_rc=(2, 2), alpha_energy=0.1, provenance=provenance())
        self.assertTrue(rule["axes"]["EW"]["active"])
        self.assertFalse(rule["axes"]["NS"]["active"])
        final = policy.interpolate_float32(b, h, rule["alpha_midpoint"])
        check = policy.evaluate_focus_after(b, final, focus_rc=(2, 2))
        self.assertTrue(check["pass"], check)
        self.assertEqual(check["axes"]["NS"]["prominence_H_m"]["fraction"], "0/1")

    def test_no_active_axes_rejected(self):
        b = np.zeros((5, 5), dtype=np.float32); h = b.copy()
        b[2, 2] = 2; b[1, 2] = b[3, 2] = b[2, 1] = b[2, 3] = 3
        with self.assertRaises(policy.PolicyReject) as ctx:
            policy.derive_scalar_rule(b, h, focus_rc=(2, 2), alpha_energy=0.2, provenance=provenance())
        self.assertEqual(ctx.exception.code, "no_active_axis")

    def test_singleton_alpha_one_rejected(self):
        b = np.zeros((5, 5), dtype=np.float32); h = b.copy()
        b[2, 2] = h[2, 2] = 4; b[2, 1] = b[2, 3] = 3; h[2, 1] = 3.25
        b[1, 2] = b[3, 2] = h[1, 2] = h[3, 2] = 5
        with self.assertRaises(policy.PolicyReject) as ctx:
            policy.derive_scalar_rule(b, h, focus_rc=(2, 2), alpha_energy=0.2, provenance=provenance())
        self.assertEqual(ctx.exception.code, "zero_width_tail")

    def test_float32_cast_failure_is_not_waived(self):
        b = np.full((5, 5), np.float32(1719.13), dtype=np.float32)
        h = b.copy()
        b[2, 2] = np.float32(1719.132)
        b[2, 1] = np.float32(1719.1317); b[2, 3] = np.float32(1719.1293)
        h[2, 2] = np.float32(1719.1317)
        h[2, 1] = np.float32(1719.1316); h[2, 3] = np.float32(1719.1292)
        b[1, 2] = b[3, 2] = h[1, 2] = h[3, 2] = np.float32(1720)
        rule = policy.derive_scalar_rule(b, h, focus_rc=(2, 2), alpha_energy=0.1, provenance=provenance())
        self.assertAlmostEqual(rule["alpha_midpoint"], 0.75)
        after = policy.interpolate_float32(b, h, rule["alpha_midpoint"])
        check = policy.evaluate_focus_after(b, after, focus_rc=(2, 2))
        self.assertFalse(check["pass"])
        self.assertFalse(check["axes"]["EW"]["pass"])

    def test_cardinal_api_matches_grid_api_and_ev92_energy_root(self):
        b = np.zeros((5, 5), dtype=np.float32); h = b.copy()
        b[2, 2] = 2; b[1, 2] = b[3, 2] = 3; h[2, 2] = 0
        grid_rule = policy.derive_scalar_rule(b, h, focus_rc=(2, 2), alpha_energy=0.1,
                                              provenance=provenance())
        base_values = np.asarray([b[2, 2], b[2, 1], b[2, 3], b[1, 2], b[3, 2]], dtype=np.float32)
        dir_values = np.asarray([h[2, 2], h[2, 1], h[2, 3], h[1, 2], h[3, 2]], dtype=np.float32)
        local_rule = policy.derive_scalar_rule_from_cardinals(base_values, dir_values,
                         alpha_energy=0.1, provenance=provenance())
        self.assertEqual(grid_rule["alpha_midpoint"], local_rule["alpha_midpoint"])
        moments = [Fraction(1), Fraction(-1), Fraction(1, 5)]
        expected = (0.5) / (1.0 + (0.8 ** 0.5))
        self.assertAlmostEqual(policy.energy_lower_from_moments(moments), expected, places=15)

    def test_shape_update_only_replaces_focus_acceptance_gate(self):
        report = {"gates": {policy.LEGACY_FOCUS_GATE: False, "no_new_strict_minima8": True,
                            "no_new_exactly_constant_2x2_windows": True},
                  "axes": {"unchanged": [1, 2]}, "new_minima8": []}
        focus = {"gate": policy.NEW_FOCUS_GATE, "pass": True, "axes": {}}
        updated = policy.replace_focus_gate(report, focus)
        self.assertEqual(updated["gates"], {"no_new_strict_minima8": True,
                         "no_new_exactly_constant_2x2_windows": True, policy.NEW_FOCUS_GATE: True})
        self.assertEqual(updated["axes"], report["axes"])
        self.assertEqual(updated["new_minima8"], report["new_minima8"])
        self.assertFalse(report["gates"][policy.LEGACY_FOCUS_GATE])

    def test_provenance_requires_exact_reason_and_pins(self):
        bad = provenance()
        object.__setattr__(bad, "source_rejection_reason", "contains the right phrase")
        with self.assertRaisesRegex(ValueError, "exact EV92"):
            bad.validate()
        bad = provenance()
        object.__setattr__(bad, "baseline_sha256", "0" * 64)
        with self.assertRaisesRegex(ValueError, "pinned source"):
            bad.validate()


if __name__ == "__main__":
    unittest.main(verbosity=2)
