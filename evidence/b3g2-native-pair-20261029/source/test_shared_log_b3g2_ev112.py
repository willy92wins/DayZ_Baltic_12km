import copy,ctypes,json,os,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
import shared_log_b3g2_ev112 as s
import observe_contact_b3g2_ev112 as observer
import contact_b3g2_native_ev112 as consumer

GOLDEN=Path('E:/DayZ-Baltic-Build/shape-repair-20261025/b3g2-observer-inputs-20261029/golden.json')
MISSION=r'C:\fixture\BalticContactB3G2.BalticTrial'

class Classifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=s.load_golden(GOLDEN)
    def raw(self):return ('\n'.join('12:03:04.005  '+x.replace('$MISSION',MISSION) for x in self.g['lines'])+'\n').encode()
    def test_golden_from_archive(self):self.assertEqual(len(s.classify(self.raw(),self.g,MISSION)['known_diagnostics']),1)
    def test_actual_archive_header(self):
        import re
        raw=Path(self.g['archive']).read_bytes().decode('utf-8-sig')
        self.assertIsNotNone(re.search(r'started at .*\((\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) UTC\)',raw))
    def test_clean_and_warning(self):
        v=s.classify(b'12:03:04.005  SCRIPT (W): x\n',self.g,MISSION);self.assertEqual(len(v['warnings']),1);self.assertEqual(v['known_diagnostics'],[])
    def test_every_frame_mutation(self):
        rows=self.raw().splitlines()
        for i in range(len(rows)):
            with self.subTest(frame=i),self.assertRaises(ValueError):
                r=rows[:];r[i]+=b'x';s.classify(b'\n'.join(r),self.g,MISSION)
    def test_each_frame_missing(self):
        r=self.raw().splitlines()
        for i in range(len(r)):
            with self.subTest(frame=i),self.assertRaises(ValueError):s.classify(b'\n'.join(r[:i]+r[i+1:]),self.g,MISSION)
    def test_timestamp_mismatch(self):
        with self.assertRaisesRegex(ValueError,'timestamp'):s.classify(self.raw().replace(b'12:03:04.005',b'12:03:05.005',1),self.g,MISSION)
    def test_extra_frame(self):
        with self.assertRaises(ValueError):s.classify(self.raw().replace(b'    -----------------',b'    extra()\n12:03:04.005  SCRIPT    (E):    -----------------'),self.g,MISSION)
    def test_duplicate(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):s.classify(self.raw()*2,self.g,MISSION)
    def test_unknown_error(self):
        with self.assertRaisesRegex(ValueError,'unknown_script_error'):s.classify(self.raw()+b'SCRIPT (E): fail\n',self.g,MISSION)
    def test_compile(self):
        for line in (b"Can't compile mission init script",b'Formula too complex'):
            with self.subTest(line=line),self.assertRaisesRegex(ValueError,'mission_compile'):s.classify(line,self.g,MISSION)
    def test_foreign_mission(self):
        with self.assertRaisesRegex(ValueError,'frames'):s.classify(self.raw(),self.g,r'C:\other')
    def test_golden_tampering(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'golden.json';g=copy.deepcopy(self.g);g['lines'][2]+='x';p.write_text(json.dumps(g),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'derivation'):s.load_golden(p)

@unittest.skipUnless(os.name=='nt','Real Windows handles')
class SharedFiles(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory(prefix='b3g2-reader-');self.p=Path(self.t.name)/'log';self.p.write_bytes(b'42');self.k=s.kernel()
    def tearDown(self):self.t.cleanup()
    def writer(self,share):
        h=self.k.CreateFileW(str(self.p),0x40000000,share,None,3,0x80,None)
        self.assertNotEqual(h,s.wt.HANDLE(-1).value);return h
    def test_shared_writer_remains_open(self):
        h=self.writer(1)
        try:
            raw,m=s.snapshot(self.p);self.assertEqual(raw,b'42');s.metadata(raw,m)
            self.assertEqual(s.info(self.k,h)['file_id'],m['file_id'])
        finally:self.k.CloseHandle(h)
    def test_exclusive_writer(self):
        h=self.writer(0)
        try:
            with self.assertRaises(OSError):s.snapshot(self.p)
        finally:self.k.CloseHandle(h)
    def test_empty(self):self.p.write_bytes(b'');raw,m=s.snapshot(self.p);self.assertEqual(raw,b'');s.metadata(raw,m)
    def test_oversize(self):
        with self.p.open('wb') as f:f.truncate(s.LIMIT+1)
        with self.assertRaisesRegex(ValueError,'snapshot_size'):s.snapshot(self.p)
    def test_stable(self):s.stable_pair(s.snapshot(self.p),s.snapshot(self.p))
    def test_filetime_integer_conversion(self):
        self.assertEqual(s.stamp(134377084422916728),'2026-10-29T00:47:22.291672+00:00')
    def test_timestamp_tampering(self):
        raw,m=s.snapshot(self.p);m['last_write_filetime']=m['checked_filetime']+100
        m['last_write_utc']=s.stamp(m['last_write_filetime'])
        with self.assertRaisesRegex(ValueError,'snapshot_times'):s.metadata(raw,m)
    def test_append_between(self):
        a=s.snapshot(self.p)
        with self.p.open('ab') as f:f.write(b'3')
        with self.assertRaisesRegex(ValueError,'not_stable'):s.stable_pair(a,s.snapshot(self.p))
    def test_replace_between(self):
        a=s.snapshot(self.p);other=self.p.with_name('other');other.write_bytes(b'42');os.replace(other,self.p)
        with self.assertRaisesRegex(ValueError,'file_changed'):s.stable_pair(a,s.snapshot(self.p))
    def test_shrink_during(self):
        actual=s.info;n=[0]
        def info(k,h):
            out=actual(k,h);n[0]+=1
            if n[0]==1:self.p.write_bytes(b'')
            return out
        with patch.object(s,'info',info),self.assertRaisesRegex(ValueError,'short_read'):s.snapshot(self.p)
    def test_append_during(self):
        actual=s.info;n=[0]
        def info(k,h):
            out=actual(k,h);n[0]+=1
            if n[0]==1:
                with self.p.open('ab') as f:f.write(b'3')
            return out
        with patch.object(s,'info',info):a=s.snapshot(self.p)
        self.assertTrue(a[1]['grew_during_read']);self.assertEqual(a[0],b'42')
        with self.assertRaises(ValueError):s.stable_pair(a,s.snapshot(self.p))

@unittest.skipUnless(os.name=='nt','Windows observer')
class Observer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=s.load_golden(GOLDEN)
    def setUp(self):
        import psutil
        self.t=tempfile.TemporaryDirectory(prefix='b3g2-observer-');self.root=Path(self.t.name)/'out';self.root.mkdir();self.profiles=Path(self.t.name)/'profiles';self.profiles.mkdir()
        self.host=dict(pid=os.getpid(),created_utc=datetime.fromtimestamp(psutil.Process().create_time(),timezone.utc).isoformat(),profiles=str(self.profiles),run_id='fixture',mission_path=MISSION,profile_filesystem='NTFS')
        self.ready=s.now();self.script=self.profiles/'script_2026-10-29_00-00-00.log'
        self.script.write_text('Log started at local ('+datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')+' UTC)\n',encoding='utf-8')
        self.native=self.profiles/'baltic_contact_b3g.log';self.native.write_text('BALTIC_CONTACT_B3G;BalticTrial\n'+'Q;fixture\n'*270+'END;270\n',encoding='utf-8')
        observer.save(self.root,'host-identity.json',self.host);observer.save(self.root,'deployment.json',dict(golden=str(GOLDEN),inputs={str(GOLDEN):s.digest(GOLDEN.read_bytes())}))
    def tearDown(self):self.t.cleanup()
    def consume(self):return consumer.snapshots(self.root,self.host,observer.read(self.root/'capture-window.json'),self.g)
    def test_complete_first_poll_consumer(self):
        self.assertEqual(observer.observe(self.root,self.ready)['status'],'CAPTURED_NOT_JUDGED');self.consume()
    def test_known_diagnostic_preserved(self):
        with self.script.open('ab') as f:f.write(Classifier.raw(self))
        observer.observe(self.root,self.ready);self.assertEqual(len(self.consume()[1]['known_diagnostics']),1)
    def test_missing_native(self):self.native.unlink();self.assertEqual(observer.observe(self.root,self.ready)['status'],'PENDING_NATIVE_LOG')
    def test_growing_no_end(self):
        self.native.write_text('BALTIC_CONTACT_B3G;BalticTrial\nQ;fixture\n',encoding='utf-8')
        self.assertEqual(observer.observe(self.root,self.ready)['status'],'PENDING_SAMPLES');self.assertFalse((self.root/'native.log').exists())
    def test_native_empty_or_header_prefix(self):
        for raw in (b'',b'BALTIC_CONTACT_B3'):
            self.native.write_bytes(raw)
            self.assertEqual(observer.observe(self.root,self.ready)['status'],'PENDING_SAMPLES')
    def test_native_bad_header_blocks(self):
        self.native.write_bytes(b'FOREIGN')
        with self.assertRaisesRegex(ValueError,'native_header'):observer.observe(self.root,self.ready)
    def test_failure_not_overwritten(self):
        observer.save(self.root,'script-failure.json',dict(original=True))
        with self.assertRaisesRegex(ValueError,'script_failure_present'):observer.observe(self.root,self.ready)
        self.assertEqual(observer.read(self.root/'script-failure.json'),dict(original=True))
    def test_pid_foreign(self):
        self.host['created_utc']='2000-01-01T00:00:00Z';(self.root/'host-identity.json').write_text(json.dumps(self.host))
        with self.assertRaisesRegex(ValueError,'process_identity'):observer.observe(self.root,self.ready)
    def test_expired(self):
        with self.assertRaisesRegex(ValueError,'deadline'):observer.observe(self.root,(s.utc(s.now())-timedelta(seconds=181)).isoformat())
    def test_compile_error_archived(self):
        with self.script.open('ab') as f:f.write(b'Formula too complex\n')
        with self.assertRaisesRegex(ValueError,'compile'):observer.observe(self.root,self.ready)
        self.assertTrue((self.root/'script-failure.log').exists());self.assertFalse((self.root/'native.log').exists())
    def test_old_header(self):
        self.script.write_text('Log started at local (2000-01-01 00:00:00 UTC)\n')
        with self.assertRaisesRegex(ValueError,'header_time'):observer.observe(self.root,self.ready)
    def test_partial_error_line(self):
        with self.script.open('ab') as f:f.write(b'12:03:04.005  SCRIPT (E')
        with self.assertRaisesRegex(ValueError,'incomplete_line'):observer.observe(self.root,self.ready)
        self.assertFalse((self.root/'native.log').exists())
    def test_profile_trailing_separator(self):
        self.host['profiles']+=os.sep;(self.root/'host-identity.json').write_text(json.dumps(self.host))
        observer.observe(self.root,self.ready);self.consume()
    def test_second_snapshot_changed(self):
        actual=s.snapshot;n=[0]
        def snapshot(p):
            if Path(p)==self.native:
                n[0]+=1
                if n[0]==2:
                    with self.native.open('ab') as f:f.write(b'extra\n')
            return actual(p)
        with patch.object(s,'snapshot',snapshot),self.assertRaisesRegex(ValueError,'not_stable'):observer.observe(self.root,self.ready)
        self.assertFalse((self.root/'native.log').exists())
    def test_consumer_reclassifies(self):
        observer.observe(self.root,self.ready);p=self.root/'script-at-capture.log';raw=p.read_bytes()+b'SCRIPT (E): extra\n';p.write_bytes(raw)
        m=observer.read(self.root/'script-at-capture.json');m.update(sha256=s.digest(raw),bytes=len(raw),size=len(raw));(self.root/'script-at-capture.json').write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'unknown_script_error'):self.consume()
    def test_consumer_ids(self):
        observer.observe(self.root,self.ready);p=self.root/'native-snapshots.json';m=observer.read(p);m['second']['file_id'][1]+=1;p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'file_changed'):self.consume()
    def test_reused_capture(self):
        observer.observe(self.root,self.ready)
        with self.assertRaisesRegex(ValueError,'consumed'):observer.observe(self.root,self.ready)

if __name__=='__main__':unittest.main()
