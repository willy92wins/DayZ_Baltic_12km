"""Real retained-handle controls; no DayZ process or MCP ownership is inferred."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,tempfile,unittest

SCRIPT=Path(__file__).resolve().parents[1]/'tools/navigation/observe_owned_server_exit.ps1'

@unittest.skipUnless(os.name=='nt','Windows process observer')
class ServerExitObserverTests(unittest.TestCase):
    def exercise(self,case):
        with tempfile.TemporaryDirectory(prefix='baltic-exit-test-') as temp:
            out=Path(temp)/'capture'
            # Windows PowerShell must discover its own native modules. A Python
            # hop otherwise preserves the parent's PowerShell 7 module path.
            ps_env={k:v for k,v in os.environ.items() if k.casefold()!='psmodulepath'}
            expected_exit=-1 if case=='exit_negative' else 23
            child=subprocess.Popen([sys.executable,'-I','-c',f'import time,sys;time.sleep(4);sys.exit({expected_exit})'],creationflags=0x08000000)
            try:
                stamp=subprocess.check_output(['powershell','-NoProfile','-Command',f"(Get-Process -Id {child.pid}).StartTime.ToUniversalTime().ToString('o')"],env=ps_env).decode().strip()
                born=datetime.datetime.fromisoformat(stamp.replace('Z','+00:00'))
                if case=='wrong_creation':born+=datetime.timedelta(seconds=20)
                executable=sys.executable+'.wrong' if case=='wrong_executable' else sys.executable
                limit='1' if case=='timeout' else '18300' if case=='exit_extended' else '10'
                q=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(SCRIPT),'-TargetProcessId',str(child.pid),'-ExpectedStartUtc',born.isoformat(),'-ExpectedExecutable',executable,'-OutputDirectory',str(out),'-MaxSeconds',limit,'-IntervalMilliseconds','100'],env=ps_env,capture_output=True,timeout=15)
                self.assertTrue((out/'terminal.json').is_file(),(q.returncode,q.stdout.decode(errors='replace'),q.stderr.decode(errors='replace')))
                terminal=json.loads((out/'terminal.json').read_text())
                if case in ('wrong_creation','wrong_executable'):
                    error='IDENTITY_MISMATCH' if case=='wrong_creation' else 'EXECUTABLE_MISMATCH'
                    self.assertEqual(q.returncode,1);self.assertEqual(terminal['status'],'OBSERVER_ERROR');self.assertIn(error,terminal['error']);self.assertFalse((out/'attached.json').exists());self.assertIsNone(child.poll())
                else:
                    attached=json.loads((out/'attached.json').read_text());self.assertTrue(attached['handle_retained']);self.assertFalse(attached['mutation_attempted']);self.assertEqual(attached['process_id'],child.pid)
                    self.assertEqual(attached['observer_sha256'],terminal['observer_sha256'])
                    self.assertEqual(attached['observer_sha256'],hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
                    if case in ('exit23','exit_negative','exit_extended'):self.assertEqual(q.returncode,0);self.assertEqual(terminal['status'],'EXIT_OBSERVED');self.assertEqual(terminal['exit_code'],expected_exit)
                    else:self.assertEqual(q.returncode,2);self.assertEqual(terminal['status'],'OBSERVER_TIMEOUT');self.assertIsNone(terminal['exit_code']);self.assertIsNone(child.poll())
            finally:self.assertEqual(child.wait(timeout=15),expected_exit & 0xffffffff)
    def test_captures_real_exit_code(self):self.exercise('exit23')
    def test_captures_signed_negative_exit_code(self):self.exercise('exit_negative')
    def test_wrong_creation_is_rejected(self):self.exercise('wrong_creation')
    def test_wrong_executable_is_rejected(self):self.exercise('wrong_executable')
    def test_timeout_does_not_terminate_process(self):self.exercise('timeout')
    def test_extended_budget_observes_actual_exit(self):self.exercise('exit_extended')

    def test_budget_above_cap_rejected_before_observation(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'capture'
            q=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(SCRIPT),'-TargetProcessId','1','-ExpectedStartUtc','2026-10-27T00:00:00Z','-ExpectedExecutable',sys.executable,'-OutputDirectory',str(out),'-MaxSeconds','18301'],capture_output=True,timeout=15)
            self.assertNotEqual(q.returncode,0)
            self.assertFalse(out.exists())
            self.assertIn('18300',q.stderr.decode(errors='replace'))

if __name__=='__main__':unittest.main()
