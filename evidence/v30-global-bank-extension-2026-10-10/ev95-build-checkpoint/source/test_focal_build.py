"""Lightweight synthetic contract fixtures for the EV95 wide adapter."""
import unittest
import wide_build_common as common

class WideAcceptanceContract(unittest.TestCase):
    def test_gate_set_is_exactly_the_reviewed_seventeen(self):
        self.assertEqual(len(common.GATES),17)
        self.assertIn('retained_499_windows_halo2_and_focus_exact',common.GATES)
        self.assertIn('unknown_P_preserved',common.GATES)

    def test_receipt_pins_are_specific_full_composition(self):
        self.assertEqual(common.COMPOSITION_SHA,'db732d229c0d7c13961355ca80e704a2bfe3fede5ac3eef2d01c80af065b0c67')
        self.assertEqual(common.WIDE_CANDIDATE_SHA,'40c174e31c8a3bf44855dad72e53a7a5e0a26f41a1fbac0afc74a98d1513c58a')
        self.assertNotEqual(common.WIDE_CANDIDATE_SHA,common.FOCAL_SHA)

    def test_preview_isolated_and_nonpromotional(self):
        self.assertEqual(str(common.PREVIEW_MOD),r'P:\Mods\@DayZ_Baltic_EV95_WideBankPreviewV1')
        manifest=common.add_acceptance_manifest({}, {'composition_report_path':common.COMPOSITION,
            'composition_report_sha256':common.COMPOSITION_SHA,'composition_source_path':common.COMPOSER,
            'composition_source_sha256':common.COMPOSER_SHA,'consumer_report_path':common.CONSUMER_REPORT,
            'consumer_report_sha256':common.CONSUMER_REPORT_SHA,'consumer_source_path':common.CONSUMER,
            'consumer_source_sha256':common.CONSUMER_SHA,'base_candidate_sha256':common.FOCAL_SHA,
            'local_candidate_sha256':common.LOCAL_SHA,'candidate_path':common.WIDE_CANDIDATE,
            'candidate_sha256':common.WIDE_CANDIDATE_SHA,'changed_vertices':1,'changed_local_vs_focal':1})
        self.assertIn('open',manifest['status_scope'])
        self.assertIn('no promotion',manifest['status_scope'])

if __name__=='__main__': unittest.main()



