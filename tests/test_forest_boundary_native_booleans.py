"""Consumer boolean spellings from captured DayZ 1.30 output, not hand-made 0/1."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/vegetation'))
from eval_forest_boundary_probe_v31 import parse

RAW=ROOT/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/boundary-recheck-20261024/results/boundary-probe.log'
ID='36be520c-80f4-4479-8a6e-242119f92cbf'


def native_fields():
    # This is a projection of the actual older diagnostic capture into the
    # boundary schema; it is not presented as a new native boundary run.
    with RAW.open() as stream:
        next(stream);next(stream)
        source=[next(stream).strip().split(';') for _ in range(2)]
    rows=[';'.join(['P',str(i),fields[2],fields[3],fields[4],fields[19]]) for i,fields in enumerate(source)]
    return '\n'.join(['BALTIC_FOREST_BOUNDARY_V1;BalticTrial','SURVEY;'+ID,'BEGIN;2',*rows,'END;2'])


class ForestNativeBooleans(unittest.TestCase):
    def test_actual_native_true_false_are_read_without_coercion(self):
        rows=parse(native_fields(),2,ID)
        self.assertTrue(rows[0]['sea']);self.assertFalse(rows[0]['pond'])
        self.assertFalse(rows[1]['sea']);self.assertFalse(rows[1]['pond'])

    def test_non_native_boolean_aliases_are_rejected(self):
        text=native_fields()
        for value in ('1','0','True','yes','', ' true'):
            with self.subTest(value=value),self.assertRaises(ValueError):
                parse(text.replace(';true;', ';'+value+';',1),2,ID)


if __name__=='__main__':unittest.main()
