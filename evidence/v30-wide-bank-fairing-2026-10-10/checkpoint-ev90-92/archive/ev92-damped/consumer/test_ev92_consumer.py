"""Small in-memory EV92 fixtures; never writes an H92 candidate or runs gates."""
import copy
import json
from pathlib import Path
import unittest
from types import SimpleNamespace

import numpy as np

import verify_ev92 as ev


class EV92ConsumerFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared=json.loads(ev.PREPARED.read_text(encoding='utf-8'))
        cls.parent_prepared=json.loads(ev.PARENT_PREP.read_text(encoding='utf-8'))
        cls.base=ev.load_npz(ev.BASE)
        cls.direction=ev.load_npz(ev.DIRECTION)
        cls.rule=ev.derive_scalar_rule(cls.base['heights'],cls.direction['heights'],cls.prepared['stencils'])
        cls.alpha=ev.validate_alpha_metadata(cls.prepared,cls.rule)

    def test_pinned_prepared_and_rule(self):
        self.assertTrue(ev.validate_prepared(self.prepared,self.parent_prepared))
        self.assertEqual(self.alpha,0.6769237551186755)
        self.assertEqual(self.prepared['scalar_rule'],self.rule)
        keys,digest=ev.pinned_gate_keys()
        self.assertEqual(len(keys),27)
        self.assertEqual(digest,ev.EXPECTED_GATE_KEYS_SHA)

    def test_exact_one_cast_interpolation_in_memory(self):
        expected=ev.expected_interpolation(self.base['heights'],self.direction['heights'],self.alpha)
        candidate={k:(expected if k=='heights' else v.copy()) for k,v in self.base.items()}
        reconstructed,changed=ev.validate_candidate_arrays(self.base,self.direction,candidate,self.alpha)
        self.assertTrue(np.array_equal(reconstructed,expected))
        self.assertEqual(changed,int(np.count_nonzero(expected!=self.base['heights'])))
        self.assertGreater(changed,0)
        self.assertFalse(ev.CANDIDATE.exists(),'fixture must not write an EV92 candidate')

    def test_metadata_and_formula_negatives_fail_closed(self):
        bad=copy.deepcopy(self.prepared)
        bad['source_pins'][str(ev.BASE)]='0'*64
        with self.assertRaises(AssertionError):ev.validate_prepared(bad,self.parent_prepared)
        bad=copy.deepcopy(self.prepared)
        bad['alpha']=float(np.nextafter(self.alpha,1.0))
        with self.assertRaises(AssertionError):ev.validate_alpha_metadata(bad,self.rule)
        bad=copy.deepcopy(self.prepared)
        bad['solver']['calls']=1
        with self.assertRaises(AssertionError):ev.validate_alpha_metadata(bad,self.rule)
        expected=ev.expected_interpolation(self.base['heights'],self.direction['heights'],self.alpha)
        wrong=expected.copy();wrong[840,370]=np.nextafter(wrong[840,370],np.float32(np.inf))
        candidate={k:(wrong if k=='heights' else v.copy()) for k,v in self.base.items()}
        with self.assertRaises(AssertionError):ev.validate_candidate_arrays(self.base,self.direction,candidate,self.alpha)
        if set(self.base)-{'heights'}:
            candidate={k:v.copy() for k,v in self.base.items()}
            key=next(iter(set(self.base)-{'heights'}))
            if candidate[key].dtype==np.bool_:
                candidate[key].flat[0]=not bool(candidate[key].flat[0])
            else:
                candidate[key].flat[0]=candidate[key].flat[0]+1
            with self.assertRaises(AssertionError):ev.validate_candidate_arrays(self.base,self.direction,candidate,self.alpha)

    def _adapter_engine(self):
        marker=object()
        def validator(*args):return {'authenticated':marker,'candidate_path':'H91','candidate_sha256':'H91sha','changed_vertices':1}
        engine=SimpleNamespace(verify_authoring_receipt=validator,
            WET_DIAGNOSTIC_PATH=ev.EV91_CONSUMER.parent/'runs/ev91-eligible-wet-support-diagnostic.json',
            HERE=ev.EV91_CONSUMER.parent,RECEIPT=ev.PARENT_RECEIPT,CANDIDATE=ev.DIRECTION)
        return engine,validator,marker

    def test_adapter_restores_bindings_after_success_and_exception(self):
        for raise_inside in (False,True):
            engine,validator,marker=self._adapter_engine()
            old_sidecar=engine.WET_DIAGNOSTIC_PATH
            with self.assertRaisesRegex(RuntimeError,'fixture') if raise_inside else _NoRaise():
                with ev.explicit_ev91_projection(engine,ev.RECEIPT,ev.CANDIDATE,
                        {'candidate_sha256':'candidate-sha'},self.prepared,self.rule,123) as info:
                    projected=engine.verify_authoring_receipt(ev.RECEIPT,ev.CANDIDATE,self.prepared)
                    self.assertIs(projected['authenticated'],marker)
                    self.assertEqual(projected['candidate_path'],str(ev.CANDIDATE.resolve()))
                    self.assertEqual(projected['candidate_sha256'],'candidate-sha')
                    self.assertEqual(projected['changed_vertices'],123)
                    self.assertTrue(info['restored_in_finally'])
                    if raise_inside:raise RuntimeError('fixture')
            self.assertIs(engine.verify_authoring_receipt,validator)
            self.assertEqual(engine.WET_DIAGNOSTIC_PATH,old_sidecar)


class _NoRaise:
    def __enter__(self):return self
    def __exit__(self,*args):return False


if __name__=='__main__':unittest.main(verbosity=2)
