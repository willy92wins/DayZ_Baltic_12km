"""Closed-form controls, not production transformation snapshots."""
from pathlib import Path
import hashlib,json,unittest
from fractions import Fraction
import numpy as np
from author_ev92 import energy_moments,scalar_rule

class AnalyticRuleTests(unittest.TestCase):
    def test_single_spike_closed_form(self):
        b=np.zeros((5,5),dtype=np.float32);h=b.copy();b[2,2]=4;h[2,2]=1
        q=energy_moments(b,h,[('xx',2,1)])
        self.assertEqual(q,[Fraction(64),Fraction(-96),Fraction(36)])
        r=scalar_rule(b,h,[('xx',2,1)],focus=(2,2))
        self.assertAlmostEqual(r['materiality_lower'],1/3,places=15)
        self.assertAlmostEqual(r['alpha'],2/3,places=15)
        self.assertEqual(np.float32(4+r['alpha']*(1-4)),2)

    def test_mixed_derivative_weight_is_two(self):
        b=np.zeros((3,3),dtype=np.float32);b[0,0]=4;h=np.zeros_like(b)
        self.assertEqual(energy_moments(b,h,[('xz',0,0)]),[Fraction(2),Fraction(-4),Fraction(2)])

    def test_unchanged_direction_rejected(self):
        b=np.zeros((5,5),dtype=np.float32);b[2,2]=4
        with self.assertRaises(ValueError):scalar_rule(b,b,[('xx',2,1)],focus=(2,2))

    def test_energy_worsening_direction_rejected(self):
        b=np.zeros((5,5),dtype=np.float32);b[2,2]=4;h=b.copy();h[2,2]=5
        with self.assertRaises(ValueError):scalar_rule(b,h,[('xx',2,1)],focus=(2,2))

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(AnalyticRuleTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    source=Path(__file__).with_name('author_ev92.py')
    Path(__file__).with_name('author-fixtures.json').write_text(json.dumps({
        'pass':result.wasSuccessful(),'tests':result.testsRun,
        'author_sha256':hashlib.sha256(source.read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
