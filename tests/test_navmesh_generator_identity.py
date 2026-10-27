import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('generator',Path(__file__).resolve().parents[1]/'tools/navigation/generate_navmesh_console.py')
generator=importlib.util.module_from_spec(spec);spec.loader.exec_module(generator)


class NavmeshGeneratorIdentity(unittest.TestCase):
    def invoke(self,format_version=9,mutate_input=False,unknown_generator=False,wrong_pilot=False,returncode=0,payload='full',count=1,delete_input=False,timeout_s=10):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);exe=root/'generator.exe';exe.write_bytes(b'fixture-generator')
            files=[]
            for name in ('world','water','pilot'):
                p=root/(name+'.pbo');p.write_bytes(name.encode());files.append((p,generator.sha(p)))
            out=root/'output'
            args=['generator','--run-id','00000000-0000-4000-8000-000000000001',
                  '--world-pbo',str(files[0][0]),'--world-sha256',files[0][1],
                  '--water-pbo',str(files[1][0]),'--water-sha256',files[1][1],
                  '--additional-pbo',str(files[2][0]),'0'*64 if wrong_pilot else files[2][1],
                  '--out',str(out),'--timeout-s',str(timeout_s)]
            def child(argv,**kwargs):
                self.assertNotIn('--kill',argv)
                if payload=='full':Path(argv[-1]).write_bytes(struct.pack('<5I',0x4d534554,format_version,count,1,1)+bytes(28))
                elif payload=='short':Path(argv[-1]).write_bytes(b'TESM')
                if mutate_input:files[2][0].write_bytes(b'changed while generating')
                if delete_input:files[2][0].unlink()
                return type('Completed',(),{'returncode':returncode})()
            profiles={} if unknown_generator else {generator.sha(exe):9}
            with patch.object(generator,'GENERATOR',exe),patch.object(generator,'GENERATOR_FORMATS',profiles),patch.object(sys,'argv',args),patch.object(generator.subprocess,'run',side_effect=child) as run,contextlib.redirect_stdout(io.StringIO()):
                if unknown_generator or wrong_pilot or not 10<=timeout_s<=18000:
                    with self.assertRaises(ValueError):generator.main()
                    run.assert_not_called();return
                code=generator.main();result=json.loads((out/'generation.json').read_text())
            return code,result

    def test_success_is_file_pending_structure_and_engine_only(self):
        code,result=self.invoke()
        self.assertEqual(code,0)
        self.assertEqual(result['status'],'GENERATED_FILE_PENDING_STRUCTURAL_AND_ENGINE_VALIDATION')
        self.assertEqual(len(result['inputs']),3)

    def test_wrong_serialized_version_is_rejected(self):
        code,result=self.invoke(format_version=6)
        self.assertEqual(code,1);self.assertEqual(result['status'],'GENERATION_FAILED')

    def test_changed_pilot_during_generation_is_rejected(self):
        code,result=self.invoke(mutate_input=True)
        self.assertEqual(code,1);self.assertFalse(result['inputs_unchanged'])

    def test_unknown_generator_never_launches(self):self.invoke(unknown_generator=True)

    def test_wrong_pilot_identity_never_launches(self):self.invoke(wrong_pilot=True)

    def test_missing_input_still_finalizes_the_receipt(self):
        code,result=self.invoke(delete_input=True)
        self.assertEqual(code,1);self.assertEqual(result['status'],'POSTCHECK_FAILED')
        self.assertIn('finished_utc',result)

    def test_return_code_and_missing_or_short_output_reject(self):
        for options in (dict(returncode=1),dict(payload='absent'),dict(payload='short')):
            code,result=self.invoke(**options)
            self.assertEqual(code,1);self.assertEqual(result['status'],'GENERATION_FAILED')

    def test_unknown_v9_header_arithmetic_is_not_accepted(self):
        code,result=self.invoke(count=2)
        self.assertEqual(code,1);self.assertFalse(result['header_ok'])
        self.assertEqual(result['status'],'GENERATED_FILE_HEADER_LAYOUT_UNVERIFIED')

    def test_extended_generation_remains_bounded(self):
        self.assertEqual(self.invoke(timeout_s=7200)[0],0)
        self.assertEqual(self.invoke(timeout_s=18000)[0],0)
        self.invoke(timeout_s=18001)
        self.invoke(timeout_s=9)


if __name__=='__main__':unittest.main()
