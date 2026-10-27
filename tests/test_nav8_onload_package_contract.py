"""Exercise packaging guards with independent tiny archives and fake external tools.

These are fault injections at the PBO/CfgConvert/FileBank boundary, not native
packaging evidence; the actual build must separately re-read every real entry.
"""
from pathlib import Path
from unittest import mock
from contextlib import redirect_stdout
import io
import json
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/navigation'))
import package_nav8_onload_config_ev112 as package

ORIGINAL = 'class CfgWorlds {class BalticTrial {class Navmesh {filterIsolatedIslandsOnLoad="true";class GenParams {tileWidth=8;filterIsolatedIslands="true";};};};};'
CHANGED = 'class CfgWorlds {class BalticTrial {class Navmesh {filterIsolatedIslandsOnLoad=1;class GenParams {tileWidth=8;filterIsolatedIslands="true";};};};};'


class PackageContract(unittest.TestCase):
    def exercise(self, fault=None):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); baseline = root/'baseline.pbo'; baseline.write_bytes(b'original archive')
            converter = root/'CfgConvert.exe'; converter.touch()
            filebank = root/'FileBank.exe'; filebank.touch()
            output = root/'output'
            config = b'\0raPbaseline'; candidate = b'\0raPcandidate'
            before = {'config.bin':config, 'baltic_trial.wrp':b'OPRWfixture', 'navmesh/baltic_trial.nm':b'NMfixture', 'texture.paa':b'preserved'}
            props = {'prefix':'dayz_baltic_12km_dev\\tb\\narva_trial', 'product':'dayz ugc'}
            raw = baseline.read_bytes(); wrp_hash = package.sha(before['baltic_trial.wrp']); nm_hash = package.sha(before['navmesh/baltic_trial.nm'])
            reads = []; commands = []

            def read_pbo(path):
                reads.append(str(path)); entries = dict(before); properties = dict(props)
                if Path(path) == baseline:
                    if fault == 'baseline_hash': return b'other archive', properties, entries
                    if fault == 'wrp_hash': entries['baltic_trial.wrp'] = b'other WRP'
                    if fault == 'nm_hash': entries['navmesh/baltic_trial.nm'] = b'other NM'
                    return raw, properties, entries
                entries['config.bin'] = candidate
                if fault == 'packed_extra': entries['extra.paa'] = b'extra'
                if fault == 'packed_geometry': entries['baltic_trial.wrp'] = b'changed geometry'
                if fault == 'packed_nm': entries['navmesh/baltic_trial.nm'] = b'changed nav'
                if fault == 'packed_props': properties['extra'] = 'unexpected'
                return b'packed archive', properties, entries

            def run(argv, **kwargs):
                commands.append(argv)
                dest = Path(argv[argv.index('-dst')+1])
                if Path(argv[0]) == filebank:
                    (dest/'narva_trial.pbo').write_bytes(b'packed archive')
                elif '-txt' in argv:
                    is_candidate = Path(argv[-1]).read_bytes() == candidate
                    content = CHANGED if is_candidate else ORIGINAL
                    if fault == 'packed_decode' and Path(argv[-1]).name == 'packed-config.bin': content = CHANGED.replace('tileWidth=8', 'tileWidth=9')
                    dest.write_text(content)
                elif dest.name == 'noop.bin':
                    self.assertEqual(Path(argv[-1]).name, 'noop-source.cpp')
                    self.assertEqual(Path(argv[-1]).read_text(), ORIGINAL)
                    dest.write_bytes(b'\0raPdifferent-null' if fault == 'null_binary' else config)
                else:
                    dest.write_bytes(b'not compiled' if fault == 'bad_candidate_prefix' else config if fault == 'unchanged_candidate' else candidate)
                return type('Result', (), {'returncode':0, 'stdout':b'', 'stderr':b''})()

            argv = ['pack', '--baseline', str(baseline), '--expected-sha256', package.sha(raw), '--wrp-sha256', wrp_hash, '--converter', str(converter), '--filebank', str(filebank), '--output', str(output)]
            with mock.patch.object(package, 'BASE_SHA', package.sha(raw)), mock.patch.object(package, 'WRP_SHA', wrp_hash), mock.patch.object(package, 'NM_SHA', nm_hash), mock.patch.object(package, 'read_pbo', side_effect=read_pbo), mock.patch.object(package.subprocess, 'run', side_effect=run), mock.patch.object(sys, 'argv', argv), redirect_stdout(io.StringIO()):
                if fault:
                    with self.assertRaises(ValueError): package.main()
                    self.assertFalse((output/'verification.json').exists())
                else:
                    package.main()
                    self.assertTrue((output/'verification.json').exists())
                    self.assertFalse(json.loads((output/'verification.json').read_text())['native_type_verified'])
                    self.assertEqual(len(reads), 2)
                    self.assertEqual(len([x for x in commands if Path(x[0]) == filebank]), 1)

    def test_successful_fixture(self): self.exercise()
    def test_wrong_baseline(self): self.exercise('baseline_hash')
    def test_wrong_wrp(self): self.exercise('wrp_hash')
    def test_wrong_nm(self): self.exercise('nm_hash')
    def test_null_compiler_difference(self): self.exercise('null_binary')
    def test_bad_candidate_prefix(self): self.exercise('bad_candidate_prefix')
    def test_unchanged_candidate(self): self.exercise('unchanged_candidate')
    def test_extra_entry(self): self.exercise('packed_extra')
    def test_changed_geometry(self): self.exercise('packed_geometry')
    def test_changed_nm(self): self.exercise('packed_nm')
    def test_extra_property(self): self.exercise('packed_props')
    def test_final_config_decoded_again(self): self.exercise('packed_decode')


if __name__ == '__main__': unittest.main()
