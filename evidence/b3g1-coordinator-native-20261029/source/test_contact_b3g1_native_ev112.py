import copy,json,os,subprocess,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
import contact_b3g1_native_ev112 as n

class Health(unittest.TestCase):
    def args(self):
        return [b'Log started at local (2026-10-29 00:00:00 UTC)\nSCRIPT (I) ready\n',
                r'C:\profiles\script_2026-10-29_00-00-00.log',
                dict(profiles=r'C:\profiles',created_utc='2026-10-29T00:00:00Z'),
                '2026-10-29T00:00:01Z','2026-10-29T00:00:02Z','2026-10-29T00:00:03Z']
    def test_valid(self):self.assertEqual(n.script_health(*self.args())['status'],'FRESH_SCRIPT_WITHOUT_RECORDED_ERROR')
    def test_invalid(self):
        mutations=[(0,b'bad'),(0,b'\xff'),(0,b'x'*(20*1024**2+1)),(1,r'C:\foreign\script_2026-10-29_00-00-00.log'),(1,r'C:\profiles\other.log'),(3,'2026-10-28T23:59:59Z'),(4,'2026-10-29T00:00:04Z')]
        for i,v in mutations:
            with self.subTest(i=i,v=str(v)[:50]),self.assertRaises((ValueError,UnicodeError)):
                a=self.args();a[i]=v;n.script_health(*a)
    def test_compile_error(self):
        for text in (b'SCRIPT (E) Formula too complex',b"Can't compile mission init script"):
            a=self.args();a[0]+=text
            with self.assertRaisesRegex(ValueError,'native_script_error'):n.script_health(*a)
    def test_wrong_header_time(self):
        a=self.args();a[0]=a[0].replace(b'00:00:00',b'00:00:59')
        with self.assertRaisesRegex(ValueError,'script_header_time'):n.script_health(*a)
    def test_non_ascii_noise_does_not_hide_error(self):
        a=self.args();a[0]+=b'path: caf\xe9\nSCRIPT (E) failed\n'
        with self.assertRaisesRegex(ValueError,'native_script_error'):n.script_health(*a)

class Continuity(unittest.TestCase):
    def args(self):
        def t(s):return '2026-10-29T00:00:'+str(s).zfill(2)+'Z'
        w=dict(ready_utc=t(1),capture_deadline_utc='2026-10-29T00:03:01Z',capture_started_utc=t(2),capture_ended_utc=t(32))
        return [dict(run_id='own'),w,dict(run_id='own',ready_utc=t(1),capture_deadline_utc=w['capture_deadline_utc']),dict(run_id='own',status='OWN_RUN_ADOPTED',at=t(0)),dict(failure=None,events=[dict(at=t(s),ok=True) for s in (0,15,30)]),dict(closed_utc=t(33),heartbeat_ended_utc=t(33)),dict(run_id='own',status='CAPTURED_PENDING_CONSUMER')]
    def test_valid(self):n.continuity(*self.args())
    def test_negative(self):
        for i,k,v in ((2,'run_id','foreign'),(2,'ready_utc','2026-10-29T00:00:02Z'),(4,'failure','failed'),(4,'events',[]),(6,'status','FAILED_CLEANUP'),(5,'closed_utc','2026-10-29T00:00:00Z')):
            a=self.args();a[i][k]=v
            with self.subTest(key=k),self.assertRaises(ValueError):n.continuity(*a)
    def test_gap(self):
        a=self.args();del a[4]['events'][1]
        with self.assertRaisesRegex(ValueError,'heartbeat_gap'):n.continuity(*a)

@unittest.skipUnless(os.name=='nt','PowerShell host integration')
class Observer(unittest.TestCase):
    def fixture(self,error=False):
        # Use this test process's identity, never a DayZ process or shared profile.
        import psutil
        birth=datetime.fromtimestamp(psutil.Process().create_time(),timezone.utc)
        now=datetime.now(timezone.utc);t=tempfile.TemporaryDirectory(prefix='b3g1-observer-');root=Path(t.name)
        profiles=root/'profiles';profiles.mkdir();out=root/'receipt';out.mkdir()
        script=profiles/'script_2026-10-29_00-00-00.log'
        script.write_text('Log started at local ('+now.strftime('%Y-%m-%d %H:%M:%S')+' UTC)\n'+('SCRIPT (E) Formula too complex\n' if error else 'SCRIPT (I) ready\n'),encoding='utf-8')
        (profiles/'baltic_contact_b3g.log').write_text('BALTIC_CONTACT_B3G;BalticTrial\n'+'Q;fixture\n'*270+'END;270\n',encoding='utf-8')
        (out/'host-identity.json').write_text(json.dumps(dict(pid=os.getpid(),created_utc=birth.isoformat(),profiles=str(profiles),run_id='fixture')),encoding='utf-8')
        ready=now.isoformat();scriptpath=Path(__file__).with_name('observe_contact_b3g1.ps1')
        result=subprocess.run(['powershell','-NoProfile','-ExecutionPolicy','Bypass','-File',str(scriptpath),'-Directory',str(out),'-ReadyUtc',ready],capture_output=True,timeout=15)
        return t,out,result
    def test_complete_on_first_observation(self):
        t,out,r=self.fixture()
        try:
            self.assertEqual(r.returncode,0,r.stderr.decode(errors='replace'))
            w=json.loads((out/'capture-window.json').read_bytes());p=json.loads((out/'script-at-capture.json').read_bytes());h=json.loads((out/'host-identity.json').read_bytes())
            self.assertGreaterEqual(n.delta.utc(p['checked_utc']),n.delta.utc(w['capture_started_utc']))
            n.script_health((out/'script-at-capture.log').read_bytes(),p['source'],h,w['script_created_utc'],p['last_write_utc'],p['checked_utc'])
        finally:t.cleanup()
    def test_error_never_captured(self):
        t,out,r=self.fixture(True)
        try:
            self.assertNotEqual(r.returncode,0);self.assertFalse((out/'native.log').exists());self.assertTrue((out/'script-failure.log').exists())
        finally:t.cleanup()

if __name__=='__main__':unittest.main()
