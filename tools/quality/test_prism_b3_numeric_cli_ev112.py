"""Negative public-CLI paths: no production input or candidate is used."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,unittest

HERE=Path(__file__).resolve().parent

class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.contract=self.root/'contract.json';self.absent=self.root/'never-created.p3d'

    def run_both(self,expected):
        for name in ('prism_b3_numeric_author_ev112.py','verify_prism_b3_numeric_ev112.py'):
            with self.subTest(script=name):
                output=self.root/name;cmd=[sys.executable,'-I',str(HERE/name),str(self.contract)]
                if name.startswith('verify'):cmd.append(str(self.absent))
                cmd.append(str(output));v=subprocess.run(cmd,capture_output=True,timeout=15)
                self.assertNotEqual(v.returncode,0)
                report=json.loads((output/'failure.json').read_bytes())
                self.assertEqual(report['status'],'INCONCLUSIVE' if name.startswith('verify') else 'INCONCLUSIVE_AUTHOR')
                self.assertIn(expected,report['reason']);self.assertFalse((output/'candidate.p3d').exists());self.assertFalse((output/'report.json').exists())

    def minimal(self):
        return dict(schema='B3D_NUMERIC_MLOD_V1',expected_counts=[9120,12160,1520],expected_changes=17)

    def all_pins(self):
        c=self.minimal();c['pins']={}
        for name in ('source','reference','witness','previous_report','original_result','prior_contract'):
            path=self.root/(name+'.json');path.write_bytes(b'{}');c[name]=str(path);c['pins'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        return c

    def save(self,c):self.contract.write_bytes(json.dumps(c).encode())

    def test_invalid_json_is_inconclusive(self):
        self.contract.write_bytes(b'{');self.run_both('Expecting property')

    def test_missing_contract_is_inconclusive(self):self.run_both('contract.json')

    def test_wrong_schema(self):
        self.save(dict(schema='wrong'));self.run_both('contract_schema')

    def test_wrong_production_counts(self):
        c=self.minimal();c['expected_counts']=[18,24,3];self.save(c);self.run_both('contract_schema')

    def test_unpinned_source(self):
        c=self.minimal();c.update(source='x',pins={});self.save(c);self.run_both('unpinned_source')

    def test_changed_pinned_input(self):
        c=self.all_pins();c['pins'][c['source']]='0'*64;self.save(c);self.run_both('input_changed:')

    def test_fake_self_consistent_prior_is_rejected(self):
        self.save(self.all_pins());self.run_both('prior_contract_identity')

    def test_existing_output_not_reused(self):
        self.save(self.all_pins());output=self.root/'existing';output.mkdir();marker=output/'keep';marker.write_bytes(b'unchanged')
        for name in ('prism_b3_numeric_author_ev112.py','verify_prism_b3_numeric_ev112.py'):
            cmd=[sys.executable,'-I',str(HERE/name),str(self.contract)]
            if name.startswith('verify'):cmd.append(str(self.absent))
            cmd.append(str(output));v=subprocess.run(cmd,capture_output=True,timeout=15)
            self.assertNotEqual(v.returncode,0);self.assertEqual(marker.read_bytes(),b'unchanged');self.assertEqual([p.name for p in output.iterdir()],['keep'])

if __name__=='__main__':unittest.main()
