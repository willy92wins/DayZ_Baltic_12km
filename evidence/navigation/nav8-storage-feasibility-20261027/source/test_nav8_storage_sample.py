"""Bounded header-reader controls, not a complete-format test suite."""
from pathlib import Path
import importlib.util,json,mmap,struct,unittest
R=Path(__file__).parent
s=importlib.util.spec_from_file_location('sample',R/'inspect_nav8_storage_sample.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class TestHeaderSample(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=R/m.ARTIFACTS[0][1]
  with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
   count=struct.unpack_from('<I',data,8)[0];base=48+count*4
   a=base+struct.unpack_from('<I',data,48)[0];b=base+struct.unpack_from('<I',data,52)[0]
   header=bytearray(data[:48]);struct.pack_into('<3I',header,8,1,1,1);struct.pack_into('<I',header,40,1)
   cls.fixture=header+struct.pack('<I',0)+data[a:b]
 def test_real_payload_in_single_tile_envelope(self):
  r=m.tile_header(self.fixture,0)
  self.assertEqual((r['polygons'],r['vertices'],r['length'],r['tail_bytes']),(4,10,908,556))
 def test_truncated_header(self):
  with self.assertRaises(ValueError):m.tile_header(b'\0'*20,0)
 def test_wrong_outer_version(self):
  b=bytearray(self.fixture);struct.pack_into('<I',b,4,6)
  with self.assertRaises(ValueError):m.tile_header(b,0)
 def test_wrong_tile_version(self):
  b=bytearray(self.fixture);struct.pack_into('<I',b,52+16+4,7)
  with self.assertRaises(ValueError):m.tile_header(b,0)
 def test_truncated_payload(self):
  with self.assertRaises(ValueError):m.tile_header(self.fixture[:-1],0)
 def test_bad_offset(self):
  b=bytearray(self.fixture);struct.pack_into('<I',b,48,0xffffffff)
  with self.assertRaises(ValueError):m.tile_header(b,0)
 def test_count_overflow_beyond_payload(self):
  b=bytearray(self.fixture);struct.pack_into('<I',b,52+16+7*4,0xffffffff)
  with self.assertRaises(ValueError):m.tile_header(b,0)

if __name__=='__main__':unittest.main()
