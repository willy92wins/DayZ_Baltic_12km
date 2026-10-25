import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/vegetation'))
from eval_forest_boundary_probe_v31 import parse, judge


class ForestBoundaryProbe(unittest.TestCase):
    def setUp(self):
        self.survey_id = '36be520c-80f4-4479-8a6e-242119f92cbf'
        self.text = 'BALTIC_FOREST_BOUNDARY_V1;BalticTrial\nSURVEY;'+self.survey_id+'\nBEGIN;3\nP;0;2;0;0;10\nP;1;2;0;0;10\nP;2;2;0;0;11\nEND;3\n'
        self.doc = dict(objects=[dict(id=7, root_y=2, embed=.1, support_required=True)],
                        points=[dict(id=i, object_id=7, kind=k, x=100, z=12285) for i, k in enumerate(('root', 'support', 'margin'))])

    def test_complete_survey_is_only_sampled_clear(self):
        self.assertEqual(judge(self.doc, parse(self.text, 3, self.survey_id))['status'], 'SAMPLED_BOUNDARY_CLEAR')

    def test_missing_duplicate_nan_bad_bool_or_backwards_clock(self):
        for text in [self.text.replace('END;3', ''), self.text.replace('P;1;', 'P;0;'), self.text.replace('P;1;2;', 'P;1;nan;'), self.text.replace(';0;0;11', ';2;0;11'), self.text.replace(';0;0;11', ';0;0;9')]:
            with self.subTest(text=text), self.assertRaises(ValueError): parse(text, 3, self.survey_id)

    def test_floatation_root_and_sea_fail_independently(self):
        for before, after, kind in [('P;0;2;', 'P;0;1.98;', 'root'), ('P;1;2;', 'P;1;1.88;', 'support'), ('P;2;2;0;', 'P;2;2;1;', 'margin_water')]:
            result = judge(self.doc, parse(self.text.replace(before, after), 3, self.survey_id))
            self.assertEqual(result['status'], 'FAIL'); self.assertEqual(result['counts'][kind], 1)

    def test_missing_support_or_unknown_expectation_cannot_pass(self):
        for kind in ('margin', 'ignored'):
            doc = copy.deepcopy(self.doc); doc['points'][1]['kind'] = kind
            with self.assertRaises(ValueError): judge(doc, parse(self.text, 3, self.survey_id))

    def test_nonfinite_model_or_coordinate_rejected(self):
        for target, key in [('objects', 'embed'), ('points', 'x')]:
            doc = copy.deepcopy(self.doc); doc[target][0][key] = float('nan')
            with self.assertRaises(ValueError): judge(doc, parse(self.text, 3, self.survey_id))

    def test_log_from_another_survey_rejected(self):
        with self.assertRaises(ValueError): parse(self.text, 3, '46be520c-80f4-4479-8a6e-242119f92cbf')


if __name__ == '__main__': unittest.main()
