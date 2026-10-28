from pathlib import Path
import copy,json,tempfile,unittest
import collision_b2_replay_binding_ev112 as b


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name);old=root/'old';old.mkdir()
        self.inputs={};self.archives={};self.new={}
        for name in sorted(b.SUPERSEDED):
            p=root/name;a=old/name;a.write_bytes(b'old-source');p.write_bytes(b'new-source')
            self.inputs[str(p)]=b.sha(a);self.archives[str(p)]=dict(path=str(a),sha256=b.sha(a));self.new[str(p)]=b.sha(p)
        p=root/'native.log';p.write_bytes(b'untouched native8');self.inputs[str(p)]=b.sha(p);self.native=p

    def test_exact_supersession(self):b.verify_superseded(self.inputs,self.archives,self.new)

    def test_capture_or_other_historical_input_drift(self):
        self.native.write_bytes(b'coerced native2')
        with self.assertRaisesRegex(ValueError,'historical_input_drift'):b.verify_superseded(self.inputs,self.archives,self.new)

    def test_old_source_drift(self):
        Path(next(iter(self.archives.values()))['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'historical_source_drift'):b.verify_superseded(self.inputs,self.archives,self.new)

    def test_new_source_drift(self):
        Path(next(iter(self.new))).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'replay_source_drift'):b.verify_superseded(self.inputs,self.archives,self.new)

    def test_no_extra_exceptions(self):
        a=copy.deepcopy(self.archives);n=dict(self.new);a[str(self.native)]=dict(path=str(self.native),sha256=b.sha(self.native));n[str(self.native)]=b.sha(self.native)
        with self.assertRaisesRegex(ValueError,'supersession_scope'):b.verify_superseded(self.inputs,a,n)

    def test_wrong_historical_hash(self):
        a=copy.deepcopy(self.archives);next(iter(a.values()))['sha256']='f'*64
        with self.assertRaisesRegex(ValueError,'historical_source_drift'):b.verify_superseded(self.inputs,a,self.new)

    def test_run_receipt_and_new_code_must_be_externally_sealed(self):
        root=Path(self.temp.name);receipt=root/'receipt.json';receipt.write_text('{}')
        helper=str(Path(b.__file__))
        inputs={str(receipt):b.sha(receipt),helper:b.sha(helper),**self.new}
        for omitted in (str(receipt),helper,next(iter(self.new))):
            pins=dict(inputs);pins.pop(omitted)
            a=dict(status='B2_REPLAY_READY',receipt=str(receipt),inputs=pins,new_sources=self.new)
            path=root/'accepted.json';path.write_text(json.dumps(a))
            with self.subTest(omitted=omitted),self.assertRaisesRegex(ValueError,'replay_manifest_unsealed'):b.replay(root,b.sha(path))


if __name__=='__main__':unittest.main()
